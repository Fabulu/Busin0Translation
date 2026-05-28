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
    elif opcode == 0x08: return 'addi %s, %s, %d' % (rn(rt), rn(rs), simm)
    elif opcode == 0x09: return 'addiu %s, %s, %d' % (rn(rt), rn(rs), simm)
    elif opcode == 0x0A: return 'slti %s, %s, %d' % (rn(rt), rn(rs), simm)
    elif opcode == 0x0C: return 'andi %s, %s, 0x%04X' % (rn(rt), rn(rs), imm)
    elif opcode == 0x0D: return 'ori %s, %s, 0x%04X' % (rn(rt), rn(rs), imm)
    elif opcode == 0x0F: return 'lui %s, 0x%04X' % (rn(rt), imm)
    elif opcode == 0x11:
        fmt = (raw >> 21) & 0x1F
        ft = (raw >> 16) & 0x1F
        fs = (raw >> 11) & 0x1F
        fd = (raw >> 6) & 0x1F
        fop = raw & 0x3F
        if fmt == 4: return 'mtc1 %s, $f%d' % (rn(rt), fs)
        if fmt == 0: return 'mfc1 %s, $f%d' % (rn(rt), fs)
        if fmt == 0x10:  # S format
            ops = {0:'add.s', 1:'sub.s', 2:'mul.s', 3:'div.s', 4:'sqrt.s', 5:'abs.s', 6:'mov.s',
                   7:'neg.s', 0x20:'cvt.s.s', 0x24:'cvt.w.s', 0x0D:'trunc.w.s'}
            name = ops.get(fop, 'cop1.s(0x%02X)' % fop)
            return '%s $f%d, $f%d, $f%d' % (name, fd, fs, ft) if fop < 8 else '%s $f%d, $f%d' % (name, fd, fs)
        return 'COP1(fmt=%d,fop=0x%02X) $f%d,$f%d,$f%d' % (fmt, fop, fd, fs, ft)
    elif opcode == 0x19: return 'daddiu %s, %s, %d' % (rn(rt), rn(rs), simm)
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
    elif opcode == 0x31: return 'lwc1 $f%d, %d(%s)' % (rt, simm, rn(rs))
    elif opcode == 0x37: return 'ld %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x39: return 'swc1 $f%d, %d(%s)' % (rt, simm, rn(rs))
    elif opcode == 0x3F: return 'sd %s, %d(%s)' % (rn(rt), simm, rn(rs))
    else: return '??? op=0x%02X raw=0x%08X' % (opcode, raw)


# Dump the full function containing vaddr 0x306140 (file 0x2061C0)
# Find function start by looking backward for addiu $sp, $sp, -N
func_start = None
for check in range(0x2061C0, max(0, 0x2061C0 - 1000), -4):
    raw = struct.unpack_from('<I', exe, check)[0]
    opcode = (raw >> 26) & 0x3F
    rs = (raw >> 21) & 0x1F
    rt = (raw >> 16) & 0x1F
    simm = (raw & 0xFFFF)
    if simm > 0x7FFF: simm -= 0x10000
    if opcode == 0x09 and rs == 29 and rt == 29 and simm < 0:
        # Verify the instruction before is likely a function end (jr $ra or nop)
        if check >= 4:
            prev = struct.unpack_from('<I', exe, check-4)[0]
            prev2 = struct.unpack_from('<I', exe, check-8)[0] if check >= 8 else 0
            prev_op = (prev >> 26) & 0x3F
            # Check if previous is nop or jr $ra delay slot
            if prev == 0 or (prev_op == 0x09 and ((prev >> 21) & 0x1F) == 29):
                func_start = check
                break
        func_start = check
        break

print("=== Function containing div-by-21 magic (vaddr 0x306140) ===")
print("Function starts at file 0x%06X (vaddr 0x%08X)" % (func_start, func_start + FILE_TO_VADDR))

# Dump first 300 instructions
for i in range(300):
    o = func_start + i*4
    if o+3 >= len(exe): break
    raw = struct.unpack_from('<I', exe, o)[0]
    va = o + FILE_TO_VADDR
    asm = disasm(raw, va)

    marker = ''
    opcode = (raw >> 26) & 0x3F
    simm = (raw & 0xFFFF)
    if simm > 0x7FFF: simm -= 0x10000
    uimm = raw & 0xFFFF

    if o == 0x2061C0: marker = ' <<<< LUI 0x30C3 (div-by-21 magic)'
    if o == 0x2061C4: marker = ' <<<< ORI 0x0C31 -> full magic = 0x30C30C31'
    if opcode in (0x09, 0x19) and simm == 12: marker = ' <<<< IMM=12'
    if opcode in (0x09, 0x19) and simm == 21: marker = ' <<<< IMM=21'
    if opcode in (0x09, 0x19) and simm == 24: marker = ' <<<< IMM=24'
    if 'jr $ra' in asm: marker = ' <-- RETURN'

    print('  0x%08X [0x%06X]: %08X  %-50s%s' % (va, o, raw, asm, marker))
    if 'jr $ra' in asm and i > 20:
        break

# Also: look at the 2nd instance (vaddr 0x306EA0 at file 0x206F20)
print()
print("=== Second function containing div-by-21 magic (vaddr 0x306EA0) ===")
func_start2 = None
for check in range(0x206F20, max(0, 0x206F20 - 1000), -4):
    raw = struct.unpack_from('<I', exe, check)[0]
    opcode = (raw >> 26) & 0x3F
    rs = (raw >> 21) & 0x1F
    rt = (raw >> 16) & 0x1F
    simm = (raw & 0xFFFF)
    if simm > 0x7FFF: simm -= 0x10000
    if opcode == 0x09 and rs == 29 and rt == 29 and simm < 0:
        if check >= 4:
            prev = struct.unpack_from('<I', exe, check-4)[0]
            if prev == 0 or ((prev >> 26) & 0x3F) == 0x09:
                func_start2 = check
                break
        func_start2 = check
        break

print("Function starts at file 0x%06X (vaddr 0x%08X)" % (func_start2, func_start2 + FILE_TO_VADDR))

for i in range(300):
    o = func_start2 + i*4
    if o+3 >= len(exe): break
    raw = struct.unpack_from('<I', exe, o)[0]
    va = o + FILE_TO_VADDR
    asm = disasm(raw, va)

    marker = ''
    opcode = (raw >> 26) & 0x3F
    simm = (raw & 0xFFFF)
    if simm > 0x7FFF: simm -= 0x10000

    if o == 0x206F20: marker = ' <<<< LUI 0x30C3'
    if opcode in (0x09, 0x19) and simm == 12: marker = ' <<<< IMM=12'
    if opcode in (0x09, 0x19) and simm == 24: marker = ' <<<< IMM=24'
    if 'jr $ra' in asm: marker = ' <-- RETURN'

    print('  0x%08X [0x%06X]: %08X  %-50s%s' % (va, o, raw, asm, marker))
    if 'jr $ra' in asm and i > 20:
        break
