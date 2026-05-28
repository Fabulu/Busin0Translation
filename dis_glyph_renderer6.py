import struct, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

EXE_PATH = "C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78"
exe = open(EXE_PATH, "rb").read()

FILE_TO_VADDR = 0x0FFF80

def rn(r):
    names = ['zero','at','v0','v1','a0','a1','a2','a3',
             't0','t1','t2','t3','t4','t5','t6','t7',
             's0','s1','s2','s3','s4','s5','s6','s7',
             't8','t9','k0','k1','gp','sp','fp','ra']
    return '$' + names[r]

def disasm(raw, vaddr):
    opcode = (raw >> 26) & 0x3F
    rs = (raw >> 21) & 0x1F
    rt = (raw >> 16) & 0x1F
    rd = (raw >> 11) & 0x1F
    imm = raw & 0xFFFF
    simm = imm - 0x10000 if imm > 0x7FFF else imm
    funct = raw & 0x3F
    sa = (raw >> 6) & 0x1F
    if opcode == 0:
        if funct == 0x00 and rd == 0 and rt == 0 and sa == 0: return 'nop'
        if funct == 0x00: return 'sll %s, %s, %d' % (rn(rd), rn(rt), sa)
        if funct == 0x02: return 'srl %s, %s, %d' % (rn(rd), rn(rt), sa)
        if funct == 0x03: return 'sra %s, %s, %d' % (rn(rd), rn(rt), sa)
        if funct == 0x08: return 'jr %s' % rn(rs)
        if funct == 0x09: return 'jalr %s, %s' % (rn(rd), rn(rs))
        if funct == 0x10: return 'mfhi %s' % rn(rd)
        if funct == 0x12: return 'mflo %s' % rn(rd)
        if funct == 0x18: return 'mult %s, %s' % (rn(rs), rn(rt))
        if funct == 0x19: return 'multu %s, %s' % (rn(rs), rn(rt))
        if funct == 0x1A: return 'div %s, %s' % (rn(rs), rn(rt))
        if funct == 0x1B: return 'divu %s, %s' % (rn(rs), rn(rt))
        if funct == 0x21: return 'addu %s, %s, %s' % (rn(rd), rn(rs), rn(rt))
        if funct == 0x23: return 'subu %s, %s, %s' % (rn(rd), rn(rs), rn(rt))
        if funct == 0x24: return 'and %s, %s, %s' % (rn(rd), rn(rs), rn(rt))
        if funct == 0x25: return 'or %s, %s, %s' % (rn(rd), rn(rs), rn(rt))
        if funct == 0x2A: return 'slt %s, %s, %s' % (rn(rd), rn(rs), rn(rt))
        if funct == 0x2D: return 'daddu %s, %s, %s' % (rn(rd), rn(rs), rn(rt))
        if funct == 0x3C: return 'dsll32 %s, %s, %d' % (rn(rd), rn(rt), sa)
        if funct == 0x3F: return 'dsra32 %s, %s, %d' % (rn(rd), rn(rt), sa)
        return 'R(0x%02X) %s,%s,%s,sa=%d' % (funct, rn(rd), rn(rs), rn(rt), sa)
    elif opcode == 0x02: return 'j 0x%08X' % ((vaddr & 0xF0000000) | ((raw & 0x3FFFFFF) << 2))
    elif opcode == 0x03: return 'jal 0x%08X' % ((vaddr & 0xF0000000) | ((raw & 0x3FFFFFF) << 2))
    elif opcode == 0x04: return 'beq %s, %s, 0x%08X' % (rn(rs), rn(rt), vaddr+4+(simm<<2))
    elif opcode == 0x05: return 'bne %s, %s, 0x%08X' % (rn(rs), rn(rt), vaddr+4+(simm<<2))
    elif opcode == 0x06: return 'blez %s, 0x%08X' % (rn(rs), vaddr+4+(simm<<2))
    elif opcode == 0x07: return 'bgtz %s, 0x%08X' % (rn(rs), vaddr+4+(simm<<2))
    elif opcode == 0x01:
        if rt == 0: return 'bltz %s, 0x%08X' % (rn(rs), vaddr+4+(simm<<2))
        if rt == 1: return 'bgez %s, 0x%08X' % (rn(rs), vaddr+4+(simm<<2))
        return 'REGIMM(rt=%d)' % rt
    elif opcode == 0x09: return 'addiu %s, %s, %d' % (rn(rt), rn(rs), simm)
    elif opcode == 0x0A: return 'slti %s, %s, %d' % (rn(rt), rn(rs), simm)
    elif opcode == 0x0C: return 'andi %s, %s, 0x%04X' % (rn(rt), rn(rs), imm)
    elif opcode == 0x0D: return 'ori %s, %s, 0x%04X' % (rn(rt), rn(rs), imm)
    elif opcode == 0x0F: return 'lui %s, 0x%04X' % (rn(rt), imm)
    elif opcode == 0x19: return 'daddiu %s, %s, %d' % (rn(rt), rn(rs), simm)
    elif opcode == 0x11:
        fmt = (raw >> 21) & 0x1F
        ft = (raw >> 16) & 0x1F
        fs = (raw >> 11) & 0x1F
        fd = (raw >> 6) & 0x1F
        fop = raw & 0x3F
        if fmt == 4: return 'mtc1 %s, $f%d' % (rn(rt), fs)
        if fmt == 0: return 'mfc1 %s, $f%d' % (rn(rt), fs)
        if fmt == 0x10:
            ops = {0:'add.s', 1:'sub.s', 2:'mul.s', 3:'div.s', 5:'abs.s', 6:'mov.s', 0x20:'cvt.s.w', 0x24:'cvt.w.s'}
            name = ops.get(fop, 'cop1.s(0x%02X)' % fop)
            if fop in (0x20, 0x24, 5, 6): return '%s $f%d, $f%d' % (name, fd, fs)
            return '%s $f%d, $f%d, $f%d' % (name, fd, fs, ft)
        if fmt == 0x14:
            return 'cvt.s.w $f%d, $f%d' % (fd, fs)
        return 'COP1(fmt=%d,fop=0x%02X)' % (fmt, fop)
    elif opcode == 0x1F: return 'sq %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x20: return 'lb %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x21: return 'lh %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x23: return 'lw %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x24: return 'lbu %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x25: return 'lhu %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x28: return 'sb %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x29: return 'sh %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x2B: return 'sw %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x31: return 'lwc1 $f%d, %d(%s)' % (rt, simm, rn(rs))
    elif opcode == 0x37: return 'ld %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x39: return 'swc1 $f%d, %d(%s)' % (rt, simm, rn(rs))
    elif opcode == 0x3F: return 'sd %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x1E: return 'lq %s, %d(%s)' % (rn(rt), simm, rn(rs))
    else: return '??? op=0x%02X raw=0x%08X' % (opcode, raw)


