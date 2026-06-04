#!/usr/bin/env python3
"""
Detailed analysis of R5 upper characters and R3 segment 1.
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

# Region 5 upper chars at threshold 3 with full pixel values
# R5U Char 1 (x146-158):
# Shape: horizontal bar at top, vertical stroke going down, base spreading
# This looks like 次 (next)
#   - Top has horizontal line with hook
#   - Cross stroke
#   - Lower diagonal strokes
# Actually let me reconsider with the pixel map:
# y177: .....##      = small start
# y178: .....###     = grows
# y179: ###########  = wide horizontal bar
# y180: #### .##     = left heavy, right separate stroke
# y181: #######      = merges
# y182: .....###     = narrows
# y183: ....## ####  = splits: left stroke + right group
# y184: ###########  = full horizontal bar
# y185: ...#####     = center mass
# y186: ..#.###      = diagonal structure
# y187: ...####      = narrows
# y188: .......##    = tail
# y189: ......###    = continues
#
# This pattern with a prominent horizontal bar (y179), another bar (y184),
# and diagonal strokes between them matches 経 (kei) but more likely
# matches 次 (tsugi/ji) given the simpler structure

print("=" * 70)
print("R5 UPPER: Detailed character shapes")
print("=" * 70)

# Let me look at all three R5U chars with raw pixel values for comparison
chars_r5u = [
    ("Char 1", 146, 158, 176, 192),
    ("Char 2", 159, 172, 176, 192),
    ("Char 3", 174, 186, 176, 192),
]

charmap = '.' + '123456789ABCDEF'
for name, x1, x2, y1, y2 in chars_r5u:
    print(f"\n--- {name} (x{x1}-{x2}) raw values ---")
    for y in range(y1, y2):
        line = ''.join(charmap[min(pixels[y*TEX_W+x], 15)] for x in range(x1, x2))
        if any(pixels[y*TEX_W+x] > 0 for x in range(x1, x2)):
            print(f"  y{y}: {line}")

# Region 3 Segment 0: inverted text on gradient background
# x35-67, y153-166
# These are the title bar characters
print("\n" + "=" * 70)
print("R3 SEGMENT 0 INVERTED CHARACTERS (x35-67)")
print("=" * 70)

# Show at two different thresholds for the INVERTED text
# Background is F (15), text is lower values
print("\nRaw values:")
for y in range(153, 166):
    line = ''.join(charmap[min(pixels[y*TEX_W+x], 15)] for x in range(35, 67))
    print(f"  y{y}: {line}")

# Invert: show where value < 10 as '#' (text strokes)
print("\nInverted (val < 10 = text):")
for y in range(153, 166):
    line = ''
    for x in range(35, 67):
        v = pixels[y*TEX_W+x]
        if v < 5: line += '#'
        elif v < 10: line += '.'
        else: line += ' '
    if '#' in line or '.' in line:
        print(f"  y{y}: {line}")

# Region 3 Segment 1 inverted characters
print("\n" + "=" * 70)
print("R3 SEGMENT 1 INVERTED CHARACTERS (x130-206)")
print("=" * 70)

# Show inverted
print("\nInverted (val < 8 = text):")
for y in range(154, 166):
    line = ''
    for x in range(130, 206):
        v = pixels[y*TEX_W+x]
        if v < 4: line += '#'
        elif v < 8: line += '.'
        else: line += ' '
    if '#' in line or '.' in line:
        print(f"  y{y}: {line}")

# Try to find character boundaries in segment 1
# Look for columns where ALL values are >= 10 (background)
print("\nColumn min-values (to find breaks):")
for x in range(130, 206):
    min_v = min(pixels[y*TEX_W+x] for y in range(154, 166))
    if min_v >= 10:
        print(f"  x={x}: min={min_v} BACKGROUND")
    elif min_v >= 7:
        print(f"  x={x}: min={min_v} near-bg")

# Split segment 1 into sub-characters at background columns
# Based on the raw data, the text columns with lower vals:
# x130-162: continuous text
# possible break around x143-145 (FE...F values seen)
# x165-167: possible break
# x177-179: possible break
# x196-198: possible break
