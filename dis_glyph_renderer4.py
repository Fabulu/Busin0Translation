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
        if funct == 0x2B: return 'sltu %s, %s, %s' % (rn(rd), rn(rs), rn(rt))
        if funct == 0x2D: return 'daddu %s, %s, %s' % (rn(rd), rn(rs), rn(rt))
        if funct == 0x3C: return 'dsll32 %s, %s, %d' % (rn(rd), rn(rt), sa)
        if funct == 0x3F: return 'dsra32 %s, %s, %d' % (rn(rd), rn(rt), sa)
        return 'R(0x%02X) %s,%s,%s,sa=%d' % (funct, rn(rd), rn(rs), rn(rt), sa)
    elif opcode == 0x01:
        if rt == 0: return 'bltz %s, 0x%08X' % (rn(rs), vaddr+4+(simm<<2))
        if rt == 1: return 'bgez %s, 0x%08X' % (rn(rs), vaddr+4+(simm<<2))
        return 'REGIMM(rt=%d)' % rt
    elif opcode == 0x02: return 'j 0x%08X' % ((vaddr & 0xF0000000) | ((raw & 0x3FFFFFF) << 2))
    elif opcode == 0x03: return 'jal 0x%08X' % ((vaddr & 0xF0000000) | ((raw & 0x3FFFFFF) << 2))
    elif opcode == 0x04: return 'beq %s, %s, 0x%08X' % (rn(rs), rn(rt), vaddr+4+(simm<<2))
    elif opcode == 0x05: return 'bne %s, %s, 0x%08X' % (rn(rs), rn(rt), vaddr+4+(simm<<2))
    elif opcode == 0x06: return 'blez %s, 0x%08X' % (rn(rs), vaddr+4+(simm<<2))
    elif opcode == 0x07: return 'bgtz %s, 0x%08X' % (rn(rs), vaddr+4+(simm<<2))
    elif opcode == 0x09: return 'addiu %s, %s, %d' % (rn(rt), rn(rs), simm)
    elif opcode == 0x0A: return 'slti %s, %s, %d' % (rn(rt), rn(rs), simm)
    elif opcode == 0x0C: return 'andi %s, %s, 0x%04X' % (rn(rt), rn(rs), imm)
    elif opcode == 0x0D: return 'ori %s, %s, 0x%04X' % (rn(rt), rn(rs), imm)
    elif opcode == 0x0F: return 'lui %s, 0x%04X' % (rn(rt), imm)
    elif opcode == 0x19: return 'daddiu %s, %s, %d' % (rn(rt), rn(rs), simm)
    elif opcode == 0x1C:
        if funct == 0x18: return 'mult1 %s, %s' % (rn(rs), rn(rt))
        return 'MMI(0x%02X)' % funct
    elif opcode == 0x1F: return 'sq %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x20: return 'lb %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x21: return 'lh %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x23: return 'lw %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x24: return 'lbu %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x25: return 'lhu %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x27: return 'lwu %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x28: return 'sb %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x29: return 'sh %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x2B: return 'sw %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x37: return 'ld %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x3F: return 'sd %s, %d(%s)' % (rn(rt), simm, rn(rs))
    else: return '??? op=0x%02X raw=0x%08X' % (opcode, raw)

# Strategy 1: Search for the magic multiplier for div-by-21
# GCC/MIPS optimizes n/21 as:
#   mult n, magic_constant  (or multu)
#   mfhi result
#   sra/srl result, shift
# The magic constant for unsigned div by 21 is 0xC30C30C3
# For signed div by 21 it could be 0x30C30C31 or similar
# Let's search for lui with high half of these constants

magic_values_21 = [0xC30C, 0x30C3, 0x6186, 0xC30D, 0x0C31, 0x9999]  # various possibilities
# Also for div by 12: magic is 0xAAAAAAAB (unsigned) -> lui 0xAAAA or 0x2AAB
magic_values_12 = [0xAAAA, 0x2AAB, 0x5555]

print("=== Search for div-by-21 magic constants (lui with specific high halves) ===")
for off in range(0, len(exe)-3, 4):
    raw = struct.unpack_from('<I', exe, off)[0]
    opcode = (raw >> 26) & 0x3F
    if opcode == 0x0F:  # lui
        imm = raw & 0xFFFF
        if imm in magic_values_21:
            vaddr = off + FILE_TO_VADDR
            rt = (raw >> 16) & 0x1F
            # Show context
            print("  lui 0x%04X at file 0x%06X (vaddr 0x%08X) reg=%s" % (imm, off, vaddr, rn(rt)))
            for i in range(-4, 20):
                o = off + i*4
                if o < 0 or o+3 >= len(exe): continue
                r = struct.unpack_from('<I', exe, o)[0]
                va = o + FILE_TO_VADDR
                marker = ' <---' if o == off else ''
                print("    0x%08X [0x%06X]: %08X  %s%s" % (va, o, r, disasm(r, va), marker))
            print()

