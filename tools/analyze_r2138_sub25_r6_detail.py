#!/usr/bin/env python3
"""
Deep analysis of Region 6 characters and Region 3 Segment 1 in R2138 sub25.
Try to identify individual characters by finding density dips.
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

# ============================================================
# REGION 6: Let me carefully trace each character
# Looking at the threshold=7 output from the previous run:
#
# LEFT (x5-59):
# The expanding triangle pattern on left (x5-17) is IDENTICAL to Region 4
# This is clearly the same katakana レ style
# Then strokes at x18-32 followed by more at x33-59
#
# But wait - let me reconsider. Region 4 = "レベルアップ!!" (Level Up!!)
# Region 6 is a DIFFERENT text on the SAME screen
# In Wizardry level-up screens, common second-line text would be:
# - 経験値獲得!! (keiken-chi kakutoku = Experience gained!!)
# - レベルが上がった!! (level went up!!)
#
# Let me look at Region 6 more carefully character by character
# ============================================================

print("=" * 70)
print("REGION 6 DETAILED CHARACTER-BY-CHARACTER ANALYSIS")
print("=" * 70)

# Region 6: x5-121, y226-249
# Let me look at VERY fine density to find character breaks

print("\nColumn density (every column):")
densities = []
for x in range(5, 121):
    d = sum(pixels[y*TEX_W+x] for y in range(228, 249))
    densities.append((x, d))

# Find local minima that could be character boundaries
for i, (x, d) in enumerate(densities):
    is_min = True
    if i > 2 and i < len(densities) - 2:
        neighbors = [densities[j][1] for j in range(i-2, i+3) if j != i]
        if d < min(neighbors) * 0.7:
            is_min = True
        else:
            is_min = False
    marker = ""
    if d < 15: marker = " *** BREAK"
    elif d < 25: marker = " ** low"
    elif d < 40: marker = " * dip"
    print(f"  x={x:3d}: {d:4d}{marker}")

# Key breaks in region 6:
# x22-23: density drops to ~17-33 -> break between char1 and char2
# x47-48: density drops to ~10-39 -> break between char3 and char4
# x58-59: density drops to ~12-23 -> break before the tall vertical line
# x70-71: density drops to ~8 -> break
# x106-108: density drops to ~5-9 -> break before !!

print("\n" + "=" * 70)
print("REGION 6: Character segments based on density dips")
print("=" * 70)

# Segment boundaries: (5,22), (23,48), (48,59), (59,71), (71,107), (107,121)
# But this gives too many segments. Let me look at the actual stroke patterns.

# Character 1: x5-22 (width=17)
print("\n--- R6 Char 1 (x5-22) ---")
for y in range(228, 249):
    line = ''
    for x in range(5, 22):
        v = pixels[y*TEX_W+x]
        if v >= 7: line += '#'
        elif v >= 3: line += '.'
        else: line += ' '
    if '#' in line or '.' in line:
        print(f"  y{y}: {line}")

# Character 2: x24-48
print("\n--- R6 Char 2 (x24-48) ---")
for y in range(228, 249):
    line = ''
    for x in range(24, 48):
        v = pixels[y*TEX_W+x]
        if v >= 7: line += '#'
        elif v >= 3: line += '.'
        else: line += ' '
    if '#' in line or '.' in line:
        print(f"  y{y}: {line}")

# Character 3: x49-59
print("\n--- R6 Char 3 (x49-59) ---")
for y in range(228, 249):
    line = ''
    for x in range(49, 59):
        v = pixels[y*TEX_W+x]
        if v >= 7: line += '#'
        elif v >= 3: line += '.'
        else: line += ' '
    if '#' in line or '.' in line:
        print(f"  y{y}: {line}")

# The tall vertical line at x61-63 + surroundings
print("\n--- R6 Area x59-72 (tall vertical + context) ---")
for y in range(226, 250):
    line = ''
    for x in range(59, 72):
        v = pixels[y*TEX_W+x]
        if v >= 7: line += '#'
        elif v >= 3: line += '.'
        else: line += ' '
    if '#' in line or '.' in line:
        print(f"  y{y}: {line}")

# Characters after the vertical line
print("\n--- R6 Area x72-107 ---")
for y in range(228, 249):
    line = ''
    for x in range(72, 107):
        v = pixels[y*TEX_W+x]
        if v >= 7: line += '#'
        elif v >= 3: line += '.'
        else: line += ' '
    if '#' in line or '.' in line:
        print(f"  y{y}: {line}")

# ============================================================
# Now let's look at the R6 characters more carefully with game context
# Region 4 = レベルアップ!! (Level Up!!)
# Region 6 should be a complementary phrase
# Common Wizardry phrases:
#   経験値 (keiken-chi = EXP)
#   獲得 (kakutoku = obtained/gained)
#   ポイント (pointo = points)
#   スキル (sukiru = skill)
#
# But looking at the stroke patterns:
# R6 Left (x5-59): Same expanding curve as R4 left
#   -> This strongly suggests it's also katakana starting with レ
#
# Actually, let me reconsider the entire shape.
# Looking at R6 LEFT (threshold=7):
# x5-17: triangle expanding left (like R4's レ)
# x17-32: internal strokes
# x33-48: more strokes with curve
# x49-59: strokes continuing
#
# If R4 is レベルアップ!! then R6 could be a DIFFERENT word
# Let me compare R4 and R6 side by side
# ============================================================

print("\n" + "=" * 70)
print("COMPARISON: Region 4 LEFT vs Region 6 LEFT")
print("=" * 70)

print("\nR4 LEFT (x4-65, y196-208) - known as レベル:")
for y in range(196, 209):
    line = ''
    for x in range(4, 65):
        v = pixels[y*TEX_W+x]
        if v >= 7: line += '#'
        elif v >= 3: line += '.'
        else: line += ' '
    print(f"  y{y}: {line}")

print("\nR6 LEFT (x5-59, y235-248) at same scale:")
for y in range(235, 249):
    line = ''
    for x in range(5, 59):
        v = pixels[y*TEX_W+x]
        if v >= 7: line += '#'
        elif v >= 3: line += '.'
        else: line += ' '
    print(f"  y{y}: {line}")

print("\n\nR4 RIGHT (x66-122, y196-208) - known as アップ!!:")
for y in range(196, 209):
    line = ''
    for x in range(66, 122):
        v = pixels[y*TEX_W+x]
        if v >= 7: line += '#'
        elif v >= 3: line += '.'
        else: line += ' '
    print(f"  y{y}: {line}")

print("\nR6 RIGHT (x59-121, y235-248):")
for y in range(235, 249):
    line = ''
    for x in range(59, 121):
        v = pixels[y*TEX_W+x]
        if v >= 7: line += '#'
        elif v >= 3: line += '.'
        else: line += ' '
    print(f"  y{y}: {line}")
