#!/usr/bin/env python3
"""Facility-menu pre-rendered kanji strip patcher (v86).

Re-renders baked Japanese UI labels into English, in place, for the four
town-facility menu sheets:
  - R2141 (Salem temple)      69632 B : sub0 menu + aux donation/everyone
  - R2144 (Adventurer's Inn)  69632 B : sub0 menu + aux Room Fee
  - R2150 (Vigger shop)      147456 B : sub0 (17 labels) + s1/s2/s3 stats
  - R2153 (branch shop)      147456 B : sub0 (7 labels); s1/s2/s3 == R2150

All label sheets are 256x256 PSMT4, decoded with
  deswizzle_psmt4(payload, 256, 256, bw_psmt4=256, dbw_ct32=128)
over a 32768-byte pixel window. Pixel-blob file offsets ("offset" in the
labels JSON) are the strip-family flush-to-end bases verified with
tools/strip_patcher.find_pixel_base over each section table and confirmed
visually against build/recon_v86 evidence PNGs. (R2144 aux is 36400, not
36384 — 36384 renders misaligned; this is the formula base.)

Polarity:
  dark_bg   : transparent bg = index 0, ink high. Clear box -> render English
              with grayscale mapped onto a 0..15 ink ramp.
  parchment : dark ink (index ~1) on bright parchment (index 6..15). The
              kanji area is first IN-PAINTED with parchment texture sampled
              from the clean strip directly above/below the glyph rows
              (technique mirrors tools/patch_r2138.py overlay preservation),
              then English is stamped as dark ink only where the glyph is.

R2153 s1/s2/s3 are byte-identical to R2150's (cmp-verified in recon); after
patching R2150 the three patched 32768-byte windows are copied verbatim into
R2153 and asserted equal.

INPUTS  (pristine only — safe to re-run after build_v9 Step 6 purges the
         build/packdata_resources copies):
  extracted/packdata_raw/{2141_type02,2144_type02,2150_type05,2153_type05}.raw
OUTPUTS:
  build/packdata_resources/{2141_type02,2144_type02,2150_type05,2153_type05}.raw
DEBUG PNGs (before/after, 2x grayscale):
  build/recon_v86/facility-out/*.png

Exits nonzero on any assertion failure.
"""

import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))

from psmt4_deswizzle import deswizzle_psmt4, swizzle_psmt4

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

# ── Paths ──
IN_DIR = os.path.join(BASE, "extracted", "packdata_raw")
OUT_DIR = os.path.join(BASE, "build", "packdata_resources")
DEBUG_DIR = os.path.join(BASE, "build", "recon_v86", "facility-out")
LABELS_PATH = os.path.join(BASE, "data", "strip_labels", "facility_labels.json")

# ── Texture constants (all sheets) ──
TEX_W = TEX_H = 256
BW_PSMT4 = 256
DBW_CT32 = 128
WINDOW = TEX_W * TEX_H // 2          # 32768 bytes
PIX_COUNT = TEX_W * TEX_H            # 65536 indices

INK_MAX = 15
FONT_FLOOR = 9

# R2153 windows that duplicate R2150 (file offset -> length).
R2153_DUP_WINDOWS = [36384, 71008, 105616]


# ═══════════════════════════ font / rendering ═══════════════════════════

_font_cache = {}


def load_font(size):
    if size in _font_cache:
        return _font_cache[size]
    for fp in ("C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf"):
        if os.path.exists(fp):
            f = ImageFont.truetype(fp, size)
            break
    else:
        f = ImageFont.load_default()
    _font_cache[size] = f
    return f


