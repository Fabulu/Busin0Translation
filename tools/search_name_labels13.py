#!/usr/bin/env python3
"""Search for name entry labels - phase 13.
Disassemble the MIPS code around the key references to understand
how the name entry screen is structured.
"""
import struct

exe = open('extracted/SLPM_653.78', 'rb').read()

REGS = ['$zero','$at','$v0','$v1','$a0','$a1','$a2','$a3',
        '$t0','$t1','$t2','$t3','$t4','$t5','$t6','$t7',
        '$s0','$s1','$s2','$s3','$s4','$s5','$s6','$s7',
        '$t8','$t9','$k0','$k1','$gp','$sp','$fp','$ra']

def disasm(off):
    """Simple MIPS disassembler for key instructions."""
    insn = struct.unpack_from('<I', exe, off)[0]
    op = (insn >> 26) & 0x3F
    rs = (insn >> 21) & 0x1F
    rt = (insn >> 16) & 0x1F
    rd = (insn >> 11) & 0x1F
    sa = (insn >> 6) & 0x1F
    func = insn & 0x3F
    imm = insn & 0xFFFF
    imm_s = imm if imm < 0x8000 else imm - 0x10000

    if op == 0:  # R-type
        if func == 0x21:
            return "addu %s, %s, %s" % (REGS[rd], REGS[rs], REGS[rt])
        elif func == 0x25:
            return "or %s, %s, %s" % (REGS[rd], REGS[rs], REGS[rt])
        elif func == 0x08:
            return "jr %s" % REGS[rs]
        elif func == 0x09:
            return "jalr %s" % REGS[rs]
        elif func == 0x00:
            if insn == 0:
                return "nop"
            return "sll %s, %s, %d" % (REGS[rd], REGS[rt], sa)
        elif func == 0x2A:
            return "slt %s, %s, %s" % (REGS[rd], REGS[rs], REGS[rt])
        elif func == 0x2B:
            return "sltu %s, %s, %s" % (REGS[rd], REGS[rs], REGS[rt])
        elif func == 0x23:
            return "subu %s, %s, %s" % (REGS[rd], REGS[rs], REGS[rt])
        return "R-type func=0x%02X" % func
    elif op == 0x09:
        return "addiu %s, %s, %d (0x%04X)" % (REGS[rt], REGS[rs], imm_s, imm)
    elif op == 0x0F:
        return "lui %s, 0x%04X" % (REGS[rt], imm)
    elif op == 0x0D:
        return "ori %s, %s, 0x%04X" % (REGS[rt], REGS[rs], imm)
    elif op == 0x23:
        return "lw %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    elif op == 0x2B:
        return "sw %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    elif op == 0x25:
        return "lhu %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    elif op == 0x21:
        return "lh %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    elif op == 0x29:
        return "sh %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    elif op == 0x20:
        return "lb %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    elif op == 0x24:
        return "lbu %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    elif op == 0x28:
        return "sb %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    elif op == 0x04:
        target = off + 4 + imm_s * 4
        return "beq %s, %s, 0x%06X" % (REGS[rs], REGS[rt], target)
    elif op == 0x05:
        target = off + 4 + imm_s * 4
        return "bne %s, %s, 0x%06X" % (REGS[rs], REGS[rt], target)
    elif op == 0x0A:
        return "slti %s, %s, %d" % (REGS[rt], REGS[rs], imm_s)
    elif op == 0x0B:
        return "sltiu %s, %s, %d" % (REGS[rt], REGS[rs], imm_s)
    elif op == 0x03:
        jtarget = (insn & 0x03FFFFFF) << 2
        return "jal 0x%08X" % jtarget
    elif op == 0x02:
        jtarget = (insn & 0x03FFFFFF) << 2
        return "j 0x%08X" % jtarget
    elif op == 0x01:
        if rt == 0x01:
            target = off + 4 + imm_s * 4
            return "bgez %s, 0x%06X" % (REGS[rs], target)
        elif rt == 0x11:
            target = off + 4 + imm_s * 4
            return "bgezal %s, 0x%06X" % (REGS[rs], target)
        elif rt == 0x00:
            target = off + 4 + imm_s * 4
            return "bltz %s, 0x%06X" % (REGS[rs], target)
    return "op=0x%02X [%08X]" % (op, insn)

# Disassemble around the mode_index reference at 0x1FB774
print("=== Code around mode_index ref at 0x1FB774 ===")
for off in range(0x1FB700, 0x1FB900, 4):
    va = off - 0x80 + 0x100000
    d = disasm(off)
    print("  0x%06X (VA 0x%08X): %s" % (off, va, d))

# Disassemble around the kana ptr table ref at 0x1ED128
print("\n=== Code around kana_ptr_table ref at 0x1ED128 ===")
for off in range(0x1ED080, 0x1ED200, 4):
    va = off - 0x80 + 0x100000
    d = disasm(off)
    print("  0x%06X (VA 0x%08X): %s" % (off, va, d))

# Disassemble around the alnum_grid ref at 0x1FAF40
print("\n=== Code around alnum_grid ref at 0x1FAF40 ===")
for off in range(0x1FAF00, 0x1FB000, 4):
    va = off - 0x80 + 0x100000
    d = disasm(off)
    print("  0x%06X (VA 0x%08X): %s" % (off, va, d))
