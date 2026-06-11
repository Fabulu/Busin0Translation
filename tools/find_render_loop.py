"""
The slti 45 checks are bounds checks for a category count, not glyph skip checks.
The base+892 table is a bitmap for cell state. These helper functions manage cell state
for a grid that is at most 45 columns x 9 rows.

The skip of glyph IDs 38 (F) and 45 (M) must happen in the RENDERING code that
decides which glyph texture to draw for each cell position.

Key insight: The unrolled loop at VA 0x463AF4 calls jal 0x3a2d10 with glyph IDs
0-94 sequentially and stores halfword results in a struct. This builds a glyph-to-texture
mapping table. If 38 and 45 are skipped there, they'd map to wrong textures.

But wait - they ARE included in that unrolled loop (glyph 38 at VA 0x463AF4, glyph 45
at VA 0x463BB8). So the mapping is built for all glyphs.

The skip must happen in the code that uses this mapping table to draw.

Let me search for what calls the function containing the unrolled glyph setup loop,
and also look at function 0x3A2D10 to understand what it returns.
"""
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
    if op == 15: return f"lui ${REG[rt]}, {imm:#06x}"
    load_ops = {32:"lb",33:"lh",35:"lw",36:"lbu",37:"lhu"}
    if op in load_ops: return f"{load_ops[op]} ${REG[rt]}, {imm_s}(${REG[rs]})"
    store_ops = {40:"sb",41:"sh",43:"sw"}
    if op in store_ops: return f"{store_ops[op]} ${REG[rt]}, {imm_s}(${REG[rs]})"
    if op == 55: return f"ld ${REG[rt]}, {imm_s}(${REG[rs]})"
    if op == 63: return f"sd ${REG[rt]}, {imm_s}(${REG[rs]})"
    if op == 31: return f"sq ${REG[rt]}, {imm_s}(${REG[rs]})"
    if op == 30: return f"lq ${REG[rt]}, {imm_s}(${REG[rs]})"
    return f"op={op:#04x} raw={instr:#010x}"

# =================================================================
# Disassemble the function 0x3A2D10 (called with each glyph ID)
# =================================================================
print("=" * 90)
print("FUNCTION at VA 0x3A2D10 (glyph ID -> texture coordinate mapper)")
print("=" * 90)

START = va2fo(0x3A2D10)
# Disassemble until we hit jr $ra
for off in range(START, START + 0x200, 4):
    va = fo2va(off)
    instr = struct.unpack_from("<I", exe, off)[0]
    text = disasm(instr, va)
    print(f"  {va:#08x}: {text}")
    if "jr $ra" in text:
        # Print delay slot too
        off2 = off + 4
        instr2 = struct.unpack_from("<I", exe, off2)[0]
        text2 = disasm(instr2, fo2va(off2))
        print(f"  {fo2va(off2):#08x}: {text2}")
        break

# =================================================================
# Let me find the ACTUAL render loop more broadly.
# Search the wider code area (0x350000-0x3A0000) for loops that:
# 1. Load halfwords (lhu/lh) from the glyph mapping table
# 2. Have a loop counter compared against 95 or similar
# =================================================================
print()
print("=" * 90)
print("Search for loop bounds in extended keyboard area (comparisons against 93-96)")
print("=" * 90)

for target_imm in [93, 94, 95, 96]:
    for off in range(0x350000, min(0x3A0000, len(exe)-3), 4):
        instr = struct.unpack_from("<I", exe, off)[0]
        op = (instr >> 26) & 0x3F
        imm = instr & 0xFFFF
        if imm == target_imm and op in (10, 11):  # slti, sltiu
            rs = (instr >> 21) & 0x1F
            rt = (instr >> 16) & 0x1F
            va = fo2va(off)
            opname = "slti" if op == 10 else "sltiu"
            print(f"  {va:#08x} (file {off:#08x}): {opname} ${REG[rt]}, ${REG[rs]}, {target_imm}")

# =================================================================
# The unrolled glyph setup loop is in a function around VA 0x463800.
# Let's find where that function starts and understand its full structure.
# The function processes glyphs 0 through 94.
# Find the function prologue before the first glyph setup (glyph 0 at ~VA 0x463898)
# =================================================================
print()
print("=" * 90)
print("FUNCTION containing unrolled glyph setup (around VA 0x463800)")
print("=" * 90)

# Search backward from the first glyph call for function prologue
START = va2fo(0x463700)
END = va2fo(0x4638B0)

for off in range(START, END, 4):
    va = fo2va(off)
    instr = struct.unpack_from("<I", exe, off)[0]
    text = disasm(instr, va)
    print(f"  {va:#08x}: {text}")

# =================================================================
# Now look for the KEY function: the one that reads from the
# halfword table built by the unrolled loop and draws glyphs
# The table is stored at $s4 + offset (halfwords starting at offset 0x26)
# Values go from sh $v0, 0x26($s4) through sh $v0, 0xE4($s4)
# That's offsets 0x26 to 0xE4 = 38 to 228 = 96 halfwords (glyph 0-95)
# =================================================================
print()
print("=" * 90)
print("SEARCHING for code that reads halfwords from offset 0x26-0xE4 of a struct")
print("(this is where the glyph mapping table is consumed)")
print("=" * 90)

# Look for lh/lhu with offsets in the range 0x26-0xE4
# Specifically the first entry (offset 0x26 = glyph 0) and entries for glyph 38 (offset 0x26+38*2=0x72)
# and glyph 45 (offset 0x26+45*2=0x82)

# Actually, let me check: glyph IDs go 0,1,2,...94
# Offsets in struct: 0x26 + glyph_id * 2
# glyph 38: 0x26 + 76 = 0x72
# glyph 45: 0x26 + 90 = 0x82

# But the rendering might access them through a loop with a base pointer offset
# Let me instead look for the function that actually does the GS/GIF drawing
# by searching for callers of the unrolled setup function

# Find what calls the unrolled setup function
# The function starts around VA 0x4637F0 or so
# Actually let me find the jal to 0x3a2d10 - where does the parent function start?

# The unrolled loop starts with moves to set up args for jal 0x3a2d10
# These are inside a larger function. Let me trace the start.
# From the disasm of 0x463800 area, look for addiu $sp, $sp, -xxx

# Actually, let me check who calls the function that CONTAINS the unrolled loop
# First, find where that function starts by scanning backward from VA 0x463898

for off in range(va2fo(0x463800), va2fo(0x463700), -4):
    va = fo2va(off)
    instr = struct.unpack_from("<I", exe, off)[0]
    text = disasm(instr, va)
    if "addiu $sp, $sp, -" in text:
        print(f"  Function prologue at {va:#08x}: {text}")
        # Find who calls this
        func_va = va
        jal_val = 0x0C000000 | (func_va >> 2)
        jal_bytes = struct.pack("<I", jal_val)
        pos = 0
        while True:
            pos = exe.find(jal_bytes, pos)
            if pos == -1: break
            print(f"    Called from file {pos:#08x} VA {fo2va(pos):#08x}")
            pos += 4
        break
