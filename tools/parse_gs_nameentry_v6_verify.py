#!/usr/bin/env python3
"""Verify F and M gaps in name entry keyboard grid.

Focused verification: look at exact X positions in each keyboard row,
check spacing for gaps where F and M should be.

Also: verify cell-to-character mapping by checking the row Y~192
special chars and the name entry input field draws.
"""

# From v4 output, the keyboard grid draws (first frame, deduplicated):
# Each position appears TWICE (XYZ3 + XYZ2 for SPRITE), and then again in frame 2

# Row Y~152: cells 33-42 (A through J if 33=A)
row_152 = [
    (100, 33),  # (1,2)
    (124, 34),  # (2,2)
    (148, 35),  # (3,2)
    (172, 36),  # (4,2)
    (196, 37),  # (5,2)
    # Expected: X=220, cell 38 -- NOT PRESENT
    (252, 39),  # (7,2)
    (276, 40),  # (8,2)
    (300, 41),  # (9,2)
    (324, 42),  # (10,2)
]

# Row Y~172: cells 43-52 (K through T if 33=A)
row_172 = [
    (100, 43),  # (11,2)
    (124, 44),  # (12,2)
    # Expected: X=148, cell 45 -- NOT PRESENT
    (172, 46),  # (14,2) -- NOTE: jumps from X=124 to X=172 (gap of 48, not 24!)
    (196, 47),  # (15,2)
    (228, 48),  # (0,3) -- also larger gap (32 instead of 24)
    (252, 49),  # (1,3)
    (276, 50),  # (2,3)
    (300, 51),  # (3,3)
    (324, 52),  # (4,3)
]

# Row Y~192: cells 53-58 then special chars
row_192 = [
    (100, 53),  # (5,3) = U
    (124, 54),  # (6,3) = V
    (148, 55),  # (7,3) = W
    (172, 56),  # (8,3) = X
    (196, 57),  # (9,3) = Y
    (228, 58),  # (10,3) = Z
    (252, 14),  # (14,0) = special
    (276, 12),  # (12,0) = special
    (300, 1),   # (1,0) = special
    (324, 31),  # (15,1) = special
]

print("=" * 70)
print("KEYBOARD ROW ANALYSIS")
print("=" * 70)

print("\nRow Y~152 (A-J):")
print("  Position  CellIdx  Expected   Spacing")
prev_x = None
for x, cell in row_152:
    letter = chr(ord('A') + cell - 33) if 33 <= cell <= 58 else f"#{cell}"
    spacing = f"{x - prev_x:+d}" if prev_x is not None else "  --"
    print(f"  X={x:4d}     {cell:3d}      '{letter}'       {spacing}")
    prev_x = x

print(f"\n  *** GAP between X=196 (E, cell 37) and X=252 (G, cell 39)")
print(f"  *** Expected X=220 for F (cell 38) -- NOT DRAWN")
print(f"  *** Gap = 56px, normal spacing = 24px")
print(f"  *** Missing: exactly 1 cell position (56 - 24 = 32, or 56/24 ~ 2.3)")

# Wait -- actually the spacing ISN'T uniform. Let me recalculate.
print(f"\n  Spacings: ", end="")
for i in range(len(row_152)-1):
    print(f"{row_152[i+1][0] - row_152[i][0]}", end=" ")
print()

print(f"\nRow Y~172 (K-T):")
prev_x = None
for x, cell in row_172:
    letter = chr(ord('A') + cell - 33) if 33 <= cell <= 58 else f"#{cell}"
    spacing = f"{x - prev_x:+d}" if prev_x is not None else "  --"
    print(f"  X={x:4d}     {cell:3d}      '{letter}'       {spacing}")
    prev_x = x

print(f"\n  *** GAP between X=124 (L, cell 44) and X=172 (N, cell 46)")
print(f"  *** Expected X=148 for M (cell 45) -- NOT DRAWN")
print(f"  *** Gap = 48px, normal spacing = 24px")

print(f"\n  Spacings: ", end="")
for i in range(len(row_172)-1):
    print(f"{row_172[i+1][0] - row_172[i][0]}", end=" ")
print()

# Check row Y~212 for consistency (should be row 4 of grid = second alphabet page?)
# Row Y~212: cells 65-74
row_212 = [
    (100, 65),   # (1,4)
    (124, 66),   # (2,4)
    (148, 67),   # (3,4)
    (172, 68),   # (4,4)
    (196, 69),   # (5,4)
    (228, 70),   # (6,4)
    (252, 71),   # (7,4)
    (276, 72),   # (8,4)
    (300, 73),   # (9,4)
    (324, 74),   # (10,4)
]

