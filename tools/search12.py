import struct

exe = open('C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78', 'rb').read()
end = min(0x200000, len(exe) - 3)

def dis(o):
    i = struct.unpack_from('<I', exe, o)[0]
    op = (i >> 26) & 0x3F
    im = i & 0xFFFF
    if im > 0x7FFF: im -= 0x10000
    rs = (i >> 21) & 0x1F
    rt = (i >> 16) & 0x1F
    rd = (i >> 11) & 0x1F
    sa = (i >> 6) & 0x1F
    fn = i & 0x3F
    if op == 9: return f'addiu r{rt}, r{rs}, {im}'
    if op == 0xF: return f'lui r{rt}, 0x{im & 0xFFFF:04X}'
    if op == 0x23: return f'lw r{rt}, {im}(r{rs})'
    if op == 0x2B: return f'sw r{rt}, {im}(r{rs})'
    if op == 0x24: return f'lbu r{rt}, {im}(r{rs})'
    if op == 0x25: return f'lhu r{rt}, {im}(r{rs})'
    if op == 0x20: return f'lb r{rt}, {im}(r{rs})'
    if op == 0x21: return f'lh r{rt}, {im}(r{rs})'
    if op == 4: return f'beq r{rs}, r{rt}, {im}'
    if op == 5: return f'bne r{rs}, r{rt}, {im}'
    if op == 0xA: return f'slti r{rt}, r{rs}, {im}'
    if op == 0xD: return f'ori r{rt}, r{rs}, 0x{im & 0xFFFF:04X}'
    if op == 3: return f'jal 0x{(i & 0x03FFFFFF) << 2:08X}'
    if op == 2: return f'j 0x{(i & 0x03FFFFFF) << 2:08X}'
    if op == 0x28: return f'sb r{rt}, {im}(r{rs})'
    if op == 0x29: return f'sh r{rt}, {im}(r{rs})'
    if op == 0:
        if fn == 0x21: return f'addu r{rd}, r{rs}, r{rt}'
        if fn == 0x23: return f'subu r{rd}, r{rs}, r{rt}'
        if fn == 0 and sa > 0: return f'sll r{rd}, r{rt}, {sa}'
        if fn == 0 and sa == 0 and rd == 0: return 'nop'
        if fn == 0x18: return f'mult r{rs}, r{rt}'
        if fn == 0x12: return f'mflo r{rd}'
        if fn == 0x10: return f'mfhi r{rd}'
        if fn == 8: return f'jr r{rs}'
        if fn == 0x25: return f'or r{rd}, r{rs}, r{rt}'
        if fn == 0x2A: return f'slt r{rd}, r{rs}, r{rt}'
        if fn == 0x24: return f'and r{rd}, r{rs}, r{rt}'
        if fn == 0x27: return f'nor r{rd}, r{rs}, r{rt}'
        if fn == 2: return f'srl r{rd}, r{rt}, {sa}'
        if fn == 3: return f'sra r{rd}, r{rt}, {sa}'
        if fn == 0x09: return f'jalr r{rd}, r{rs}'
    if op == 1:
        if rt == 1: return f'bgez r{rs}, {im}'
        if rt == 0: return f'bltz r{rs}, {im}'
    if op == 6: return f'blez r{rs}, {im}'
    if op == 7: return f'bgtz r{rs}, {im}'
    return f'0x{i:08X}'

# Part 1: mult near li 12
print('=== mult near li 12 ===')
for o in range(0, end, 4):
    i = struct.unpack_from('<I', exe, o)[0]
    if (i >> 26) == 0 and (i & 0x3F) == 0x18:
        rs = (i >> 21) & 0x1F
        rt = (i >> 16) & 0x1F
        for j in range(-8, 0):
            noff = o + j * 4
            if 0 <= noff < end:
                ni = struct.unpack_from('<I', exe, noff)[0]
                if (ni >> 26) == 9 and (ni >> 21) & 0x1F == 0 and ni & 0xFFFF == 12:
                    nrt = (ni >> 16) & 0x1F
                    if nrt in [rs, rt]:
                        print(f'  li r{nrt},12 @ 0x{noff:06X} -> mult r{rs},r{rt} @ 0x{o:06X}')

# Part 2: sll+addu producing *12 (sll 2 + sll 1 + original, etc)
# x*12 = (x<<2)*3 = (x<<3) + (x<<2)
# Look for sll by 2 near sll by 3 of same register
# Actually simpler: just look for sll r_x, r_y, 2 followed within 4 by addu using sll r_z, r_y, 1
# Skip this for now, it's complex

# Part 3: look for the glyph rendering loop more directly
# The font width table is at a known address. Let's find references to it.
# From project notes, we know about font width table. Let's search for
# any addiu with 12 near JAL calls (function calls to render glyph)
print()
print('=== addiu reg,reg,12 in branch delay or near JAL (glyph render?) ===')
for o in range(0, end, 4):
    i = struct.unpack_from('<I', exe, o)[0]
    op = (i >> 26) & 0x3F
    im = i & 0xFFFF
    if im > 0x7FFF: im -= 0x10000
    rs = (i >> 21) & 0x1F
    rt = (i >> 16) & 0x1F
    if op == 9 and im == 12 and rs == rt and rs != 29:
        # Check if there's a JAL within +/- 8 instructions
        has_jal = False
        for j in range(-8, 9):
            noff = o + j * 4
            if 0 <= noff < end:
                ni = struct.unpack_from('<I', exe, noff)[0]
                if (ni >> 26) == 3:  # jal
                    has_jal = True
                    break
        # Check if there's a lbu/lhu (character load) within +/- 16 instructions
        has_charload = False
        for j in range(-16, 17):
            noff = o + j * 4
            if 0 <= noff < end:
                ni = struct.unpack_from('<I', exe, noff)[0]
                nop = (ni >> 26) & 0x3F
                if nop in [0x24, 0x25]:  # lbu, lhu
                    has_charload = True
                    break
        if has_jal and has_charload:
            print(f'  0x{o:06X}: addiu r{rt}, r{rt}, 12  (near JAL + char load)')
