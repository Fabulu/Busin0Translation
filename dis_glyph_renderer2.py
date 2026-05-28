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
        if funct == 0x04: return 'sllv %s, %s, %s' % (rn(rd), rn(rt), rn(rs))
        if funct == 0x06: return 'srlv %s, %s, %s' % (rn(rd), rn(rt), rn(rs))
        if funct == 0x07: return 'srav %s, %s, %s' % (rn(rd), rn(rt), rn(rs))
        if funct == 0x08: return 'jr %s' % rn(rs)
        if funct == 0x09: return 'jalr %s, %s' % (rn(rd), rn(rs))
        if funct == 0x10: return 'mfhi %s' % rn(rd)
        if funct == 0x12: return 'mflo %s' % rn(rd)
        if funct == 0x18: return 'mult %s, %s' % (rn(rs), rn(rt))
        if funct == 0x19: return 'multu %s, %s' % (rn(rs), rn(rt))
        if funct == 0x1A: return 'div %s, %s' % (rn(rs), rn(rt))
        if funct == 0x1B: return 'divu %s, %s' % (rn(rs), rn(rt))
        if funct == 0x20: return 'add %s, %s, %s' % (rn(rd), rn(rs), rn(rt))
        if funct == 0x21: return 'addu %s, %s, %s' % (rn(rd), rn(rs), rn(rt))
        if funct == 0x23: return 'subu %s, %s, %s' % (rn(rd), rn(rs), rn(rt))
        if funct == 0x24: return 'and %s, %s, %s' % (rn(rd), rn(rs), rn(rt))
        if funct == 0x25: return 'or %s, %s, %s' % (rn(rd), rn(rs), rn(rt))
        if funct == 0x26: return 'xor %s, %s, %s' % (rn(rd), rn(rs), rn(rt))
        if funct == 0x27: return 'nor %s, %s, %s' % (rn(rd), rn(rs), rn(rt))
        if funct == 0x2A: return 'slt %s, %s, %s' % (rn(rd), rn(rs), rn(rt))
        if funct == 0x2B: return 'sltu %s, %s, %s' % (rn(rd), rn(rs), rn(rt))
        if funct == 0x0D: return 'break'
        # MIPS R5900 (EE) specific
        if funct == 0x2D: return 'daddu %s, %s, %s' % (rn(rd), rn(rs), rn(rt))
        if funct == 0x3C: return 'pmaxw %s, %s, %s' % (rn(rd), rn(rs), rn(rt))  # or dsll32
        if funct == 0x3F: return 'dsra32 %s, %s, %d' % (rn(rd), rn(rt), sa)
        return 'R-type(0x%02X) %s,%s,%s' % (funct, rn(rd), rn(rs), rn(rt))
    elif opcode == 0x01:
        if rt == 0: return 'bltz %s, 0x%08X' % (rn(rs), vaddr+4+(simm<<2))
        if rt == 1: return 'bgez %s, 0x%08X' % (rn(rs), vaddr+4+(simm<<2))
        if rt == 0x11: return 'bgezal %s, 0x%08X' % (rn(rs), vaddr+4+(simm<<2))
        return 'REGIMM(rt=%d)' % rt
    elif opcode == 0x02: return 'j 0x%08X' % ((vaddr & 0xF0000000) | ((raw & 0x3FFFFFF) << 2))
    elif opcode == 0x03: return 'jal 0x%08X' % ((vaddr & 0xF0000000) | ((raw & 0x3FFFFFF) << 2))
    elif opcode == 0x04: return 'beq %s, %s, 0x%08X' % (rn(rs), rn(rt), vaddr+4+(simm<<2))
    elif opcode == 0x05: return 'bne %s, %s, 0x%08X' % (rn(rs), rn(rt), vaddr+4+(simm<<2))
    elif opcode == 0x06: return 'blez %s, 0x%08X' % (rn(rs), vaddr+4+(simm<<2))
    elif opcode == 0x07: return 'bgtz %s, 0x%08X' % (rn(rs), vaddr+4+(simm<<2))
    elif opcode == 0x09: return 'addiu %s, %s, %d' % (rn(rt), rn(rs), simm)
    elif opcode == 0x0A: return 'slti %s, %s, %d' % (rn(rt), rn(rs), simm)
    elif opcode == 0x0B: return 'sltiu %s, %s, %d' % (rn(rt), rn(rs), simm)
    elif opcode == 0x0C: return 'andi %s, %s, 0x%04X' % (rn(rt), rn(rs), imm)
    elif opcode == 0x0D: return 'ori %s, %s, 0x%04X' % (rn(rt), rn(rs), imm)
    elif opcode == 0x0E: return 'xori %s, %s, 0x%04X' % (rn(rt), rn(rs), imm)
    elif opcode == 0x0F: return 'lui %s, 0x%04X' % (rn(rt), imm)
    elif opcode == 0x19: return 'daddiu %s, %s, %d' % (rn(rt), rn(rs), simm)
    elif opcode == 0x1F:
        # EE special: sq (store quadword)
        return 'sq %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x20: return 'lb %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x21: return 'lh %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x23: return 'lw %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x24: return 'lbu %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x25: return 'lhu %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x27: return 'lwu %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x28: return 'sb %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x29: return 'sh %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x2B: return 'sw %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x3F: return 'sd %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x37: return 'ld %s, %d(%s)' % (rn(rt), simm, rn(rs))
    else: return '??? op=0x%02X raw=0x%08X' % (opcode, raw)