# The function at 0x3060B0 is the main glyph rendering function.
# It takes glyph IDs, computes UV from atlas position, and builds GS draw packets.
#
# Key constants found:
#   42 = columns per row in the atlas  (stored at file 0x2061A8, addiu $v0, $zero, 42)
#   24 = cell size in UV coordinates    (computed as (n*2+n)*8 = n*24)
#
# The x-advance is likely computed elsewhere. Let me look at what calls this function.
# We know jal 0x3060B0 would be the calling pattern.

target_jal = 0x3060B0 >> 2  # JAL target field
jal_instr = (0x03 << 26) | (target_jal & 0x3FFFFFF)
print("Looking for jal 0x%08X (instruction encoding: 0x%08X)" % (0x3060B0, jal_instr))

for off in range(0, len(exe)-3, 4):
    raw = struct.unpack_from('<I', exe, off)[0]
    if raw == jal_instr:
        vaddr = off + FILE_TO_VADDR
        print("  Found jal at file 0x%06X (vaddr 0x%08X)" % (off, vaddr))
        # Show context
        for i in range(-8, 20):
            o = off + i*4
            if o < 0 or o+3 >= len(exe): continue
            r = struct.unpack_from('<I', exe, o)[0]
            va = o + FILE_TO_VADDR
            marker = ' <--- JAL HERE' if i == 0 else ''
            a = disasm(r, va)
            # Highlight any immediate value that could be width/advance
            op = (r >> 26) & 0x3F
            simm = (r & 0xFFFF)
            if simm > 0x7FFF: simm -= 0x10000
            if op in (0x09, 0x19) and simm in (6, 7, 8, 10, 12, 14, 24):
                marker += ' <<<< IMM=%d' % simm
            print("    0x%08X [0x%06X]: %08X  %-45s%s" % (va, o, r, a, marker))
        print()

