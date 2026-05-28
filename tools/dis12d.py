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

def show(start, end, highlight=None):
    for o in range(start, end, 4):
        m = ' <<<' if highlight and o in highlight else ''
        print(f'  0x{o:06X}: {dis(o)}{m}')
    print()

# The width table read is at 0x01A600-0x01A900.
# The function that CALLS this width reader would be the text renderer.
# Let's find JAL targets that point into this range
# i.e., find all jal 0x001Axxxx

# Actually the width table reader function needs to be identified.
# Let's look for function prologue near 0x01A600
# Back up to find the function start
print('=== Function around width table (0x01A5C0-0x01A620) ===')
show(0x01A5C0, 0x01A620)

# Let's also look at where the text rendering loop is.
# The glyph UV lookup at 0x1E4200 - let's see what's there
print('=== 0x1E4200-0x1E4300 (glyph UV lookup) ===')
show(0x1E4200, 0x1E4300)

# And let's find callers of the function at ~0x01A5D0 or wherever the width reader starts
# by searching for jal instructions targeting near 0x01A600
print('=== JAL calls into 0x1A500-0x1AB00 range ===')
for o in range(0, min(0x200000, len(exe)-3), 4):
    i = struct.unpack_from('<I', exe, o)[0]
    if (i >> 26) & 0x3F == 3:  # jal
        target = (i & 0x03FFFFFF) << 2
        if 0x1A500 <= target <= 0x1AB00:
            print(f'  0x{o:06X}: jal 0x{target:08X}')