# Strategy 2: Search for the MIPS divu instruction followed by mfhi (modulo) and mflo (quotient)
# with value 21 loaded into a register nearby
print("=== Search for divu near value 21 ===")
for off in range(0, len(exe)-3, 4):
    raw = struct.unpack_from('<I', exe, off)[0]
    opcode = (raw >> 26) & 0x3F
    funct = raw & 0x3F
    if opcode == 0 and funct == 0x1B:  # divu
        # Check if 21 is loaded nearby
        for check_off in range(max(0, off-60), off, 4):
            r2 = struct.unpack_from('<I', exe, check_off)[0]
            op2 = (r2 >> 26) & 0x3F
            simm2 = (r2 & 0xFFFF)
            if simm2 > 0x7FFF: simm2 -= 0x10000
            if op2 in (0x09, 0x19) and simm2 == 21:
                vaddr = off + FILE_TO_VADDR
                print("  divu at file 0x%06X (vaddr 0x%08X) with 21 loaded at 0x%06X" % (off, vaddr, check_off))
                for i in range(-8, 16):
                    o = off + i*4
                    if o < 0 or o+3 >= len(exe): continue
                    r = struct.unpack_from('<I', exe, o)[0]
                    va = o + FILE_TO_VADDR
                    print("    0x%08X [0x%06X]: %08X  %s" % (va, o, r, disasm(r, va)))
                print()
                break

# Strategy 3: Search for "divu" near value 12 (maybe 12 is used as divisor for row calculation)
print("=== Search for divu near value 12 ===")
found_divu_12 = 0
for off in range(0, len(exe)-3, 4):
    raw = struct.unpack_from('<I', exe, off)[0]
    opcode = (raw >> 26) & 0x3F
    funct = raw & 0x3F
    if opcode == 0 and funct in (0x1A, 0x1B):  # div or divu
        for check_off in range(max(0, off-60), off, 4):
            r2 = struct.unpack_from('<I', exe, check_off)[0]
            op2 = (r2 >> 26) & 0x3F
            simm2 = (r2 & 0xFFFF)
            if simm2 > 0x7FFF: simm2 -= 0x10000
            if op2 in (0x09, 0x19) and simm2 == 12:
                vaddr = off + FILE_TO_VADDR
                print("  div(u) at file 0x%06X (vaddr 0x%08X) with 12 at 0x%06X" % (off, vaddr, check_off))
                for i in range(-8, 16):
                    o = off + i*4
                    if o < 0 or o+3 >= len(exe): continue
                    r = struct.unpack_from('<I', exe, o)[0]
                    va = o + FILE_TO_VADDR
                    print("    0x%08X [0x%06X]: %08X  %s" % (va, o, r, disasm(r, va)))
                print()
                found_divu_12 += 1
                if found_divu_12 >= 20:
                    break
                break
    if found_divu_12 >= 20:
        break

# Strategy 4: The main renderer might not use 12/21 directly
# Instead it might store the glyph width in a struct field
# Let's look for where $s0 (x-position tracker) gets incremented
# In the main function 0x302DB0, $s0 is set to 0 at start
# and probably gets incremented by glyph width after rendering each character
# Look for addiu $s0, $s0, N or addu $s0, $s0, $reg

print("=== Search for $s0 increment in main renderer (0x202E30 - 0x203530) ===")
for off in range(0x202E30, 0x203530, 4):
    raw = struct.unpack_from('<I', exe, off)[0]
    opcode = (raw >> 26) & 0x3F
    rs = (raw >> 21) & 0x1F
    rt = (raw >> 16) & 0x1F
    rd = (raw >> 11) & 0x1F
    funct = raw & 0x3F
    simm = (raw & 0xFFFF)
    if simm > 0x7FFF: simm -= 0x10000

    # addiu $s0, $s0, N
    if opcode == 0x09 and rt == 16 and rs == 16:
        vaddr = off + FILE_TO_VADDR
        print("  addiu $s0, $s0, %d at file 0x%06X (vaddr 0x%08X)" % (simm, off, vaddr))
    # addu $s0, $s0, $reg or addu $s0, $reg, $s0
    if opcode == 0 and funct == 0x21 and rd == 16 and (rs == 16 or rt == 16):
        vaddr = off + FILE_TO_VADDR
        print("  addu $s0, %s, %s at file 0x%06X (vaddr 0x%08X)" % (rn(rs), rn(rt), off, vaddr))
    # daddiu $s0
    if opcode == 0x19 and rt == 16:
        vaddr = off + FILE_TO_VADDR
        print("  daddiu $s0, %s, %d at file 0x%06X (vaddr 0x%08X)" % (rn(rs), simm, off, vaddr))

print()
print("=== Search for $s2 increment in main renderer ===")
for off in range(0x202E30, 0x203530, 4):
    raw = struct.unpack_from('<I', exe, off)[0]
    opcode = (raw >> 26) & 0x3F
    rs = (raw >> 21) & 0x1F
    rt = (raw >> 16) & 0x1F
    rd = (raw >> 11) & 0x1F
    funct = raw & 0x3F
    simm = (raw & 0xFFFF)
    if simm > 0x7FFF: simm -= 0x10000

    if opcode == 0x09 and rt == 18 and rs == 18:
        vaddr = off + FILE_TO_VADDR
        print("  addiu $s2, $s2, %d at file 0x%06X (vaddr 0x%08X)" % (simm, off, vaddr))
    if opcode == 0 and funct == 0x21 and rd == 18:
        vaddr = off + FILE_TO_VADDR
        print("  addu $s2, %s, %s at file 0x%06X (vaddr 0x%08X)" % (rn(rs), rn(rt), off, vaddr))
