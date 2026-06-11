"""
Different approach: The function 0x3A2D10 returns texture coordinates.
If it returns 0 for glyph IDs 38 and 45, the renderer might skip them.

But 0x3A2D10 reads from memory ($a0+8+offset). So the data is in a resource,
not hardcoded in the EXE.

The REAL skip must be in the code that iterates over the keyboard grid and
issues draw calls. Let me search for the draw/render function by looking
at what happens AFTER the glyph setup, specifically the code that reads
the halfword table and decides whether to draw.

Let me focus on functions that:
1. Take a cell/glyph index
2. Load the halfword from the mapping table
3. Conditionally skip based on the loaded value
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

# ================================================================
# The unrolled setup writes glyphs 38 and 45 at $s4+80 and $s4+94
# The halfword values are texture coordinates from 0x3A2D10
# If these are 0, the renderer might skip drawing.
#
# But the function checks: if $a0 == 0, return 0. Otherwise read data.
# $a0 is the base pointer (resource data), not the glyph ID.
# So if the resource data is loaded, it should be non-zero.
#
# Let me look at the RENDERING code more broadly.
# The caller at VA 0x499398 calls 0x46c580 and then checks if result is zero.
# Let me disassemble that caller.
# ================================================================

print("=" * 90)
print("CALLER AT VA 0x499380 AREA (calls 0x46c580 then checks result)")
print("=" * 90)

START = va2fo(0x499300)
END = va2fo(0x499500)
for off in range(START, END, 4):
    va = fo2va(off)
    instr = struct.unpack_from("<I", exe, off)[0]
    text = disasm(instr, va)
    print(f"  {va:#08x}: {text}")

# ================================================================
# Now let me look at the caller at 0x48B578 (calls 0x46c590)
# and 0x48B798 (calls 0x46c5D0)
# These might be the actual keyboard rendering code
# ================================================================
print()
print("=" * 90)
print("CALLER AT VA 0x48B500 AREA (keyboard rendering?)")
print("=" * 90)

START = va2fo(0x48B500)
END = va2fo(0x48BA00)
for off in range(START, END, 4):
    va = fo2va(off)
    instr = struct.unpack_from("<I", exe, off)[0]
    text = disasm(instr, va)
    print(f"  {va:#08x}: {text}")

# ================================================================
# Let me also check: does the keyboard use a DIFFERENT mechanism?
# The Japanese keyboard might use kana which are indexed differently.
# With our English R1188, cells map to ASCII. Positions 38=F and 45=M
# in the ENGLISH layout. But the JAPANESE keyboard had different chars.
#
# Wait - the user says "nuclear swap test proved it's GLYPH-ID-SPECIFIC".
# So swapping glyph data for cell 38 with another cell still results in
# cell 38 being blank. This means the skip is based on CELL INDEX,
# not on the actual glyph content.
#
# So I should look for hardcoded comparisons against 38 and 45 in the
# cell rendering path. But we already found those only in the width
# lookup tables (which return pixel width values 38 and 45, not
# compare cell IDs against them).
#
# Wait - let me reconsider. What if the rendering code calls the
# width function, gets 0 for certain cells, and skips drawing?
# The jump table at 0x46c7F0 returns 0 for cases 3 and 10-20.
# What if case 3 corresponds to cells 38 and 45?
# ================================================================

# The jump table at 0x46c610 converts a category index (0-20) to
# a glyph offset. Let me compute which cells fall in each category.
print()
print("=" * 90)
print("CATEGORY TO GLYPH MAPPING (from offset lookup at 0x46c610)")
print("=" * 90)

# Category 0 returns v0 unchanged (0 offset)
# Category 1 returns v0 + 159
# etc.
# The input v0 comes from 0x46c580 which returns a base pointer.
# The categories represent keyboard "rows" or "sections".
# The width function at 0x46c710 returns pixel widths per category.
# The enable function at 0x46c7F0 returns 0/1/2 per category.
#
# Category 3 returns 0 from 0x46c7F0, meaning "disabled/hidden"
# Category 3's width (from 0x46c710) is 38.
# Categories 10-20 also return 0 from 0x46c7F0.
# Category 10's width is 45.
#
# So the VALUES 38 and 45 are widths of CATEGORIES that happen to be
# disabled. The rendering code checks if the category's enable value
# is 0 and skips drawing if so.
#
# But wait - this is about categories/rows, not individual cells.
# If category 3 (width 38px) is disabled, ALL cells in that row
# would be missing, not just F and M.
#
# Unless... the keyboard layout maps cell positions to glyph IDs
# through the category system, and cells for F and M happen to be
# in disabled categories?
#
# That doesn't match - the user says ONLY cells 38 and 45 are
# missing, not entire rows.

# Let me try another approach: search for the value 892 (0x037C)
# which is the base+892 offset used in the bitmap table functions
# at VA 0x46DE60-0x46E0C8. This table seems to control which cells
# are active.
print()
print("=" * 90)
print("SEARCH: Who writes to the base+892 bitmap table?")
print("=" * 90)

# The functions at 0x46DEF0 etc write to base+892 table
# with ori 0x01 or ori 0x10 operations.
# But who initializes this table? If it starts as zero,
# and cells 38/45 never get their bit set, they'd be skipped.

# Search for stores at offset 892 (0x037C)
for off in range(0x350000, min(0x3A0000, len(exe)-3), 4):
    instr = struct.unpack_from("<I", exe, off)[0]
    op = (instr >> 26) & 0x3F
    imm = instr & 0xFFFF
    imm_s = imm - 0x10000 if imm & 0x8000 else imm

    if op in (40, 41, 43) and imm_s == 892:  # sb/sh/sw at offset 892
        rs = (instr >> 21) & 0x1F
        rt = (instr >> 16) & 0x1F
        va = fo2va(off)
        stname = {40:"sb", 41:"sh", 43:"sw"}[op]
        print(f"  {va:#08x}: {stname} ${REG[rt]}, 892(${REG[rs]})")

# Also look at the function 0x46ca80 and 0x46cee0 which are called
# from the rendering code right before the bitmap write
print()
print("=" * 90)
print("FUNCTION at VA 0x46CA80 (called from keyboard render)")
print("=" * 90)

START = va2fo(0x46CA80)
END = va2fo(0x46CC00)
for off in range(START, END, 4):
    va = fo2va(off)
    instr = struct.unpack_from("<I", exe, off)[0]
    text = disasm(instr, va)
    marker = ""
    if "jr $ra" in text: marker = " --- RET ---"
    elif text.startswith("jal"): marker = " --- CALL ---"
    print(f"  {va:#08x}: {text}{marker}")