def render_gray(text, w, h, start_size, align):
    """Render text into a w*h grayscale (0..255) cell, shrinking to fit."""
    size = start_size
    font = load_font(size)
    bbox = font.getbbox(text)
    while bbox and (bbox[2] - bbox[0]) > w - 2 and size > FONT_FLOOR:
        size -= 1
        font = load_font(size)
        bbox = font.getbbox(text)
    img = Image.new("L", (w, h), 0)
    if bbox:
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        if align == "left":
            ox = 1 - bbox[0]
        else:
            ox = max(0, (w - tw) // 2) - bbox[0]
        oy = max(0, (h - th) // 2) - bbox[1]
        ImageDraw.Draw(img).text((ox, oy), text, fill=255, font=font)
    return list(img.getdata()), size


# ═══════════════════════════ pixel helpers ═══════════════════════════

def desw(window):
    return bytearray(deswizzle_psmt4(bytes(window), TEX_W, TEX_H,
                                     bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32))


def resw(linear):
    return bytes(swizzle_psmt4(linear, TEX_W, TEX_H,
                               bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32))


def draw_dark_bg(linear, box, text, font_size, align):
    """Clear box to 0, stamp English with grayscale -> 0..15 ink ramp."""
    x, y, w, h = box
    gray, used = render_gray(text, w, h, font_size, align)
    for dy in range(h):
        row = (y + dy) * TEX_W
        for dx in range(w):
            g = gray[dy * w + dx]
            linear[row + x + dx] = (g * INK_MAX + 127) // 255
    return used


def inpaint_parchment(linear, box):
    """Fill a box with parchment texture sampled column-wise from the clean
    parchment rows just above and below the glyph band.

    For each column x in the box we collect the non-ink (index >= 4) parchment
    indices from a margin strip above and below the box, then fill every pixel
    of that column in the box by cycling through the sampled values. This
    reproduces the horizontal wrinkle banding without leaving black holes.
    """
    x, y, w, h = box
    margin = 6

    def col_avg(col, y0, y1):
        """Average parchment (index >= 4) value over a vertical strip; widen
        horizontally up to +/-3 px if the strip is all ink. Returns None if
        no parchment found anywhere nearby."""
        for spread in range(0, 4):
            vals = []
            for cc in {col - spread, col + spread}:
                if 0 <= cc < TEX_W:
                    for yy in range(max(0, y0), min(TEX_H, y1)):
                        v = linear[yy * TEX_W + cc]
                        if v >= 4:
                            vals.append(v)
            if vals:
                return sum(vals) / len(vals)
        return None

    for dx in range(w):
        col = x + dx
        top = col_avg(col, y - margin, y)
        bot = col_avg(col, y + h, y + h + margin)
        if top is None and bot is None:
            top = bot = 12.0          # parchment mid-tone fallback
        elif top is None:
            top = bot
        elif bot is None:
            bot = top
        # vertically interpolate between the above/below parchment tone so the
        # fill has no horizontal banding ("comb") artifacts
        for dy in range(h):
            t = (dy + 0.5) / h
            val = top * (1 - t) + bot * t
            linear[(y + dy) * TEX_W + col] = max(4, min(15, int(val + 0.5)))


def draw_parchment(linear, box, text, font_size, align):
    """In-paint parchment, then stamp dark ink (low index) where glyph is."""
    x, y, w, h = box
    inpaint_parchment(linear, box)
    gray, used = render_gray(text, w, h, font_size, align)
    for dy in range(h):
        row = (y + dy) * TEX_W
        for dx in range(w):
            g = gray[dy * w + dx]
            if g > 40:                      # glyph stroke
                # dark ink: brightest text -> index 1, fade to parchment
                ink = 1 + (255 - g) * 4 // 255   # 1..5
                linear[row + x + dx] = ink
    return used


def save_2x(linear, path):
    img = Image.new("L", (TEX_W, TEX_H))
    img.putdata([min(255, p * 17) for p in linear])
    img.resize((TEX_W * 2, TEX_H * 2), Image.NEAREST).save(path)


# ═══════════════════════════ sheet patching ═══════════════════════════

def patch_sheet(file_bytes, sheet, tag):
    """Patch one sheet window in `file_bytes` (bytearray). Returns
    (changed_window_offset, list_of_label_boxes). Raises on roundtrip fail."""
    off = sheet["offset"]
    window = file_bytes[off:off + WINDOW]
    assert len(window) == WINDOW, f"{tag}: window @{off} truncated"

    linear = desw(window)
    # roundtrip gate (parameter self-consistency)
    assert resw(linear) == bytes(window), \
        f"{tag} @{off}: deswizzle roundtrip FAILED (bad params/offset)"
    before = bytes(linear)

    sheet_pol = sheet.get("polarity", "dark_bg")
    default_size = sheet.get("font_size", 12)
    boxes = []
    for lab in sheet["labels"]:
        box = lab["box"]
        x, y, w, h = box
        assert x >= 0 and y >= 0 and x + w <= TEX_W and y + h <= TEX_H, \
            f"{tag}: box {box} out of bounds"
        boxes.append(tuple(box))
        pol = lab.get("polarity", sheet_pol)
        align = lab.get("align", "center")
        size = lab.get("font_size", default_size)
        text = lab["text"]
        if pol == "parchment":
            used = draw_parchment(linear, box, text, size, align)
        else:
            used = draw_dark_bg(linear, box, text, size, align)
        print(f"    [{x:3},{y:3} {w:3}x{h:2}] {pol:9} f{used} '{text}'")

    # containment: only listed boxes changed in decoded space
    allowed = bytearray(PIX_COUNT)
    for (x, y, w, h) in boxes:
        for yy in range(y, y + h):
            base = yy * TEX_W
            for xx in range(x, x + w):
                allowed[base + xx] = 1
    bad = next((i for i in range(PIX_COUNT)
                if linear[i] != before[i] and not allowed[i]), None)
    assert bad is None, \
        f"{tag} @{off}: pixel changed outside listed boxes at " \
        f"({bad % TEX_W},{bad // TEX_W})"

    # re-swizzle, post-edit roundtrip, splice
    new_window = resw(linear)
    assert len(new_window) == WINDOW
    assert bytes(desw(new_window)) == bytes(linear), \
        f"{tag} @{off}: post-edit roundtrip NOT exact"
    file_bytes[off:off + WINDOW] = new_window

    # debug previews
    os.makedirs(DEBUG_DIR, exist_ok=True)
    safe = sheet["name"].split("(")[0].strip().replace(" ", "_")[:24]
    stem = f"{tag}_{off}_{safe}"
    save_2x(before, os.path.join(DEBUG_DIR, f"{stem}_before.png"))
    save_2x(linear, os.path.join(DEBUG_DIR, f"{stem}_after.png"))
    return off, boxes


def patch_resource(key, cfg):
    tag = key
    in_path = os.path.join(IN_DIR, key + ".raw")
    out_path = os.path.join(OUT_DIR, key + ".raw")
    pristine = open(in_path, "rb").read()
    assert len(pristine) == cfg["size"], \
        f"{tag}: size {len(pristine)} != {cfg['size']}"
    print(f"\n=== {tag}  ({len(pristine)} bytes) ===")

    buf = bytearray(pristine)
    windows = []
    for sheet in cfg["sheets"]:
        print(f"  -- {sheet['name']} @off {sheet['offset']}")
        off, _ = patch_sheet(buf, sheet, tag)
        windows.append(off)

    # assert: only the patched windows differ from pristine
    win_ranges = sorted((o, o + WINDOW) for o in windows)
    pos = 0
    for s, e in win_ranges:
        assert pristine[pos:s] == buf[pos:s], \
            f"{tag}: bytes changed outside windows in [{pos},{s})"
        pos = e
    assert pristine[pos:] == buf[pos:], \
        f"{tag}: bytes changed after last window @{pos}"
    print(f"  containment OK: only {len(windows)} window(s) differ")

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(buf)
    assert len(buf) == cfg["size"]
    print(f"  wrote {out_path} ({len(buf)} bytes)")
    return buf


def main():
    print("=" * 64)
    print("  Facility strip patcher — R2141 / R2144 / R2150 / R2153")
    print("=" * 64)
    with open(LABELS_PATH, encoding="utf-8") as f:
        spec = json.load(f)

    # Order matters: R2150 before R2153 (s1/s2/s3 copied into R2153).
    r2141 = patch_resource("2141_type02", spec["2141_type02"])
    r2144 = patch_resource("2144_type02", spec["2144_type02"])
    r2150 = patch_resource("2150_type05", spec["2150_type05"])
    r2153 = patch_resource("2153_type05", spec["2153_type05"])

    # ── Copy patched R2150 s1/s2/s3 windows into R2153, assert equality ──
    print("\n=== R2153 <- R2150 stat-window copy ===")
    r2150_pristine = open(os.path.join(IN_DIR, "2150_type05.raw"), "rb").read()
    r2153_pristine = open(os.path.join(IN_DIR, "2153_type05.raw"), "rb").read()
    out = bytearray(r2153)
    for off in R2153_DUP_WINDOWS:
        # Verify the duplicate claim on PRISTINE data before copying.
        assert r2150_pristine[off:off + WINDOW] == \
            r2153_pristine[off:off + WINDOW], \
            f"R2150/R2153 NOT byte-identical at window {off} (pristine) — " \
            "copy assumption invalid"
        out[off:off + WINDOW] = r2150[off:off + WINDOW]
        assert out[off:off + WINDOW] == r2150[off:off + WINDOW]
        print(f"  copied window @{off} (R2150 -> R2153), equality OK")

    # sub0 (R2153's own translation) must be untouched by the copy
    assert out[0:R2153_DUP_WINDOWS[0]] == r2153[0:R2153_DUP_WINDOWS[0]], \
        "R2153 sub0 region disturbed by stat-window copy"
    out_path = os.path.join(OUT_DIR, "2153_type05.raw")
    with open(out_path, "wb") as f:
        f.write(out)
    assert len(out) == len(r2153_pristine)
    print(f"  rewrote {out_path} with copied windows ({len(out)} bytes)")

    print("\n" + "=" * 64)
    print("  DONE. Outputs in build/packdata_resources/, PNGs in",
          "build/recon_v86/facility-out/")
    print("=" * 64)


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, OSError, KeyError) as e:
        print(f"FAILED: {e}")
        sys.exit(1)
