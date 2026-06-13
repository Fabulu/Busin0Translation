#!/usr/bin/env python3
"""
R1365 patcher — master status/bottom-bar atlas (~34 Japanese label rects).

Resource: extracted/packdata_raw/1365_type02.raw (EXACTLY 38912 bytes)
Layout (verified against GS dumps at VRAM TBP0=0x2BA4, byte-match 1.0000):
  0     .. 1920   header                 (must stay byte-identical)
  1920  .. 34688  pixel payload, 32768 B (256x256 PSMT4, dbw_ct32=128)
  34688 .. 35712  CLUTs                  (must stay byte-identical)
  35712 .. 38912  rect table + tail      (must stay byte-identical)

Rect table at 35712: BE u32 header (5, 80), then 80 entries of
5 BE u32 (x, y, w, h, clut_idx); entry i at 35720 + 20*i.

Translations live in data/strip_labels/r1365_labels.json (rect idx -> English).
Rect coordinates are read from the file's own rect table — never hardcoded.

Render technique (model: tools/patch_r2138.py): deswizzle to linear indices,
clear each listed rect to 0, draw English text, antialias by mapping grayscale
onto the rect's ORIGINAL sorted nonzero-index set (some rects only use odd
indices), re-swizzle, splice payload back. 16px rows render at font 11,
32px brush rows at font 16; auto-shrink to fit, floor 9px.

Output: build/packdata_resources/1365_type02.raw
Debug:  build/recon_v86/r1365-status/r1365_before_2x.png / r1365_after_2x.png
Exits nonzero on any failure.
"""

import json
import os
import struct
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
INPUT_PATH = os.path.join(BASE, "extracted", "packdata_raw", "1365_type02.raw")
LABELS_PATH = os.path.join(BASE, "data", "strip_labels", "r1365_labels.json")
OUTPUT_PATH = os.path.join(BASE, "build", "packdata_resources", "1365_type02.raw")
DEBUG_DIR = os.path.join(BASE, "build", "recon_v86", "r1365-status")

# ── Verified layout constants ──
EXPECTED_SIZE = 38912
PIX_OFF = 1920
PIX_END = 34688          # PIX_OFF + 32768
CLUT_END = 35712
RECT_TABLE_OFF = 35712
TEX_W, TEX_H = 256, 256
BW_PSMT4 = 256
DBW_CT32 = 128

# ── Font sizing per spec ──
FONT_16PX_ROW = 11       # rects with h <= 16
FONT_32PX_BRUSH = 16     # brush-style condition rects (h >= 32)
FONT_FLOOR = 9


# ═══════════════════════════════════════════════════════════════════════
# Font / rendering
# ═══════════════════════════════════════════════════════════════════════

_font_cache = {}


