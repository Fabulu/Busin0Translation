"""
Check the drawing function table. Need to correctly compute the VA.
"""
import struct

EXE_PATH = r"C:\Programmieren\wizardrytranslation\extracted\SLPM_653.78"
VA_BASE = 0x0FFF80

def fo2va(fo): return fo + VA_BASE
def va2fo(va): return va - VA_BASE

with open(EXE_PATH, "rb") as f:
    exe = f.read()

print(f"EXE size: {len(exe)} bytes, max VA: {fo2va(len(exe)):#x}")

# Re-read the instruction at 0x3A2ED0
raw = struct.unpack_from("<I", exe, va2fo(0x3A2ED0))[0]
imm = raw & 0xFFFF
imm_s = imm - 0x10000 if imm & 0x8000 else imm
print(f"Instruction at 0x3A2ED0: raw={raw:#010x}, imm_s={imm_s}")

# lui v0, 0x0057 -> 0x00570000
# addiu v0, v0, imm_s -> table_va
table_va = 0x570000 + imm_s
table_fo = table_va - VA_BASE
print(f"Table VA: {table_va:#x}, file offset: {table_fo:#x}")

if table_fo + 128 > len(exe):
    print("Table is BEYOND EXE end! This must be in BSS/RAM, not file data.")
    print("The table at this VA is populated at RUNTIME, not in the EXE file.")
    print()
    print("This means the drawing function pointers are set up dynamically")
    print("based on which font resources are loaded.")
    print()
    print("The skip mechanism is likely in the RESOURCE DATA, not the EXE.")
else:
    for i in range(32):
        val = struct.unpack_from("<I", exe, table_fo + i*4)[0]
        print(f"  Row {i:3d}: {val:#010x}")

# ============================================================
# NEW APPROACH: The rendering system reads glyph codes from a
# data stream. The glyph codes encode UV positions in the font atlas.
# If the font atlas resource has zero-width entries for positions
# corresponding to cells 38 and 45, those won't draw.
#
# But the user says the nuclear swap test proves it follows the
# glyph ID. That means: if you swap the texture DATA of cell 38
# with cell 37 (for example), cell 38 is STILL blank and cell 37
# now also shows cell 37's original content. This would prove the
# skip is based on the cell INDEX, not the texture content.
#
# The font data includes a METRICS table (the 4 bytes per glyph
# read by 0x3A2D10). If the metrics for cells 38 and 45 encode
# a zero width or special skip value, that would cause the skip.
#
# The unrolled setup at 0x463800 reads these metrics and stores
# halfword results. Let me check what happens when the halfword
# stored for glyph 38 or 45 is 0.
#
# The halfword is stored by sh $v0, 80($s4) for glyph 38.
# 0x3A2D10 packs 4 bytes big-endian into a 32-bit word.
# But the unrolled setup stores the result as a HALFWORD (sh).
# So only the low 16 bits are kept.
#
# For some glyphs (14, 15, 55, 56, 57), the result is stored as
# a WORD (sw) -- these might be wider glyphs.
#
# If the resource data has 0x00000000 at position glyph_id*4+8,
# the halfword stored would be 0x0000.
#
# When the rendering code later reads this halfword and uses it
# as a glyph code, a 0x0000 code would be drawn as row=0, col=0
# (the first cell in the atlas, usually blank or a default char).
# It wouldn't produce a "skip" - it would draw something.
#
# So the skip must be happening elsewhere.
# ============================================================

# Let me look at this completely differently.
# The keyboard layout uses hardcoded glyph indices 0-94.
# Each cell has an SJIS code or a glyph code.
# In the JAPANESE game, cells 38 and 45 might correspond to
# characters that don't exist or are blank in the font.
#
# With the ENGLISH patch, we replaced the font atlas but
# the glyph codes in the keyboard layout stream might point
# to cells that are empty or use a "skip" marker.
#
# Let me find the keyboard layout data.
# The function 0x48CFB0 at VA 0x48D170 calls:
#   li $a0, 2      -- category 2 (or some other value)
#   li $a1, 21     -- 21 items
#   sd $v0, 0($sp) -- some value (250)
#   jal 0x48c810   -- render row

# Actually 0x48CFB0 takes $a0 = mode (1=keyboard type), $a1 = count (13 or 22)
# The row rendering at 0x48D170 uses:
#   li $a0, 2    -- row index
#   li $a1, 21   -- glyph count in this row
#   li $t2, 128  -- alpha/opacity
# And calls 0x48C810 with these params.

# So the keyboard has rows of 21 glyphs each.
# 21 * 5 rows = 105 total positions (more than 95 cells).
# Some positions might be empty (separator spaces, etc.).

# The key question: WHERE is the keyboard grid layout data that
# maps grid positions to glyph IDs?
#
# Look at what happens between the two jal 0x48C810 calls.
# Between rows, position is incremented.

# Let me look at the FULL function 0x48CFB0 more carefully,
# specifically the part after 0x48D148 where it sets up and
# renders the keyboard rows.

# Actually - I already have the full disassembly. The keyboard
# rendering section is 0x48D148-0x48D240 and it calls 0x48C810
# TWICE (for two rows). But a full keyboard needs 5+ rows.
# Maybe each call to 0x48CFB0 renders one row, and it's called
# multiple times from the parent function.

