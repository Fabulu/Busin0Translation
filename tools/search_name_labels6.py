#!/usr/bin/env python3
"""Search for name entry labels - phase 6.
The labels カナ, かな, 英数, 記号, 決定, 男名, 女名 are NOT:
- SJIS strings anywhere in the EXE
- Glyph ID pairs (BE or LE)

They must be either:
1. Pre-rendered textures (image data)
2. Hardcoded in MIPS code as individual glyph IDs loaded via immediate operands
3. Part of a UI descriptor table with a different format

Let's search for the individual glyph IDs as MIPS immediate values.
MIPS addiu $reg, $zero, GLYPH_ID would be a common pattern.
Also check: li $reg, GLYPH_ID (which is ori $reg, $zero, GLYPH_ID)

カ=198, ナ=213 - if loaded consecutively that would be the label.
"""
import struct, json

exe = open('extracted/SLPM_653.78', 'rb').read()
gmap = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))

# Let's look at the region between the grids more carefully
# We have:
# 0x3C9600-0x3C96E4: pointer table (symbols grid?)
# 0x3C96F0-0x3C99A0: structs with glyph IDs 1193-1214 (kana chars)
# 0x3C99B0-0x3C9A08: pointer table (20 entries -> kana char structs)
# 0x3CA690-0x3CA770: alphanumeric grid (glyph IDs 0-55, with 60=blank)
# 0x3CA770-0x3CA790: small table (0,2,1,FFFF,4,FFFF,5,6,7,8,9,10,...)
# 0x3CA79A-0x3CA900+: paired glyph IDs 1215-1259 (more kana chars?)

# The small table at 0x3CA770 is interesting:
# 0, 2, 1, FFFF, 4, FFFF, 5, 6, 7, 8, 9, 10
# These could be tab/button indices!
# 0=something, 2=kana tab, 1=hiragana tab, FFFF=separator,
# 4=symbols, FFFF=sep, 5=confirm, 6=male, 7=female...

print("=== Region 0x3CA770-0x3CA7A0 as LE uint16 ===")
for off in range(0x3CA770, 0x3CA7A0, 2):
    v = struct.unpack_from('<H', exe, off)[0]
    ch = gmap.get(str(v), '[%d]' % v)
    if v == 0xFFFF:
        ch = 'FFFF'
    print("  0x%06X: %5d (0x%04X)  %s" % (off, v, v, ch))

# Let's look at the WIDER region - what's between the symbol pointer
# table and the kana structs?
print("\n=== Region 0x3C94F0-0x3C9610 raw hex (looking for more tables) ===")
for off in range(0x3C94F0, 0x3C9610, 32):
    raw = exe[off:off+32]
    print("  0x%06X: %s" % (off, raw.hex()))

# Search for the exact boundary of where text-rendering related data lives
# Let's look at the broader region 0x3CA900-0x3CAC00
print("\n=== Region 0x3CA900-0x3CAC00 as LE uint16 (non-zero) ===")
for off in range(0x3CA900, 0x3CAC00, 2):
    v = struct.unpack_from('<H', exe, off)[0]
    if v == 0:
        continue
    ch = gmap.get(str(v), '[%d]' % v)
    if v == 0xFFFF:
        ch = 'FFFF'
    print("  0x%06X: %5d (0x%04X)  %s" % (off, v, v, ch))

# Also check: maybe the labels use a DIFFERENT glyph system
# The name entry might have its own font with label textures
# Let's search for common UI label patterns in the code section
# Code is roughly 0x80-0x200000 (rough estimate)

# Search for addiu with value 198 (カ) in the code
print("\n=== MIPS instructions loading glyph 198 (カ) ===")
count = 0
for off in range(0x80, 0x200000, 4):
    insn = struct.unpack_from('<I', exe, off)[0]
    imm = insn & 0xFFFF
    op = (insn >> 26) & 0x3F
    rs = (insn >> 21) & 0x1F
    rt = (insn >> 16) & 0x1F
    # addiu rt, rs, 198 (op=9) or ori rt, rs, 198 (op=13)
    if imm == 198 and op in (9, 13) and rs == 0:
        # Check next instruction for 213 (ナ)
        insn2 = struct.unpack_from('<I', exe, off+4)[0]
        imm2 = insn2 & 0xFFFF
        op2 = (insn2 >> 26) & 0x3F
        # Also check a few instructions ahead
        found_na = False
        for d in range(1, 10):
            if off + d*4 + 4 > len(exe):
                break
            insn_n = struct.unpack_from('<I', exe, off+d*4)[0]
            if (insn_n & 0xFFFF) == 213:
                found_na = True
                break
        if found_na:
            print("  0x%06X: op=%d rs=$%d rt=$%d imm=%d  (ナ found nearby!)" %
                  (off, op, rs, rt, imm))
            # Dump surrounding instructions
            for d in range(-2, 12):
                o = off + d*4
                ins = struct.unpack_from('<I', exe, o)[0]
                print("    0x%06X: %08X  imm=%d" % (o, ins, ins & 0xFFFF))
            count += 1
    if count >= 5:
        break

# Also try: search for the sequence of all 7 labels' first chars
# as immediate values in nearby code
print("\n=== Search for 記号 glyph 801 in code ===")
count = 0
for off in range(0x80, 0x200000, 4):
    insn = struct.unpack_from('<I', exe, off)[0]
    imm = insn & 0xFFFF
    op = (insn >> 26) & 0x3F
    if imm == 801 and op in (9, 13):
        print("  0x%06X: %08X" % (off, insn))
        count += 1
    if count >= 10:
        break
