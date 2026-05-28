import struct

exe = open('C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78', 'rb').read()

P_OFFSET = 0x80
P_VADDR = 0x00100000

def vaddr_to_file(va):
    return va - P_VADDR + P_OFFSET

def file_to_vaddr(foff):
    return P_VADDR + (foff - P_OFFSET)

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

def show_va(start_va, end_va, highlights=None):
    for va in range(start_va, end_va, 4):
        o = vaddr_to_file(va)
        m = ' <<<' if highlights and va in highlights else ''
        print(f'  {va:08X} (f{o:06X}): {dis(o)}{m}')
    print()

# The 0x303E70 and 0x303EF4 are 12-byte stride through a display buffer.
# But we need to find where PIXEL WIDTH = 12 is used.
# Let me look at the FontDispSetCnt function area (near vaddr 0x305800)
# and the actual glyph rendering function.

# Let's find the FontDispSetCnt function
# Search for "FontDispSetCnt" string reference
print('=== Searching for FontDispSetCnt string ===')
for i in range(len(exe) - 15):
    if exe[i:i+14] == b'FontDispSetCnt':
        va = file_to_vaddr(i)
        print(f'  String at VA 0x{va:08X} (file 0x{i:06X})')
        # Now find references to this string
        hi = (va >> 16) & 0xFFFF
        lo = va & 0xFFFF
        # With addiu, if lo < 0x8000, lui loads hi, addiu lo
        for o in range(P_OFFSET, len(exe) - 4, 4):
            raw = struct.unpack_from('<I', exe, o)[0]
            if (raw >> 26) & 0x3F == 9:  # addiu
                if (raw & 0xFFFF) == lo:
                    fva = file_to_vaddr(o)
                    print(f'    Referenced from VA 0x{fva:08X} (file 0x{o:06X})')

# Search for the function that actually renders/positions glyphs
# Look for sh (store halfword) patterns that store X position after adding 12
# The text system uses sh to store positions -- look for patterns like:
# addiu reg, reg, 12; sh reg, N(base)
print()
print('=== Searching for "sh after addiu 12" patterns ===')
end = min(0x300000, len(exe) - 3)
for o in range(P_OFFSET, end, 4):
    i = struct.unpack_from('<I', exe, o)[0]
    op = (i >> 26) & 0x3F
    im = i & 0xFFFF
    if im > 0x7FFF: im -= 0x10000
    rs = (i >> 21) & 0x1F
    rt = (i >> 16) & 0x1F
    # Look for addiu rX, rX, 12 (or addiu rX, rY, 12)
    if op == 9 and im == 12 and rs != 29:
        dest_reg = rt
        # Check nearby for sh of that register
        for j in range(-6, 7):
            if j == 0: continue
            noff = o + j * 4
            if noff >= P_OFFSET and noff < end:
                ni = struct.unpack_from('<I', exe, noff)[0]
                nop = (ni >> 26) & 0x3F
                nrt = (ni >> 16) & 0x1F
                if nop == 0x29 and nrt == dest_reg:  # sh
                    va = file_to_vaddr(o)
                    print(f'  VA 0x{va:08X}: addiu r{rt}, r{rs}, 12  (sh r{dest_reg} nearby at +{j*4})')
                    break

# Let's also look at the function 0x303510 which is called from the text renderer
print()
print('=== Function at VA 0x303510 (called from text renderer) ===')
show_va(0x303510, 0x303620)