print(f"\nRow Y~212 (lowercase a-j if 65='a'):")
print(f"  Spacings: ", end="")
for i in range(len(row_212)-1):
    print(f"{row_212[i+1][0] - row_212[i][0]}", end=" ")
print()
print(f"  NOTE: consistent spacing 24,24,24,24,32,24,24,24,24")
print(f"  The 32px gap at X=196->228 is the mid-row separator")
print(f"  ALL 10 cells present -- NO gaps in the lowercase row!")

# Row Y~232: cells 75-84
row_232 = [
    (100, 75),   # (11,4)
    (124, 76),   # (12,4)
    (148, 77),   # (13,4)
    (172, 78),   # (14,4)
    (196, 79),   # (15,4)
    (228, 80),   # (0,5)
    (252, 81),   # (1,5)
    (276, 82),   # (2,5)
    (300, 83),   # (3,5)
    (324, 84),   # (4,5)
]

print(f"\nRow Y~232 (lowercase k-t if 65='a'):")
print(f"  Spacings: ", end="")
for i in range(len(row_232)-1):
    print(f"{row_232[i+1][0] - row_232[i][0]}", end=" ")
print()
print(f"  ALL 10 cells present -- NO gaps!")

# Row Y~252: cells 85-90 + specials
row_252 = [
    (100, 85),   # (5,5)
    (124, 86),   # (6,5)
    (148, 87),   # (7,5)
    (172, 88),   # (8,5)
    (196, 89),   # (9,5)
    (228, 90),   # (10,5) = z
    (252, 0),    # special
    (276, 13),   # special
    (300, 7),    # special
]

print(f"\nRow Y~252 (lowercase u-z + specials):")
print(f"  Spacings: ", end="")
for i in range(len(row_252)-1):
    print(f"{row_252[i+1][0] - row_252[i][0]}", end=" ")
print()

print("\n" + "=" * 70)
print("KEY FINDING: SPACING ANALYSIS")
print("=" * 70)
print("""
Normal spacing pattern: 5 chars at 24px, then 32px gap, then 5 more at 24px
  X: 100, 124, 148, 172, 196, [228], 252, 276, 300, 324
  Spacing: 24, 24, 24, 24, 32, 24, 24, 24, 24

This is the pattern for ALL COMPLETE rows (Y~212, Y~232).

Row Y~152 (A-J, expected):
  Actual:   100, 124, 148, 172, 196, 252, 276, 300, 324
  Spacing:  24,  24,  24,  24,  56,  24,  24,  24
  Expected: 100, 124, 148, 172, 196, [228], 252, 276, 300, 324
  MISSING: X=228 (where the gap expands to 56 instead of 32+24)

  Wait -- actually comparing to the complete rows:
  Complete: 100, 124, 148, 172, 196, 228, 252, 276, 300, 324
  Row 152:  100, 124, 148, 172, 196,      252, 276, 300, 324

  The draw at X=228 is MISSING. This is cell 38 = F.
  Remaining chars shift LEFT to fill the gap? NO -- they DON'T shift.
  X=252 still has cell 39 (G), not 38. So there's a blank spot at X=228.

Row Y~172 (K-T, expected):
  Actual:   100, 124, 172, 196, 228, 252, 276, 300, 324
  Expected: 100, 124, 148, 172, 196, 228, 252, 276, 300, 324
  MISSING: X=148 (cell 45 = M)

  The draw at X=148 is MISSING. Remaining chars DON'T shift -- there's
  a blank spot where M should be.
""")

print("=" * 70)
print("DEFINITIVE CONCLUSION")
print("=" * 70)
print("""
1. The game renders the name entry keyboard using TBP0=0x2840 (PSMT4 256x256).
2. Each keyboard character is a 16x16 cell in the atlas, drawn as SPRITE.
3. The grid has 6 rows of 10 characters each (with 5+5 split at mid-gap).
4. Cells 33-58 = uppercase A-Z, cells 65-90 = lowercase a-z.
5. Cells 59-64 = SKIPPED (between Z and a) -- probably blank in original atlas.
6. Cell 38 (F) and Cell 45 (M) are NEVER DRAWN.
7. The grid positions X=228/Y=152 (F) and X=148/Y=172 (M) have NO draw call.
8. This is a CODE-LEVEL issue -- the game's character table or rendering
   loop skips these specific cell indices.

IMPORTANT: The cells are NOT drawn from a wrong texture or showing blank.
They are COMPLETELY ABSENT from the draw call stream. The game does not
emit GIF packets for these two grid positions at all.

The TBP0=0x2840 texture IS being uploaded to VRAM (via host->local transfers
that appear earlier in the frame). The issue is purely in the draw generation
logic, not in the texture data itself.
""")
