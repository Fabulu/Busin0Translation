#!/usr/bin/env python3
"""Search for name entry labels - phase 15.
Let's search for ALL lui 0x004D references in the name entry code region
(around 0x1F4000-0x200000 in file, corresponding to name entry functions).
This should find all data table references for the name entry system.
"""
import struct, json

exe = open('extracted/SLPM_653.78', 'rb').read()
gmap = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))

# Search for lui $X, 0x004D in the name entry code region
print("=== All lui 0x004D references in 0x1E0000-0x200000 ===")
for off in range(0x1E0000, 0x200000, 4):
    insn = struct.unpack_from('<I', exe, off)[0]
    op = (insn >> 26) & 0x3F
    rt = (insn >> 16) & 0x1F
    imm = insn & 0xFFFF
    if op == 0x0F and imm == 0x004D:
        # Find matching addiu
        for d in range(1, 20):
            off2 = off + d*4
            if off2 >= len(exe) - 4:
                break
            insn2 = struct.unpack_from('<I', exe, off2)[0]
            op2 = (insn2 >> 26) & 0x3F
            rs2 = (insn2 >> 21) & 0x1F
            rt2 = (insn2 >> 16) & 0x1F
            imm2 = insn2 & 0xFFFF
            if op2 == 0x09 and rs2 == rt:
                imm2_s = imm2 if imm2 < 0x8000 else imm2 - 0x10000
                va = 0x004D0000 + imm2_s
                foff = va - 0x100000 + 0x80
                print("  0x%06X: lui $%d, 0x004D + addiu at +%d -> VA 0x%08X (file 0x%06X)" %
                      (off, rt, d*4, va, foff))
                break

# Also search in the broader function at 0x392000-0x396000 (VA 0x00492000-0x00496000)
print("\n=== All lui 0x004D references in 0x390000-0x396000 ===")
for off in range(0x390000, 0x396000, 4):
    insn = struct.unpack_from('<I', exe, off)[0]
    op = (insn >> 26) & 0x3F
    rt = (insn >> 16) & 0x1F
    imm = insn & 0xFFFF
    if op == 0x0F and imm == 0x004D:
        for d in range(1, 20):
            off2 = off + d*4
            if off2 >= len(exe) - 4:
                break
            insn2 = struct.unpack_from('<I', exe, off2)[0]
            op2 = (insn2 >> 26) & 0x3F
            rs2 = (insn2 >> 21) & 0x1F
            imm2 = insn2 & 0xFFFF
            if op2 == 0x09 and rs2 == rt:
                imm2_s = imm2 if imm2 < 0x8000 else imm2 - 0x10000
                va = 0x004D0000 + imm2_s
                foff = va - 0x100000 + 0x80
                print("  0x%06X: lui $%d, 0x004D + addiu at +%d -> VA 0x%08X (file 0x%06X)" %
                      (off, rt, d*4, va, foff))
                break

# Now let's also search for lui 0x004C (which would address the lower part of data)
print("\n=== All lui 0x004C references in 0x1E0000-0x200000 ===")
for off in range(0x1E0000, 0x200000, 4):
    insn = struct.unpack_from('<I', exe, off)[0]
    op = (insn >> 26) & 0x3F
    rt = (insn >> 16) & 0x1F
    imm = insn & 0xFFFF
    if op == 0x0F and imm == 0x004C:
        for d in range(1, 20):
            off2 = off + d*4
            if off2 >= len(exe) - 4:
                break
            insn2 = struct.unpack_from('<I', exe, off2)[0]
            op2 = (insn2 >> 26) & 0x3F
            rs2 = (insn2 >> 21) & 0x1F
            imm2 = insn2 & 0xFFFF
            if op2 == 0x09 and rs2 == rt:
                imm2_s = imm2 if imm2 < 0x8000 else imm2 - 0x10000
                va = 0x004C0000 + imm2_s
                foff = va - 0x100000 + 0x80
                print("  0x%06X: lui $%d, 0x004C + addiu at +%d -> VA 0x%08X (file 0x%06X)" %
                      (off, rt, d*4, va, foff))
                break
