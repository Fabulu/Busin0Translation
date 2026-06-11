"""
Search the Busin 0 EXE for the mechanism that skips glyph IDs 38 (F) and 45 (M)
in the name entry keyboard rendering loop.
"""
import struct
import sys

EXE_PATH = r"C:\Programmieren\wizardrytranslation\extracted\SLPM_653.78"
VA_BASE = 0x0FFF80  # file_offset = VA - VA_BASE

def fo2va(fo):
    return fo + VA_BASE

def va2fo(va):
    return va - VA_BASE

with open(EXE_PATH, "rb") as f:
    exe = f.read()

print(f"EXE size: {len(exe)} bytes ({len(exe):#x})")
print()

# MIPS register names
REG_NAMES = [
    "zero","at","v0","v1","a0","a1","a2","a3",
    "t0","t1","t2","t3","t4","t5","t6","t7",
    "s0","s1","s2","s3","s4","s5","s6","s7",
    "t8","t9","k0","k1","gp","sp","s8","ra"
]

def decode_i_type(instr):
    """Decode I-type MIPS instruction: op(6) rs(5) rt(5) imm(16)"""
    op = (instr >> 26) & 0x3F
    rs = (instr >> 21) & 0x1F
    rt = (instr >> 16) & 0x1F
    imm = instr & 0xFFFF
    # Sign extend
    if imm & 0x8000:
        imm_signed = imm - 0x10000
    else:
        imm_signed = imm
    return op, rs, rt, imm, imm_signed

# ============================================================
# 1. Search for MIPS instructions with immediates 38 or 45
# ============================================================
print("=" * 70)
print("1. MIPS INSTRUCTIONS WITH IMMEDIATE VALUES 38 (0x26) OR 45 (0x2D)")
print("=" * 70)

TARGETS = {38: "F (glyph 38)", 45: "M (glyph 45)"}

# Keyboard code region
KB_START = 0x36C600
KB_END = 0x36E1D0

# Also search broader regions
SEARCH_REGIONS = [
    ("Keyboard code", KB_START, KB_END),
    ("Extended keyboard area", 0x360000, 0x380000),
    ("Data section", 0x3C0000, 0x400000),
    ("Full EXE", 0, len(exe)),
]

for region_name, start, end in SEARCH_REGIONS:
    print(f"\n--- Region: {region_name} (file {start:#x}-{end:#x}, VA {fo2va(start):#x}-{fo2va(end):#x}) ---")
    found_count = 0

    for offset in range(start, min(end, len(exe) - 3), 4):
        instr = struct.unpack_from("<I", exe, offset)[0]
        op, rs, rt, imm, imm_signed = decode_i_type(instr)

        # Check for immediates 38 or 45 (unsigned) or -38/-45 (signed)
        for target_val, target_name in TARGETS.items():
            match = False
            match_desc = ""

            if imm == target_val:
                # ADDIU: op=9, ORI: op=13, ANDI: op=12, SLTI: op=10, SLTIU: op=11
                # BEQ: op=4, BNE: op=5 (but imm is branch offset, not value)
                # LI pseudo = ADDIU rt, zero, imm  or  ORI rt, zero, imm
                if op == 9:  # ADDIU
                    match = True
                    match_desc = f"addiu ${REG_NAMES[rt]}, ${REG_NAMES[rs]}, {target_val}"
                elif op == 13:  # ORI
                    match = True
                    match_desc = f"ori ${REG_NAMES[rt]}, ${REG_NAMES[rs]}, {target_val}"
                elif op == 12:  # ANDI
                    match = True
                    match_desc = f"andi ${REG_NAMES[rt]}, ${REG_NAMES[rs]}, {target_val}"
                elif op == 10:  # SLTI
                    match = True
                    match_desc = f"slti ${REG_NAMES[rt]}, ${REG_NAMES[rs]}, {target_val}"
                elif op == 11:  # SLTIU
                    match = True
                    match_desc = f"sltiu ${REG_NAMES[rt]}, ${REG_NAMES[rs]}, {target_val}"
                elif op == 0x0F:  # LUI
                    pass  # upper immediate, not relevant for small values
                elif op == 0x23 or op == 0x21 or op == 0x20:  # LW, LH, LB
                    # offset=38 or 45 in a load - could be table access
                    match = True
                    ldnames = {0x23: "lw", 0x21: "lh", 0x20: "lb"}
                    match_desc = f"{ldnames[op]} ${REG_NAMES[rt]}, {target_val}(${REG_NAMES[rs]})"
                elif op == 0x2B or op == 0x29 or op == 0x28:  # SW, SH, SB
                    match = True
                    stnames = {0x2B: "sw", 0x29: "sh", 0x28: "sb"}
                    match_desc = f"{stnames[op]} ${REG_NAMES[rt]}, {target_val}(${REG_NAMES[rs]})"

            if match:
                va = fo2va(offset)
                # Only print non-load/store in full EXE scan to reduce noise
                if region_name == "Full EXE" and op in (0x23, 0x21, 0x20, 0x2B, 0x29, 0x28):
                    continue
                if region_name == "Full EXE" and found_count > 100:
                    continue
                print(f"  File {offset:#08x} VA {va:#08x}: {match_desc}  [{target_name}]  raw={instr:#010x}")
                found_count += 1

    if found_count == 0:
        print("  (none found)")

