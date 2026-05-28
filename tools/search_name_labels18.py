#!/usr/bin/env python3
"""Search for name entry labels - phase 18.
Found the tab label glyph IDs: 6400-6409 (0x1900-0x1909) at 0x3C9DA0-0x3C9DFC.
These use the name entry's own font system (separate from MSG glyphs).

The IDs encode: page (high byte) and index (low byte):
  0x1900-0x1909 = page 0x19, indices 0-9
  0x1A00-0x1A0C = page 0x1A, indices 0-12
  0x1B00-0x1B0C = page 0x1B, indices 0-12
  0x1C00-0x1C09 = page 0x1C, indices 0-9

Now the key question: These glyph IDs are used to render tab labels.
The function 0x00494050 loads glyph data using these IDs.
Let's trace that function to find where the font data comes from.
Also, let's check the rendering function 0x00494D00 which handles
individual cell rendering.
"""
import struct, json

exe = open('extracted/SLPM_653.78', 'rb').read()
gmap = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))

REGS = ['$zero','$at','$v0','$v1','$a0','$a1','$a2','$a3',
        '$t0','$t1','$t2','$t3','$t4','$t5','$t6','$t7',
        '$s0','$s1','$s2','$s3','$s4','$s5','$s6','$s7',
        '$t8','$t9','$k0','$k1','$gp','$sp','$fp','$ra']

def disasm(off):
    insn = struct.unpack_from('<I', exe, off)[0]
    op = (insn >> 26) & 0x3F
    rs = (insn >> 21) & 0x1F
    rt = (insn >> 16) & 0x1F
    rd = (insn >> 11) & 0x1F
    sa = (insn >> 6) & 0x1F
    func = insn & 0x3F
    imm = insn & 0xFFFF
    imm_s = imm if imm < 0x8000 else imm - 0x10000
    if op == 0:
        if insn == 0: return "nop"
        if func == 0x21: return "addu %s, %s, %s" % (REGS[rd], REGS[rs], REGS[rt])
        if func == 0x00: return "sll %s, %s, %d" % (REGS[rd], REGS[rt], sa)
        if func == 0x02: return "srl %s, %s, %d" % (REGS[rd], REGS[rt], sa)
        if func == 0x08: return "jr %s" % REGS[rs]
        if func == 0x09: return "jalr %s" % REGS[rs]
        if func == 0x2D: return "daddu %s, %s, %s" % (REGS[rd], REGS[rs], REGS[rt])
        if func == 0x24: return "and %s, %s, %s" % (REGS[rd], REGS[rs], REGS[rt])
        if func == 0x18: return "mult %s, %s" % (REGS[rs], REGS[rt])
        if func == 0x12: return "mflo %s" % REGS[rd]
        if func == 0x10: return "mfhi %s" % REGS[rd]
        if func == 0x3C: return "dsll32 %s, %s, %d" % (REGS[rd], REGS[rt], sa)
        if func == 0x3F: return "dsra32 %s, %s, %d" % (REGS[rd], REGS[rt], sa)
        return "R 0x%02X [%08X]" % (func, insn)
    if op == 0x09: return "addiu %s, %s, %d (0x%04X)" % (REGS[rt], REGS[rs], imm_s, imm)
    if op == 0x0F: return "lui %s, 0x%04X" % (REGS[rt], imm)
    if op == 0x0D: return "ori %s, %s, 0x%04X" % (REGS[rt], REGS[rs], imm)
    if op == 0x0C: return "andi %s, %s, 0x%04X" % (REGS[rt], REGS[rs], imm)
    if op == 0x23: return "lw %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    if op == 0x2B: return "sw %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    if op == 0x25: return "lhu %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    if op == 0x21: return "lh %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    if op == 0x29: return "sh %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    if op == 0x20: return "lb %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    if op == 0x24: return "lbu %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    if op == 0x28: return "sb %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    if op == 0x04: return "beq %s, %s, 0x%06X" % (REGS[rs], REGS[rt], off + 4 + imm_s*4)
    if op == 0x05: return "bne %s, %s, 0x%06X" % (REGS[rs], REGS[rt], off + 4 + imm_s*4)
    if op == 0x06: return "blez %s, 0x%06X" % (REGS[rs], off + 4 + imm_s*4)
    if op == 0x07: return "bgtz %s, 0x%06X" % (REGS[rs], off + 4 + imm_s*4)
    if op == 0x0A: return "slti %s, %s, %d" % (REGS[rt], REGS[rs], imm_s)
    if op == 0x03: return "jal 0x%08X" % ((insn & 0x03FFFFFF) << 2)
    if op == 0x02: return "j 0x%08X" % ((insn & 0x03FFFFFF) << 2)
    if op == 0x37: return "ld %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    if op == 0x3F: return "sd %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    if op == 0x1F: return "sq %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    if op == 0x1E: return "lq %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    if op == 0x01:
        if rt == 0: return "bltz %s, 0x%06X" % (REGS[rs], off + 4 + imm_s*4)
        if rt == 1: return "bgez %s, 0x%06X" % (REGS[rs], off + 4 + imm_s*4)
    return "op=0x%02X [%08X]" % (op, insn)

# Function at VA 0x00494050 (file 0x3930D0)
print("=== Function at VA 0x00494050 (glyph loader) ===")
foff = 0x00494050 - 0x100000 + 0x80
for i in range(100):
    off = foff + i*4
    va = off + 0x100000 - 0x80
    d = disasm(off)
    print("  0x%06X (VA 0x%08X): %s" % (off, va, d))
    if d.startswith("jr $ra") and i > 4:
        for j in range(1, 3):
            off2 = off + j*4
            print("  0x%06X (VA 0x%08X): %s" % (off2, off2+0x100000-0x80, disasm(off2)))
        break

# Function at VA 0x00494D00 (file 0x393D80)
print("\n=== Function at VA 0x00494D00 (glyph render) ===")
foff = 0x00494D00 - 0x100000 + 0x80
for i in range(60):
    off = foff + i*4
    va = off + 0x100000 - 0x80
    d = disasm(off)
    print("  0x%06X (VA 0x%08X): %s" % (off, va, d))
    if d.startswith("jr $ra") and i > 4:
        for j in range(1, 3):
            off2 = off + j*4
            print("  0x%06X (VA 0x%08X): %s" % (off2, off2+0x100000-0x80, disasm(off2)))
        break
