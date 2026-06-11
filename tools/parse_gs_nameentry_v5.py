#!/usr/bin/env python3
"""Analyze name entry keyboard grid from GS dump data.

Based on v4 output, we know:
- TBP0=0x2840 TBW=4 PSMT4 256x256 CBP=0x28C0
- 160 draws total (80 per frame, doubled for 2 vsyncs)
- Each cell is 16x16 pixels in the atlas
- The atlas is 256x256 = 16 columns x 16 rows of cells

Key observation from v4 data:
- The keyboard grid rows are at Y~152, Y~172, Y~192, Y~212, Y~232, Y~252
- Each row has ~10 cells spaced at 24px with a gap at X~228
- Cells are drawn RIGHT-TO-LEFT (high X first), BOTTOM-TO-TOP

The cell indices used are sequential: 33-90 plus some from row 0.
Let's map these to characters.

Critical question: are cell indices 6,2 (col=6,row=2) = index 38
and 13,2 (col=13,row=2) = index 45 present? Those would be F and M
if the atlas goes A=33, B=34, C=35, D=36, E=37, F=38, G=39...
"""

# Data from v4 output - cells used in keyboard grid (first frame only)
# Format: (cell_col, cell_row, cell_idx, screen_x, screen_y)
keyboard_cells = [
    # Row Y~152 (row 1 of keyboard, bottom of first visible row going up)
    (1,2,33, 100, 152),   # col 0
    (2,2,34, 124, 152),   # col 1
    (3,2,35, 148, 152),   # col 2
    (4,2,36, 172, 152),   # col 3
    (5,2,37, 196, 152),   # col 4
    # GAP at X=220
    (7,2,39, 252, 152),   # col 5 (after gap)
    (8,2,40, 276, 152),   # col 6
    (9,2,41, 300, 152),   # col 7
    (10,2,42, 324, 152),  # col 8

    # Row Y~172
    (11,2,43, 100, 172),
    (12,2,44, 124, 172),
    # GAP at X=148 (cell 45 = (13,2) MISSING!)
    (14,2,46, 172, 172),
    (15,2,47, 196, 172),
    (0,3,48, 228, 172),
    (1,3,49, 252, 172),
    (2,3,50, 276, 172),
    (3,3,51, 300, 172),
    (4,3,52, 324, 172),

    # Row Y~192
    (5,3,53, 100, 192),
    (6,3,54, 124, 192),
    (7,3,55, 148, 192),
    (8,3,56, 172, 192),
    (9,3,57, 196, 192),
    (10,3,58, 228, 192),
    (14,0,14, 252, 192),  # NOT sequential! Uses cell 14 instead of 59?
    (12,0,12, 276, 192),  # Uses cell 12
    (1,0,1, 300, 192),    # Uses cell 1
    (15,1,31, 324, 192),  # Uses cell 31

    # Row Y~212
    (1,4,65, 100, 212),
    (2,4,66, 124, 212),
    (3,4,67, 148, 212),
    (4,4,68, 172, 212),
    (5,4,69, 196, 212),
    (6,4,70, 228, 212),
    (7,4,71, 252, 212),
    (8,4,72, 276, 212),
    (9,4,73, 300, 212),
    (10,4,74, 324, 212),

    # Row Y~232
    (11,4,75, 100, 232),
    (12,4,76, 124, 232),
    (13,4,77, 148, 232),
    (14,4,78, 172, 232),
    (15,4,79, 196, 232),
    (0,5,80, 228, 232),
    (1,5,81, 252, 232),
    (2,5,82, 276, 232),
    (3,5,83, 300, 232),
    (4,5,84, 324, 232),

    # Row Y~252
    (5,5,85, 100, 252),
    (6,5,86, 124, 252),
    (7,5,87, 148, 252),
    (8,5,88, 172, 252),
    (9,5,89, 196, 252),
    (10,5,90, 228, 252),
    (0,0,0, 252, 252),    # Not sequential - uses cell 0
    (13,0,13, 276, 252),  # Uses cell 13
    (7,0,7, 300, 252),    # Uses cell 7
]

# The original Japanese name entry keyboard has hiragana/katakana
# After patching with English, the R1188 (or R2100) atlas should have ASCII
# But TBP0=0x2840 is a DIFFERENT atlas from R1188/R2100

# Key analysis: what cell indices are MISSING from the keyboard grid?

