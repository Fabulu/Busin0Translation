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

# The text renderer function at 0x303C60 is large. Let me look at the full thing
# focusing on where glyph entries are populated and X position is computed.
# The key area is where sh stores to display buffer entries.

# Let me look at the main text processing loop where normal glyphs are handled
# (not control codes). This would be after all the control code checks.
# From the code at 0x303F28: ori r2, 0xFE09 followed by comparisons...
# After all control code checks, the fallthrough would be the normal glyph handler.

# Let me look at where the glyph goes into the display buffer
# From 0x303E00 area: lw r4, 8(r21) loads buffer ptr, addu r6, r4, r2 computes entry,
# lh r4, 6(r6) reads x_pos from entry, addiu r4, r4, 4 adds 4 to it (NOT 12!),
# sh r4, 6(r6) stores it back.
# Wait -- it adds 4 to the halfword at offset 6? That's suspicious.

# Actually wait: at 0x303E0C: addiu r4, r4, 4 -- but the context shows
# sh r4, 6(r6) at 0x303E10. So field+6 gets += 4. What is this field?

# Let me look more carefully at the complete loop
print('=== Text renderer main loop 0x303C60-0x303E80 ===')
show_va(0x303C60, 0x303E80, {0x303E70})

# Now let me check the function 0x002F2B60 and 0x002F2BC0 which are called
# for each glyph in the FE00-FE08 handlers. These might set the glyph entry up.
print('=== Function 0x2F2B60 (glyph setup?) ===')
show_va(0x2F2B60, 0x2F2C80)