# Let me look at who calls 0x48CFB0 and trace the loop.
# From the callers, I see calls with $a1=13 and $a1=22.
# Category 13 might be for the name entry keyboard.
# Let me check function 0x48B8F0 which calls 0x48CFB0 with a1=13.

print()
print("=" * 90)
print("FUNCTION AT VA 0x48B8F0 (calls 0x48CFB0 -- keyboard parent)")
print("=" * 90)

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
        r_ops = {0x20:"add",0x21:"addu",0x22:"sub",0x23:"subu",0x24:"and",0x25:"or",0x2A:"slt",0x2B:"sltu",0x00:"sll",0x02:"srl",0x03:"sra",0x10:"mfhi",0x12:"mflo",0x18:"mult",0x19:"multu",0x3C:"dsll32",0x3F:"dsra32"}
        if funct in (0x00,0x02,0x03,0x3C,0x3F): return f"{r_ops.get(funct,'?')} ${REG[rd]}, ${REG[rt]}, {sa}"
        if funct in (0x10,0x12): return f"{r_ops[funct]} ${REG[rd]}"
        if funct in (0x18,0x19): return f"{r_ops[funct]} ${REG[rs]}, ${REG[rt]}"
        if funct in r_ops: return f"{r_ops[funct]} ${REG[rd]}, ${REG[rs]}, ${REG[rt]}"
        return f"special funct={funct:#04x}"
    if op == 1: return {0:"bltz",1:"bgez"}.get(rt,"regimm") + f" ${REG[rs]}, {pc_va+4+imm_s*4:#08x}"
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

START = va2fo(0x48B8F0)
END = START + 0x300
for off in range(START, END, 4):
    va = fo2va(off)
    if off + 4 > len(exe): break
    instr = struct.unpack_from("<I", exe, off)[0]
    text = disasm(instr, va)
    marker = ""
    if "jr $ra" in text: marker = " --- RET ---"
    elif text.startswith("jal"): marker = " --- CALL ---"
    print(f"  {va:#08x}: {text}{marker}")
    if "jr $ra" in text:
        off2 = off + 4
        if off2 + 4 <= len(exe):
            instr2 = struct.unpack_from("<I", exe, off2)[0]
            print(f"  {fo2va(off2):#08x}: {disasm(instr2, fo2va(off2))}")
        break

# Also look at the DATA at the location referenced by lui 0x0057 + offset 17056
# 0x570000 + 17056 = 0x5742A0? No: 17056 = 0x42A0, so VA 0x5742A0
# File offset: 0x5742A0 - 0xFFF80 = 0x474320
# This is the keyboard state/config area
print()
print("Let me check if 17056 = 0x42A0 is correct:")
print(f"  0x570000 + 17056 = {0x570000 + 17056:#x}")
print(f"  File offset: {0x570000 + 17056 - VA_BASE:#x}")

# Check if within file
config_fo = 0x570000 + 17056 - VA_BASE
if config_fo < len(exe):
    print(f"  Within EXE at file offset {config_fo:#x}")
    data = exe[config_fo:config_fo+32]
    print(f"  Data: {data.hex(' ')}")
else:
    print(f"  BEYOND EXE (BSS/RAM area)")

# ============================================================
# FINAL INSIGHT: The keyboard uses category 13 in 0x3A49D0.
# In 0x3A49D0, when $a0 == 2 (category 2), it reads from a
# lookup table at VA 0x4D10E0 (file 0x3D1160).
# When $a0 == 10, different table.
# Otherwise, it uses a third table at VA 0x4D10A0 (file 0x3D1120).
#
# The render function gets category 12 from 0x48C810.
# Let me check what 0x3A49D0 does with category 12.
# ============================================================
print()
print("=" * 90)
print("RENDER CONTEXT TABLE at VA 0x4D10A0 (general category table)")
print("=" * 90)

# 0x3A49F0: lui $v0, 0x0056; addiu $v0, $v0, 27792
# 0x560000 + 27792 = 0x560000 + 0x6C90 = 0x566C90
# File: 0x566C90 - 0xFFF80 = 0x466D10
# Wait, 27792 = 0x6C90

table_va2 = 0x560000 + 27792
table_fo2 = table_va2 - VA_BASE
print(f"Table at VA {table_va2:#x}, file {table_fo2:#x}")

if table_fo2 + 128 <= len(exe):
    for i in range(16):
        val = struct.unpack_from("<I", exe, table_fo2 + i*8)[0]
        val2 = struct.unpack_from("<I", exe, table_fo2 + i*8 + 4)[0]
        print(f"  Slot {i:3d}: {val:#010x} {val2:#010x}")
else:
    print("  BEYOND EXE")

# 0x3A4A68: lui $v0, 0x004d; addiu $v0, $v0, 4256
# 0x4D0000 + 4256 = 0x4D10A0
# file: 0x4D10A0 - 0xFFF80 = 0x3D1120
table_va3 = 0x4D0000 + 4256
table_fo3 = table_va3 - VA_BASE
print(f"\nFunction pointer table at VA {table_va3:#x}, file {table_fo3:#x}")

if table_fo3 + 64 <= len(exe):
    for i in range(16):
        val = struct.unpack_from("<I", exe, table_fo3 + i*4)[0]
        if val:
            print(f"  Slot {i:3d}: VA {val:#010x}")
        else:
            print(f"  Slot {i:3d}: NULL")
else:
    print("  BEYOND EXE")
