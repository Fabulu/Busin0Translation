"""Disassemble the cell rendering function at VA 0x3A3260."""
import struct

EXE_PATH = r"C:\Programmieren\wizardrytranslation\extracted\SLPM_653.78"
VA_BASE = 0x0FFF80

def fo2va(fo): return fo + VA_BASE
def va2fo(va): return va - VA_BASE

with open(EXE_PATH, "rb") as f:
    exe = f.read()

REG = ["zero","at","v0","v1","a0","a1","a2","a3",
       "t0","t1","t2","t3","t4","t5","t6","t7",
       "s0","s1","s2","s3","s4","s5","s6","s7",
       "t8","t9","k0","k1","gp","sp","s8","ra"]

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
    if instr == 0: return "nop"
    if op == 0:
        if funct == 0x2d: return f"daddu ${REG[rd]}, ${REG[rs]}, ${REG[rt]}"
        if funct == 0x08: return f"jr ${REG[rs]}"
        if funct == 0x09: return f"jalr ${REG[rd]}, ${REG[rs]}"
        r_ops = {0x20:"add",0x21:"addu",0x22:"sub",0x23:"subu",0x24:"and",0x25:"or",0x26:"xor",0x2A:"slt",0x2B:"sltu",0x00:"sll",0x02:"srl",0x03:"sra",0x10:"mfhi",0x12:"mflo",0x18:"mult",0x19:"multu",0x1A:"div",0x1B:"divu",0x3C:"dsll32",0x3F:"dsra32"}
        if funct in (0x00,0x02,0x03,0x3C,0x3F): return f"{r_ops.get(funct,'?')} ${REG[rd]}, ${REG[rt]}, {sa}"
        if funct in (0x10,0x12): return f"{r_ops[funct]} ${REG[rd]}"
        if funct in (0x18,0x19,0x1A,0x1B): return f"{r_ops[funct]} ${REG[rs]}, ${REG[rt]}"
        if funct in r_ops: return f"{r_ops[funct]} ${REG[rd]}, ${REG[rs]}, ${REG[rt]}"
        return f"special funct={funct:#04x}"
    if op == 1:
        bt = pc_va + 4 + imm_s * 4
        return {0:"bltz",1:"bgez"}.get(rt,"regimm") + f" ${REG[rs]}, {bt:#08x}"
    if op == 2: return f"j {target:#08x}"
    if op == 3: return f"jal {target:#08x}"
    if op == 4:
        bt = pc_va + 4 + imm_s * 4
        if rs==0 and rt==0: return f"b {bt:#08x}"
        return f"beq ${REG[rs]}, ${REG[rt]}, {bt:#08x}"
    if op == 5: return f"bne ${REG[rs]}, ${REG[rt]}, {pc_va+4+imm_s*4:#08x}"
    if op == 6: return f"blez ${REG[rs]}, {pc_va+4+imm_s*4:#08x}"
    if op == 7: return f"bgtz ${REG[rs]}, {pc_va+4+imm_s*4:#08x}"
    if op == 9:
        if rs == 0: return f"li ${REG[rt]}, {imm_s}"
        return f"addiu ${REG[rt]}, ${REG[rs]}, {imm_s}"
    if op == 10: return f"slti ${REG[rt]}, ${REG[rs]}, {imm_s}"
    if op == 11: return f"sltiu ${REG[rt]}, ${REG[rs]}, {imm_s}"
    if op == 12: return f"andi ${REG[rt]}, ${REG[rs]}, {imm:#06x}"
    if op == 13: return f"ori ${REG[rt]}, ${REG[rs]}, {imm:#06x}"
    if op == 14: return f"xori ${REG[rt]}, ${REG[rs]}, {imm:#06x}"
    if op == 15: return f"lui ${REG[rt]}, {imm:#06x}"
    load_ops = {32:"lb",33:"lh",35:"lw",36:"lbu",37:"lhu"}
    if op in load_ops: return f"{load_ops[op]} ${REG[rt]}, {imm_s}(${REG[rs]})"
    store_ops = {40:"sb",41:"sh",43:"sw"}
    if op in store_ops: return f"{store_ops[op]} ${REG[rt]}, {imm_s}(${REG[rs]})"
    if op == 55: return f"ld ${REG[rt]}, {imm_s}(${REG[rs]})"
    if op == 63: return f"sd ${REG[rt]}, {imm_s}(${REG[rs]})"
    if op == 31: return f"sq ${REG[rt]}, {imm_s}(${REG[rs]})"
    if op == 30: return f"lq ${REG[rt]}, {imm_s}(${REG[rs]})"
    if op == 25: return f"daddiu ${REG[rt]}, ${REG[rs]}, {imm_s}"
    return f"op={op:#04x} raw={instr:#010x}"

print("=" * 90)
print("FUNCTION AT VA 0x3A3260 (main cell rendering loop)")
print("=" * 90)

START = va2fo(0x3A3260)
ret_count = 0
nop_streak = 0
for off in range(START, START + 0x1000, 4):
    va = fo2va(off)
    instr = struct.unpack_from("<I", exe, off)[0]
    text = disasm(instr, va)
    marker = ""
    if "jr $ra" in text: marker = " --- RET ---"
    elif text.startswith("jal"): marker = " --- CALL ---"
    elif "beq" in text and "$zero" in text: marker = " [branch]"
    elif "bne" in text: marker = " [branch]"

    print(f"  {va:#08x}: {text}{marker}")

    if instr == 0:
        nop_streak += 1
        if nop_streak >= 3:
            break
    else:
        nop_streak = 0

# Also look at function 0x3A49D0 - called to allocate/get render context
print()
print("=" * 90)
print("FUNCTION AT VA 0x3A49D0 (render context allocator)")
print("=" * 90)

START = va2fo(0x3A49D0)
for off in range(START, START + 0x200, 4):
    va = fo2va(off)
    instr = struct.unpack_from("<I", exe, off)[0]
    text = disasm(instr, va)
    marker = ""
    if "jr $ra" in text: marker = " --- RET ---"
    elif text.startswith("jal"): marker = " --- CALL ---"
    print(f"  {va:#08x}: {text}{marker}")
    if "jr $ra" in text:
        off2 = off + 4
        print(f"  {fo2va(off2):#08x}: {disasm(struct.unpack_from('<I', exe, off2)[0], fo2va(off2))}")
        break
