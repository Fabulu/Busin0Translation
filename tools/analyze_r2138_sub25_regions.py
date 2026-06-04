#!/usr/bin/env python3
"""
Analyze R2138 sub25 regions 3, 4, 5, 6.
Deswizzle PSMT4 texture, extract regions at 8x zoom, print pixel maps.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from psmt4_deswizzle import deswizzle_psmt4
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PATH = os.path.join(BASE, "extracted", "packdata_raw", "2138_type29.raw")
DUMP_DIR = os.path.join(BASE, "dumps")
os.makedirs(DUMP_DIR, exist_ok=True)

# Sub25 parameters
SUB_OFFSET = 0x15C4D0
HEADER_SIZE = 0x6E0
PIXEL_OFFSET = SUB_OFFSET + HEADER_SIZE  # 0x15CBB0
PIXEL_SIZE = 32768
TEX_W, TEX_H = 256, 256
DBW_CT32 = 128  # Same as sub7 (256-wide PSMT4)

data = open(RAW_PATH, 'rb').read()
pixel_data = data[PIXEL_OFFSET:PIXEL_OFFSET + PIXEL_SIZE]
print(f"Pixel data: {len(pixel_data)} bytes from offset 0x{PIXEL_OFFSET:X}")

# Deswizzle
pixels = deswizzle_psmt4(pixel_data, TEX_W, TEX_H, dbw_ct32=DBW_CT32)
print(f"Deswizzled {len(pixels)} pixels, non-zero: {sum(1 for p in pixels if p)}")

# --- Regions to analyze ---
regions = {
    3: (0, 128, 256, 176, "Region 3 - kanji phrase area"),
    4: (4, 176, 122, 217, "Region 4 - Large AA text + !!"),
    5: (144, 176, 188, 217, "Region 5 - Two stacked small text"),
    6: (5, 224, 121, 254, "Region 6 - Large AA text line 2"),
}

# Also look at the FULL texture to understand layout
print("\n=== FULL TEXTURE: row-by-row non-zero pixel scan ===")
for y in range(0, TEX_H, 4):
    row_data = []
    for x in range(TEX_W):
        if pixels[y * TEX_W + x] != 0:
            row_data.append(x)
    if row_data:
        print(f"  y={y:3d}: {len(row_data)} non-zero px, x-range [{min(row_data)}-{max(row_data)}]")

# Render grayscale images (palette index -> brightness)
# PSMT4 has indices 0-15; use index as brightness (0=black, 15=white)
ZOOM = 8

for rid, (x1, y1, x2, y2, desc) in regions.items():
    w = x2 - x1
    h = y2 - y1
    print(f"\n=== {desc} ({w}x{h} pixels) ===")

    # Extract region pixels
    region_px = []
    for y in range(y1, y2):
        row = []
        for x in range(x1, x2):
            row.append(pixels[y * TEX_W + x])
        region_px.append(row)

    # Print numerical map (condensed: use chars for palette indices)
    # 0='.', 1-9='1'-'9', 10-15='A'-'F'
    charmap = '.' + '123456789ABCDEF'
    for y_idx, row in enumerate(region_px):
        line = ''.join(charmap[min(v, 15)] for v in row)
        # Only print rows that have non-zero content
        if any(v != 0 for v in row):
            print(f"  y{y1+y_idx:3d}: {line}")

    # Create grayscale PNG at 8x zoom
    img = Image.new('L', (w * ZOOM, h * ZOOM))
    for y_idx, row in enumerate(region_px):
        for x_idx, val in enumerate(row):
            brightness = val * 17  # 0-15 -> 0-255
            for zy in range(ZOOM):
                for zx in range(ZOOM):
                    img.putpixel((x_idx * ZOOM + zx, y_idx * ZOOM + zy), brightness)

    out_path = os.path.join(DUMP_DIR, f"r2138_sub25_region{rid}_8x.png")
    img.save(out_path)
    print(f"  Saved: {out_path}")

    # Analyze character shapes: find vertical columns with content
    col_has_content = [any(region_px[y][x] != 0 for y in range(h)) for x in range(w)]
    # Find character boundaries (gaps of empty columns)
    in_char = False
    char_ranges = []
    char_start = 0
    for x in range(w):
        if col_has_content[x] and not in_char:
            char_start = x
            in_char = True
        elif not col_has_content[x] and in_char:
            char_ranges.append((char_start, x))
            in_char = False
    if in_char:
        char_ranges.append((char_start, w))

    print(f"  Character column ranges: {char_ranges}")
    print(f"  Number of distinct shapes: {len(char_ranges)}")
    for ci, (cs, ce) in enumerate(char_ranges):
        print(f"    Char {ci}: cols {cs}-{ce} (width={ce-cs}px)")

# Also save full texture overview
print("\n=== Saving full texture overview ===")
img_full = Image.new('L', (TEX_W * 2, TEX_H * 2))
for y in range(TEX_H):
    for x in range(TEX_W):
        brightness = pixels[y * TEX_W + x] * 17
        for zy in range(2):
            for zx in range(2):
                img_full.putpixel((x * 2 + zx, y * 2 + zy), brightness)
img_full.save(os.path.join(DUMP_DIR, "r2138_sub25_full_2x.png"))
print(f"  Saved full texture")