def load_font(size):
    """Serif font to match the atlas's existing English (LEVEL/STATUS/...)."""
    if size in _font_cache:
        return _font_cache[size]
    candidates = [
        "C:/Windows/Fonts/timesbd.ttf",
        "C:/Windows/Fonts/times.ttf",
        "C:/Windows/Fonts/georgiab.ttf",
        "C:/Windows/Fonts/georgia.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    font = None
    for fp in candidates:
        if os.path.exists(fp):
            font = ImageFont.truetype(fp, size)
            break
    if font is None:
        font = ImageFont.load_default()
    _font_cache[size] = font
    return font


def render_text_gray(text, w, h, start_size):
    """Render text centered into a w x h grayscale canvas, auto-shrinking
    from start_size down to FONT_FLOOR until it fits the width."""
    size = start_size
    font = load_font(size)
    bbox = font.getbbox(text)
    while (bbox[2] - bbox[0]) > w - 2 and size > FONT_FLOOR:
        size -= 1
        font = load_font(size)
        bbox = font.getbbox(text)
    img = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(img)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    ox = max(0, (w - tw) // 2) - bbox[0]
    oy = max(0, (h - th) // 2) - bbox[1]
    draw.text((ox, oy), text, fill=255, font=font)
    return list(img.getdata()), size


def rect_levels(linear, x, y, w, h):
    """Sorted list of nonzero palette indices present in the original rect."""
    levels = set()
    for yy in range(y, y + h):
        row = yy * TEX_W
        for xx in range(x, x + w):
            v = linear[row + xx]
            if v:
                levels.add(v)
    return sorted(levels)


def draw_rect(linear, x, y, w, h, text, levels):
    """Clear rect to 0 and draw English text using only the rect's original
    nonzero indices for antialiasing (brightest gray -> highest index)."""
    start_size = FONT_32PX_BRUSH if h >= 32 else FONT_16PX_ROW
    gray, used_size = render_text_gray(text, w, h, start_size)
    nlev = len(levels)
    for dy in range(h):
        row = (y + dy) * TEX_W
        for dx in range(w):
            g = gray[dy * w + dx]
            if g == 0:
                val = 0
            else:
                val = levels[min(nlev - 1, (g * nlev) // 256)]
            linear[row + x + dx] = val
    return used_size


def save_preview_2x(linear, path):
    """Grayscale 2x preview (index*17, NEAREST) matching the recon PNGs."""
    img = Image.new("L", (TEX_W, TEX_H))
    img.putdata([p * 17 for p in linear])
    img.resize((TEX_W * 2, TEX_H * 2), Image.NEAREST).save(path)


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("  R1365 Patcher — status/bottom-bar atlas labels")
    print("=" * 60)

    # ── Load pristine resource ──
    pristine = open(INPUT_PATH, "rb").read()
    assert len(pristine) == EXPECTED_SIZE, \
        f"R1365 size mismatch: {len(pristine)} != {EXPECTED_SIZE}"
    print(f"  Input: {INPUT_PATH} ({len(pristine)} bytes, OK)")

    # ── Parse rect table from the file itself ──
    hdr_a, rect_count = struct.unpack_from(">II", pristine, RECT_TABLE_OFF)
    assert (hdr_a, rect_count) == (5, 80), \
        f"Unexpected rect table header: ({hdr_a}, {rect_count})"
    rects = []
    for i in range(rect_count):
        x, y, w, h, clut = struct.unpack_from(">5I", pristine,
                                              RECT_TABLE_OFF + 8 + i * 20)
        rects.append((x, y, w, h, clut))

    # ── Load translations ──
    with open(LABELS_PATH, encoding="utf-8") as f:
        labels = {int(k): v for k, v in json.load(f)["labels"].items()}
    print(f"  Labels: {len(labels)} rect entries from {LABELS_PATH}")
    for idx in labels:
        assert 0 <= idx < rect_count, f"Label rect index {idx} out of range"

    # ── Deswizzle + exact roundtrip check (pre-edit) ──
    payload = pristine[PIX_OFF:PIX_END]
    linear = bytearray(deswizzle_psmt4(payload, TEX_W, TEX_H,
                                       bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32))
    assert len(linear) == TEX_W * TEX_H
    rt = swizzle_psmt4(linear, TEX_W, TEX_H,
                       bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32)
    assert bytes(rt) == payload, "Pre-edit swizzle roundtrip NOT exact"
    print("  Pre-edit roundtrip: PASS (exact)")
    original_linear = bytes(linear)

    # ── Merge listed rects: same text + overlapping region -> one render ──
    # (rects 25/29 are duplicates and 26 is contained within them)
    def overlaps(a, b):
        ax, ay, aw, ah = a
        bx, by, bw_, bh = b
        return ax < bx + bw_ and bx < ax + aw and ay < by + bh and by < ay + ah

    regions = []  # [bbox(x,y,w,h), text, [indices]]
    for idx in sorted(labels):
        x, y, w, h, _ = rects[idx]
        text = labels[idx]
        merged = False
        for reg in regions:
            if reg[1] == text and overlaps(reg[0], (x, y, w, h)):
                rx, ry, rw, rh = reg[0]
                nx, ny = min(rx, x), min(ry, y)
                nw = max(rx + rw, x + w) - nx
                nh = max(ry + rh, y + h) - ny
                reg[0] = (nx, ny, nw, nh)
                reg[2].append(idx)
                merged = True
                break
        if not merged:
            regions.append([(x, y, w, h), text, [idx]])

    # Sanity: no listed region may overlap another with DIFFERENT text
    for i in range(len(regions)):
        for j in range(i + 1, len(regions)):
            assert not overlaps(regions[i][0], regions[j][0]), \
                f"Conflicting overlap: {regions[i][2]} vs {regions[j][2]}"

    # ── Render ──
    for bbox, text, idxs in regions:
        x, y, w, h = bbox
        levels = rect_levels(original_linear, x, y, w, h)
        assert levels, f"Rect(s) {idxs} have no nonzero pixels to sample"
        size = draw_rect(linear, x, y, w, h, text, levels)
        tag = "+".join(str(i) for i in idxs)
        print(f"  [{tag:>8s}] ({x:3d},{y:3d} {w:3d}x{h:2d}) '{text}'"
              f"  font={size}  levels={len(levels)}"
              f" (max {levels[-1]})")

    # ── Assert: only listed rects changed in decoded space ──
    allowed = bytearray(TEX_W * TEX_H)
    for bbox, _, _ in regions:
        x, y, w, h = bbox
        for yy in range(y, y + h):
            row = yy * TEX_W
            for xx in range(x, x + w):
                allowed[row + xx] = 1
    bad = [i for i in range(TEX_W * TEX_H)
           if linear[i] != original_linear[i] and not allowed[i]]
    assert not bad, \
        f"{len(bad)} pixels changed OUTSIDE listed rects, first at " \
        f"({bad[0] % TEX_W},{bad[0] // TEX_W})"
    print("  Pixel containment: PASS (changes only inside listed rects)")

    # ── Re-swizzle and splice ──
    new_payload = swizzle_psmt4(linear, TEX_W, TEX_H,
                                bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32)
    assert len(new_payload) == PIX_END - PIX_OFF, \
        f"Re-swizzled payload size {len(new_payload)} != {PIX_END - PIX_OFF}"
    # Post-edit roundtrip: decode of new payload must equal edited linear
    verify = deswizzle_psmt4(bytes(new_payload), TEX_W, TEX_H,
                             bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32)
    assert bytes(verify) == bytes(linear), "Post-edit roundtrip NOT exact"

    out = pristine[:PIX_OFF] + bytes(new_payload) + pristine[PIX_END:]
    assert len(out) == EXPECTED_SIZE, f"Output size {len(out)} != {EXPECTED_SIZE}"
    assert out[:PIX_OFF] == pristine[:PIX_OFF], "Header region modified!"
    assert out[PIX_END:] == pristine[PIX_END:], \
        "CLUT/rect-table/tail region modified!"
    print("  Integrity: PASS (header, CLUTs, rect table, tail byte-identical)")

    # ── Write output + debug previews ──
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "wb") as f:
        f.write(out)
    print(f"  Output: {OUTPUT_PATH} ({len(out)} bytes)")

    os.makedirs(DEBUG_DIR, exist_ok=True)
    before_png = os.path.join(DEBUG_DIR, "r1365_before_2x.png")
    after_png = os.path.join(DEBUG_DIR, "r1365_after_2x.png")
    save_preview_2x(original_linear, before_png)
    save_preview_2x(linear, after_png)
    print(f"  Previews: {before_png}")
    print(f"            {after_png}")

    print("=" * 60)
    print(f"  DONE: {len(regions)} regions ({len(labels)} rect entries) patched")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, OSError) as e:
        print(f"FAILED: {e}")
        sys.exit(1)
