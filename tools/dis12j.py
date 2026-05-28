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

# The text renderer at VA 0x303C60 has character display entries of 12 bytes.
# Each entry appears to have: glyph_index (2 bytes at +0), color? (+4), x_pos (+6), etc.
# The 12 at 0x303E70 and 0x303EF4 is the STRIDE through the display buffer (12 bytes per glyph slot).
# This IS the 12px constant the user is asking about.

# But let me also check: is 12 used as a pixel width for advancing X?
# Look at where sh stores to offset +2 or +4 in the display entry
# Specifically, at 0x303E44: lh r4, 6(r4) -- reads field at offset 6
# at 0x303E0C: addiu r4, r4, 4  -- adds 4 to x position???
# Wait that's suspicious. Let me look more carefully.

# Let me examine the complete text rendering loop more carefully
# Find function start for the 0x303C60 area
print('=== Finding text renderer function start ===')
for va in range(0x303C60, 0x303000, -4):
    o = vaddr_to_file(va)
    i = struct.unpack_from('<I', exe, o)[0]
    op = (i >> 26) & 0x3F
    im = i & 0xFFFF
    if im > 0x7FFF: im -= 0x10000
    rs = (i >> 21) & 0x1F
    rt = (i >> 16) & 0x1F
    if op == 9 and rs == 29 and rt == 29 and im < 0:
        start_va = va
        print(f'Function starts at VA 0x{va:08X}')
        break

# Now let's look at the function that builds the display entries
# The display buffer pointer is at r21+8. Let's see where sh stores glyph index
# and x position. The x advance would be: read x, add glyph_width, store x.
# For fixed-width, width = 12.

# Let's trace back to where the display entry is populated with x-position
# Look at the function around 0x3035A0 which handles glyph codes
# and the part that stores character data into the display buffer

# Actually, let me look for where x_pos is calculated with constant 12
# Look at function 0x3035A0 (handles glyph rendering after 0x303510)
print()
print('=== Function 0x3035A0 (glyph handler) ===')
show_va(0x3035A0, 0x303900)

# Also look at 0x302990 which is called from the text renderer
print('=== Function 0x302990 (called from text renderer) ===')
show_va(0x302990, 0x302B80)
