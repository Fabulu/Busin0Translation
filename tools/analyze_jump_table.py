"""
Analyze the jump tables used by the switch-case functions containing li $v0, 38 and 45.

Function at VA 0x46c710 (file 0x36c790):
  sltiu $at, $a0, 21    -- 21 cases (0-20)
  beq $at, $zero, default
  lui $v1, 0x0050
  sll $v0, $a0, 2
  addiu $v1, $v1, -30192  -- v1 = 0x4F8A10  (but this is VA, file = 0x4F8A10 - 0xFFF80 = 0x3F8A90)
  addu $v0, $v0, $v1
  lw $v0, 0($v0)          -- load jump target from table
  jr $v0

The jump table is at VA 0x4F8A10 = file offset 0x3F8A90
21 entries (cases 0-20)
"""
import struct

EXE_PATH = r"C:\Programmieren\wizardrytranslation\extracted\SLPM_653.78"
VA_BASE = 0x0FFF80

def fo2va(fo):
    return fo + VA_BASE

def va2fo(va):
    return va - VA_BASE

with open(EXE_PATH, "rb") as f:
    exe = f.read()

# Jump table 1: at VA 0x4F8A10, file 0x3F8A90
# Actually: lui $v1, 0x0050; addiu $v1, $v1, -30192
# 0x0050 << 16 = 0x500000; + (-30192 = -0x7600 + something)
# -30192 = 0xFFFF89B0... no. -30192 signed = 0x8A10 - 0x10000 = nah
# addiu sign extends: -30192 decimal = ? Let me compute properly
# 0x8A10 = 35344. Since bit 15 is set, sign-extended = 0x8A10 - 0x10000 = -30192.
# So v1 = 0x00500000 + (-30192) = 0x004F8A10. Wait, 0x00500000 - 30192 = 0x004F8A10
# VA 0x4F8A10, file offset = 0x4F8A10 - 0xFFF80 = 0x3F8A90

print("=" * 80)
print("JUMP TABLE 1: Function at VA 0x46c710 (glyph width table)")
print("Jump table at VA 0x4F8A10, file 0x3F8A90, 21 entries")
print("=" * 80)

jt1_fo = 0x3F8A90
for i in range(21):
    addr = struct.unpack_from("<I", exe, jt1_fo + i*4)[0]
    print(f"  Case {i:2d}: jump to VA {addr:#010x}")

# Now let's understand what this function returns
# The function takes $a0 (case index 0-20) and returns $v0 (a value)
# Let me map each case to its return value from the disassembly
print()
print("RETURN VALUES (from disassembly):")
# The switch cases are at VA 0x46c734 through 0x46c7E0
# Let me read what value each case jumps to
# From the disasm above:
# Case entries (working backwards from the code):
# VA 0x46c738: b 0x46c7e8; li $v0, 159
# VA 0x46c740: b 0x46c7e8; li $v0, 105
# VA 0x46c748: b 0x46c7e8; li $v0, 42
# VA 0x46c750: b 0x46c7e8; li $v0, 38    <-- THIS ONE RETURNS 38
# VA 0x46c758: b 0x46c7e8; li $v0, 46
# VA 0x46c760: b 0x46c7e8; li $v0, 56  (default case target)
# VA 0x46c768: b 0x46c7e8; li $v0, 40
# VA 0x46c770: b 0x46c7e8; li $v0, 30
# VA 0x46c778: b 0x46c7e8; li $v0, 117
# VA 0x46c780: b 0x46c7e8; li $v0, 37
# VA 0x46c788: b 0x46c7e8; li $v0, 45    <-- THIS ONE RETURNS 45
# VA 0x46c790: b 0x46c7e8; li $v0, 30
# VA 0x46c798: b 0x46c7e8; li $v0, 42
# VA 0x46c7a0: b 0x46c7e8; li $v0, 7
# VA 0x46c7a8: b 0x46c7e8; li $v0, 40
# VA 0x46c7b0: b 0x46c7e8; li $v0, 17
# VA 0x46c7b8: b 0x46c7e8; li $v0, 30
# VA 0x46c7c0: b 0x46c7e8; li $v0, 8
# VA 0x46c7c8: b 0x46c7e8; li $v0, 1
# VA 0x46c7d0: b 0x46c7e8; li $v0, 1
# VA 0x46c7d8: b 0x46c7e8; li $v0, 1
# VA 0x46c7E0 (default): v0 = 0

