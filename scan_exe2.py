import struct

EXE_PATH = "C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78"
with open(EXE_PATH, "rb") as f:
    exe = f.read()

# The table at 0x5191F0 must be initialized somewhere.
# Look for memcpy-like patterns where 0x5191F0 is the destination ($a0).
# Pattern: lui $a0, 0x0052; addiu $a0, $a0, 0x91F0; ... jal memcpy

# First, let me find instances where $a0 ($4) gets loaded with 0x5191F0
print("=== Places where $a0 ($4) = 0x5191F0 ===")
for i in range(0, len(exe) - 7, 4):
    insn = struct.unpack_from("<I", exe, i)[0]
    op = (insn >> 26) & 0x3F
    if op == 0x0F:  # lui
        rt = (insn >> 16) & 0x1F
        imm = insn & 0xFFFF
        if rt == 4 and imm == 0x0052:  # lui $a0, 0x0052
            # Check next few instructions for addiu $a0, $a0, 0x91F0
            for j in range(i+4, min(i+32, len(exe)-3), 4):
                insn2 = struct.unpack_from("<I", exe, j)[0]
                op2 = (insn2 >> 26) & 0x3F
                rs2 = (insn2 >> 21) & 0x1F
                rt2 = (insn2 >> 16) & 0x1F
                imm2 = insn2 & 0xFFFF
                if op2 == 0x09 and rt2 == 4 and rs2 == 4 and imm2 == 0x91F0:
                    # Found lui $a0, 0x0052 + addiu $a0, $a0, 0x91F0
                    print("  Found at EXE offset 0x%06x (lui) + 0x%06x (addiu)" % (i, j))
                    # Dump context
                    for k in range(max(0, i-32), min(len(exe)-3, j+48), 4):
                        insn3 = struct.unpack_from("<I", exe, k)[0]
                        op3 = (insn3 >> 26) & 0x3F
                        rt3 = (insn3 >> 16) & 0x1F
                        rs3 = (insn3 >> 21) & 0x1F
                        imm3 = insn3 & 0xFFFF
                        simm3 = imm3 if imm3 < 0x8000 else imm3 - 0x10000
                        rd3 = (insn3 >> 11) & 0x1F
                        marker = ""
                        if k == i:
                            marker = " <-- lui $a0"
                        elif k == j:
                            marker = " <-- addiu $a0"
                        if op3 == 0x0F:
                            print("    0x%06x: lui $%d, 0x%04x%s" % (k, rt3, imm3, marker))
                        elif op3 == 0x09:
                            print("    0x%06x: addiu $%d, $%d, %d (0x%04x)%s" % (k, rt3, rs3, simm3, imm3, marker))
                        elif op3 == 0x03:
                            target = (insn3 & 0x03FFFFFF) << 2
                            print("    0x%06x: jal 0x%08x" % (k, target))
                        elif op3 == 0x0D:
                            print("    0x%06x: ori $%d, $%d, 0x%04x" % (k, rt3, rs3, imm3))
                        elif op3 == 0x2B:
                            print("    0x%06x: sw $%d, %d($%d)" % (k, rt3, simm3, rs3))
                        elif op3 == 0x23:
                            print("    0x%06x: lw $%d, %d($%d)" % (k, rt3, simm3, rs3))
                        elif op3 == 0x00:
                            func = insn3 & 0x3F
                            if func == 0x21:
                                print("    0x%06x: addu $%d, $%d, $%d" % (k, rd3, rs3, rt3))
                            elif func == 0x25:
                                print("    0x%06x: or $%d, $%d, $%d" % (k, rd3, rs3, rt3))
                            elif func == 0:
                                sa = (insn3 >> 6) & 0x1F
                                print("    0x%06x: sll $%d, $%d, %d" % (k, rd3, rt3, sa))
                            elif func == 0x08:
                                print("    0x%06x: jr $%d" % (k, rs3))
                            else:
                                print("    0x%06x: %08x (R-type func=%d)" % (k, insn3, func))
                        else:
                            print("    0x%06x: %08x (op=%d)" % (k, insn3, op3))
                    print()
                    break

# Also look for $a0 = 0x5191F0 via addiu with $a0 already set
# This covers the case where lui sets $a0 to 0x0052 and then
# the destination is set using $a0 as base in a sw/sh instruction

print()
print("=== Search for $5 (a1) = 0x5191F0 (src for memcpy) ===")
for i in range(0, len(exe) - 7, 4):
    insn = struct.unpack_from("<I", exe, i)[0]
    op = (insn >> 26) & 0x3F
    if op == 0x0F:
        rt = (insn >> 16) & 0x1F
        imm = insn & 0xFFFF
        if rt == 5 and imm == 0x0052:  # lui $a1, 0x0052
            for j in range(i+4, min(i+32, len(exe)-3), 4):
                insn2 = struct.unpack_from("<I", exe, j)[0]
                op2 = (insn2 >> 26) & 0x3F
                rs2 = (insn2 >> 21) & 0x1F
                rt2 = (insn2 >> 16) & 0x1F
                imm2 = insn2 & 0xFFFF
                if op2 == 0x09 and rt2 == 5 and rs2 == 5 and imm2 == 0x91F0:
                    print("  Found $a1=0x5191F0 at EXE 0x%06x + 0x%06x" % (i, j))
                    for k in range(max(0, i-32), min(len(exe)-3, j+48), 4):
                        insn3 = struct.unpack_from("<I", exe, k)[0]
                        op3 = (insn3 >> 26) & 0x3F
                        rt3 = (insn3 >> 16) & 0x1F
                        rs3 = (insn3 >> 21) & 0x1F
                        imm3 = insn3 & 0xFFFF
                        simm3 = imm3 if imm3 < 0x8000 else imm3 - 0x10000
                        if op3 == 0x0F:
                            print("    0x%06x: lui $%d, 0x%04x" % (k, rt3, imm3))
                        elif op3 == 0x09:
                            print("    0x%06x: addiu $%d, $%d, %d" % (k, rt3, rs3, simm3))
                        elif op3 == 0x03:
                            target = (insn3 & 0x03FFFFFF) << 2
                            print("    0x%06x: jal 0x%08x" % (k, target))
                        else:
                            print("    0x%06x: %08x (op=%d)" % (k, insn3, op3))
                    print()
                    break

print("Done.")
