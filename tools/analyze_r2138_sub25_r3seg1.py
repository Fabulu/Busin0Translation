#!/usr/bin/env python3
"""
Split R3 segment 1 into sub-characters using background columns.
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

# R3 Seg1 spans x=130 to x=205
# Background breaks at x=130-131 (BG), x=172-175 (BG)
# So we have two character groups:
# Group A: x=132-171 (40px = likely 3 kanji at ~13px each)
# Group B: x=176-205 (30px = likely 2 kanji at ~15px each)

print("=" * 70)
print("R3 SEG1 GROUP A: x=132-171 (40 pixels)")
print("=" * 70)

# Check for internal breaks within group A
print("\nColumn min values:")
for x in range(132, 172):
    min_v = min(pixels[y*TEX_W+x] for y in range(155, 165))
    max_v = max(pixels[y*TEX_W+x] for y in range(155, 165))
    if min_v >= 8:
        print(f"  x={x}: min={min_v} max={max_v} *** POSSIBLE BREAK")

# Show inverted text for group A
print("\nGroup A inverted (< 7 = text):")
for y in range(154, 166):
    line = ''
    for x in range(132, 172):
        v = pixels[y*TEX_W+x]
        if v < 4: line += '#'
        elif v < 7: line += '.'
        else: line += ' '
    if '#' in line:
        print(f"  y{y}: {line}")

print("\n" + "=" * 70)
print("R3 SEG1 GROUP B: x=176-205 (30 pixels)")
print("=" * 70)

# Check for internal breaks
print("\nColumn min values:")
for x in range(176, 206):
    min_v = min(pixels[y*TEX_W+x] for y in range(155, 165))
    max_v = max(pixels[y*TEX_W+x] for y in range(155, 165))
    if min_v >= 8:
        print(f"  x={x}: min={min_v} max={max_v} *** POSSIBLE BREAK")

# Show inverted text for group B
print("\nGroup B inverted (< 7 = text):")
for y in range(154, 166):
    line = ''
    for x in range(176, 206):
        v = pixels[y*TEX_W+x]
        if v < 4: line += '#'
        elif v < 7: line += '.'
        else: line += ' '
    if '#' in line:
        print(f"  y{y}: {line}")

# R3 Seg0: x=35-66 - also check for internal breaks
print("\n" + "=" * 70)
print("R3 SEG0: x=35-66 column analysis")
print("=" * 70)
print("\nColumn min values:")
for x in range(35, 67):
    min_v = min(pixels[y*TEX_W+x] for y in range(155, 165))
    max_v = max(pixels[y*TEX_W+x] for y in range(155, 165))
    if min_v >= 8:
        print(f"  x={x}: min={min_v} max={max_v} *** POSSIBLE BREAK")

# Split seg0 based on breaks
# If there's a break around x=50-51 that would give us two chars
# Let me check
print("\nSeg0 LEFT (x=35-50) inverted:")
for y in range(155, 165):
    line = ''
    for x in range(35, 51):
        v = pixels[y*TEX_W+x]
        if v < 4: line += '#'
        elif v < 7: line += '.'
        else: line += ' '
    if '#' in line:
        print(f"  y{y}: {line}")

print("\nSeg0 RIGHT (x=51-66) inverted:")
for y in range(155, 165):
    line = ''
    for x in range(51, 67):
        v = pixels[y*TEX_W+x]
        if v < 4: line += '#'
        elif v < 7: line += '.'
        else: line += ' '
    if '#' in line:
        print(f"  y{y}: {line}")
