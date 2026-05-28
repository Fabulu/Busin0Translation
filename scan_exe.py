import struct, os

EXE_PATH = "C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78"

with open(EXE_PATH, "rb") as f:
    exe = f.read()

print("EXE size: %d bytes" % len(exe))

# PS2 EXE header: first 0x800 bytes usually
# Text section typically loaded at 0x100000
# BSS at 0x5191F0

# Search for lui instructions that load upper half of 0x5191F0
# 0x5191F0 = 0x0052_91F0 ... wait, 0x5191F0 = 0x0051_91F0
# lui $reg, 0x0052 then addiu $reg, $reg, -0x6E10 (0x91F0)
# Actually: 0x5191F0. Upper = 0x0052 (since 0x91F0 is negative in signed, 0x0051 + 1 = 0x0052)
# addiu: 0x91F0 as signed = -0x6E10
# So: lui $reg, 0x0052; addiu $reg, $reg, 0x91F0 (or -0x6E10)

# MIPS: lui rt, imm => 0x3C000000 | (rt << 16) | imm
# Search for lui with imm=0x0052
# 0x3Cxx0052 in LE bytes: 52 00 xx 3C
target_lui_imm = 0x0052
count = 0
for i in range(0, len(exe) - 3, 4):
    insn = struct.unpack_from("<I", exe, i)[0]
    op = (insn >> 26) & 0x3F
    if op == 0x0F:  # lui
        imm = insn & 0xFFFF
        if imm == target_lui_imm:
            rt = (insn >> 16) & 0x1F
            # Look at nearby instructions for addiu with 0x91F0
            print("  lui $%d, 0x0052 at offset 0x%06x" % (rt, i))
            # Check surrounding instructions (within 20 insn)
            for j in range(max(0, i-40), min(len(exe)-3, i+80), 4):
                insn2 = struct.unpack_from("<I", exe, j)[0]
                op2 = (insn2 >> 26) & 0x3F
                if op2 == 0x09:  # addiu
                    imm2 = insn2 & 0xFFFF
                    if imm2 == 0x91F0:
                        rs2 = (insn2 >> 21) & 0x1F
                        rt2 = (insn2 >> 16) & 0x1F
                        print("    addiu $%d, $%d, 0x91F0 at offset 0x%06x (==> 0x5191F0!)" % (rt2, rs2, j))
            count += 1

print("Total lui 0x0052: %d" % count)

# Also search for lui 0x0051
print()
print("=== lui $reg, 0x0051 ===")
for i in range(0, len(exe) - 3, 4):
    insn = struct.unpack_from("<I", exe, i)[0]
    op = (insn >> 26) & 0x3F
    if op == 0x0F:
        imm = insn & 0xFFFF
        if imm == 0x0051:
            rt = (insn >> 16) & 0x1F
            # Check for addiu with upper bits that could reach 0x5191F0
            # 0x0051_0000 + 0x91F0 = 0x5191F0
            for j in range(max(0, i-40), min(len(exe)-3, i+80), 4):
                insn2 = struct.unpack_from("<I", exe, j)[0]
                op2 = (insn2 >> 26) & 0x3F
                if op2 == 0x09:  # addiu
                    imm2 = insn2 & 0xFFFF
                    if imm2 == 0x91F0:
                        rs2 = (insn2 >> 21) & 0x1F
                        rt2 = (insn2 >> 16) & 0x1F
                        print("  lui $%d, 0x0051 at 0x%06x + addiu $%d,$%d,0x91F0 at 0x%06x" % (rt, i, rt2, rs2, j))

# The address 0x5191F0 with MIPS sign extension:
# lui loads 0x0052_0000 (if imm is 0x0052)
# addiu with 0x91F0 (signed = -0x6E10): 0x0052_0000 - 0x6E10 = 0x0051_91F0  
# Wait: 0x0052_0000 + sign_ext(0x91F0) = 0x00520000 + 0xFFFF91F0 = 0x005191F0
# Actually in 32-bit: 0x00520000 + 0xFFFF91F0 = 0x005191F0. Yes!
# So: lui 0x0052 + addiu 0x91F0 => 0x5191F0. Correct.

print()
print("=== Search for the literal value 0x5191F0 in EXE ===")
target_bytes_le = struct.pack("<I", 0x005191F0)
for i in range(0, len(exe) - 3):
    if exe[i:i+4] == target_bytes_le:
        print("  Found 0x005191F0 at EXE offset 0x%06x" % i)

# Also look for resource index being loaded near our lui/addiu sequences
# A common pattern: li $a0, <resource_id> before a jal (function call)
print()
print("=== Context around lui 0x0052 + addiu 0x91F0 matches ===")
for i in range(0, len(exe) - 3, 4):
    insn = struct.unpack_from("<I", exe, i)[0]
    op = (insn >> 26) & 0x3F
    if op == 0x0F:
        imm = insn & 0xFFFF
        if imm == 0x0052:
            rt = (insn >> 16) & 0x1F
            has_91f0 = False
            for j in range(max(0, i-40), min(len(exe)-3, i+80), 4):
                insn2 = struct.unpack_from("<I", exe, j)[0]
                op2 = (insn2 >> 26) & 0x3F
                if op2 == 0x09 and (insn2 & 0xFFFF) == 0x91F0:
                    has_91f0 = True
                    break
            if has_91f0:
                print("  Match at 0x%06x, dumping context:" % i)
                for k in range(max(0, i-48), min(len(exe)-3, i+80), 4):
                    insn3 = struct.unpack_from("<I", exe, k)[0]
                    op3 = (insn3 >> 26) & 0x3F
                    rt3 = (insn3 >> 16) & 0x1F
                    rs3 = (insn3 >> 21) & 0x1F
                    imm3 = insn3 & 0xFFFF
                    # Simple disasm
                    marker = " <--" if k == i else ""
                    if op3 == 0x0F:
                        print("    0x%06x: lui $%d, 0x%04x%s" % (k, rt3, imm3, marker))
                    elif op3 == 0x09:
                        simm = imm3 if imm3 < 0x8000 else imm3 - 0x10000
                        print("    0x%06x: addiu $%d, $%d, 0x%04x (%d)%s" % (k, rt3, rs3, imm3, simm, marker))
                    elif op3 == 0x03:
                        target = (insn3 & 0x03FFFFFF) << 2
                        print("    0x%06x: jal 0x%08x" % (k, target))
                    elif op3 == 0x0D:
                        print("    0x%06x: ori $%d, $%d, 0x%04x" % (k, rt3, rs3, imm3))
                    elif op3 == 0x2B:
                        print("    0x%06x: sw $%d, 0x%04x($%d)" % (k, rt3, imm3, rs3))
                    elif op3 == 0x23:
                        print("    0x%06x: lw $%d, 0x%04x($%d)" % (k, rt3, imm3, rs3))
                    elif op3 == 0x25:
                        print("    0x%06x: lhu $%d, 0x%04x($%d)" % (k, rt3, imm3, rs3))
                    elif op3 == 0x21:
                        print("    0x%06x: lh $%d, 0x%04x($%d)" % (k, rt3, imm3, rs3))
                    else:
                        print("    0x%06x: %08x (op=%d)" % (k, insn3, op3))
                print()

print("Done.")
