"""Check what the renderer reads from $s0 entry and where width might be."""
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
    if op == 0x11:
        fmt = (raw >> 21) & 0x1F
        if fmt == 0: return f'mfc1 ${R[rt]}, $f{rd}'
        if fmt == 4: return f'mtc1 ${R[rt]}, $f{rd}'
        if fmt == 0x10:  # single
            subfn = raw & 0x3F
            fd = (raw >> 6) & 0x1F
            fs = (raw >> 11) & 0x1F
            ft = (raw >> 16) & 0x1F
            ops = {0:'add.s', 1:'sub.s', 2:'mul.s', 3:'div.s', 6:'mov.s', 0x24:'cvt.w.s', 0x20:'cvt.s.w'}
            name = ops.get(subfn, f'cop1.s.{subfn:#x}')
            return f'{name} $f{fd}, $f{fs}, $f{ft}' if subfn < 4 else f'{name} $f{fd}, $f{fs}'
        if fmt == 0x14:  # word
            subfn = raw & 0x3F
            fd = (raw >> 6) & 0x1F
            fs = (raw >> 11) & 0x1F
            if subfn == 0x20: return f'cvt.s.w $f{fd}, $f{fs}'
            return f'cop1.w.{subfn:#x} $f{fd}, $f{fs}'
        return f'COP1(0x{raw:08X})'
    if op == 0x31: return f'lwc1 $f{rt}, {si}(${R[rs]})'
    if op == 0x39: return f'swc1 $f{rt}, {si}(${R[rs]})'
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
        if o < 0 or o+4 > len(exe): continue
        raw = struct.unpack_from('<I', exe, o)[0]
        op = (raw >> 26) & 0x3F
        rs = (raw >> 21) & 0x1F
        si = (raw & 0xFFFF)
        if si > 0x7FFF: si -= 0x10000
        m = ''
        if op in (0x20,0x21,0x23,0x24,0x25) and rs == 16:  # loads from $s0
            m = '  <-- LOAD from $s0 entry'
        if op in (0x28,0x29,0x2B) and rs == 16:
            m = '  <-- STORE to $s0 entry'
        print(f'  {va:08X}: {dis(o)}{m}')

# Show the complete renderer glyph handling (0x3063D0-0x306500)
show(0x3063D0, 0x306500, "Renderer: glyph data access from entry ($s0)")

# Also show the 0x306400-0x306480 area
show(0x306400, 0x306500, "Renderer continued")

# Now look at how the TEXT X position is computed
# The glyph's sequential index determines its column position
# We saw Y_text = (idx/21) * 24 at 0x3061BC stored to 272($sp)
# The X_text must be somewhere. Let me search for * 12 pattern
# sll r, r, 1; addu r, r, r_orig; sll r, r, 2 = x*12
print('\n=== Search for *12 pattern (sll 1 + addu + sll 2) in renderer 0x305000-0x310000 ===')
for va in range(0x305000, 0x310000, 4):
    o = va - FILE_TO_VADDR
    raw = struct.unpack_from('<I', exe, o)[0]
    op = (raw >> 26) & 0x3F
    fn = raw & 0x3F
    sa = (raw >> 6) & 0x1F
    rd = (raw >> 11) & 0x1F
    rt = (raw >> 16) & 0x1F
    # Look for sll rd, rt, 1 (first step of x*3 then sll 2 = x*12)
    if op == 0 and fn == 0 and sa == 1:
        # Check if next is addu rd2, rd, rt (where rt is the original)
        o2 = o + 4
        if o2 + 4 <= len(exe):
            raw2 = struct.unpack_from('<I', exe, o2)[0]
            if (raw2 >> 26) & 0x3F == 0 and (raw2 & 0x3F) == 0x21:
                # Check if next is sll by 2
                o3 = o + 8
                if o3 + 4 <= len(exe):
                    raw3 = struct.unpack_from('<I', exe, o3)[0]
                    if (raw3 >> 26) & 0x3F == 0 and (raw3 & 0x3F) == 0 and ((raw3 >> 6) & 0x1F) == 2:
                        print(f'  {va:08X}: {dis(o)}')
                        print(f'  {va+4:08X}: {dis(o2)}')
                        print(f'  {va+8:08X}: {dis(o3)}')
                        print()

# Also search for the *24 pattern (sll 1 + addu + sll 3) for Y
print('\n=== Search for *24 pattern (sll 1 + addu + sll 3) in renderer ===')
for va in range(0x305000, 0x310000, 4):
    o = va - FILE_TO_VADDR
    raw = struct.unpack_from('<I', exe, o)[0]
    op = (raw >> 26) & 0x3F
    fn = raw & 0x3F
    sa = (raw >> 6) & 0x1F
    if op == 0 and fn == 0 and sa == 1:
        o2 = o + 4
        if o2 + 4 <= len(exe):
            raw2 = struct.unpack_from('<I', exe, o2)[0]
            if (raw2 >> 26) & 0x3F == 0 and (raw2 & 0x3F) == 0x21:
                o3 = o + 8
                if o3 + 4 <= len(exe):
                    raw3 = struct.unpack_from('<I', exe, o3)[0]
                    if (raw3 >> 26) & 0x3F == 0 and (raw3 & 0x3F) == 0 and ((raw3 >> 6) & 0x1F) == 3:
                        vaddr = va
                        print(f'  {vaddr:08X}: {dis(o)} ; {dis(o2)} ; {dis(o3)}  == *24')
