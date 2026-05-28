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

# Full function 0x2F2BC0 - this sets up glyph display entries
print('=== Function 0x2F2BC0 (full - glyph display entry setup) ===')
show_va(0x2F2BC0, 0x2F2D80)

# The main text renderer at 0x303C60 is huge. Let me look at the part where
# it actually places characters. After the control code checks at 0x303F28+,
# there should be the normal glyph placement. Let me search for where
# glyph index is stored into the display entry and X position is computed.

# First, let me look at what fields a display entry has:
# Offset 0-1: glyph index (sh)
# Offset 2-3: ?
# Offset 4-5: color/attribute?
# Offset 6-7: fade counter
# Offset 8-11: ?

# Let me search for where sh stores glyph index (offset 0 of entries)
# and look at what x_pos calculation happens nearby

# The actual character output to screen might be in a separate drawing function.
# Let me search for functions called from the large text renderer.
print('=== All JAL targets in text renderer 0x303C60-0x306000 ===')
targets = set()
for va in range(0x303C60, 0x306000, 4):
    o = vaddr_to_file(va)
    i = struct.unpack_from('<I', exe, o)[0]
    if (i >> 26) & 0x3F == 3:
        target = (i & 0x03FFFFFF) << 2
        targets.add(target)
for t in sorted(targets):
    print(f'  jal 0x{t:08X}')

# Now let me look at how the "12 bytes per entry" display buffer is built.
# The glyph placement function should compute x = base_x + char_index * glyph_width
# where glyph_width = 12. But it might also be that the entries already contain
# pre-computed x coordinates.

# Look at 0x2F2BC0 to see what it stores in the entry
print()
print('=== 0x2F2BC0 continued (after branching) to 0x2F2E00 ===')
show_va(0x2F2D80, 0x2F2F00)
