#!/usr/bin/env python3
"""Search for name entry labels - phase 3.
The grid at 0x3C99B8 contains 32-bit LE pointers (VA).
Follow these pointers to find the actual character data.
Also search for tab labels as single glyph IDs in MIPS lui/ori/addiu patterns.
"""
import struct, json

exe = open('extracted/SLPM_653.78', 'rb').read()
gmap = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))

# VA base: file offset 0x80 maps to VA 0x100000
# So: VA = file_offset - 0x80 + 0x100000
# file_offset = VA - 0x100000 + 0x80

def va_to_file(va):
    return va - 0x100000 + 0x80

def file_to_va(foff):
    return foff + 0x100000 - 0x80

# Follow the pointers at 0x3C99B8
print("=== Following pointers at 0x3C99B8 ===")
for i in range(20):
    off = 0x3C99B8 + i * 4
    va = struct.unpack_from('<I', exe, off)[0]
    if va == 0:
        break
    foff = va_to_file(va)
    print("  ptr[%d]: VA=0x%08X -> file=0x%06X" % (i, va, foff))
    if 0 <= foff < len(exe) - 20:
        # Read what's there - try as LE uint16 glyph IDs
        vals = []
        for j in range(10):
            v = struct.unpack_from('<H', exe, foff + j*2)[0]
            ch = gmap.get(str(v), '[%d]' % v)
            vals.append('%s(%d)' % (ch, v))
        print("    LE u16: " + ' '.join(vals))
        # Also try as bytes
        raw = exe[foff:foff+20]
        print("    raw hex: " + raw.hex())

# Let's also check what the pre-grid structs at 0x3C9800 point to
# They have pattern: 0x00 * 18 bytes, then value, 0x00*4, value, 0x00*2, 0x01, 0x00, value
# Let's read them as 32-byte structs
print("\n=== Structs at 0x3C9800 (stride 0x20) ===")
for i in range(13):
    off = 0x3C9800 + i * 0x20
    raw = exe[off:off+0x20]
    # Parse as mixed LE
    vals = struct.unpack_from('<8I', raw)
    print("  struct[%d] at 0x%06X:" % (i, off))
    print("    " + ' '.join('0x%08X' % v for v in vals))
    # The non-zero values at bytes 18-19 are glyph IDs?
    gid = struct.unpack_from('<H', raw, 0x12)[0]
    ch = gmap.get(str(gid), '[%d]' % gid)
    print("    glyph at +0x12: %d = %s" % (gid, ch))

# Now look even further back - what's at 0x3C9700-0x3C9800?
print("\n=== Region 0x3C9700-0x3C9800 (non-zero LE u16) ===")
for off in range(0x3C9700, 0x3C9800, 2):
    v = struct.unpack_from('<H', exe, off)[0]
    if v == 0:
        continue
    ch = gmap.get(str(v), '[%d]' % v)
    print("  0x%06X: %5d (0x%04X)  %s" % (off, v, v, ch))

# And check 0x3C9600-0x3C9700
print("\n=== Region 0x3C9600-0x3C9700 (non-zero LE u16) ===")
for off in range(0x3C9600, 0x3C9700, 2):
    v = struct.unpack_from('<H', exe, off)[0]
    if v == 0:
        continue
    ch = gmap.get(str(v), '[%d]' % v)
    print("  0x%06X: %5d (0x%04X)  %s" % (off, v, v, ch))

# Search for the pointer to the grid table itself in MIPS code
# The grid table VA is at 0x4C99B8 (well, 0x4C9938 based on our calc)
grid_table_va = file_to_va(0x3C99B8)
print("\n=== Grid table VA: 0x%08X ===" % grid_table_va)
# MIPS loads addresses with lui $r, HI16 / addiu $r, $r, LO16
hi = (grid_table_va >> 16) & 0xFFFF
lo = grid_table_va & 0xFFFF
if lo >= 0x8000:  # sign extension
    hi += 1
    lo = lo - 0x10000
    lo_unsigned = lo & 0xFFFF
else:
    lo_unsigned = lo

print("  lui hi=0x%04X, addiu lo=0x%04X (signed=%d)" % (hi, lo_unsigned, lo))

# Search for lui with this hi value
lui_pat = struct.pack('<H', hi)
print("\n=== Searching for MIPS lui 0x%04X ====" % hi)
count = 0
for off in range(0, len(exe)-4, 4):
    insn = struct.unpack_from('<I', exe, off)[0]
    op = (insn >> 26) & 0x3F
    rt = (insn >> 16) & 0x1F
    imm = insn & 0xFFFF
    if op == 0x0F and imm == hi:  # lui
        # Check next few instructions for addiu with lo
        for delta in range(1, 8):
            off2 = off + delta * 4
            if off2 >= len(exe) - 4:
                break
            insn2 = struct.unpack_from('<I', exe, off2)[0]
            op2 = (insn2 >> 26) & 0x3F
            imm2 = insn2 & 0xFFFF
            if op2 == 0x09 and imm2 == lo_unsigned:  # addiu
                print("  lui+addiu at 0x%06X: lui $%d,0x%04X; addiu at +%d with 0x%04X" %
                      (off, rt, hi, delta*4, lo_unsigned))
                count += 1
                break
    if count >= 20:
        break