# Map jump targets to values
case_targets = {}
for i in range(21):
    addr = struct.unpack_from("<I", exe, jt1_fo + i*4)[0]
    # Read the instruction at this VA (it's a branch, delay slot has the value)
    target_fo = va2fo(addr)
    if 0 <= target_fo < len(exe) - 8:
        instr1 = struct.unpack_from("<I", exe, target_fo)[0]
        instr2 = struct.unpack_from("<I", exe, target_fo + 4)[0]
        # The branch is at target, delay slot is target+4
        # Delay slot should be li $v0, VALUE or move $v0, $zero
        op2 = (instr2 >> 26) & 0x3F
        rt2 = (instr2 >> 16) & 0x1F
        imm2 = instr2 & 0xFFFF
        if imm2 & 0x8000:
            imm2_s = imm2 - 0x10000
        else:
            imm2_s = imm2

        if instr2 == 0x0000102d:  # move $v0, $zero (daddu $v0, $zero, $zero)
            value = 0
        elif op2 == 9:  # addiu
            value = imm2_s
        else:
            value = f"??? ({instr2:#010x})"

        print(f"  Case {i:2d} -> VA {addr:#010x} -> returns $v0 = {value}")
        case_targets[i] = value

print()
print("INTERPRETATION:")
print("This function is a LOOKUP TABLE that takes a 'category/row index' (0-20)")
print("and returns a PIXEL WIDTH or SPACING value.")
print("It is NOT the skip mechanism - it's a width/metrics function.")
print()

# ============================================================
# Now look at the SECOND pair: li $a3, 38/45 at 0x363b74/0x363c38
# This is in a linear unrolled loop calling jal 0x3a2d10 with
# sequential glyph IDs 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46...
# This is clearly setting up glyph rendering for ALL glyphs including 38 and 45
# ============================================================
print("=" * 80)
print("SECOND PAIR: li $a3, 38/45 at VA 0x463af4/0x463bb8")
print("This is a linear unrolled glyph setup loop - calls jal 0x3a2d10")
print("with sequential glyph IDs and stores results at s4+offset")
print("Glyph 38 (F) and 45 (M) ARE included in this sequence.")
print("This is NOT the skip mechanism either - it processes ALL glyphs.")
print("=" * 80)

# ============================================================
# Now let's look at the ACTUAL rendering loop more carefully
# The skip must be happening in the rendering/drawing code
# Let me search for the function that iterates over cells and decides to draw
# ============================================================
print()
print("=" * 80)
print("SEARCHING FOR THE ACTUAL RENDER LOOP")
print("Looking for loops that iterate 0-94 (or similar) with skip conditions")
print("=" * 80)

# The keyboard has cells 0-94. The rendering loop should iterate over them.
# Look for comparisons against 95 (0x5F) which would be the loop bound
# In the keyboard code area
KB_START = 0x36C600
KB_END = 0x36E1D0

