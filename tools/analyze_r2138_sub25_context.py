#!/usr/bin/env python3
"""
Context-based character identification for R2138 sub25.
Cross-reference with known Wizardry Busin 0 game text.
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

print("=" * 70)
print("FINAL CHARACTER IDENTIFICATION - R2138 sub25")
print("Level Up Notification Screen")
print("=" * 70)

# ============================================================
# REGION 4: レベルアップ!! (Level Up!!)
# ============================================================
print("""
REGION 4 (x4-122, y176-217): LARGE ANTI-ALIASED TEXT

The text is rendered with heavy anti-aliasing (values 0-F with smooth gradients).
It forms one continuous phrase split by a density gap at x66-71.

LEFT PORTION (x4-65):
  The expanding triangular shape (wider at bottom, narrow peak at top)
  with internal curved strokes is characteristic of:
  - レ (re): The leftmost expanding curve (x4-20)
  - ベ (be): The middle section with two short horizontal/diagonal strokes (x20-44)
  - ル (ru): The rightmost section with two near-vertical strokes (x44-65)
  Combined: レベル = "Level" (reberu)

RIGHT PORTION (x66-122):
  The density dips reveal character structure:
  - x72-89 peak: ア (a) - horizontal bar with downward diagonal
  - x89-91 gap, then x93-105 peak: ップ (small-tsu + pu)
    Actually the two peaks at x75-88 and x85-97 overlap significantly
    This is ップ with the ッ being smaller/narrower
  - x105-120: Two vertical strokes = !! (exclamation marks)
    - x109-112: First !
    - x116-119: Second !
    - Each has a dense core with AA fading
  Combined: アップ!! = "Up!!"

FULL TEXT: レベルアップ!! = "LEVEL UP!!"
""")

# ============================================================
# REGION 6: Similar large AA text
# ============================================================
print("""
REGION 6 (x5-121, y224-254): LARGE ANTI-ALIASED TEXT LINE 2

Structure based on density breaks:
  Break points: x48 (BREAK), x59 (BREAK), x65 (BREAK), x70-71 (BREAK),
                x106-108 (BREAK), x114 (BREAK)

Identified characters:
  x5-22 (17px): レ (re) - expanding leftward curve, same style as Region 4

  x24-48 (24px): Contains multiple strokes including:
    - Horizontal bar at top connecting to hook
    - Cross strokes
    - Diagonal strokes below
    This is TWO characters: ベル (be-ru) at approx x24-32 and x33-48
    Wait - density shows continuous strokes from x24-48
    Actually this section x24-48 has THREE distinct stroke groups visible:
    x24-32: vertical + curved strokes = ベ (be)
    x33-48: two near-vertical strokes with base = ル (ru)

  So x5-48 = レベル = "Level" again? No, that seems too wide.

  Actually, let me reconsider by looking at the character shapes more carefully.
  The R6 LEFT shows DIFFERENT internal structure than R4's レベル.

  x5-22: Expanding curve = similar to レ but also matches the kanji 経
    Actually: y230-y248 shows:
    - Left edge: triangle outline expanding left (x5-16)
    - Right side: vertical strokes at x17-21
    This is NOT レ. The internal structure has vertical lines that レ doesn't have.

  Let me reconsider: could this be 経験値獲得!! (EXP gained)?
  経 (kei): Left radical 糸 (thread) + right part

  Actually, with the game context, the level-up screen would show:
  Line 1: レベルアップ!! (Level Up!!)
  Line 2: Could be one of:
    - スキルアップ!! (Skill Up!!)
    - ボーナスポイント (Bonus Points)
    - 能力アップ!! (Ability Up!!)
""")

# Let me compare R6 LEFT (x5-22) with R4 LEFT (x4-20) more precisely
print("DETAILED COMPARISON: R4 レ vs R6 first char")
print("=" * 70)

print("\nR4 first char (x4-22, y192-210):")
for y in range(192, 211):
    line = ''
    for x in range(4, 22):
        v = pixels[y*TEX_W+x]
        if v >= 7: line += '#'
        elif v >= 3: line += '.'
        else: line += ' '
    print(f"  y{y}: {line}")

print("\nR6 first char (x5-22, y232-249):")
for y in range(232, 250):
    line = ''
    for x in range(5, 22):
        v = pixels[y*TEX_W+x]
        if v >= 7: line += '#'
        elif v >= 3: line += '.'
        else: line += ' '
    print(f"  y{y}: {line}")

# Now let me compare R4 area around "アップ" with R6 area after the tall vertical
# R4 アップ is at x72-105
# R6 after vertical line is at x72-105
print("\nR4 'アップ' (x72-106, y196-209):")
for y in range(196, 210):
    line = ''
    for x in range(72, 106):
        v = pixels[y*TEX_W+x]
        if v >= 7: line += '#'
        elif v >= 3: line += '.'
        else: line += ' '
    print(f"  y{y}: {line}")

print("\nR6 same area (x72-106, y235-249):")
for y in range(235, 250):
    line = ''
    for x in range(72, 106):
        v = pixels[y*TEX_W+x]
        if v >= 7: line += '#'
        elif v >= 3: line += '.'
        else: line += ' '
    print(f"  y{y}: {line}")

# The critical difference: R6 has a TALL VERTICAL LINE at x61-63 that R4 doesn't
# This changes everything. Let me look at what character has a tall vertical line.
#
# In katakana: ト (to), ド (do) - single vertical stroke
# The R6 x61-63 vertical line with a small top-right hook (y226-229) looks like:
# - ト (to) katakana
# - Or part of a larger character
#
# Given that it has hooks at top-right (y226-229: ##.####. / ##..## / ##.  .##)
# This is actually ポ (po) - the combination of a vertical stroke + two dots
# Wait no, looking again:
# y226: .....##
# y227: ....#####.
# y228: ...##.####.
# y229: ..##..##
# y230: .###
# y231-y245: .### (continuous vertical)
# y246: .####.
# This is a tall vertical line with a decorative top - looks like ポ or ド
# Actually the top part (y226-229) shows a separate small shape at the RIGHT
# of the vertical. This is ポ (po): ホ radical with two dots.
# But ポ has a horizontal bar...
#
# Actually the y226-229 area shows:
# y227:  #####.
# y228: ##.####.
# y229: ##  .##   #
# This is more like ボ (bo) with dakuten, or simply an elongated stroke.
#
# Wait - I should look at this differently. The tall vertical from y230-y246
# with the top-right decoration is EXACTLY the shape of:
# イ (i) katakana - a single tall vertical stroke with a short diagonal at top-right
# No wait, イ has a SHORT diagonal, not a curved hook.
#
# This is actually ド (do) - which has a vertical line + two small marks at top
#
# Hmm, let me just look at the full R6 structure with fresh eyes.

print("\n" + "=" * 70)
print("REGION 6 FULL TEXT - Fresh analysis at threshold>=5")
print("=" * 70)
for y in range(226, 250):
    line = ''
    for x in range(5, 121):
        v = pixels[y*TEX_W+x]
        if v >= 7: line += '#'
        elif v >= 3: line += '.'
        else: line += ' '
    print(f"  y{y}: {line}")
