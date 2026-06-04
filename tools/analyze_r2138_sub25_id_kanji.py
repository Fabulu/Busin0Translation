#!/usr/bin/env python3
"""
Final kanji identification pass for R2138 sub25.
Render specific characters at high zoom for comparison with known kanji.
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

charmap = '.' + '123456789ABCDEF'

# ============================================================
# Region 4 deep character analysis
# The threshold=8 view shows the core strokes clearly:
# LEFT half (x4-65):
#   - y190-209: A shape that expands from top to bottom
#   - Top: narrow peak (~6px wide at y190)
#   - Bottom: very wide (~50px at y208)
#   - Left edge curves out progressively
#   - Right side has a vertical stroke + diagonal branch
#   - This expanding triangular shape with internal structure is characteristic
#     of レベル (Reberu) written as a connected word, OR
#     could be a single large kanji
#
# Looking again at threshold=8:
# The LEFT portion x4-65 has:
# - A triangle-like outline that opens downward (lines 190-209 get progressively wider)
# - Internal: vertical line near x14-16, a curve x22-28, another curve x36-54
# - The bottom is a FLAT BASE (y208-209: continuous ###### across full width)
#
# This is actually NOT text characters - this is a DECORATIVE SHAPE/ARROW
# pointing upward! Like an upward arrow or triangle indicating "level up"
#
# Wait, let me reconsider. Let me look at what the original agent said:
# "3 large characters possibly レベル!! (Level Up!!)"
#
# Let me look at the RIGHT portion more carefully
# ============================================================

print("=" * 70)
print("REGION 4 - Separated into LEFT HALF and RIGHT HALF")
print("=" * 70)

# LEFT: x4-65, but the actual "content" is one big shape
# Let me check if it could be レベル written large
# レ = katakana re: looks like a backwards J or hook
# ベ = katakana be: two strokes going right-down from center
# ル = katakana ru: two vertical strokes, right one curves right

# At threshold 7, the LEFT side shows:
# Upper portion (y196-y200): a shape with internal structure
# - Left side: expanding triangle outline
# - Right side: two separate curved areas
# This is CLEARLY multiple katakana characters written with heavy AA

# Let me look at specific vertical slices
print("\nLEFT (x4-65) - Row by row at threshold>=7:")
for y in range(188, 213):
    line = ''
    for x in range(4, 65):
        v = pixels[y*TEX_W+x]
        if v >= 7: line += '#'
        elif v >= 3: line += '.'
        else: line += ' '
    print(f"  y{y:3d}: {line}")

print("\nRIGHT (x66-122) - Row by row at threshold>=7:")
for y in range(188, 213):
    line = ''
    for x in range(66, 122):
        v = pixels[y*TEX_W+x]
        if v >= 7: line += '#'
        elif v >= 3: line += '.'
        else: line += ' '
    print(f"  y{y:3d}: {line}")

# ============================================================
# Region 6 - Second line of large text
# ============================================================
print("\n" + "=" * 70)
print("REGION 6 - LEFT (x5-59) at threshold>=7")
print("=" * 70)
for y in range(226, 250):
    line = ''
    for x in range(5, 59):
        v = pixels[y*TEX_W+x]
        if v >= 7: line += '#'
        elif v >= 3: line += '.'
        else: line += ' '
    print(f"  y{y:3d}: {line}")

print("\nREGION 6 - MID (x59-107) at threshold>=7")
for y in range(226, 250):
    line = ''
    for x in range(59, 107):
        v = pixels[y*TEX_W+x]
        if v >= 7: line += '#'
        elif v >= 3: line += '.'
        else: line += ' '
    print(f"  y{y:3d}: {line}")

print("\nREGION 6 - RIGHT (x107-121) at threshold>=7")
for y in range(226, 253):
    line = ''
    for x in range(107, 121):
        v = pixels[y*TEX_W+x]
        if v >= 7: line += '#'
        elif v >= 3: line += '.'
        else: line += ' '
    print(f"  y{y:3d}: {line}")

# ============================================================
# Region 5 upper - 3 small kanji
# ============================================================
print("\n" + "=" * 70)
print("REGION 5 UPPER - Three characters at threshold>=3")
print("=" * 70)
print("\nChar 1 (x146-158, y176-192):")
for y in range(176, 192):
    line = ''
    for x in range(146, 158):
        v = pixels[y*TEX_W+x]
        if v >= 5: line += '#'
        elif v >= 2: line += '.'
        else: line += ' '
    print(f"  y{y:3d}: {line}")

print("\nChar 2 (x159-172, y176-192):")
for y in range(176, 192):
    line = ''
    for x in range(159, 172):
        v = pixels[y*TEX_W+x]
        if v >= 5: line += '#'
        elif v >= 2: line += '.'
        else: line += ' '
    print(f"  y{y:3d}: {line}")

print("\nChar 3 (x174-186, y176-192):")
for y in range(176, 192):
    line = ''
    for x in range(174, 186):
        v = pixels[y*TEX_W+x]
        if v >= 5: line += '#'
        elif v >= 2: line += '.'
        else: line += ' '
    print(f"  y{y:3d}: {line}")
