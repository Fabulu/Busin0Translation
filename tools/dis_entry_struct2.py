"""Trace X position calculation and check if width is stored in display entry."""
import struct

exe = open('C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78', 'rb').read()
FILE_TO_VADDR = 0x0FFF80
R = ['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7','s0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra']

def dis(off_f):
    raw = struct.unpack_from('<I', exe, off_f)[0]
    va = off_f + FILE_TO_VADDR
    op = (raw >> 26) & 0x3F
    rs = (raw >> 21) & 0x1F; rt = (raw >> 16) & 0x1F; rd = (raw >> 11) & 0x1F
    sa = (raw >> 6) & 0x1F; fn = raw & 0x3F
    imm = raw & 0xFFFF; si = imm - 0x10000 if imm > 0x7FFF else imm

    if op == 0x28: return f'sb ${R[rt]}, {si}(${R[rs]})'
    if op == 0x29: return f'sh ${R[rt]}, {si}(${R[rs]})'
    if op == 0x2B: return f'sw ${R[rt]}, {si}(${R[rs]})'
    if op == 0x20: return f'lb ${R[rt]}, {si}(${R[rs]})'
    if op == 0x21: return f'lh ${R[rt]}, {si}(${R[rs]})'
    if op == 0x23: return f'lw ${R[rt]}, {si}(${R[rs]})'
    if op == 0x24: return f'lbu ${R[rt]}, {si}(${R[rs]})'
    if op == 0x25: return f'lhu ${R[rt]}, {si}(${R[rs]})'
    if op == 0x09: return f'addiu ${R[rt]}, ${R[rs]}, {si}'
    if op == 0x0F: return f'lui ${R[rt]}, 0x{imm:04X}'
    if op == 0x0D: return f'ori ${R[rt]}, ${R[rs]}, 0x{imm:04X}'
    if op == 0x0C: return f'andi ${R[rt]}, ${R[rs]}, 0x{imm:04X}'
    if op == 0x04: return f'beq ${R[rs]}, ${R[rt]}, 0x{va+4+(si<<2):08X}'
    if op == 0x05: return f'bne ${R[rs]}, ${R[rt]}, 0x{va+4+(si<<2):08X}'
    if op == 0x03: return f'jal 0x{(va & 0xF0000000) | ((raw & 0x3FFFFFF) << 2):08X}'
    if op == 0x02: return f'j 0x{(va & 0xF0000000) | ((raw & 0x3FFFFFF) << 2):08X}'
    if op == 0x0A: return f'slti ${R[rt]}, ${R[rs]}, {si}'
    if op == 0x07: return f'bgtz ${R[rs]}, 0x{va+4+(si<<2):08X}'
    if op == 0x06: return f'blez ${R[rs]}, 0x{va+4+(si<<2):08X}'
    if op == 0x19: return f'daddiu ${R[rt]}, ${R[rs]}, {si}'
    if op == 0x1F: return f'sq ${R[rt]}, {si}(${R[rs]})'
    if op == 0x3F: return f'sd ${R[rt]}, {si}(${R[rs]})'
    if op == 0x37: return f'ld ${R[rt]}, {si}(${R[rs]})'
    if op == 0x01 and rt == 0: return f'bltz ${R[rs]}, 0x{va+4+(si<<2):08X}'
    if op == 0x01 and rt == 1: return f'bgez ${R[rs]}, 0x{va+4+(si<<2):08X}'
    if op == 0x11: return f'COP1(0x{raw:08X})'
    if op == 0x31: return f'lwc1 f{rt}, {si}(${R[rs]})'
    if op == 0x39: return f'swc1 f{rt}, {si}(${R[rs]})'
    if op == 0:
        if fn == 0x21: return f'addu ${R[rd]}, ${R[rs]}, ${R[rt]}'
        if fn == 0x25: return f'or ${R[rd]}, ${R[rs]}, ${R[rt]}'
        if fn == 0x24: return f'and ${R[rd]}, ${R[rs]}, ${R[rt]}'
        if fn == 0 and rd == 0 and rt == 0 and sa == 0: return 'nop'
        if fn == 0: return f'sll ${R[rd]}, ${R[rt]}, {sa}'
        if fn == 8: return f'jr ${R[rs]}'
        if fn == 9: return f'jalr ${R[rd]}, ${R[rs]}'
        if fn == 0x2D: return f'daddu ${R[rd]}, ${R[rs]}, ${R[rt]}'
        if fn == 0x23: return f'subu ${R[rd]}, ${R[rs]}, ${R[rt]}'
        if fn == 0x2A: return f'slt ${R[rd]}, ${R[rs]}, ${R[rt]}'
        if fn == 0x2B: return f'sltu ${R[rd]}, ${R[rs]}, ${R[rt]}'
        if fn == 0x3C: return f'dsll32 ${R[rd]}, ${R[rt]}, {sa}'
        if fn == 0x3F: return f'dsra32 ${R[rd]}, ${R[rt]}, {sa}'
        if fn == 0x18: return f'mult ${R[rs]}, ${R[rt]}'
        if fn == 0x19: return f'multu ${R[rs]}, ${R[rt]}'
        if fn == 0x1A: return f'div ${R[rs]}, ${R[rt]}'
        if fn == 0x1B: return f'divu ${R[rs]}, ${R[rt]}'
        if fn == 0x12: return f'mflo ${R[rd]}'
        if fn == 0x10: return f'mfhi ${R[rd]}'
        if fn == 2: return f'srl ${R[rd]}, ${R[rt]}, {sa}'
        if fn == 3: return f'sra ${R[rd]}, ${R[rt]}, {sa}'
    return f'raw=0x{raw:08X}'