# ============================================================
# 2. Search for BEQ/BNE comparing a register loaded with 38 or 45
# ============================================================
print()
print("=" * 70)
print("2. LOAD-THEN-BRANCH PATTERNS (li reg, 38/45 followed by beq/bne)")
print("=" * 70)

for region_name, start, end in [("Keyboard code", KB_START, KB_END), ("Extended", 0x360000, 0x380000)]:
    print(f"\n--- Region: {region_name} ---")
    found = False

    for offset in range(start, min(end, len(exe) - 3), 4):
        instr = struct.unpack_from("<I", exe, offset)[0]
        op, rs, rt, imm, imm_signed = decode_i_type(instr)

        # Look for addiu/ori with 38 or 45
        if (op == 9 or op == 13) and imm in (38, 45):
            loaded_reg = rt
            target_val = imm
            # Check next 4 instructions for BEQ/BNE using this register
            for delta in range(1, 5):
                next_off = offset + delta * 4
                if next_off + 4 > len(exe):
                    break
                next_instr = struct.unpack_from("<I", exe, next_off)[0]
                next_op = (next_instr >> 26) & 0x3F
                next_rs = (next_instr >> 21) & 0x1F
                next_rt = (next_instr >> 16) & 0x1F
                next_imm = next_instr & 0xFFFF
                if next_imm & 0x8000:
                    next_imm_s = next_imm - 0x10000
                else:
                    next_imm_s = next_imm

                if next_op in (4, 5):  # BEQ, BNE
                    if next_rs == loaded_reg or next_rt == loaded_reg:
                        branch_target = fo2va(next_off + 4) + next_imm_s * 4
                        bname = "beq" if next_op == 4 else "bne"
                        print(f"  Load: File {offset:#08x} VA {fo2va(offset):#08x}: li ${REG_NAMES[loaded_reg]}, {target_val}")
                        print(f"  Branch: File {next_off:#08x} VA {fo2va(next_off):#08x}: {bname} ${REG_NAMES[next_rs]}, ${REG_NAMES[next_rt]} -> VA {branch_target:#08x}")
                        found = True

    if not found:
        print("  (none found)")

# ============================================================
# 3. Search for data tables containing/excluding 38 and 45
# ============================================================
print()
print("=" * 70)
print("3. DATA TABLES - BYTE SEQUENCES WITH KEYBOARD CELL INDICES")
print("=" * 70)

# Look for sequences of bytes that look like cell index lists (consecutive or near-consecutive values 0-94)
# An inclusion list would have most of 0-94 but skip 38 and 45
# An exclusion list might just list 38 and 45

# 3a. Search for byte pair [38, 45] or [45, 38] anywhere
print("\n--- 3a. Byte pair 38,45 or 45,38 ---")
for i in range(len(exe) - 1):
    if (exe[i] == 38 and exe[i+1] == 45) or (exe[i] == 45 and exe[i+1] == 38):
        context = exe[max(0,i-8):i+10]
        print(f"  File {i:#08x} VA {fo2va(i):#08x}: {context.hex(' ')}")

# 3b. Search for short exclusion lists: look for [38] or [45] as halfwords in exclusion contexts
print("\n--- 3b. Halfword pairs (0x0026, 0x002D) nearby ---")
for i in range(len(exe) - 3):
    hw1 = struct.unpack_from("<H", exe, i)[0]
    hw2 = struct.unpack_from("<H", exe, i+2)[0]
    if (hw1 == 38 and hw2 == 45) or (hw1 == 45 and hw2 == 38):
        context = exe[max(0,i-8):i+12]
        print(f"  File {i:#08x} VA {fo2va(i):#08x}: {context.hex(' ')}")

