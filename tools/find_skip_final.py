"""
The rendering loop at 0x3A2EF0 is a generic text stream renderer.
It reads glyph codes from a byte stream. The keyboard grid is NOT
rendered by iterating cells 0-94. Instead, the keyboard layout is
defined by a data stream of glyph codes.

If the data stream doesn't contain glyph codes for 38 (F) and 45 (M),
those won't be drawn. The data stream is in a RESOURCE, not the EXE.

BUT - the user said "nuclear swap test proved GLYPH-ID-SPECIFIC."
This means swapping glyph cell DATA (not codes) still results in
missing F and M. So the codes for F and M ARE in the stream, but
something else prevents drawing.

Let me re-examine the rendering path:
1. 0x48CFB0 calls 0x48C810 (row rendering)
2. 0x48C810 calls 0x3A49D0 (context setup) then 0x3A3260
3. 0x3A3260 calls 0x3A2D90 (data pointer lookup) then 0x3A2EF0 (render loop)
4. 0x3A2EF0 calls 0x3A2E10 (draw single glyph)

The function 0x3A2D10 (called in the unrolled setup) returns texture coordinates.
If it returns 0 for certain glyph IDs, 0x3A2E10 might skip drawing.

But 0x3A2D10 reads from a resource ($a0 pointer), not hardcoded in EXE.

WAIT - Let me re-read 0x3A2D10 more carefully:
  0x3a2d10: bne $a0, $zero, 0x3a2d20  -- if $a0 == 0, return 0
  0x3a2d14: daddu $v0, $zero, $zero
  0x3a2d18: b 0x3a2d60              -- return 0
  0x3a2d20: addiu $a0, $a0, 8       -- $a0 = ptr + 8 (skip header)
  0x3a2d24: mult $t0, $a1           -- offset = $t0 * $a1
  0x3a2d28: addu $v0, $a3, $v0      -- ??? $v0 is initially... from mflo?

Wait, mult result goes to HI/LO. And $v0 is $zero (daddu $v0,$zero,$zero in the delay slot?). No - on the first path ($a0 != 0), the delay slot of bne already executed daddu $v0,$zero,$zero.

Actually wait: MIPS branch delay slots. At 0x3a2d10:
  bne $a0, $zero, 0x3a2d20     -- branch if $a0 != 0
  daddu $v0, $zero, $zero      -- delay slot: $v0 = 0 (always executes)

If $a0 == 0: fall through, $v0 = 0, then b 0x3a2d60, jr $ra (return 0)
If $a0 != 0: take branch, $v0 = 0 (from delay slot), continue at 0x3a2d20

At 0x3a2d20:
  addiu $a0, $a0, 8       -- skip 8-byte header
  mult $t0, $a1           -- LO = $t0 * $a1 (but where's mflo?)

Hmm, $v0 = 0 still. Then:
  addu $v0, $a3, $v0      -- $v0 = $a3 + 0 = $a3 (glyph ID)
  sll $v0, $v0, 2          -- $v0 = glyph_id * 4
  addu $a0, $a0, $v0       -- $a0 = base + 8 + glyph_id * 4
  lbu $v0, 0($a0)
  lbu $a2, 1($a0)
  lbu $a1, 2($a0)
  lbu $v1, 3($a0)
  -- Reads 4 bytes big-endian: $v0 = byte[0]<<24 | byte[1]<<16 | byte[2]<<8 | byte[3]

So 0x3A2D10 reads a 4-byte entry from position (base + 8 + glyph_id * 4).
If this 4-byte value is 0 for glyph IDs 38 and 45 in the resource data,
the renderer would get a zero value -> might skip drawing.

The halfword stored in the glyph mapping table at $s4+offset would be 0.
When the rendering code reads this 0 value and uses it as a glyph code in
the data stream, the stream renderer would try to draw "glyph 0" or skip.

Actually wait - I misread the data flow. Let me separate two systems:
1. The unrolled setup (0x463800) builds a table of texture coords per glyph
2. The rendering loop (0x3A2EF0) reads a glyph stream and draws each one

These are TWO DIFFERENT systems for the same keyboard. The setup pre-computes
where each glyph's texture is on the atlas. The render loop iterates the
actual keyboard layout stream.

For the render loop, the data comes from the resource loaded by 0x3A2D90.
The resource contains the keyboard layout as a glyph stream.
If glyphs 38 and 45 are MISSING from this stream (replaced by skip codes
like 0xFFFF), they won't draw.

BUT the nuclear swap proves the issue follows the glyph ID, not position.
So the data stream probably DOES include codes for positions 38 and 45,
but the texture data for those glyphs might be blank or zero-sized.

Let me check if the issue is in the texture coordinate table by looking
at the R1188 resource structure. The 4-byte entries at base+8+glyph_id*4
might have zeros for indices corresponding to where F and M would be
in the Japanese character set.

Actually - I think the answer might be simpler. Let me check the function
0x3A2E10 which does the actual GS drawing. If the texture coordinates
indicate a zero-width or zero-height glyph, it might skip the draw call.
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

# Disassemble 0x3A2E10 - the actual glyph drawing function
print("=" * 90)
print("FUNCTION AT VA 0x3A2E10 (draw single glyph/sprite)")
print("=" * 90)

START = va2fo(0x3A2E10)
END = va2fo(0x3A2EF0)
for off in range(START, END, 4):
    va = fo2va(off)
    instr = struct.unpack_from("<I", exe, off)[0]
    text = disasm(instr, va)
    marker = ""
    if "jr $ra" in text: marker = " --- RET ---"
    elif text.startswith("jal"): marker = " --- CALL ---"
    elif "beq" in text and "$zero" in text and "0x00" not in text: marker = " [SKIP?]"
    elif "bne" in text: marker = " [branch]"
    print(f"  {va:#08x}: {text}{marker}")

# Now look at who calls 0x48CFB0 to understand the keyboard layout data
print()
print("=" * 90)
print("CALLERS OF VA 0x48CFB0 (keyboard init)")
print("=" * 90)

target_va = 0x48CFB0
jal_val = 0x0C000000 | (target_va >> 2)
jal_bytes = struct.pack("<I", jal_val)
pos = 0
while True:
    pos = exe.find(jal_bytes, pos)
    if pos == -1: break
    va = fo2va(pos)
    # Show context
    print(f"\n  Caller at VA {va:#08x}:")
    for delta in range(-5, 5):
        off = pos + delta * 4
        if 0 <= off < len(exe) - 4:
            instr = struct.unpack_from("<I", exe, off)[0]
            text = disasm(instr, fo2va(off))
            m = " <<<" if delta == 0 else ""
            print(f"    [{delta:+d}] {fo2va(off):#08x}: {text}{m}")
    pos += 4

# Now look at function 0x490F50 (called from 0x48C810 before render)
print()
print("=" * 90)
print("FUNCTION AT VA 0x490F50 (color/palette setup?)")
print("=" * 90)

START = va2fo(0x490F50)
for off in range(START, START + 0x100, 4):
    va = fo2va(off)
    instr = struct.unpack_from("<I", exe, off)[0]
    text = disasm(instr, va)
    print(f"  {va:#08x}: {text}")
    if "jr $ra" in text:
        off2 = off + 4
        print(f"  {fo2va(off2):#08x}: {disasm(struct.unpack_from('<I', exe, off2)[0], fo2va(off2))}")
        break
