#!/usr/bin/env python3
"""
patch_r2124.py — R2124 town-hub location banner strip: render 13 English labels.

R2124 (extracted/packdata_raw/2124_type01.raw, EXACTLY 34816 bytes) holds the
town-hub button-strip texture: 256x256 PSMT4, stored as a PSMCT32 upload
(dbw=128) in the byte range 0x02E0-0x82DF (32768 bytes). Everything else in
the resource is NEVER written:

  0x0000-0x000F  header                          NEVER WRITE
  0x0010-0x01FF  6 GIF A+D packets               NEVER WRITE (v83 VIF crash zone)
  0x0200-0x02DF  sprite/control records          NEVER WRITE
  0x02E0-0x82DF  32768 B pixel payload           << the ONLY writable range
  0x82E0-0x841F  5 CLUTs x 64 B                  NEVER WRITE
  0x8420-0x87FF  zeros                           NEVER WRITE

Labels live in data/strip_labels/r2124_labels.json. Each label rect is cleared
to palette index 0 (transparent) and English text is rendered re-using the
existing palette ramp (CLUT0: idx1 = bright glyph core ~224, idx2-13 = AA
ramp, idx14/15 = dark outline), so all five state CLUTs
(normal/highlight/pressed/disabled/alert) keep working without modification.

Spec: build/recon_v86/r2124-adjudicate/r2124_patch_spec.json (ROUTE A).

Output: build/packdata_resources/2124_type01.raw
Exit code: nonzero on any assertion failure.
"""
import json
import os
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))

from psmt4_deswizzle import deswizzle_psmt4, swizzle_psmt4  # noqa: E402

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

# ---------------------------------------------------------------------------
RAW_IN = os.path.join(BASE, "extracted", "packdata_raw", "2124_type01.raw")
RAW_OUT = os.path.join(BASE, "build", "packdata_resources", "2124_type01.raw")
LABELS_JSON = os.path.join(BASE, "data", "strip_labels", "r2124_labels.json")
PNG_DIR = os.path.join(BASE, "build", "recon_v86", "v86-out")

RES_SIZE = 34816
PIX_OFF = 0x02E0
PIX_END = 0x82E0          # exclusive
CLUT_OFF = 0x82E0
TEX_W, TEX_H = 256, 256
BW_PSMT4 = 256
DBW_CT32 = 128

FONT_SIZE_START = 13
FONT_SIZE_FLOOR = 9
STROKE_W = 1


def fail(msg):
    print(f"ASSERT FAILED: {msg}")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Font / rendering
# ---------------------------------------------------------------------------
_font_cache = {}


def load_font(size):
    if size in _font_cache:
        return _font_cache[size]
    for fp in ("C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf"):
        if os.path.exists(fp):
            f = ImageFont.truetype(fp, size)
            _font_cache[size] = f
            return f
    fail("no Arial TTF found on this system")


def clut_grays(data, clut_index=0):
    """Average luminance per palette index from one of the 5 RGB555 CLUTs."""
    grays = []
    off = CLUT_OFF + 64 * clut_index
    for i in range(16):
        w = struct.unpack_from("<I", data, off + 4 * i)[0]
        v = w & 0xFFFF
        r = (v & 31) * 8
        g = ((v >> 5) & 31) * 8
        b = ((v >> 10) & 31) * 8
        grays.append((r + g + b) / 3.0)
    return grays


