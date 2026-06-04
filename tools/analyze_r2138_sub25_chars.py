#!/usr/bin/env python3
"""
Detailed character analysis of R2138 sub25 regions 4, 5, 6.
Use column density to find gaps between characters in anti-aliased text.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from psmt4_deswizzle import deswizzle_psmt4
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PATH = os.path.join(BASE, "extracted", "packdata_raw", "2138_type29.raw")
DUMP_DIR = os.path.join(BASE, "dumps")

SUB_OFFSET = 0x15C4D0
HEADER_SIZE = 0x6E0
PIXEL_OFFSET = SUB_OFFSET + HEADER_SIZE
PIXEL_SIZE = 32768
TEX_W, TEX_H = 256, 256
DBW_CT32 = 128

data = open(RAW_PATH, 'rb').read()
pixel_data = data[PIXEL_OFFSET:PIXEL_OFFSET + PIXEL_SIZE]
pixels = deswizzle_psmt4(pixel_data, TEX_W, TEX_H, dbw_ct32=DBW_CT32)

def get_region(x1, y1, x2, y2):
    """Extract region as 2D list."""
    rows = []
    for y in range(y1, y2):
        row = []
        for x in range(x1, x2):
            row.append(pixels[y * TEX_W + x])
        rows.append(row)
    return rows

def col_density(region, col):
    """Sum of pixel values in a column (higher = more ink)."""
    return sum(row[col] for row in region)

def print_col_profile(region, name, x_offset=0):
    """Print column density profile to identify character boundaries."""
    w = len(region[0])
    h = len(region)
    print(f"\n=== {name}: Column density profile (h={h}) ===")
    densities = [col_density(region, x) for x in range(w)]
    max_d = max(densities) if densities else 1

    # Find columns with zero or very low density (gaps)
    threshold = max_d * 0.02  # 2% of max
    gaps = []
    for x, d in enumerate(densities):
        if d <= threshold:
            gaps.append(x + x_offset)

    # Print condensed bar chart
    for x in range(w):
        d = densities[x]
        bar_len = int(d / max_d * 40) if max_d > 0 else 0
        bar = '#' * bar_len
        gap_marker = ' GAP' if d <= threshold else ''
        if x % 2 == 0 or d <= threshold:  # Print every other column + gaps
            print(f"  x={x+x_offset:3d}: {d:4d} |{bar}{gap_marker}")

    print(f"  Gap columns (density <= {threshold:.0f}): {gaps}")

    # Find character segments between gaps
    in_char = False
    segments = []
    seg_start = 0
    for x in range(w):
        d = densities[x]
        if d > threshold and not in_char:
            seg_start = x
            in_char = True
        elif d <= threshold and in_char:
            segments.append((seg_start + x_offset, x + x_offset, x - seg_start))
            in_char = False
    if in_char:
        segments.append((seg_start + x_offset, w + x_offset, w - seg_start))

    print(f"  Character segments: {segments}")
    for i, (s, e, w2) in enumerate(segments):
        print(f"    Segment {i}: x={s}-{e} width={w2}px")

    return segments

# ---- Region 4: (4,176)-(122,217) "Large AA text + !!" ----
print("=" * 70)
print("REGION 4: Large anti-aliased text (4,176)-(122,217)")
print("=" * 70)
r4 = get_region(4, 188, 122, 214)  # Trim to just the character area
print_col_profile(r4, "Region 4 (trimmed y188-214)", x_offset=4)

# Print the pixel map for region 4 more precisely
print("\n--- Region 4 pixel map (trimmed, y188-214) ---")
charmap = '.' + '123456789ABCDEF'
for y_idx, row in enumerate(r4):
    line = ''.join(charmap[min(v, 15)] for v in row)
    if any(v > 0 for v in row):
        print(f"  y{188+y_idx}: {line}")

# ---- Region 5 upper: (144,176)-(188,192) ----
print("\n" + "=" * 70)
print("REGION 5 UPPER: (144,176)-(188,192)")
print("=" * 70)
r5u = get_region(144, 176, 188, 192)
print_col_profile(r5u, "Region 5 upper", x_offset=144)
print("\n--- Region 5 upper pixel map ---")
for y_idx, row in enumerate(r5u):
    line = ''.join(charmap[min(v, 15)] for v in row)
    if any(v > 0 for v in row):
        print(f"  y{176+y_idx}: {line}")

# ---- Region 5 lower: (144,196)-(188,217) ----
print("\n" + "=" * 70)
print("REGION 5 LOWER: (144,196)-(188,217)")
print("=" * 70)
r5l = get_region(144, 196, 188, 217)
print_col_profile(r5l, "Region 5 lower", x_offset=144)
print("\n--- Region 5 lower pixel map ---")
for y_idx, row in enumerate(r5l):
    line = ''.join(charmap[min(v, 15)] for v in row)
    if any(v > 0 for v in row):
        print(f"  y{196+y_idx}: {line}")

# ---- Region 6: (5,224)-(121,254) "Large AA text line 2" ----
print("\n" + "=" * 70)
print("REGION 6: Large anti-aliased text (5,224)-(121,254)")
print("=" * 70)
r6 = get_region(5, 226, 121, 252)  # Trim
print_col_profile(r6, "Region 6 (trimmed y226-252)", x_offset=5)

print("\n--- Region 6 pixel map (trimmed, y226-252) ---")
for y_idx, row in enumerate(r6):
    line = ''.join(charmap[min(v, 15)] for v in row)
    if any(v > 0 for v in row):
        print(f"  y{226+y_idx}: {line}")

# ---- Region 3 right side: kanji at x=132-204 ----
print("\n" + "=" * 70)
print("REGION 3: Kanji text area (132,152)-(232,166)")
print("=" * 70)
r3 = get_region(35, 153, 232, 166)
print_col_profile(r3, "Region 3 text (y153-166)", x_offset=35)

# Print region 3 character pixel maps for each identified segment
print("\n--- Region 3 pixel map (y153-166) ---")
for y_idx, row in enumerate(r3):
    line = ''.join(charmap[min(v, 15)] for v in row)
    if any(v > 0 for v in row):
        print(f"  y{153+y_idx}: {line}")