# Also search for addiu with constant 42
print()
print("=== Search for constant 42 (0x2A) as addiu immediate ===")
for off in range(0, len(exe)-3, 4):
    raw = struct.unpack_from('<I', exe, off)[0]
    opcode = (raw >> 26) & 0x3F
    simm = (raw & 0xFFFF)
    if simm > 0x7FFF: simm -= 0x10000
    if opcode == 0x09 and simm == 42:
        vaddr = off + FILE_TO_VADDR
        # Check if near a div instruction
        near_div = False
        for check in range(off, min(off+40, len(exe)-3), 4):
            r2 = struct.unpack_from('<I', exe, check)[0]
            if (r2 >> 26) & 0x3F == 0 and (r2 & 0x3F) in (0x1A, 0x1B):
                near_div = True
                break
        if near_div:
            print("  file 0x%06X (vaddr 0x%08X): %s  [DIV NEARBY]" % (off, vaddr, disasm(raw, vaddr)))
        else:
            print("  file 0x%06X (vaddr 0x%08X): %s" % (off, vaddr, disasm(raw, vaddr)))

# Now let's look at the x-advance: in the original renderer 0x302DB0,
# the $s0 register is described as tracking x-position. Let me look at
# how $s0 changes in the dispatch handling for normal glyphs (not control codes)
# The dispatch table starts at vaddr 0x302FB8 and normal glyphs would fall through
# to where the glyph gets rendered

# Let's look at what happens AFTER the giant dispatch table for normal characters
# The "else" case for glyph codes that don't match any control code
print()
print("=== Normal glyph path: fall-through from dispatch table ===")
# The last control code check was around 0x303260, then falls to code that
# processes the normal glyph. Let me look at the area after the dispatch table

# From the first disassembly, we see the function at 0x302DB0 reads 2-byte codes,
# checks for FFFF, FFFE, FFFD, FFC0, FFD0-FFD9, FB00-FB09, FC00-FC0A, FD00-FD27
# If none match, the code falls through. Let me find where.

# The end of the dispatch table should be after 0x303260 (last FD code checks)
# Let me dump from 0x303260 to the end of function

for off in range(0x2032E0, 0x2033D0, 4):
    raw = struct.unpack_from('<I', exe, off)[0]
    va = off + FILE_TO_VADDR
    asm = disasm(raw, va)
    marker = ''
    opcode = (raw >> 26) & 0x3F
    simm = (raw & 0xFFFF)
    if simm > 0x7FFF: simm -= 0x10000
    if opcode in (0x09, 0x19) and simm in (6, 7, 8, 12, 24, 42):
        marker = ' <<<< IMM=%d' % simm
    if 'jal' in asm:
        target = (va & 0xF0000000) | ((raw & 0x3FFFFFF) << 2)
        if target == 0x3060B0:
            marker = ' <<<< GLYPH RENDERER!'
    print('  0x%08X [0x%06X]: %08X  %-50s%s' % (va, off, raw, asm, marker))