# Sequential range that SHOULD be present if it's A-Z + specials:
# The keyboard appears to use cells 33-90 for the grid
# With some cells from row 0 (0,1,7,12,13,14) for special characters
# And cell 31 for something

# Full list of sequential cells that should appear:
all_grid_cells = set()
for cc, cr, ci, sx, sy in keyboard_cells:
    all_grid_cells.add(ci)

print("CELLS USED IN KEYBOARD GRID:")
print(sorted(all_grid_cells))

print(f"\nTotal unique cells: {len(all_grid_cells)}")

# Check for gaps in the sequential range 33-90
print("\nSEQUENTIAL RANGE ANALYSIS (cells 33-90):")
for i in range(33, 91):
    status = "PRESENT" if i in all_grid_cells else "*** MISSING ***"
    col = i % 16
    row = i // 16
    print(f"  Cell {i:3d} ({col:2d},{row:2d}): {status}")

# Key finding: Cell 38 (6,2) is MISSING - this would be F if A=33
# Cell 45 (13,2) is MISSING - this would be M if A=33
# Cell 59-64 are MISSING - these are the chars after Z

print("\n" + "=" * 70)
print("CRITICAL FINDING: MISSING CELLS")
print("=" * 70)

# If A=33, then:
# A=33, B=34, C=35, D=36, E=37, F=38, G=39, H=40, I=41, J=42
# K=43, L=44, M=45, N=46, O=47, P=48, Q=49, R=50, S=51, T=52
# U=53, V=54, W=55, X=56, Y=57, Z=58
# Then 59-64 would be special chars, 65 onwards = lowercase or more

missing_33_90 = [i for i in range(33, 91) if i not in all_grid_cells]
print(f"Missing cells in range 33-90: {missing_33_90}")

if 38 in missing_33_90:
    print("  Cell 38 = F (if A=33) is MISSING!")
if 45 in missing_33_90:
    print("  Cell 45 = M (if A=33) is MISSING!")

print(f"\nMapping (if cell 33 = 'A'):")
for i in range(33, 59):
    letter = chr(ord('A') + (i - 33))
    status = "DRAWN" if i in all_grid_cells else "MISSING"
    print(f"  Cell {i} = '{letter}': {status}")

# Also check the gap in row Y~152
print("\n" + "=" * 70)
print("GAPS IN SCREEN LAYOUT")
print("=" * 70)

print("\nRow Y~152 (first alphabet row):")
print("  X=100(33), 124(34), 148(35), 172(36), 196(37)")
print("  GAP: X=220 expected cell 38 (F) - NOT DRAWN")
print("  X=252(39), 276(40), 300(41), 324(42)")

print("\nRow Y~172 (second alphabet row):")
print("  X=100(43), 124(44)")
print("  GAP: X=148 expected cell 45 (M) - NOT DRAWN")
print("  X=172(46), 196(47), 228(48), 252(49), 276(50), 300(51), 324(52)")

print("\nRow Y~192 (third alphabet row + specials):")
print("  X=100(53), 124(54), 148(55), 172(56), 196(57), 228(58)")
print("  X=252(14?), 276(12?), 300(1?), 324(31?)")
print("  NOTE: After Z (cell 58), the game uses non-sequential cells")
print("  Cells 59-64 are SKIPPED entirely - these are blank/unused in atlas?")

print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)
print("""
The name entry screen uses TBP0=0x2840 (256x256 PSMT4, TBW=4, CBP=0x28C0).

The keyboard grid draws cells 33-90 sequentially (with gaps) for the main
character set. If cell 33='A', then:

  Cell 38 = 'F' -- THIS CELL IS NEVER DRAWN (gap at X=220 in row Y~152)
  Cell 45 = 'M' -- THIS CELL IS NEVER DRAWN (gap at X=148 in row Y~172)

The game SKIPS drawing at these grid positions. It's not drawing a wrong
character -- it's not drawing ANYTHING at the F and M positions.

This is NOT a texture/atlas issue. The DRAW CALLS themselves are missing.
The game's rendering code skips F and M entirely.

Additional observations:
- Cells 59-64 (after Z) are also skipped
- The last 4 positions in row Y~192 use non-sequential cells (0,1,7,12,13,14,31)
  which are likely special characters (space, -, etc.)
- Cell (14,6)=110 is used for cursor/placeholder blanks
- The atlas at TBP0=0x2840 is uploaded via host->local transfer, NOT via BITBLTBUF
""")

if __name__ == '__main__':
    main() if False else None
