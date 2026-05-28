"""Analyze the 12-byte display entry struct to determine if glyph width is stored."""
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
        print(f'  {va:08X}: {dis(o)}')

# 1) Func 0x302DB0: the glyph QUEUE function that populates the display struct
# Focus on 0x302E60-0x303000 where entry data is written
show(0x302DB0, 0x303000, "func_302DB0: glyph queue/store (full)")

# 2) Look at the rendering function around the div-by-21 at 0x306140
# This computes row = charIndex / 21, then Y = row * 24
# And presumably col = charIndex % 21, X = col * 12
# Show wider context
show(0x3060E0, 0x3061C0, "Renderer: div-by-21 for row/Y calculation (near 0x306140)")

# 3) Function 0x2F2BC0 identified as display entry setup
show(0x2F2BC0, 0x2F2D80, "func_2F2BC0: display entry accessor (uses index*12 stride)")

# 4) Check what the font width table access looks like
# The width table is at VA 0x4DDCC0 (lui 0x004E, offset -9024)
# Search specifically in func_302DB0 range for any lui 0x004E
print('\n=== Search for font width table access (lui 0x004E) near renderer ===')
for va in range(0x300000, 0x310000, 4):
    o = va - FILE_TO_VADDR
    raw = struct.unpack_from('<I', exe, o)[0]
    if (raw >> 26) & 0x3F == 0x0F and (raw & 0xFFFF) == 0x004E:
        print(f'  VA {va:08X}: lui ${R[(raw>>16)&0x1F]}, 0x004E')
        # Show context
        for j in range(-4, 12):
            cv = va + j*4
            co = cv - FILE_TO_VADDR
            marker = ' <---' if j == 0 else ''
            print(f'    {cv:08X}: {dis(co)}{marker}')
