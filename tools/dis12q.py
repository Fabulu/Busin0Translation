import struct

exe = open('C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78', 'rb').read()

def vaddr_to_file(va): return va - 0x100000 + 0x80

def dis(o):
    i = struct.unpack_from('<I', exe, o)[0]
    op = (i >> 26) & 0x3F; im = i & 0xFFFF
    if im > 0x7FFF: im -= 0x10000
    rs = (i >> 21) & 0x1F; rt = (i >> 16) & 0x1F; rd = (i >> 11) & 0x1F
    sa = (i >> 6) & 0x1F; fn = i & 0x3F
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
        if fn == 8: return f'jr r{rs}'
        if fn == 0x25: return f'or r{rd}, r{rs}, r{rt}'
        if fn == 0x2A: return f'slt r{rd}, r{rs}, r{rt}'
        if fn == 2: return f'srl r{rd}, r{rt}, {sa}'
        if fn == 3: return f'sra r{rd}, r{rt}, {sa}'
        if fn == 9: return f'jalr r{rd}, r{rs}'
    if op == 1:
        if rt == 1: return f'bgez r{rs}, {im}'
        if rt == 0: return f'bltz r{rs}, {im}'
    if op == 6: return f'blez r{rs}, {im}'
    if op == 7: return f'bgtz r{rs}, {im}'
    return f'0x{i:08X}'

# Function 0x3039B0 is the rendering function. Let me look at the full thing.
# It calls 0x1E6DF0 (font dispatch), 0x127078, etc.
# Specifically I want to see where it computes x = base + index * 12 (or similar)
print('=== Function 0x3039B0 (rendering) continued 0x303B00-0x303C60 ===')
for va in range(0x303B00, 0x303C60, 4):
    o = vaddr_to_file(va)
    d = dis(o)
    # Highlight 12 and key patterns
    i = struct.unpack_from('<I', exe, o)[0]
    im = i & 0xFFFF
    if im > 0x7FFF: im -= 0x10000
    m = ''
    if im == 12 and (i >> 26) & 0x3F == 9:
        m = ' <<<< IMM 12!'
    print(f'  {va:08X}: {d}{m}')

# Now let me look at 0x2F2B60 more carefully. It computes:
# sll r2, r3, 1  => r2 = index * 2
# addu r3, r2, r3 => r3 = index * 3
# sll r3, r3, 2  => r3 = index * 12
# addu r3, r3, r4 => r3 = base + index * 12
# lh r4, 168(r3) => load halfword at base + index*12 + 168
# This is the glyph display entry accessor.
# entry_addr = obj_base + 168 + char_index * 12
# Each entry is 12 bytes. Fields at offsets within the entry:
# +0 = glyph index (lh at 168)
# +2 = ?
# +4 = ?
# +6 = alpha/fade (lh at 174)
# etc.

# The rendering function 0x3039B0 iterates entries and draws them.
# At 0x303B60:
#   lh r6, 94(r20)  -- current glyph index in display
#   addu r7, r6, r16  -- r7 = glyphIdx + r16 (offset)
# Then it calls font rendering.

# The X PIXEL position is computed at render time from the character index.
# Let's look for where character index * pixel_width happens.
# In 0x3039B0, at 0x303B5C: lui r4, 0x4580 = float 4096.0
# Then 0x303B60: lh r6, 94(r20) = current char
# And 0x303B6C: lui r2, 0x4100 = float 8.0
# These might be the scaling factors for position.

# Let me check what 0x303B7C stores -- it might be x = charIndex * 8.0 + base
print()
print('=== Render positioning (0x303B5C-0x303C00) with float analysis ===')
for va in range(0x303B5C, 0x303C60, 4):
    o = vaddr_to_file(va)
    d = dis(o)
    i = struct.unpack_from('<I', exe, o)[0]
    op = (i >> 26) & 0x3F
    m = ''
    if op == 0xF:  # lui
        imm = i & 0xFFFF
        rt = (i >> 16) & 0x1F
        # Interpret as float upper half
        fval = struct.unpack('>f', struct.pack('>HH', imm, 0))[0]
        m = f'  (float high = {fval})'
    print(f'  {va:08X}: {d}{m}')

# Also check: is 12 loaded as float? 12.0f = 0x41400000
# So lui would load 0x4140
print()
print('=== Search for lui 0x4140 (float 12.0) in text render area ===')
for va in range(0x300000, 0x310000, 4):
    o = vaddr_to_file(va)
    i = struct.unpack_from('<I', exe, o)[0]
    if (i >> 26) & 0x3F == 0xF:  # lui
        if (i & 0xFFFF) == 0x4140:
            rt = (i >> 16) & 0x1F
            print(f'  VA 0x{va:08X}: lui r{rt}, 0x4140  (float 12.0!)')

# Also search broader
for va in range(0x2F0000, 0x320000, 4):
    o = vaddr_to_file(va)
    i = struct.unpack_from('<I', exe, o)[0]
    if (i >> 26) & 0x3F == 0xF:
        if (i & 0xFFFF) == 0x4140:
            rt = (i >> 16) & 0x1F
            print(f'  VA 0x{va:08X}: lui r{rt}, 0x4140  (float 12.0!)')