# 3c. Word pairs
print("\n--- 3c. Word pairs (0x00000026, 0x0000002D) nearby ---")
for i in range(0, len(exe) - 7, 4):
    w1 = struct.unpack_from("<I", exe, i)[0]
    w2 = struct.unpack_from("<I", exe, i+4)[0]
    if (w1 == 38 and w2 == 45) or (w1 == 45 and w2 == 38):
        context = exe[max(0,i-8):i+16]
        print(f"  File {i:#08x} VA {fo2va(i):#08x}: {context.hex(' ')}")

# 3d. Look for a bitmap/bitfield where bits 38 and 45 are special
# 95 glyphs = 12 bytes for a bitmap. Bit 38 = byte 4 bit 6, Bit 45 = byte 5 bit 5
print("\n--- 3d. Searching for potential bitmaps (12 bytes covering 95 bits) ---")
# Look for 12-byte sequences where most bits are 1 but bits 38 and 45 are 0
for i in range(len(exe) - 12):
    bitmap = exe[i:i+12]
    # Check bit 38 (byte 4, bit 6) and bit 45 (byte 5, bit 5)
    bit38 = (bitmap[4] >> 6) & 1
    bit45 = (bitmap[5] >> 5) & 1
    if bit38 == 0 and bit45 == 0:
        # Count how many of the first 95 bits are set
        set_bits = 0
        for byte_idx in range(12):
            for bit_idx in range(8):
                bit_num = byte_idx * 8 + bit_idx
                if bit_num >= 95:
                    break
                if (bitmap[byte_idx] >> bit_idx) & 1:
                    set_bits += 1
        # If most bits are set (say 85+), this could be our bitmap
        if set_bits >= 85:
            print(f"  File {i:#08x} VA {fo2va(i):#08x}: {bitmap.hex(' ')} (set_bits={set_bits}/93)")

# ============================================================
# 4. Look for sequences in data section that list cell indices
# ============================================================
print()
print("=" * 70)
print("4. SEQUENTIAL BYTE PATTERNS IN DATA SECTION (cell index tables)")
print("=" * 70)

# Look for runs of increasing bytes that look like cell index lists
DATA_START = 0x3C0000
DATA_END = min(0x400000, len(exe))

for start in range(DATA_START, DATA_END - 10):
    # Check if this looks like a sequence of cell indices (increasing, within 0-94)
    if exe[start] > 94:
        continue
    seq = [exe[start]]
    for j in range(1, 100):
        if start + j >= DATA_END:
            break
        val = exe[start + j]
        if val > 94 or val < seq[-1]:
            break
        seq.append(val)

    if len(seq) >= 20:  # At least 20 sequential-ish values
        # Check if 38 or 45 are missing
        seq_set = set(seq)
        missing_38 = 38 not in seq_set
        missing_45 = 45 not in seq_set
        if missing_38 or missing_45:
            missing = []
            if missing_38: missing.append("38(F)")
            if missing_45: missing.append("45(M)")
            print(f"  File {start:#08x} VA {fo2va(start):#08x}: {len(seq)} indices, MISSING: {', '.join(missing)}")
            print(f"    Values: {seq[:30]}{'...' if len(seq) > 30 else ''}")

# ============================================================
# 5. Detailed disassembly of keyboard rendering area
# ============================================================
print()
print("=" * 70)
print("5. FULL DISASSEMBLY OF KEYBOARD CODE AREA (looking for skip logic)")
print("=" * 70)

# Focus on the core keyboard rendering loop
# Look for any conditional that could skip specific iterations
DISASM_START = KB_START
DISASM_END = KB_END

I_TYPE_OPS = {
    4: "beq", 5: "bne", 6: "blez", 7: "bgtz",
    8: "addi", 9: "addiu", 10: "slti", 11: "sltiu",
    12: "andi", 13: "ori", 14: "xori", 15: "lui",
    32: "lb", 33: "lh", 35: "lw", 36: "lbu", 37: "lhu",
    40: "sb", 41: "sh", 43: "sw",
}

# Instead of full disasm, look for conditional branches that could be skip logic
# Specifically: comparisons against small values followed by branches
print("\n--- Conditional branches near small-value comparisons ---")

