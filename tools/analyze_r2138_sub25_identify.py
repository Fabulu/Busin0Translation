#!/usr/bin/env python3
"""
Identify specific characters in R2138 sub25 regions.
Focus on region 4, 5, 6, and region 3 segments.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from psmt4_deswizzle import deswizzle_psmt4
from PIL import Image, ImageDraw

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

def extract_save(x1, y1, x2, y2, name, zoom=8):
    w, h = x2 - x1, y2 - y1
    img = Image.new('L', (w * zoom, h * zoom))
    for dy in range(h):
        for dx in range(w):
            v = pixels[(y1+dy) * TEX_W + (x1+dx)] * 17
            for zy in range(zoom):
                for zx in range(zoom):
                    img.putpixel((dx*zoom+zx, dy*zoom+zy), v)
    path = os.path.join(DUMP_DIR, name)
    img.save(path)
    return path

charmap = '.' + '123456789ABCDEF'

# ============================================================
# REGION 4: The large anti-aliased text
# It appears to be ONE continuous shape without clear gaps.
# Let me look at it more carefully by examining low-density columns.
# ============================================================
print("=" * 70)
print("REGION 4 ANALYSIS: Large AA text (4,188)-(122,212)")
print("=" * 70)

# Print with column markers to help identify character boundaries
print("\nLooking for character structure in region 4...")
print("Key observation: The text has a distinctive shape:")
print("- Left part (x4-64): sweeping curved strokes, getting wider toward bottom")
print("- Middle dip around x66-72: low density area")
print("- Right part (x72-122): continues with different structure")

# Let me look at specific column densities in fine detail
print("\nPer-column density (every column):")
for x_abs in range(4, 122):
    x = x_abs - 4
    d = sum(pixels[(y)*TEX_W + x_abs] for y in range(188, 212))
    marker = ""
    if d < 10:
        marker = " <<< LOW"
    elif d < 20:
        marker = " << low"
    print(f"  x={x_abs:3d}: density={d:4d}{marker}")

# ============================================================
# REGION 6: Second large text line
# Previous analysis showed segments at (6-107, width=101) and (109-121, width=12)
# ============================================================
print("\n" + "=" * 70)
print("REGION 6 ANALYSIS: Large AA text (5,226)-(121,249)")
print("=" * 70)

print("\nPer-column density:")
for x_abs in range(5, 121):
    d = sum(pixels[(y)*TEX_W + x_abs] for y in range(226, 249))
    marker = ""
    if d < 10:
        marker = " <<< LOW"
    elif d < 20:
        marker = " << low"
    print(f"  x={x_abs:3d}: density={d:4d}{marker}")

# ============================================================
# REGION 3: Three segments identified
# Segment 0: x=35-67 (width=32px) - matches 2 kanji ~16px each
# Segment 1: x=130-206 (width=76px) - matches ~5 kanji
# Segment 2: x=213-232 (width=19px) - decorative triangle
# ============================================================
print("\n" + "=" * 70)
print("REGION 3 ANALYSIS")
print("=" * 70)

# Segment 0 at x=35-67
print("\n--- Region 3, Segment 0: x=35-67 (width=32) ---")
print("This is likely 2 kanji, each ~16px wide")
for y in range(153, 166):
    line = ''.join(charmap[min(pixels[y*TEX_W+x], 15)] for x in range(35, 67))
    if any(pixels[y*TEX_W+x] > 0 for x in range(35, 67)):
        print(f"  y{y}: {line}")

# Per-column density for segment 0
print("\n  Column densities:")
for x in range(35, 67):
    d = sum(pixels[y*TEX_W+x] for y in range(153, 166))
    marker = " <<< LOW" if d < 10 else (" << low" if d < 20 else "")
    print(f"    x={x}: {d:4d}{marker}")

# Segment 1 at x=130-206
print("\n--- Region 3, Segment 1: x=130-206 (width=76) ---")
print("This should be ~5 kanji at ~14-16px each")
for y in range(153, 166):
    line = ''.join(charmap[min(pixels[y*TEX_W+x], 15)] for x in range(130, 206))
    if any(pixels[y*TEX_W+x] > 0 for x in range(130, 206)):
        print(f"  y{y}: {line}")

# Per-column density for segment 1
print("\n  Column densities:")
for x in range(130, 206):
    d = sum(pixels[y*TEX_W+x] for y in range(153, 166))
    marker = " <<< LOW" if d < 10 else (" << low" if d < 20 else "")
    print(f"    x={x}: {d:4d}{marker}")

# ============================================================
# REGION 5 UPPER: small text group (144,176)-(186,192)
# ============================================================
print("\n" + "=" * 70)
print("REGION 5 UPPER: Per-column density")
print("=" * 70)
for x in range(144, 188):
    d = sum(pixels[y*TEX_W+x] for y in range(176, 192))
    marker = " <<< LOW" if d < 5 else (" << low" if d < 10 else "")
    print(f"  x={x}: {d:4d}{marker}")

# ============================================================
# REGION 5 LOWER: two segments (145-167, width=22) and (174-188, width=14)
# ============================================================
print("\n" + "=" * 70)
print("REGION 5 LOWER analysis")
print("=" * 70)
print("\n--- Segment 0 (x=145-167, width=22) - likely 1 kanji ---")
for y in range(198, 217):
    line = ''.join(charmap[min(pixels[y*TEX_W+x], 15)] for x in range(145, 167))
    if any(pixels[y*TEX_W+x] > 0 for x in range(145, 167)):
        print(f"  y{y}: {line}")

print("\n--- Segment 1 (x=174-188, width=14) - likely 1 kanji ---")
for y in range(198, 217):
    line = ''.join(charmap[min(pixels[y*TEX_W+x], 15)] for x in range(174, 188))
    if any(pixels[y*TEX_W+x] > 0 for x in range(174, 188)):
        print(f"  y{y}: {line}")

# Save specific region extractions at 8x
extract_save(35, 153, 51, 166, "r2138_sub25_r3_char1_8x.png")
extract_save(51, 153, 67, 166, "r2138_sub25_r3_char2_8x.png")
extract_save(130, 153, 206, 166, "r2138_sub25_r3_seg1_8x.png")
extract_save(213, 153, 232, 166, "r2138_sub25_r3_triangle_8x.png")
extract_save(145, 198, 167, 217, "r2138_sub25_r5l_char1_8x.png")
extract_save(174, 198, 188, 217, "r2138_sub25_r5l_char2_8x.png")
extract_save(4, 188, 68, 212, "r2138_sub25_r4_left_8x.png")
extract_save(68, 188, 122, 212, "r2138_sub25_r4_right_8x.png")
extract_save(5, 226, 60, 249, "r2138_sub25_r6_left_8x.png")
extract_save(60, 226, 107, 249, "r2138_sub25_r6_mid_8x.png")
extract_save(109, 226, 121, 252, "r2138_sub25_r6_right_8x.png")
print("\nExtracted sub-region PNGs saved.")