def show(start_va, end_va, label=""):
    if label: print(f'\n=== {label} ===')
    for va in range(start_va, end_va, 4):
        o = va - FILE_TO_VADDR
        if o < 0 or o+4 > len(exe): continue
        print(f'  {va:08X}: {dis(o)}')

# 1. Show the COMPLETE rendering area around div-by-21 (0x306100-0x306280)
show(0x306100, 0x306280, "Renderer: atlas/position calculation (0x306100-0x306280)")

# 2. Show what happens after the second div-by-21 result
show(0x306280, 0x306400, "Renderer continued (0x306280-0x306400)")

# 3. The func_2F2BC0 accesses entries at offset +168 from base
# Let's check: what's the struct layout?
# base + index*12 + 168. So entry fields are at +168, +170, etc.
# Let's search for loads/stores at offsets 168-179 in the renderer area
print('\n=== Loads at offsets 168-179 (12-byte entry fields) in renderer ===')
for va in range(0x2F0000, 0x310000, 4):
    o = va - FILE_TO_VADDR
    if o < 0 or o+4 > len(exe): continue
    raw = struct.unpack_from('<I', exe, o)[0]
    op = (raw >> 26) & 0x3F
    si = (raw & 0xFFFF)
    if si > 0x7FFF: si -= 0x10000
    if op in (0x20, 0x21, 0x23, 0x24, 0x25) and 168 <= si <= 179:
        rt = (raw >> 16) & 0x1F
        rs = (raw >> 21) & 0x1F
        print(f'  {va:08X}: {dis(o)}')

# 4. Also check stores at offsets 168-179
print('\n=== Stores at offsets 168-179 (12-byte entry fields) in same range ===')
for va in range(0x2F0000, 0x310000, 4):
    o = va - FILE_TO_VADDR
    if o < 0 or o+4 > len(exe): continue
    raw = struct.unpack_from('<I', exe, o)[0]
    op = (raw >> 26) & 0x3F
    si = (raw & 0xFFFF)
    if si > 0x7FFF: si -= 0x10000
    if op in (0x28, 0x29, 0x2B) and 168 <= si <= 179:
        print(f'  {va:08X}: {dis(o)}')

# 5. Search for font width table (lui 0x004E) ANYWHERE in the EXE
print('\n=== ALL font width table accesses (lui 0x004E) in entire EXE ===')
count = 0
for o in range(0, len(exe)-3, 4):
    raw = struct.unpack_from('<I', exe, o)[0]
    if (raw >> 26) & 0x3F == 0x0F and (raw & 0xFFFF) == 0x004E:
        va = o + FILE_TO_VADDR
        print(f'  VA {va:08X} (file {o:06X}): lui ${R[(raw>>16)&0x1F]}, 0x004E')
        count += 1
print(f'  Total: {count} references')