for offset in range(DISASM_START, DISASM_END - 3, 4):
    instr = struct.unpack_from("<I", exe, offset)[0]
    op, rs, rt, imm, imm_signed = decode_i_type(instr)

    # SLTI/SLTIU with small immediates (potential loop bounds or range checks)
    if op in (10, 11) and 0 < imm < 100:
        opname = "slti" if op == 10 else "sltiu"
        print(f"  File {offset:#08x} VA {fo2va(offset):#08x}: {opname} ${REG_NAMES[rt]}, ${REG_NAMES[rs]}, {imm}")

    # ADDIU with zero source and small immediate (loading a constant)
    if op == 9 and rs == 0 and 0 < imm < 100:
        print(f"  File {offset:#08x} VA {fo2va(offset):#08x}: li ${REG_NAMES[rt]}, {imm}")

    # ORI with zero source and small immediate
    if op == 13 and rs == 0 and 0 < imm < 100:
        print(f"  File {offset:#08x} VA {fo2va(offset):#08x}: li ${REG_NAMES[rt]}, {imm}  (ori)")

# ============================================================
# 6. Look for the values 38 and 45 as halfwords in keyboard area
# ============================================================
print()
print("=" * 70)
print("6. RAW SEARCH FOR 0x26 (38) AND 0x2D (45) BYTES IN KEYBOARD AREA")
print("=" * 70)

# In the keyboard code area, find all occurrences of bytes 0x26 and 0x2D
# and show context
for target, name in [(0x26, "38/F"), (0x2D, "45/M")]:
    print(f"\n--- Byte 0x{target:02X} ({name}) in keyboard area ---")
    count = 0
    for i in range(KB_START, KB_END):
        if exe[i] == target:
            # Show as part of a 4-byte aligned instruction
            aligned = i & ~3
            instr = struct.unpack_from("<I", exe, aligned)[0]
            byte_pos = i - aligned
            context = exe[max(0,aligned-4):aligned+8]
            print(f"  Byte at file {i:#08x} (in instr at {aligned:#08x} VA {fo2va(aligned):#08x}): "
                  f"instr={instr:#010x} byte_pos={byte_pos} context={context.hex(' ')}")
            count += 1
    print(f"  Total: {count} occurrences")

# ============================================================
# 7. Specifically look for REGIMM (op=1) instructions: BLTZ, BGEZ
# ============================================================
print()
print("=" * 70)
print("7. ALL BRANCH INSTRUCTIONS IN KEYBOARD AREA")
print("=" * 70)

for offset in range(KB_START, KB_END - 3, 4):
    instr = struct.unpack_from("<I", exe, offset)[0]
    op = (instr >> 26) & 0x3F
    rs = (instr >> 21) & 0x1F
    rt = (instr >> 16) & 0x1F
    imm = instr & 0xFFFF
    if imm & 0x8000:
        imm_s = imm - 0x10000
    else:
        imm_s = imm

    branch_target = fo2va(offset + 4) + imm_s * 4

    if op == 4:
        print(f"  File {offset:#08x} VA {fo2va(offset):#08x}: beq ${REG_NAMES[rs]}, ${REG_NAMES[rt]}, {branch_target:#08x}")
    elif op == 5:
        print(f"  File {offset:#08x} VA {fo2va(offset):#08x}: bne ${REG_NAMES[rs]}, ${REG_NAMES[rt]}, {branch_target:#08x}")
    elif op == 6:
        print(f"  File {offset:#08x} VA {fo2va(offset):#08x}: blez ${REG_NAMES[rs]}, {branch_target:#08x}")
    elif op == 7:
        print(f"  File {offset:#08x} VA {fo2va(offset):#08x}: bgtz ${REG_NAMES[rs]}, {branch_target:#08x}")
    elif op == 1:
        sub = rt
        if sub == 0:
            print(f"  File {offset:#08x} VA {fo2va(offset):#08x}: bltz ${REG_NAMES[rs]}, {branch_target:#08x}")
        elif sub == 1:
            print(f"  File {offset:#08x} VA {fo2va(offset):#08x}: bgez ${REG_NAMES[rs]}, {branch_target:#08x}")

print()
print("=" * 70)
print("8. SEARCH FOR JAL (function calls) IN KEYBOARD AREA")
print("=" * 70)

for offset in range(KB_START, KB_END - 3, 4):
    instr = struct.unpack_from("<I", exe, offset)[0]
    op = (instr >> 26) & 0x3F
    if op == 3:  # JAL
        target_addr = (instr & 0x03FFFFFF) << 2
        # Add upper bits from PC (assuming kernel segment)
        target_addr |= (fo2va(offset) & 0xF0000000)
        print(f"  File {offset:#08x} VA {fo2va(offset):#08x}: jal {target_addr:#08x}")

print("\nDone.")
