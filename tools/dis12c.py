import struct

exe = open('C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78', 'rb').read()

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

# The 0x02CBF8 cluster is interpolation/animation code (float ops everywhere).
# The 0x1F0150 is processing 12-byte GS primitive packets.
# Let me look harder at the font width table area for where glyph advance happens.

# The font width table at 0x004E with offset -9024 = 0x4DDCC0
# 0x004E << 16 = 0x004E0000, + (-9024) = 0x004E0000 - 0x2340 = 0x4DDCC0
# So font width table is at virtual address 0x4DDCC0

# Let's find ALL references to 0x004E (lui) near lbu instructions
# to find all the width table access points
print('=== All font width table accesses (lui 0x004E + lbu) ===')
for o in range(0, min(0x200000, len(exe)-3), 4):
    i = struct.unpack_from('<I', exe, o)[0]
    op = (i >> 26) & 0x3F
    if op == 0x0F:  # lui
        rt = (i >> 16) & 0x1F
        im = i & 0xFFFF
        if im == 0x004E:
            # Check next few instructions for lbu with -9024 offset
            for j in range(1, 8):
                noff = o + j * 4
                if noff < len(exe) - 3:
                    ni = struct.unpack_from('<I', exe, noff)[0]
                    nop = (ni >> 26) & 0x3F
                    nim = ni & 0xFFFF
                    if nim > 0x7FFF: nim -= 0x10000
                    if nop == 0x24 and nim == -9024:  # lbu with -9024
                        print(f'  0x{o:06X}: lui + 0x{noff:06X}: lbu (width table access)')
                        # Now look nearby for immediate 12 as fallback/override
                        for k in range(-20, 30):
                            koff = o + k * 4
                            if 0 <= koff < len(exe) - 3:
                                ki = struct.unpack_from('<I', exe, koff)[0]
                                kop = (ki >> 26) & 0x3F
                                kim = ki & 0xFFFF
                                if kim > 0x7FFF: kim -= 0x10000
                                krs = (ki >> 21) & 0x1F
                                krt = (ki >> 16) & 0x1F
                                if kop == 9 and kim == 12:
                                    print(f'    -> 0x{koff:06X}: addiu r{krt}, r{krs}, 12 (NEARBY!)')
                        break