# The big dispatch table branches to 0x303350. Let's disassemble from there to the end of the function
# Also, functions called by this renderer (like the actual glyph draw subroutine) matter

# First, let's look at the tail of the function from 0x303350 onwards
print("=== CONTINUATION from 0x303350 (after dispatch table) ===")
for vaddr in range(0x303350, 0x303700, 4):
    off = vaddr - FILE_TO_VADDR
    if off < 0 or off+3 >= len(exe): continue
    raw = struct.unpack_from('<I', exe, off)[0]
    asm = disasm(raw, vaddr)

    marker = ''
    opcode = (raw >> 26) & 0x3F
    simm = (raw & 0xFFFF)
    if simm > 0x7FFF: simm -= 0x10000
    uimm = raw & 0xFFFF

    if opcode in (0x09, 0x0A, 0x0B, 0x19) and simm == 12: marker = ' <<<< IMM=12'
    if opcode in (0x0C, 0x0D, 0x0E) and uimm == 12: marker = ' <<<< IMM=12'
    if opcode in (0x09, 0x0A, 0x0B, 0x19) and simm == 21: marker = ' <<<< IMM=21'
    if opcode in (0x0C, 0x0D, 0x0E) and uimm == 21: marker = ' <<<< IMM=21'
    if opcode == 0x0F and uimm == 0x30C3: marker = ' <<<< LUI magic div-by-21'

    if 'jr $ra' in asm: marker = ' <-- RETURN'

    print('  0x%08X [file 0x%06X]: %08X  %-45s%s' % (vaddr, off, raw, asm, marker))

# Now search ALL jal targets from this function to find the subroutine that does actual rendering
print()
print("=== JAL targets called from 0x302DB0-0x3034FF ===")
jal_targets = set()
for vaddr in range(0x302DB0, 0x303500, 4):
    off = vaddr - FILE_TO_VADDR
    raw = struct.unpack_from('<I', exe, off)[0]
    opcode = (raw >> 26) & 0x3F
    if opcode == 0x03:  # jal
        target = (vaddr & 0xF0000000) | ((raw & 0x3FFFFFF) << 2)
        jal_targets.add(target)
for t in sorted(jal_targets):
    off = t - FILE_TO_VADDR
    print("  jal 0x%08X (file 0x%06X)" % (t, off))