def render_label(text, width, height, x_offset, grays):
    """Render text into a width x height cell of palette indices.

    Style matches the original JP glyphs: bright core (idx1), anti-alias ramp
    (idx2-13), 1px dark outline (idx14/15), background idx0 (transparent).
    Returns (cell_indices, font_size_used, text_width_px).
    """
    avail = width - x_offset
    size = FONT_SIZE_START
    font = load_font(size)
    while True:
        bbox = font.getbbox(text, stroke_width=STROKE_W)
        tw = bbox[2] - bbox[0]
        if tw <= avail or size <= FONT_SIZE_FLOOR:
            break
        size -= 1
        font = load_font(size)
    if tw > avail:
        fail(f"label '{text}' is {tw}px wide even at floor size "
             f"{FONT_SIZE_FLOOR} (available {avail}px)")

    bbox = font.getbbox(text, stroke_width=STROKE_W)
    th = bbox[3] - bbox[1]
    ox = x_offset - bbox[0]
    oy = max(0, (height - th) // 2) - bbox[1]

    # Two grayscale coverage masks: ink (glyph body) and ink+outline.
    ink = Image.new("L", (width, height), 0)
    ImageDraw.Draw(ink).text((ox, oy), text, fill=255, font=font)
    outl = Image.new("L", (width, height), 0)
    ImageDraw.Draw(outl).text((ox, oy), text, fill=255, font=font,
                              stroke_width=STROKE_W, stroke_fill=255)

    ink_px = list(ink.getdata())
    outl_px = list(outl.getdata())

    core_lum = grays[1]      # ~224 (bright glyph core)
    outline_lum = grays[14]  # ~24  (dark outline)

    cell = [0] * (width * height)
    for i, (iv, ov) in enumerate(zip(ink_px, outl_px)):
        if ov < 16:
            continue  # transparent background, keep idx0
        # Simulated luminance: glyph body blended over the dark outline.
        a = iv / 255.0
        o = ov / 255.0
        lum = a * core_lum + (1.0 - a) * o * outline_lum
        # Nearest nonzero palette index by luminance.
        best, bd = 15, 1e9
        for idx in range(1, 16):
            d = abs(grays[idx] - lum)
            if d < bd:
                best, bd = idx, d
        cell[i] = best
    return cell, size, tw


# ---------------------------------------------------------------------------
def main():
    original = open(RAW_IN, "rb").read()
    if len(original) != RES_SIZE:
        fail(f"input size {len(original)} != {RES_SIZE}")

    spec = json.load(open(LABELS_JSON, encoding="utf-8"))
    labels = spec["labels"]
    if len(labels) != 13:
        fail(f"expected 13 labels in {LABELS_JSON}, got {len(labels)}")

    # --- pre-flight roundtrip on pristine payload --------------------------
    payload = original[PIX_OFF:PIX_END]
    pixels = deswizzle_psmt4(payload, TEX_W, TEX_H,
                             bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32)
    re_sw = swizzle_psmt4(pixels, TEX_W, TEX_H,
                          bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32)
    if bytes(re_sw) != bytes(payload):
        fail("pre-flight roundtrip swizzle(deswizzle(payload)) != payload")
    print("pre-flight roundtrip: PASS (32768/32768 bytes)")

    grays = clut_grays(original, 0)

    # --- edit the 13 label rects -------------------------------------------
    orig_pixels = bytes(pixels)
    edited = bytearray(orig_pixels)
    for lab in labels:
        x, y, w, h = lab["rect"]
        xo = lab.get("text_x_offset", 2)
        cell, size, tw = render_label(lab["english"], w, h, xo, grays)
        for dy in range(h):
            row = (y + dy) * TEX_W + x
            edited[row:row + w] = bytes(cell[dy * w:(dy + 1) * w])
        print(f"  {lab['name']:14s} '{lab['english']}' -> {tw}px @ {size}px "
              f"in rect {lab['rect']}")

    # --- assert: modified pixels lie ONLY inside the 13 label rects --------
    def in_rects(px, py):
        for lab in labels:
            x, y, w, h = lab["rect"]
            if x <= px < x + w and y <= py < y + h:
                return True
        return False

    outside_diffs = 0
    for i in range(TEX_W * TEX_H):
        if edited[i] != orig_pixels[i] and not in_rects(i % TEX_W, i // TEX_W):
            outside_diffs += 1
    if outside_diffs:
        fail(f"{outside_diffs} modified pixels lie OUTSIDE the 13 label rects")
    for dnt in spec.get("do_not_touch", []):
        x, y, w, h = dnt["rect"]
        for dy in range(h):
            row = (y + dy) * TEX_W + x
            if edited[row:row + w] != orig_pixels[row:row + w]:
                fail(f"do_not_touch region {dnt['name']} was modified")
    print("pixel containment: PASS (all diffs inside the 13 label rects; "
          "do_not_touch regions untouched)")

    # --- re-swizzle and verify post-write roundtrip ------------------------
    new_payload = swizzle_psmt4(edited, TEX_W, TEX_H,
                                bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32)
    if len(new_payload) != PIX_END - PIX_OFF:
        fail(f"re-swizzled payload size {len(new_payload)} != 32768")
    back = deswizzle_psmt4(new_payload, TEX_W, TEX_H,
                           bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32)
    if bytes(back) != bytes(edited):
        fail("post-write roundtrip deswizzle(swizzle(edited)) != edited")
    print("post-write roundtrip: PASS")

    # --- assemble output ----------------------------------------------------
    patched = bytearray(original)
    patched[PIX_OFF:PIX_END] = new_payload

    if len(patched) != RES_SIZE:
        fail(f"output size {len(patched)} != {RES_SIZE}")
    if patched[0:PIX_OFF] != original[0:PIX_OFF]:
        fail("bytes [0x0000:0x02E0] (header/GIF/sprites) were modified")
    if patched[PIX_END:RES_SIZE] != original[PIX_END:RES_SIZE]:
        fail("bytes [0x82E0:0x8800] (CLUTs/zeros) were modified")

    lo = next(i for i in range(RES_SIZE) if patched[i] != original[i])
    hi = next(i for i in range(RES_SIZE - 1, -1, -1)
              if patched[i] != original[i])
    if lo < PIX_OFF or hi >= PIX_END:
        fail(f"modified byte range 0x{lo:04X}-0x{hi:04X} escapes "
             f"0x{PIX_OFF:04X}-0x{PIX_END - 1:04X}")
    nmod = sum(1 for a, b in zip(patched, original) if a != b)
    print(f"modified bytes: {nmod}, range 0x{lo:04X}-0x{hi:04X} "
          f"(writable window 0x02E0-0x82DF): OK")

    os.makedirs(os.path.dirname(RAW_OUT), exist_ok=True)
    with open(RAW_OUT, "wb") as f:
        f.write(patched)
    print(f"wrote {RAW_OUT} ({len(patched)} bytes)")

    # --- verification PNGs ---------------------------------------------------
    os.makedirs(PNG_DIR, exist_ok=True)

    def save_gray(pix, path):
        img = Image.new("L", (TEX_W, TEX_H))
        img.putdata([p * 17 for p in pix])
        img.resize((TEX_W * 2, TEX_H * 2), Image.NEAREST).save(path)
        print(f"  saved {path}")

    def save_clut(pix, path, clut_index=0):
        off = CLUT_OFF + 64 * clut_index
        pal = []
        for i in range(16):
            w = struct.unpack_from("<I", original, off + 4 * i)[0]
            v = w & 0xFFFF
            pal.append(((v & 31) * 8, ((v >> 5) & 31) * 8,
                        ((v >> 10) & 31) * 8, 0 if i == 0 else 255))
        img = Image.new("RGBA", (TEX_W, TEX_H))
        img.putdata([pal[p] for p in pix])
        img.resize((TEX_W * 2, TEX_H * 2), Image.NEAREST).save(path)
        print(f"  saved {path}")

    save_gray(orig_pixels, os.path.join(PNG_DIR, "r2124_before_gray_2x.png"))
    save_gray(edited, os.path.join(PNG_DIR, "r2124_after_gray_2x.png"))
    save_clut(edited, os.path.join(PNG_DIR, "r2124_after_clut0_2x.png"))
    print("ALL ASSERTS PASSED")


if __name__ == "__main__":
    main()
