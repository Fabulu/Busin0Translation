#!/usr/bin/env python3
"""Search for name entry labels - phase 17.
Found potential tab label IDs at 0x3C9DA0:
  6400, 6401, 6402, 6403, 6404  (first row of buttons)
  6405, 6406, 6407, 6408, 6409  (second row of buttons)

These are stored as LE uint32 with 0 padding (like the glyph IDs at 0x3C9D60).
Let's check if 6400-6409 appear elsewhere in the EXE (esp. in glyph definition tables).

Also - the name entry has 7 tabs/buttons: カナ, かな, 英数, 記号, 決定, 男名, 女名
But we have 10 values (6400-6409). Possible mapping:
  Row 1 (6400-6404): カナ, かな, 英数, 記号, (something else?)
  Row 2 (6405-6409): 決定, 男名, 女名, (1文字消す?), (全消去?)

Let's also dump the complete table at 0x3C9D60-0x3C9E00 more carefully,
and check what's at 0x3C9E00+ (more tables?).
"""
import struct, json

exe = open('extracted/SLPM_653.78', 'rb').read()
gmap = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))

# The table at 0x3C9D60 has LE uint32 entries where lower 16 = glyph ID
print("=== Table at 0x3C9D60 as LE uint32 ===")
for off in range(0x3C9D60, 0x3C9E20, 4):
    v = struct.unpack_from('<I', exe, off)[0]
    if v == 0:
        continue
    if v == 0xFFFFFFFF:
        continue
    lo = v & 0xFFFF
    hi = (v >> 16) & 0xFFFF
    ch = gmap.get(str(lo), '[%d]' % lo)
    print("  0x%06X: 0x%08X  lo=%d(%s) hi=%d" % (off, v, lo, ch, hi))

# Search for 6400 as uint32 in the entire EXE data section
print("\n=== Searching for value 6400 (0x1900) as LE uint32 in data section ===")
target = struct.pack('<I', 6400)
pos = 0x300000  # data section starts well into the file
while True:
    pos = exe.find(target, pos)
    if pos < 0:
        break
    # Only print if 4-byte aligned
    if pos % 4 == 0:
        print("  0x%06X" % pos)
    pos += 1

# Check if there's a table mapping 6400-6409 to texture coordinates
# or some other rendering info
# First, let's see if these values appear in the glyph table at 0x3C96F0
# (the 0x20-byte structs with glyph IDs)
print("\n=== Searching for glyph ID 6400 in 0x20-byte structs ===")
for off in range(0x3C8000, 0x3CB200, 0x20):
    for field_off in [0x12, 0x16, 0x18, 0x1A]:
        v = struct.unpack_from('<H', exe, off + field_off)[0]
        if v == 6400:
            print("  Found at 0x%06X + 0x%02X" % (off, field_off))
            print("  Full struct: %s" % exe[off:off+0x20].hex())

# Now let's check 0x3C9E00+ for more tables
print("\n=== Region 0x3C9E00-0x3CA000 as LE uint32 (non-zero, not FFFF) ===")
for off in range(0x3C9E00, 0x3CA000, 4):
    v = struct.unpack_from('<I', exe, off)[0]
    if v == 0 or v == 0xFFFFFFFF:
        continue
    lo = v & 0xFFFF
    hi = (v >> 16) & 0xFFFF
    ch = gmap.get(str(lo), '[%d]' % lo)
    print("  0x%06X: 0x%08X  lo=%d(%s) hi=%d" % (off, v, lo, ch, hi))

# Dump 0x3C9D90-0x3C9DA0 more carefully
print("\n=== 0x3C9D90-0x3C9E00 raw ===")
for off in range(0x3C9D90, 0x3C9E00, 16):
    raw = exe[off:off+16]
    print("  0x%06X: %s" % (off, raw.hex()))

# Look at what 0x1F2708 references (VA 0x4C9CE0 = file 0x3C9D60)
# This was the function that loads the alphanumeric+symbol grid
# The table starting at 0x3C9D60 has glyph IDs 25-36 (numbers 9-d!)
# Then at 0x3C9D90: value 114=う, then at 0x3C9DA0: 6400-6404
# Wait - 0x3C9D90 has 0x00000072 = 114(う)
# This doesn't fit. Let me re-examine.

# The entry at 0x3C9D60 is referenced as a base pointer for the grid.
# The glyph IDs 25-36 at stride 4 bytes are the BOTTOM ROW of the symbol grid.
# Then 6400-6409 are likely the TAB BUTTONS which are rendered separately.
# Let's check how the code at 0x1F2708 uses this pointer.

REGS = ['$zero','$at','$v0','$v1','$a0','$a1','$a2','$a3',
        '$t0','$t1','$t2','$t3','$t4','$t5','$t6','$t7',
        '$s0','$s1','$s2','$s3','$s4','$s5','$s6','$s7',
        '$t8','$t9','$k0','$k1','$gp','$sp','$fp','$ra']

def disasm_simple(off):
    insn = struct.unpack_from('<I', exe, off)[0]
    op = (insn >> 26) & 0x3F
    rs = (insn >> 21) & 0x1F
    rt = (insn >> 16) & 0x1F
    imm = insn & 0xFFFF
    imm_s = imm if imm < 0x8000 else imm - 0x10000
    if op == 0x09: return "addiu %s, %s, %d (0x%04X)" % (REGS[rt], REGS[rs], imm_s, imm)
    if op == 0x0F: return "lui %s, 0x%04X" % (REGS[rt], imm)
    if op == 0x23: return "lw %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    if op == 0x21: return "lh %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    if op == 0x25: return "lhu %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    if op == 0x03: return "jal 0x%08X" % ((insn & 0x03FFFFFF) << 2)
    if op == 0x04: return "beq %s, %s, 0x%06X" % (REGS[rs], REGS[rt], off + 4 + imm_s*4)
    if op == 0x05: return "bne %s, %s, 0x%06X" % (REGS[rs], REGS[rt], off + 4 + imm_s*4)
    if op == 0 and insn == 0: return "nop"
    return "[%08X]" % insn

print("\n=== Code at 0x1F2700-0x1F2800 (grid cell rendering) ===")
for off in range(0x1F2700, 0x1F2800, 4):
    print("  0x%06X: %s" % (off, disasm_simple(off)))
