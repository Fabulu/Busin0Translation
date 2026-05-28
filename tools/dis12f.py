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

# Search the text renderer area (vaddr 0x300000-0x310000) for immediate 12
print('=== addiu with imm=12 in text renderer area (vaddr 0x300000-0x310000) ===')
for va in range(0x300000, 0x310000, 4):
    o = vaddr_to_file(va)
    if o < 0 or o + 4 > len(exe): continue
    i = struct.unpack_from('<I', exe, o)[0]
    op = (i >> 26) & 0x3F
    im = i & 0xFFFF
    if im > 0x7FFF: im -= 0x10000
    rs = (i >> 21) & 0x1F
    rt = (i >> 16) & 0x1F
    if op == 9 and im == 12:
        print(f'  VA 0x{va:08X} (file 0x{o:06X}): addiu r{rt}, r{rs}, {im}')

# Also search wider text processing area
print()
print('=== addiu with imm=12 in wider area (vaddr 0x2F0000-0x320000) ===')
for va in range(0x2F0000, 0x320000, 4):
    o = vaddr_to_file(va)
    if o < 0 or o + 4 > len(exe): continue
    i = struct.unpack_from('<I', exe, o)[0]
    op = (i >> 26) & 0x3F
    im = i & 0xFFFF
    if im > 0x7FFF: im -= 0x10000
    rs = (i >> 21) & 0x1F
    rt = (i >> 16) & 0x1F
    if op == 9 and im == 12:
        print(f'  VA 0x{va:08X} (file 0x{o:06X}): addiu r{rt}, r{rs}, {im}')

# Also check: the font width table at virtual address 0x4DDCC0
# The width read code at file 0x1A600 = vaddr 0x2A5F80
# Let me check the callers - search for jal to this function area
print()
print('=== Function boundary near width table code (vaddr 0x2A5F80) ===')
# Find function start
for va in range(0x2A5F80, 0x2A5000, -4):
    o = vaddr_to_file(va)
    i = struct.unpack_from('<I', exe, o)[0]
    op = (i >> 26) & 0x3F
    im = i & 0xFFFF
    if im > 0x7FFF: im -= 0x10000
    rs = (i >> 21) & 0x1F
    rt = (i >> 16) & 0x1F
    if op == 9 and rs == 29 and rt == 29 and im < 0:
        print(f'  Width table function starts at VA 0x{va:08X} (file 0x{o:06X})')
        # Search for callers
        target = va
        for sva in range(0x100000, 0x400000, 4):
            so = vaddr_to_file(sva)
            if so < 0 or so + 4 > len(exe): continue
            si = struct.unpack_from('<I', exe, so)[0]
            if (si >> 26) & 0x3F == 3:  # jal
                jtarget = (si & 0x03FFFFFF) << 2
                if jtarget == target:
                    print(f'    Called from VA 0x{sva:08X} (file 0x{so:06X})')
        break