print("\n--- Instructions with immediate 95 (0x5F) in keyboard area ---")
for off in range(KB_START, KB_END, 4):
    instr = struct.unpack_from("<I", exe, off)[0]
    op = (instr >> 26) & 0x3F
    imm = instr & 0xFFFF
    if imm & 0x8000:
        imm_s = imm - 0x10000
    else:
        imm_s = imm

    if imm == 95 and op in (9, 10, 11, 12, 13):
        rs = (instr >> 21) & 0x1F
        rt = (instr >> 16) & 0x1F
        REG = ["zero","at","v0","v1","a0","a1","a2","a3",
               "t0","t1","t2","t3","t4","t5","t6","t7",
               "s0","s1","s2","s3","s4","s5","s6","s7",
               "t8","t9","k0","k1","gp","sp","s8","ra"]
        opnames = {9: "addiu", 10: "slti", 11: "sltiu", 12: "andi", 13: "ori"}
        va = fo2va(off)
        print(f"  File {off:#08x} VA {va:#08x}: {opnames[op]} ${REG[rt]}, ${REG[rs]}, {imm}")

# Also search for 94 (0x5E) as loop bound might be < 95 or <= 94
print("\n--- Instructions with immediate 94 (0x5E) in keyboard area ---")
for off in range(KB_START, KB_END, 4):
    instr = struct.unpack_from("<I", exe, off)[0]
    op = (instr >> 26) & 0x3F
    imm = instr & 0xFFFF
    if imm == 94 and op in (9, 10, 11):
        rs = (instr >> 21) & 0x1F
        rt = (instr >> 16) & 0x1F
        REG = ["zero","at","v0","v1","a0","a1","a2","a3",
               "t0","t1","t2","t3","t4","t5","t6","t7",
               "s0","s1","s2","s3","s4","s5","s6","s7",
               "t8","t9","k0","k1","gp","sp","s8","ra"]
        opnames = {9: "addiu", 10: "slti", 11: "sltiu"}
        va = fo2va(off)
        print(f"  File {off:#08x} VA {va:#08x}: {opnames[op]} ${REG[rt]}, ${REG[rs]}, {imm}")

# Also look for the third jump table function at VA 0x46c7F0 (file 0x36c870)
# This one also has 21 cases with jump table at 0x4F8A70
print()
print("=" * 80)
print("JUMP TABLE 2: Function at VA 0x46c7F0")
print("Jump table at VA 0x4F8A70, file 0x3F8AF0, 21 entries")
print("=" * 80)

# 0x00500000 + 0xFFFF8A70 sign ext = 0x00500000 - 0x7590 = 0x004F8A70
# file = 0x4F8A70 - 0xFFF80 = 0x3F8AF0
jt2_fo = 0x3F8AF0
for i in range(21):
    addr = struct.unpack_from("<I", exe, jt2_fo + i*4)[0]
    target_fo = va2fo(addr)
    if 0 <= target_fo < len(exe) - 8:
        instr1 = struct.unpack_from("<I", exe, target_fo)[0]
        instr2 = struct.unpack_from("<I", exe, target_fo + 4)[0]
        op2 = (instr2 >> 26) & 0x3F
        if instr2 == 0x0000102d:
            value = 0
        elif op2 == 9:
            v = instr2 & 0xFFFF
            value = v - 0x10000 if v & 0x8000 else v
        else:
            value = f"??? ({instr2:#010x})"
        print(f"  Case {i:2d} -> VA {addr:#010x} -> returns $v0 = {value}")

# ============================================================
# Also look at the FIRST jump table function at VA 0x46c610 (file 0x36c690)
# Jump table at 0x4F89B0 = file 0x3F8A30
print()
print("=" * 80)
print("JUMP TABLE 0: Function at VA 0x46c610")
print("Jump table at VA 0x4F89B0, file 0x3F8A30, 21 entries")
print("=" * 80)

