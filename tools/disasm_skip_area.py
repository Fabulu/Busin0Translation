"""
Detailed disassembly around the skip mechanism for glyph IDs 38 and 45.
Focus on file offsets 0x36c7a0-0x36c880 (around the li $v0, 38 / li $v0, 45).
"""
import struct

EXE_PATH = r"C:\Programmieren\wizardrytranslation\extracted\SLPM_653.78"
VA_BASE = 0x0FFF80

def fo2va(fo):
    return fo + VA_BASE

with open(EXE_PATH, "rb") as f:
    exe = f.read()

REG = [
    "zero","at","v0","v1","a0","a1","a2","a3",
    "t0","t1","t2","t3","t4","t5","t6","t7",
    "s0","s1","s2","s3","s4","s5","s6","s7",
    "t8","t9","k0","k1","gp","sp","s8","ra"
]

def disasm(instr, pc_va):
    op = (instr >> 26) & 0x3F
    rs = (instr >> 21) & 0x1F
    rt = (instr >> 16) & 0x1F
    rd = (instr >> 11) & 0x1F
    sa = (instr >> 6) & 0x1F
    funct = instr & 0x3F
    imm = instr & 0xFFFF
    imm_s = imm - 0x10000 if imm & 0x8000 else imm
    target = (instr & 0x03FFFFFF) << 2 | (pc_va & 0xF0000000)

    if instr == 0:
        return "nop"

    if op == 0:  # R-type
        r_ops = {
            0x20: "add", 0x21: "addu", 0x22: "sub", 0x23: "subu",
            0x24: "and", 0x25: "or", 0x26: "xor", 0x27: "nor",
            0x2A: "slt", 0x2B: "sltu",
            0x00: "sll", 0x02: "srl", 0x03: "sra",
            0x04: "sllv", 0x06: "srlv", 0x07: "srav",
            0x08: "jr", 0x09: "jalr",
            0x10: "mfhi", 0x12: "mflo",
            0x18: "mult", 0x19: "multu", 0x1A: "div", 0x1B: "divu",
            0x0C: "syscall", 0x0D: "break",
        }
        if funct == 0x08:
            return f"jr ${REG[rs]}"
        elif funct == 0x09:
            return f"jalr ${REG[rd]}, ${REG[rs]}"
        elif funct in (0x00, 0x02, 0x03):
            name = r_ops[funct]
            if funct == 0 and rd == 0 and rt == 0 and sa == 0:
                return "nop"
            return f"{name} ${REG[rd]}, ${REG[rt]}, {sa}"
        elif funct in (0x04, 0x06, 0x07):
            name = r_ops[funct]
            return f"{name} ${REG[rd]}, ${REG[rt]}, ${REG[rs]}"
        elif funct in (0x10, 0x12):
            name = r_ops[funct]
            return f"{name} ${REG[rd]}"
        elif funct in (0x18, 0x19, 0x1A, 0x1B):
            name = r_ops[funct]
            return f"{name} ${REG[rs]}, ${REG[rt]}"
        elif funct in r_ops:
            name = r_ops[funct]
            return f"{name} ${REG[rd]}, ${REG[rs]}, ${REG[rt]}"
        else:
            return f"R-type funct={funct:#04x} rs={REG[rs]} rt={REG[rt]} rd={REG[rd]}"

    elif op == 1:  # REGIMM
        if rt == 0:
            bt = pc_va + 4 + imm_s * 4
            return f"bltz ${REG[rs]}, {bt:#08x}"
        elif rt == 1:
            bt = pc_va + 4 + imm_s * 4
            return f"bgez ${REG[rs]}, {bt:#08x}"
        else:
            return f"REGIMM sub={rt} rs={REG[rs]} imm={imm:#06x}"

    elif op == 2:
        return f"j {target:#08x}"
    elif op == 3:
        return f"jal {target:#08x}"
    elif op == 4:
        bt = pc_va + 4 + imm_s * 4
        return f"beq ${REG[rs]}, ${REG[rt]}, {bt:#08x}"
    elif op == 5:
        bt = pc_va + 4 + imm_s * 4
        return f"bne ${REG[rs]}, ${REG[rt]}, {bt:#08x}"
    elif op == 6:
        bt = pc_va + 4 + imm_s * 4
        return f"blez ${REG[rs]}, {bt:#08x}"
    elif op == 7:
        bt = pc_va + 4 + imm_s * 4
        return f"bgtz ${REG[rs]}, {bt:#08x}"
    elif op == 8:
        return f"addi ${REG[rt]}, ${REG[rs]}, {imm_s}"
    elif op == 9:
        if rs == 0:
            return f"li ${REG[rt]}, {imm_s}  (addiu)"
        return f"addiu ${REG[rt]}, ${REG[rs]}, {imm_s}"
    elif op == 10:
        return f"slti ${REG[rt]}, ${REG[rs]}, {imm_s}"
    elif op == 11:
        return f"sltiu ${REG[rt]}, ${REG[rs]}, {imm_s}"
    elif op == 12:
        return f"andi ${REG[rt]}, ${REG[rs]}, {imm:#06x}"
    elif op == 13:
        return f"ori ${REG[rt]}, ${REG[rs]}, {imm:#06x}"
    elif op == 14:
        return f"xori ${REG[rt]}, ${REG[rs]}, {imm:#06x}"
    elif op == 15:
        return f"lui ${REG[rt]}, {imm:#06x}"
    elif op == 32:
        return f"lb ${REG[rt]}, {imm_s}(${REG[rs]})"
    elif op == 33:
        return f"lh ${REG[rt]}, {imm_s}(${REG[rs]})"
    elif op == 35:
        return f"lw ${REG[rt]}, {imm_s}(${REG[rs]})"
    elif op == 36:
        return f"lbu ${REG[rt]}, {imm_s}(${REG[rs]})"
    elif op == 37:
        return f"lhu ${REG[rt]}, {imm_s}(${REG[rs]})"
    elif op == 40:
        return f"sb ${REG[rt]}, {imm_s}(${REG[rs]})"
    elif op == 41:
        return f"sh ${REG[rt]}, {imm_s}(${REG[rs]})"
    elif op == 43:
        return f"sw ${REG[rt]}, {imm_s}(${REG[rs]})"
    else:
        return f"op={op} rs={REG[rs]} rt={REG[rt]} imm={imm:#06x}  raw={instr:#010x}"

