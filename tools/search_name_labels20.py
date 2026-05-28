#!/usr/bin/env python3
"""Search for name entry labels - phase 20.
Trace how glyph IDs from the grid (like 6400) get converted before rendering.

Looking at code at 0x1F2700:
  lh $v1, 666($s1)          // loads a mode/state value
  lui $v0, 0x004D
  addiu $v0, $v0, -25376    // VA 0x4C9CE0 (file 0x3C9D60)
  sll $v1, $v1, 2           // v1 * 4 (assuming sll 3 via func)
  addu $v1, $v1, ...        // index into table
  jal 0x00494050             // call with $a0 = value from table
  lw $a0, 0($v0)            // $a0 = table[index] (32-bit LE)

So $a0 is the raw 32-bit value from the table, like 0x00001900 (=6400).
Then 0x00494050 does: sll $a0, $a0, 4 -> 6400 * 16 = 102400
And accesses table at 0x4EBBEC + 102400 = 0x4EBBEC + 0x19000 = 0x50BBEC
But that's in the BSS/data segment, not in the EXE file.
The table at 0x4EBBEC is likely POPULATED AT RUNTIME by loading font data!

So the glyph lookup table at 0x4EBBEC is NOT in the EXE -- it's built
dynamically when the game loads its font resources.

This means the tab label images come from a RUNTIME-LOADED FONT RESOURCE.

Let's check what function 0x00493930 does (called at start of 0x494C90)
and whether the font loading code references any PACKDATA resources.
"""
import struct, json

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
        if func == 0x00 and rd == 0 and rt == 0: return "nop"
        if func == 0x00: return "sll %s, %s, %d" % (REGS[rd], REGS[rt], sa)
        if func == 0x02: return "srl %s, %s, %d" % (REGS[rd], REGS[rt], sa)
        if func == 0x08: return "jr %s" % REGS[rs]
        if func == 0x09: return "jalr %s" % REGS[rs]
        if func == 0x2D: return "daddu %s, %s, %s" % (REGS[rd], REGS[rs], REGS[rt])
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
    if op == 0x0A: return "slti %s, %s, %d" % (REGS[rt], REGS[rs], imm_s)
    if op == 0x03: return "jal 0x%08X" % ((insn & 0x03FFFFFF) << 2)
    if op == 0x02: return "j 0x%08X" % ((insn & 0x03FFFFFF) << 2)
    if op == 0x37: return "ld %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    if op == 0x3F: return "sd %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    if op == 0x1E: return "lq %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    if op == 0x1F: return "sq %s, %d(%s)" % (REGS[rt], imm_s, REGS[rs])
    if op == 0x01:
        if rt == 0: return "bltz %s, 0x%06X" % (REGS[rs], off + 4 + imm_s*4)
        if rt == 1: return "bgez %s, 0x%06X" % (REGS[rs], off + 4 + imm_s*4)
    return "op=0x%02X [%08X]" % (op, insn)

# Look at glyph loading code at 0x1ED100 more carefully
# This is where the kana grid is initialized
print("=== Code at 0x1ED100-0x1ED180 (kana grid init) ===")
for off in range(0x1ED100, 0x1ED180, 4):
    print("  0x%06X: %s" % (off, disasm(off)))

# The function 0x00492510 is called multiple times with lui $a0 values
# like 0x04A4, 0x04A5 which are resource IDs!
# Let's look at what these resource IDs mean
print("\n=== Calls to 0x00492510 with resource IDs ===")
# At 0x1ED10C: lui $a0, 0x04A4 then jal 0x00492510
# At 0x1ED120: lui $a0, 0x04A5 then jal 0x00492510
# These are font resource identifiers!

# Let's check function 0x00492510
print("\n=== Function at VA 0x00492510 (resource loader?) ===")
foff = 0x00492510 - 0x100000 + 0x80
for i in range(40):
    off = foff + i*4
    va = off + 0x100000 - 0x80
    d = disasm(off)
    print("  0x%06X (VA 0x%08X): %s" % (off, va, d))
    if d.startswith("jr $ra") and i > 2:
        off2 = off + 4
        print("  0x%06X (VA 0x%08X): %s" % (off2, off2+0x100000-0x80, disasm(off2)))
        break

# Let's also check the full name entry init at 0x1ED0B0
# which calls 0x2ED060 and 0x2EC9D0
print("\n=== Function at VA 0x002ED060 (name entry init) ===")
foff = 0x002ED060 - 0x100000 + 0x80
for i in range(100):
    off = foff + i*4
    va = off + 0x100000 - 0x80
    d = disasm(off)
    print("  0x%06X (VA 0x%08X): %s" % (off, va, d))
    if d.startswith("jr $ra") and i > 10:
        off2 = off + 4
        print("  0x%06X (VA 0x%08X): %s" % (off2, off2+0x100000-0x80, disasm(off2)))
        break

# The key insight: lui $a0, 0x04A4 means the resource ID is 0x04A40000
# But that seems very large. Actually, on PS2 with lui, the value gets
# shifted left by 16. So the full immediate for jal argument is just
# the function address. The lui $a0, 0x04A4 is loading the upper 16 bits
# of the resource ID parameter.
# So resource IDs are 0x04A40000 and 0x04A50000 - or maybe just 0x04A4 and 0x04A5
# since the lower bits might be set by addiu/ori.

# Let's look at how 0x04A4/0x04A5 are used in context
print("\n=== Context around resource load at 0x1ED108 ===")
for off in range(0x1ED100, 0x1ED128, 4):
    print("  0x%06X: %s" % (off, disasm(off)))
