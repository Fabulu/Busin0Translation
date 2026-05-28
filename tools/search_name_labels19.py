#!/usr/bin/env python3
"""Search for name entry labels - phase 19.
Check function 0x00494C70 and look at the lookup table at VA 0x4EBBEC.
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
        if func == 0x2D: return "daddu %s, %s, %s" % (REGS[rd], REGS[rs], REGS[rt])
        if func == 0x23: return "subu %s, %s, %s" % (REGS[rd], REGS[rs], REGS[rt])
        if func == 0x2A: return "slt %s, %s, %s" % (REGS[rd], REGS[rs], REGS[rt])
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
    if op == 0x01:
        if rt == 0: return "bltz %s, 0x%06X" % (REGS[rs], off + 4 + imm_s*4)
        if rt == 1: return "bgez %s, 0x%06X" % (REGS[rs], off + 4 + imm_s*4)
    return "op=0x%02X [%08X]" % (op, insn)

# Function at VA 0x00494C70 (file 0x393CF0)
print("=== Function at VA 0x00494C70 ===")
foff = 0x00494C70 - 0x100000 + 0x80
for i in range(40):
    off = foff + i*4
    va = off + 0x100000 - 0x80
    d = disasm(off)
    print("  0x%06X (VA 0x%08X): %s" % (off, va, d))
    if d.startswith("jr $ra") and i > 2:
        for j in range(1, 3):
            off2 = off + j*4
            print("  0x%06X (VA 0x%08X): %s" % (off2, off2+0x100000-0x80, disasm(off2)))
        break

# Function at VA 0x00494C90 (called from glyph render)
print("\n=== Function at VA 0x00494C90 ===")
foff = 0x00494C90 - 0x100000 + 0x80
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

# Check the lookup table at VA 0x4EBBEC (file 0x3EBC6C)
# The glyph loader uses: table[glyph_id * 16] (16-byte entries)
# But glyph ID 6400 would be offset 6400*16 = 102400 bytes
# That's 0x19000 bytes from 0x3EBC6C = 0x3FDC6C which is near end of file
# Let's check!
table_file = 0x3EBC6C
print("\n=== Glyph lookup table at 0x%06X ===")
# Check entry for glyph IDs 0-5 (first few)
for gid in [0, 1, 2, 3, 4, 5, 33, 34, 198, 213, 6400, 6401, 6402]:
    off = table_file + gid * 16
    if off + 16 > len(exe):
        print("  glyph %d: offset 0x%06X is BEYOND file (len=0x%06X)" %
              (gid, off, len(exe)))
        continue
    raw = exe[off:off+16]
    vals = struct.unpack_from('<hh4bI', raw)
    print("  glyph %5d at 0x%06X: %s  (%s)" %
          (gid, off, raw.hex(), str(vals)))
