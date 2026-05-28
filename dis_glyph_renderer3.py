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
        # MMI (EE multimedia instructions)
        if funct == 0x12: return 'mflo1 %s' % rn(rd)
        if funct == 0x10: return 'mfhi1 %s' % rn(rd)
        if funct == 0x18: return 'mult1 %s, %s' % (rn(rs), rn(rt))
        if funct == 0x1B: return 'divu1 %s, %s' % (rn(rs), rn(rt))
        return 'MMI(0x%02X) %s,%s,%s' % (funct, rn(rd), rn(rs), rn(rt))
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

# Disassemble the function at 0x3029B0 (called from main renderer)
# This is the most likely candidate for the actual glyph draw
targets = [0x3029B0, 0x120E20, 0x2F15F0]

for target in targets:
    off = target - FILE_TO_VADDR
    print("=== FUNCTION at vaddr 0x%08X (file 0x%06X) ===" % (target, off))
    for i in range(120):
        o = off + i*4
        if o < 0 or o+3 >= len(exe): break
        raw = struct.unpack_from('<I', exe, o)[0]
        va = o + FILE_TO_VADDR
        asm = disasm(raw, va)

        opcode = (raw >> 26) & 0x3F
        simm = (raw & 0xFFFF)
        if simm > 0x7FFF: simm -= 0x10000
        uimm = raw & 0xFFFF
        marker = ''
        if opcode in (0x09, 0x0A, 0x19) and simm == 12: marker = ' <<<< IMM=12'
        if opcode in (0x0C, 0x0D) and uimm == 12: marker = ' <<<< IMM=12'
        if opcode in (0x09, 0x0A, 0x19) and simm == 21: marker = ' <<<< IMM=21'
        if opcode in (0x0C, 0x0D) and uimm == 21: marker = ' <<<< IMM=21'
        if opcode in (0x09, 0x0A, 0x19) and simm == 6: marker = ' <<<< IMM=6'
        if opcode == 0x0F and uimm in (0x30C3, 0x6187, 0xC30D): marker = ' <<<< LUI magic-21'
        if 'jr $ra' in asm: marker = ' <-- RETURN'

        print('  0x%08X [0x%06X]: %08X  %-45s%s' % (va, o, raw, asm, marker))
        if 'jr $ra' in asm and i > 4:
            break
    print()

# Now look at the most promising candidates that have BOTH 12 and 21 nearby
print("=" * 70)
print("=== FUNCTIONS with BOTH 12 and 21 nearby ===")
print("=" * 70)

# Collect all spots with addiu/daddiu imm=12
spots_12 = []
spots_21 = []
for off in range(0, len(exe)-3, 4):
    raw = struct.unpack_from('<I', exe, off)[0]
    opcode = (raw >> 26) & 0x3F
    simm = (raw & 0xFFFF)
    if simm > 0x7FFF: simm -= 0x10000
    uimm = raw & 0xFFFF
    if opcode in (0x09, 0x19) and simm == 12:
        spots_12.append(off)
    if opcode in (0x09, 0x19) and simm == 21:
        spots_21.append(off)

# Find spots where 12 and 21 are within 200 bytes of each other
pairs = []
j = 0
for s12 in spots_12:
    while j < len(spots_21) and spots_21[j] < s12 - 200:
        j += 1
    k = j
    while k < len(spots_21) and spots_21[k] <= s12 + 200:
        pairs.append((s12, spots_21[k]))
        k += 1

print("Found %d pairs of (12, 21) within 200 bytes:" % len(pairs))
seen_funcs = set()
for s12, s21 in pairs:
    # Find function start (look backward for addiu $sp, $sp, -N)
    func_start = None
    for check in range(min(s12, s21), max(0, min(s12, s21) - 400), -4):
        raw = struct.unpack_from('<I', exe, check)[0]
        opcode = (raw >> 26) & 0x3F
        rs = (raw >> 21) & 0x1F
        rt = (raw >> 16) & 0x1F
        simm = (raw & 0xFFFF)
        if simm > 0x7FFF: simm -= 0x10000
        if opcode == 0x09 and rs == 29 and rt == 29 and simm < 0:  # addiu $sp, $sp, -N
            func_start = check
            break

    func_key = func_start if func_start else min(s12, s21)
    if func_key in seen_funcs:
        continue
    seen_funcs.add(func_key)

    vaddr12 = s12 + FILE_TO_VADDR
    vaddr21 = s21 + FILE_TO_VADDR
    print("\n  12 @ file 0x%06X (vaddr 0x%08X), 21 @ file 0x%06X (vaddr 0x%08X)" % (s12, vaddr12, s21, vaddr21))
    if func_start:
        print("  Function starts at file 0x%06X (vaddr 0x%08X)" % (func_start, func_start + FILE_TO_VADDR))

    # Dump context around the pair
    start_dump = min(s12, s21) - 40
    end_dump = max(s12, s21) + 60
    for o in range(max(0, start_dump), min(len(exe)-3, end_dump), 4):
        raw = struct.unpack_from('<I', exe, o)[0]
        va = o + FILE_TO_VADDR
        asm = disasm(raw, va)
        marker = ''
        if o == s12: marker = ' <<<< THIS IS THE 12'
        if o == s21: marker = ' <<<< THIS IS THE 21'
        print('    0x%08X [0x%06X]: %08X  %-45s%s' % (va, o, raw, asm, marker))