# ============================================================
# Disassemble around the two key instructions
# li $v0, 38 at file 0x36c7d4
# li $v0, 45 at file 0x36c80c
# ============================================================
print("=" * 80)
print("DISASSEMBLY: Around li $v0, 38 (file 0x36c7d4) and li $v0, 45 (file 0x36c80c)")
print("=" * 80)

# Go back a bit and forward a bit
START = 0x36c780
END = 0x36c8a0

for off in range(START, END, 4):
    va = fo2va(off)
    instr = struct.unpack_from("<I", exe, off)[0]
    text = disasm(instr, va)
    marker = ""
    if off == 0x36c7d4:
        marker = "  <--- li $v0, 38 (F)"
    elif off == 0x36c80c:
        marker = "  <--- li $v0, 45 (M)"
    print(f"  {off:#08x} [{va:#08x}]: {instr:#010x}  {text}{marker}")

# ============================================================
# Now disassemble a wider area to understand the full function
# ============================================================
print()
print("=" * 80)
print("DISASSEMBLY: Full keyboard rendering function area (0x36c600-0x36c900)")
print("=" * 80)

START2 = 0x36c600
END2 = 0x36c900

for off in range(START2, END2, 4):
    va = fo2va(off)
    instr = struct.unpack_from("<I", exe, off)[0]
    text = disasm(instr, va)
    marker = ""
    if off == 0x36c7d4:
        marker = "  <<<< li $v0, 38 (F)"
    elif off == 0x36c80c:
        marker = "  <<<< li $v0, 45 (M)"
    # Mark branches/jumps
    print(f"  {off:#08x} [{va:#08x}]: {instr:#010x}  {text}{marker}")

# ============================================================
# Also look at the other pair: li $a3, 38 and li $a3, 45 at 0x363b74/0x363c38
# ============================================================
print()
print("=" * 80)
print("DISASSEMBLY: Around li $a3, 38 (0x363b74) and li $a3, 45 (0x363c38)")
print("=" * 80)

START3 = 0x363b00
END3 = 0x363d00

for off in range(START3, END3, 4):
    va = fo2va(off)
    instr = struct.unpack_from("<I", exe, off)[0]
    text = disasm(instr, va)
    marker = ""
    if off == 0x363b74:
        marker = "  <<<< li $a3, 38 (F)"
    elif off == 0x363c38:
        marker = "  <<<< li $a3, 45 (M)"
    print(f"  {off:#08x} [{va:#08x}]: {instr:#010x}  {text}{marker}")
