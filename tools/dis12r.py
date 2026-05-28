import struct

exe = open('C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78', 'rb').read()

def vaddr_to_file(va): return va - 0x100000 + 0x80

# The rendering function computes positions via shift-add patterns.
# Let me trace the exact computation:

# At 0x303B5C-0x303BD4:
# lui r4, 0x4580      ; r4 = 4096.0 (PS2 texture page base?)
# lh r6, 94(r20)      ; r6 = currentCharIndex (from text state)
# lui r2, 0x4100       ; r2 = 8.0f
# lbu r5, 165(r21)     ; r5 = line number / font style
# addu r7, r6, r16     ; r7 = charIndex + scrollOffset
# sll r7, r7, 1        ; r7 *= 2
# addu r6, r6, r5      ; r6 = charIndex + lineNum
# addu r7, r7, r21     ; r7 = &textObj + (charIdx+scroll)*2 => ptr into glyph array
# 0x46011043           ; float sub/compare
# subu r4, r0, r3      ; r4 = -r3 (negate something)
# sll r5, r6, 1        ; r5 = (charIndex + lineNum) * 2
# lhu r3, 18(r18)      ; r3 = screenWidth or similar from font metrics
# addu r5, r5, r6      ; r5 = (charIndex + lineNum) * 3
# lh r6, 64(r7)        ; r6 = glyph data from display buffer
# sll r2, r4, 1        ; r2 = -r3 * 2
# addu r4, r2, r4      ; r4 = -r3 * 3
# lhu r2, 14(r18)      ; r2 = another font metric
# sll r4, r4, 2        ; r4 = -r3 * 12  <== HERE IS THE *12
# subu r2, r3, r2      ; r2 = metric1 - metric2
# sll r3, r5, 3        ; r3 = (charIndex + lineNum) * 24  <== HERE IS *24
# addiu r2, r2, -24    ; r2 = diff - 24
# addu r3, r4, r3      ; r3 = -negVal*12 + charTotal*24
# sra r2, r2, 1        ; r2 = (diff-24) / 2

# So the *12 pattern appears as: sll+addu+sll (x*2+x = x*3, then <<2 = x*12)
# This is applied to negative glyph counter for spacing calculation.

# But where exactly is the per-character pixel advance?
# The *24 pattern at 0x303BC4: sll r3, r5, 3 where r5 = charTotal * 3
# So charTotal * 3 * 8 = charTotal * 24
# And -negCounter * 12

# Hmm, this could mean each line is 24 pixels tall and each char is 12 pixels wide.
# Or it could be more complex with the text box layout.

# Let me now look at the *12 pattern at 0x303BAC-0x303BB8:
# This uses r4 (which was set to subu r4, r0, r3 = -r3 where r3 is some counter)
# sll r2, r4, 1   => r2 = r4*2
# addu r4, r2, r4 => r4 = r4*3
# sll r4, r4, 2   => r4 = r4*12

# And separately:
# sll r5, r6, 1   => r5 = r6*2
# addu r5, r5, r6 => r5 = r6*3
# sll r3, r5, 3   => r3 = r6*24

# So there are TWO multiply patterns: one *12 and one *24

# The *24 could be *12 * 2 (accounting for half-pixel or double resolution)
# Or line_height * char_advance

# Let me search the ENTIRE EXE for the sll+addu pattern that makes *12
# Pattern: sll rA, rB, 1; addu rC, rA, rB; sll rD, rC, 2
# This gives rD = rB * 12

print("=== sll*2 + addu + sll*4 = multiply by 12 patterns ===")
end = min(0x300000, len(exe) - 12)
for o in range(0x80, end, 4):
    i0 = struct.unpack_from('<I', exe, o)[0]
    i1 = struct.unpack_from('<I', exe, o+4)[0]
    i2 = struct.unpack_from('<I', exe, o+8)[0]

    # sll rA, rB, 1
    if (i0 & 0xFC0007FF) == 0x00000040:  # sll with sa=1
        rA = (i0 >> 11) & 0x1F
        rB = (i0 >> 16) & 0x1F
        # addu rC, rA, rB
        if (i1 & 0xFC0007FF) == 0x00000021:
            rC = (i1 >> 11) & 0x1F
            rs1 = (i1 >> 21) & 0x1F
            rt1 = (i1 >> 16) & 0x1F
            if (rs1 == rA and rt1 == rB) or (rs1 == rB and rt1 == rA):
                # sll rD, rC, 2
                if (i2 & 0xFC0007FF) == 0x00000080:  # sll with sa=2
                    rt2 = (i2 >> 16) & 0x1F
                    if rt2 == rC:
                        va = 0x100000 + o - 0x80
                        # Check if this is in/near text renderer
                        near_text = 0x2F0000 <= va <= 0x320000
                        tag = " [TEXT RENDERER AREA]" if near_text else ""
                        print(f"  VA 0x{va:08X} (file 0x{o:06X}): r{rB} * 12{tag}")
