import struct, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

EXE_PATH = "C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78"
exe = open(EXE_PATH, "rb").read()

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

    if opcode == 0:  # R-type
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
    elif opcode == 0x20: return 'lb %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x21: return 'lh %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x23: return 'lw %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x24: return 'lbu %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x25: return 'lhu %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x28: return 'sb %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x29: return 'sh %s, %d(%s)' % (rn(rt), simm, rn(rs))
    elif opcode == 0x2B: return 'sw %s, %d(%s)' % (rn(rt), simm, rn(rs))
    else: return '??? op=0x%02X raw=0x%08X' % (opcode, raw)

# ELF header: text segment starts at file offset 0x1000, loaded to vaddr 0x100000
# So vaddr = file_offset - 0x1000 + 0x100000 = file_offset + 0x0FF000
# Given: vaddr 0x302DB0 -> file offset 0x202E30 -> diff = 0x302DB0 - 0x202E30 = 0x0FFF80
# Let's verify: 0x202E30 + 0x0FFF80 = 0x302DB0 YES
FILE_TO_VADDR = 0x0FFF80

start = 0x202E30
vaddr_base = start + FILE_TO_VADDR  # 0x302DB0

print("=== Glyph renderer @ vaddr 0x%08X (file 0x%06X) ===" % (vaddr_base, start))
print("Looking for constants: 12 (0xC) for glyph width, 21 (0x15) for columns-per-row")
print()

found_12 = []
found_21 = []
jr_ra_count = 0

for off in range(start, min(start + 1200, len(exe)-3), 4):
    raw = struct.unpack_from('<I', exe, off)[0]
    vaddr = off + FILE_TO_VADDR
    asm = disasm(raw, vaddr)

    marker = ''
    opcode = (raw >> 26) & 0x3F
    simm = (raw & 0xFFFF)
    if simm > 0x7FFF: simm -= 0x10000
    uimm = raw & 0xFFFF

    # Check for immediate 12
    if opcode in (0x09, 0x0A, 0x0B) and simm == 12:
        marker = ' <<<< IMM=12 (GLYPH WIDTH?)'
        found_12.append(off)
    if opcode in (0x0C, 0x0D, 0x0E) and uimm == 12:
        marker = ' <<<< IMM=12 (GLYPH WIDTH?)'
        found_12.append(off)
    # Check for immediate 21
    if opcode in (0x09, 0x0A, 0x0B) and simm == 21:
        marker = ' <<<< IMM=21 (COLS-PER-ROW?)'
        found_21.append(off)
    if opcode in (0x0C, 0x0D, 0x0E) and uimm == 21:
        marker = ' <<<< IMM=21 (COLS-PER-ROW?)'
        found_21.append(off)

    # Also check for multiply-by-12 via shifts (sll by 2 + sll by 3 = *12)
    # or addiu with 12
    # Check for div-by-21 magic multiplier: 0x30C30C3D or lui 0x30C3
    if opcode == 0x0F and uimm == 0x30C3:
        marker = ' <<<< LUI magic for div-by-21!'
        found_21.append(off)

    # Check for 0x0C in LUI (unlikely but check)

    if 'jr $ra' in asm:
        marker = ' <-- RETURN'
        jr_ra_count += 1

    print('  0x%08X [file 0x%06X]: %08X  %-40s%s' % (vaddr, off, raw, asm, marker))

    if jr_ra_count >= 2 and off > start + 200:
        break

print()
print("=== SUMMARY ===")
print("Instructions with immediate 12 (glyph width candidates):")
for o in found_12:
    raw = struct.unpack_from('<I', exe, o)[0]
    print("  file offset 0x%06X (vaddr 0x%08X): %08X  %s" % (o, o+FILE_TO_VADDR, raw, disasm(raw, o+FILE_TO_VADDR)))
print("Instructions with immediate 21 (column count candidates):")
for o in found_21:
    raw = struct.unpack_from('<I', exe, o)[0]
    print("  file offset 0x%06X (vaddr 0x%08X): %08X  %s" % (o, o+FILE_TO_VADDR, raw, disasm(raw, o+FILE_TO_VADDR)))

# Also search wider: scan for addiu $reg, $reg, 12 anywhere near the function
print()
print("=== WIDER SEARCH: 0xC (12) in addiu within +/- 512 bytes of func start ===")
for off in range(max(0, start-512), min(start+1500, len(exe)-3), 4):
    raw = struct.unpack_from('<I', exe, off)[0]
    opcode = (raw >> 26) & 0x3F
    simm = (raw & 0xFFFF)
    if simm > 0x7FFF: simm -= 0x10000
    if opcode == 0x09 and simm == 12:
        vaddr = off + FILE_TO_VADDR
        print("  file 0x%06X (vaddr 0x%08X): %s" % (off, vaddr, disasm(raw, vaddr)))

# Search for sll $reg, $reg, 2 followed by add (multiply by 12 = x*8 + x*4 pattern)
print()
print("=== SEARCH: Multiply-by-12 patterns (sll+add combos) ===")
for off in range(start, min(start+800, len(exe)-7), 4):
    raw = struct.unpack_from('<I', exe, off)[0]
    opcode = (raw >> 26) & 0x3F
    if opcode == 0 and (raw & 0x3F) == 0:  # sll
        sa = (raw >> 6) & 0x1F
        if sa in (2, 3):  # *4 or *8
            vaddr = off + FILE_TO_VADDR
            print("  file 0x%06X (vaddr 0x%08X): %s" % (off, vaddr, disasm(raw, vaddr)))