# lui $a0, 0x0050; addiu $a0, $a0, -30288
# 0x500000 + (-30288) = 0x500000 - 0x7650 = 0x4F89B0
# file = 0x4F89B0 - 0xFFF80 = 0x3F8A30
jt0_fo = 0x3F8A30
for i in range(21):
    addr = struct.unpack_from("<I", exe, jt0_fo + i*4)[0]
    target_fo = va2fo(addr)
    if 0 <= target_fo < len(exe) - 8:
        instr1 = struct.unpack_from("<I", exe, target_fo)[0]
        instr2 = struct.unpack_from("<I", exe, target_fo + 4)[0]
        # For this one, the cases add to $v0 (addiu $v0, $v0, imm)
        op2 = (instr2 >> 26) & 0x3F
        rs2 = (instr2 >> 21) & 0x1F
        rt2 = (instr2 >> 16) & 0x1F
        imm2 = instr2 & 0xFFFF
        if imm2 & 0x8000:
            imm2_s = imm2 - 0x10000
        else:
            imm2_s = imm2

        if instr2 == 0:
            desc = "nop (v0 unchanged)"
        elif op2 == 9 and rs2 == 2:  # addiu $v0, $v0, imm
            desc = f"$v0 += {imm2_s}"
        elif instr2 == 0x0000102d:
            desc = "$v0 = 0"
        else:
            desc = f"??? ({instr2:#010x})"
        print(f"  Case {i:2d} -> VA {addr:#010x} -> {desc}")

# ============================================================
# Now the REAL question: who CALLS these functions?
# These are width/metric lookup functions. The caller decides whether to draw.
# Let's search for who calls the function at VA 0x46c710
# jal target encodes as: 0x0C000000 | (target >> 2)
# target = 0x46c710, target >> 2 = 0x11B1C4
# jal encoding = 0x0C11B1C4
# ============================================================
print()
print("=" * 80)
print("WHO CALLS THESE FUNCTIONS?")
print("=" * 80)

functions_to_find = [
    ("0x46c580", 0x46c580),  # First tiny function (returns an address)
    ("0x46c590", 0x46c590),  # Second function
    ("0x46c5D0", 0x46c5D0),  # Third function
    ("0x46c610", 0x46c610),  # Glyph offset lookup
    ("0x46c710", 0x46c710),  # Width lookup (has li $v0, 38)
    ("0x46c7F0", 0x46c7F0),  # Another lookup
]

REG = ["zero","at","v0","v1","a0","a1","a2","a3",
       "t0","t1","t2","t3","t4","t5","t6","t7",
       "s0","s1","s2","s3","s4","s5","s6","s7",
       "t8","t9","k0","k1","gp","sp","s8","ra"]

for name, target_va in functions_to_find:
    jal_val = 0x0C000000 | (target_va >> 2)
    jal_bytes = struct.pack("<I", jal_val)
    print(f"\n--- Callers of {name} (jal encoding {jal_val:#010x}) ---")
    pos = 0
    while True:
        pos = exe.find(jal_bytes, pos)
        if pos == -1:
            break
        va = fo2va(pos)
        # Show a few instructions around the call
        print(f"  File {pos:#08x} VA {va:#08x}: jal {name}")
        # Show 3 instructions before and 2 after
        for delta in range(-3, 3):
            off = pos + delta * 4
            if 0 <= off < len(exe) - 4:
                instr = struct.unpack_from("<I", exe, off)[0]
                # Quick decode
                op = (instr >> 26) & 0x3F
                marker = " <<<" if delta == 0 else ""
                if op == 9:
                    rs = (instr >> 21) & 0x1F
                    rt = (instr >> 16) & 0x1F
                    imm = instr & 0xFFFF
                    imm_s = imm - 0x10000 if imm & 0x8000 else imm
                    if rs == 0:
                        print(f"    [{delta:+d}] {fo2va(off):#08x}: li ${REG[rt]}, {imm_s}{marker}")
                    else:
                        print(f"    [{delta:+d}] {fo2va(off):#08x}: addiu ${REG[rt]}, ${REG[rs]}, {imm_s}{marker}")
                elif op == 3:
                    t = ((instr & 0x03FFFFFF) << 2) | (fo2va(off) & 0xF0000000)
                    print(f"    [{delta:+d}] {fo2va(off):#08x}: jal {t:#08x}{marker}")
                else:
                    print(f"    [{delta:+d}] {fo2va(off):#08x}: {instr:#010x}{marker}")
        print()
        pos += 4

print("\nDone.")
