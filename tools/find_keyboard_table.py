"""
The keyboard callers pass category IDs 13, 14, 22, 23, 24 to 0x48CFB0.
0x48CFB0 calls 0x48C810 with (category, count=21, ...).
0x48C810 calls 0x3A49D0 with (slot_id=12, subslot=1) to get a render context,
then 0x3A3260 which calls 0x3A2D90 to get the glyph data pointer.

0x3A2D90 reads from a base pointer + offset table. The base pointer comes
from a global table at VA 0x56EC90 (0x0056*0x10000 + 0x6C90).

The keyboard layout data is in PACKDATA resources, not the EXE.
The glyph codes in the data stream determine which glyphs to draw.

But the user's nuclear swap test proves the issue is glyph-ID-specific.
This means the glyph STREAM contains codes for all cells including 38 and 45,
but the rendering of those specific codes is suppressed.

In the function 0x3A2E10 at VA 0x3A2EC4:
  lui $v0, 0x0057
  addiu $v0, $v0, 18064  -> VA 0x5746A0 -> file offset 0x474720
  sll $v1, $v1, 2        -> $v1 = row * 4
  addu $v0, $v0, $v1     -> table[row]
  lw $a2, 0($v0)         -> load function pointer from table

This table at 0x5746A0 (file 0x474720) contains pointers to drawing functions
indexed by the glyph's row (high byte of the glyph code).

The glyph code format: high byte = row, low byte = column.
row*16 = texture V coordinate (approximately)
column*16 = texture U coordinate

For the R1188 font atlas (1024x1024), the glyphs are arranged in a grid.
Cell index 38 corresponds to a specific (U,V) position.

But the actual cell index isn't used directly - the glyph CODE in the data
stream encodes the position. So cells 38 and 45 in the keyboard grid would
have specific glyph codes.

Let me check the drawing function table at 0x474720.
"""
import struct

EXE_PATH = r"C:\Programmieren\wizardrytranslation\extracted\SLPM_653.78"
VA_BASE = 0x0FFF80

def fo2va(fo): return fo + VA_BASE
def va2fo(va): return va - VA_BASE

with open(EXE_PATH, "rb") as f:
    exe = f.read()

# Table at VA 0x5746A0 = file 0x474720
# This is indexed by the row (high byte of glyph code shifted right 8)
print("=" * 90)
print("DRAWING FUNCTION TABLE at VA 0x5746A0 (file 0x474720)")
print("=" * 90)

table_fo = 0x474720
for i in range(32):  # Check first 32 entries
    val = struct.unpack_from("<I", exe, table_fo + i*4)[0]
    if val == 0:
        print(f"  Row {i:3d}: NULL (no draw function)")
    else:
        print(f"  Row {i:3d}: VA {val:#010x}")

# Wait, the actual offset is:
# lui $v0, 0x0057 -> 0x570000
# addiu $v0, $v0, 18064 -> 0x570000 + 18064 = 0x5746A0
# But 18064 = 0x4690, and 0x570000 + 0x4690 = 0x574690
# Hmm, 18064 decimal: let me recalculate
# 18064 = 0x4690, but addiu sign-extends
# 0x4690 bit 15 is 0, so positive: 0x570000 + 0x4690 = 0x574690
# File offset: 0x574690 - 0xFFF80 = 0x474710

print()
print("Let me recalculate: VA = 0x570000 + 0x4690 = 0x574690, file = 0x474710")
print()

table_fo = 0x474710
for i in range(32):
    val = struct.unpack_from("<I", exe, table_fo + i*4)[0]
    if val == 0:
        print(f"  Row {i:3d}: NULL (no draw function)")
    else:
        print(f"  Row {i:3d}: VA {val:#010x}")

# Actually, let me re-read the instruction more carefully
# 0x3a2ec4: lui $v0, 0x0057   -> v0 = 0x00570000
# 0x3a2ed0: addiu $v0, $v0, 18064
# 18064 in hex: 18064 / 16 = 1129, 18064 = 0x4690
# v0 = 0x00570000 + 0x4690 = 0x00574690
# file offset = 0x574690 - 0x0FFF80 = 0x474710
# But wait, the instruction at 0x3a2ed0 was:
# "addiu $v0, $v0, 18064" -- let me verify the raw bytes

raw = struct.unpack_from("<I", exe, va2fo(0x3A2ED0))[0]
imm = raw & 0xFFFF
imm_s = imm - 0x10000 if imm & 0x8000 else imm
print(f"\nInstruction at 0x3A2ED0: raw={raw:#010x}, imm={imm:#06x} ({imm_s})")
print(f"v0 = 0x570000 + {imm_s} = {0x570000 + imm_s:#010x}")
print(f"file offset = {0x570000 + imm_s - VA_BASE:#010x}")

table_va = 0x570000 + imm_s
table_fo = table_va - VA_BASE

print(f"\nTable at VA {table_va:#010x}, file {table_fo:#010x}")
for i in range(32):
    if table_fo + i*4 + 4 > len(exe):
        break
    val = struct.unpack_from("<I", exe, table_fo + i*4)[0]
    if val == 0:
        print(f"  Row {i:3d}: NULL (no draw function -> SKIP DRAWING)")
    else:
        print(f"  Row {i:3d}: VA {val:#010x}")
