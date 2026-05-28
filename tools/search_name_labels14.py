#!/usr/bin/env python3
"""Search for name entry labels - phase 14.
Looking at key rendering functions.
0x00495DC0 = called with mode index from tab selection
0x00494FA0 = appears related to tab rendering
0x00494D00 = renders individual glyphs
Let's examine these + broader search for where the labels get their text.
"""
import struct

exe = open('extracted/SLPM_653.78', 'rb').read()

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
        if func == 0x25: return "or %s, %s, %s" % (REGS[rd], REGS[rs], REGS[rt])
        if func == 0x08: return "jr %s" % REGS[rs]
        if func == 0x09: return "jalr %s" % REGS[rs]
        if func == 0x00: return "sll %s, %s, %d" % (REGS[rd], REGS[rt], sa)
        if func == 0x02: return "srl %s, %s, %d" % (REGS[rd], REGS[rt], sa)
        if func == 0x03: return "sra %s, %s, %d" % (REGS[rd], REGS[rt], sa)
        if func == 0x2A: return "slt %s, %s, %s" % (REGS[rd], REGS[rs], REGS[rt])
        if func == 0x2B: return "sltu %s, %s, %s" % (REGS[rd], REGS[rs], REGS[rt])
        if func == 0x23: return "subu %s, %s, %s" % (REGS[rd], REGS[rs], REGS[rt])
        if func == 0x2D: return "daddu %s, %s, %s" % (REGS[rd], REGS[rs], REGS[rt])
        if func == 0x3C: return "dsll32 %s, %s, %d" % (REGS[rd], REGS[rt], sa)
        if func == 0x3F: return "dsra32 %s, %s, %d" % (REGS[rd], REGS[rt], sa)
        return "R func=0x%02X (%08X)" % (func, insn)
    if op == 0x09: return "addiu %s, %s, %d (0x%04X)" % (REGS[rt], REGS[rs], imm_s, imm)
    if op == 0x0F: return "lui %s, 0x%04X" % (REGS[rt], imm)
    if op == 0x0D: return "ori %s, %s, 0x%04X" % (REGS[rt], REGS[rs], imm)
    if op == 0x23: return "lw %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    if op == 0x2B: return "sw %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    if op == 0x25: return "lhu %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    if op == 0x21: return "lh %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    if op == 0x29: return "sh %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    if op == 0x20: return "lb %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    if op == 0x24: return "lbu %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    if op == 0x28: return "sb %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    if op == 0x04:
        target = off + 4 + imm_s * 4
        return "beq %s, %s, 0x%06X" % (REGS[rs], REGS[rt], target)
    if op == 0x05:
        target = off + 4 + imm_s * 4
        return "bne %s, %s, 0x%06X" % (REGS[rs], REGS[rt], target)
    if op == 0x0A: return "slti %s, %s, %d" % (REGS[rt], REGS[rs], imm_s)
    if op == 0x0B: return "sltiu %s, %s, %d" % (REGS[rt], REGS[rs], imm_s)
    if op == 0x03:
        jtarget = (insn & 0x03FFFFFF) << 2
        return "jal 0x%08X" % jtarget
    if op == 0x02:
        jtarget = (insn & 0x03FFFFFF) << 2
        return "j 0x%08X" % jtarget
    if op == 0x01:
        target = off + 4 + imm_s * 4
        if rt == 0x01: return "bgez %s, 0x%06X" % (REGS[rs], target)
        if rt == 0x00: return "bltz %s, 0x%06X" % (REGS[rs], target)
    if op == 0x06:
        target = off + 4 + imm_s * 4
        return "blez %s, 0x%06X" % (REGS[rs], target)
    if op == 0x07:
        target = off + 4 + imm_s * 4
        return "bgtz %s, 0x%06X" % (REGS[rs], target)
    if op == 0x0C: return "andi %s, %s, 0x%04X" % (REGS[rt], REGS[rs], imm)
    if op == 0x37: return "ld %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    if op == 0x3F: return "sd %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    if op == 0x1F: return "sq %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])  # PS2 specific
    if op == 0x1E: return "lq %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])  # PS2 specific
    return "op=0x%02X [%08X]" % (op, insn)

def va_to_file(va):
    return va - 0x100000 + 0x80

# Function at VA 0x00495DC0 (file 0x394D40)
print("=== Function at VA 0x00495DC0 (tab mode handler) ===")
foff = va_to_file(0x00495DC0)
for i in range(80):
    off = foff + i*4
    va = off + 0x100000 - 0x80
    d = disasm(off)
    print("  0x%06X (VA 0x%08X): %s" % (off, va, d))
    if d.startswith("jr $ra") and i > 4:
        # Print 2 more instructions (delay slot + padding)
        for j in range(1, 3):
            off2 = off + j*4
            va2 = off2 + 0x100000 - 0x80
            print("  0x%06X (VA 0x%08X): %s" % (off2, va2, disasm(off2)))
        break

# Function at VA 0x00494FA0 (file 0x393F20)
print("\n=== Function at VA 0x00494FA0 ===")
foff = va_to_file(0x00494FA0)
for i in range(80):
    off = foff + i*4
    va = off + 0x100000 - 0x80
    d = disasm(off)
    print("  0x%06X (VA 0x%08X): %s" % (off, va, d))
    if d.startswith("jr $ra") and i > 4:
        for j in range(1, 3):
            off2 = off + j*4
            va2 = off2 + 0x100000 - 0x80
            print("  0x%06X (VA 0x%08X): %s" % (off2, va2, disasm(off2)))
        break
