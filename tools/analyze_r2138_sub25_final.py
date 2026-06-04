#!/usr/bin/env python3
"""
Final character identification for R2138 sub25.
Focus on the large anti-aliased characters in regions 4 and 6.
These are rendered with heavy anti-aliasing (smooth gradients from 0-F).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from psmt4_deswizzle import deswizzle_psmt4

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PATH = os.path.join(BASE, "extracted", "packdata_raw", "2138_type29.raw")

SUB_OFFSET = 0x15C4D0
HEADER_SIZE = 0x6E0
PIXEL_OFFSET = SUB_OFFSET + HEADER_SIZE
PIXEL_SIZE = 32768
TEX_W, TEX_H = 256, 256
DBW_CT32 = 128

data = open(RAW_PATH, 'rb').read()
pixel_data = data[PIXEL_OFFSET:PIXEL_OFFSET + PIXEL_SIZE]
pixels = deswizzle_psmt4(pixel_data, TEX_W, TEX_H, dbw_ct32=DBW_CT32)

charmap = '.' + '123456789ABCDEF'

def print_region_thresholded(x1, y1, x2, y2, threshold=3, label=""):
    """Print region with threshold to show character skeleton."""
    print(f"\n{label} (threshold >= {threshold}):")
    for y in range(y1, y2):
        line = ''
        for x in range(x1, x2):
            v = pixels[y * TEX_W + x]
            if v >= threshold:
                line += '#'
            else:
                line += '.'
        if '#' in line:
            print(f"  y{y:3d}: {line}")

# ============================================================
# REGION 4 analysis
# ============================================================
print("=" * 80)
print("REGION 4: Large AA text (x4-122, y188-214)")
print("=" * 80)
print()
print("This region has heavy anti-aliasing. Let me threshold at different levels")
print("to see the character skeleton.")

# Threshold at 5 (medium)
print_region_thresholded(4, 188, 122, 213, threshold=5, label="Region 4, threshold=5")

# Threshold at 8 (high - shows only darkest strokes)
print_region_thresholded(4, 188, 122, 213, threshold=8, label="Region 4, threshold=8")

# The pattern shows:
# - x4-65: A large character with a triangular/expanding shape (wider at bottom)
#   This looks like an upward-pointing or expanding shape
# - x66-71: gap (low density)
# - x72-122: More characters

# Let's look at the LEFT half and RIGHT half separately at threshold=7
print("\n--- Region 4 LEFT (x4-65) threshold=7 ---")
print_region_thresholded(4, 188, 65, 213, threshold=7, label="R4 Left")

print("\n--- Region 4 RIGHT (x66-122) threshold=7 ---")
print_region_thresholded(66, 188, 122, 213, threshold=7, label="R4 Right")

# ============================================================
# REGION 6 analysis
# ============================================================
print("\n" + "=" * 80)
print("REGION 6: Large AA text (x5-121, y226-250)")
print("=" * 80)

print_region_thresholded(5, 226, 121, 250, threshold=5, label="Region 6, threshold=5")
print_region_thresholded(5, 226, 121, 250, threshold=8, label="Region 6, threshold=8")

# Region 6 has two segments: (6-107) and (109-121)
print("\n--- Region 6 LEFT (x5-60) threshold=7 ---")
print_region_thresholded(5, 226, 60, 250, threshold=7, label="R6 Left")

print("\n--- Region 6 MID (x60-107) threshold=7 ---")
print_region_thresholded(60, 226, 107, 250, threshold=7, label="R6 Mid")

print("\n--- Region 6 RIGHT (x107-121) threshold=7 ---")
print_region_thresholded(107, 226, 121, 253, threshold=7, label="R6 Right")

# ============================================================
# REGION 5 analysis
# ============================================================
print("\n" + "=" * 80)
print("REGION 5 UPPER: (x144-188, y176-192)")
print("=" * 80)

# Region 5 upper has gaps at x=158-159 and x=171-173
# So 3 characters: (146-158), (160-171), (174-185)
print("\n--- R5U Char 1 (x146-158) ---")
print_region_thresholded(146, 176, 158, 192, threshold=3, label="R5U Char1")

print("\n--- R5U Char 2 (x159-171) ---")
print_region_thresholded(159, 176, 171, 192, threshold=3, label="R5U Char2")

print("\n--- R5U Char 3 (x174-185) ---")
print_region_thresholded(174, 176, 185, 192, threshold=3, label="R5U Char3")

# Region 5 lower: (145-167) and (174-188)
print("\n" + "=" * 80)
print("REGION 5 LOWER")
print("=" * 80)

print_region_thresholded(145, 198, 167, 217, threshold=3, label="R5L Char1 (x145-167)")
print_region_thresholded(174, 198, 188, 217, threshold=3, label="R5L Char2 (x174-188)")

# ============================================================
# REGION 3 segment analysis
# ============================================================
print("\n" + "=" * 80)
print("REGION 3 SEGMENTS")
print("=" * 80)

# Segment 0: x=35-67 - note these are INVERTED (light on dark background)
# The palette values F=max mean background, lower values are the text
# For region 3, let me show it inverted (F=background=., lower=text=#)
print("\n--- R3 Segment 0 (x=35-67) - INVERTED (F=bg) ---")
for y in range(153, 166):
    line = ''
    for x in range(35, 67):
        v = pixels[y * TEX_W + x]
        if v < 12:  # 0-11 are "text" (dark on light bg = inverted)
            line += '#'
        else:
            line += '.'
    if '#' in line:
        print(f"  y{y:3d}: {line}")

# Segment 1: x=130-206 - also inverted
print("\n--- R3 Segment 1 (x=130-206) - INVERTED (F=bg) ---")
for y in range(153, 166):
    line = ''
    for x in range(130, 206):
        v = pixels[y * TEX_W + x]
        if v < 12:
            line += '#'
        else:
            line += '.'
    if '#' in line:
        print(f"  y{y:3d}: {line}")

# Let me split segment 1 into individual characters
# Looking at the density data, there are some dips but no clear zero gaps
# The text is anti-aliased on background F
# Let me check column-by-column for columns that are ALL high (>=12, i.e. background)
print("\n--- R3 Seg1 column analysis (cols with ALL pixels >= 12 = background) ---")
for x in range(130, 206):
    all_bg = all(pixels[y*TEX_W+x] >= 12 for y in range(153, 166))
    if all_bg:
        print(f"  x={x}: ALL BACKGROUND")