# Now search BROADLY in the entire EXE for addiu with immediate 12 near divu/mult with 21
# The glyph UV calc would use: glyph_id / 21 and glyph_id % 21, then * 12
print()
print("=== BROAD SEARCH: addiu $reg, $reg, 12 in entire EXE (showing first 30) ===")
count = 0
for off in range(0, len(exe)-3, 4):
    raw = struct.unpack_from('<I', exe, off)[0]
    opcode = (raw >> 26) & 0x3F
    simm = (raw & 0xFFFF)
    if simm > 0x7FFF: simm -= 0x10000
    # addiu or daddiu with immediate exactly 12
    if opcode in (0x09, 0x19) and simm == 12:
        vaddr = off + FILE_TO_VADDR
        # Check nearby for 21
        has_21_nearby = False
        for off2 in range(max(0, off-100), min(len(exe)-3, off+100), 4):
            raw2 = struct.unpack_from('<I', exe, off2)[0]
            op2 = (raw2 >> 26) & 0x3F
            s2 = (raw2 & 0xFFFF)
            if s2 > 0x7FFF: s2 -= 0x10000
            if op2 in (0x09, 0x19) and s2 == 21:
                has_21_nearby = True
                break
            # Also check for lui with magic multiplier for 21
            if op2 == 0x0F and (raw2 & 0xFFFF) in (0x30C3, 0x6187, 0xC30D, 0x0C31):
                has_21_nearby = True
                break
        if has_21_nearby:
            print("  *** file 0x%06X (vaddr 0x%08X): %s  [21 NEARBY!]" % (off, vaddr, disasm(raw, vaddr)))
        else:
            if count < 30:
                print("  file 0x%06X (vaddr 0x%08X): %s" % (off, vaddr, disasm(raw, vaddr)))
        count += 1
print("  ... total: %d" % count)

# Search for multiply by 12: look for the constant 0xC in various forms
# On MIPS, multiply by 12 can be: sll $t, $x, 2; addu $t, $t, $x; sll $t, $t, 2 (but that's *20)
# or: sll $t1, $x, 3; sll $t2, $x, 2; addu $t, $t1, $t2 (that's *12!)
# But compilers usually just use mult instruction or addiu after a loop

# Let's look at each jal target function for constants 12 and 21
print()
print("=== DISASM of each JAL target (first 40 insns), looking for 12/21 ===")
for target in sorted(jal_targets):
    off = target - FILE_TO_VADDR
    if off < 0 or off + 160 >= len(exe): continue
    found_markers = []
    lines = []
    for i in range(40):
        o = off + i*4
        raw = struct.unpack_from('<I', exe, o)[0]
        va = o + FILE_TO_VADDR
        asm = disasm(raw, va)
        opcode = (raw >> 26) & 0x3F
        simm = (raw & 0xFFFF)
        if simm > 0x7FFF: simm -= 0x10000
        uimm = raw & 0xFFFF
        marker = ''
        if opcode in (0x09, 0x0A, 0x0B, 0x19) and simm == 12: marker = ' <<<< 12'; found_markers.append(('12', o))
        if opcode in (0x0C, 0x0D, 0x0E) and uimm == 12: marker = ' <<<< 12'; found_markers.append(('12', o))
        if opcode in (0x09, 0x0A, 0x0B, 0x19) and simm == 21: marker = ' <<<< 21'; found_markers.append(('21', o))
        if opcode in (0x0C, 0x0D, 0x0E) and uimm == 21: marker = ' <<<< 21'; found_markers.append(('21', o))
        if opcode == 0x0F and uimm in (0x30C3, 0x6187): marker = ' <<<< magic-21'; found_markers.append(('m21', o))
        lines.append('    0x%08X [file 0x%06X]: %08X  %-45s%s' % (va, o, raw, asm, marker))
        if 'jr $ra' in asm and i > 2:
            break
    if found_markers:
        print("  --- func 0x%08X (file 0x%06X) --- FOUND: %s" % (target, off, found_markers))
        for l in lines:
            print(l)
        print()
