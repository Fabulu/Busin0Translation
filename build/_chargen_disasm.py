import struct

PATCHED = r"C:\programmieren\wizardrytranslation\build\SLPM_653.78_patched"
PRISTINE = r"C:\programmieren\wizardrytranslation\extracted\SLPM_653.78"

def load(p):
    with open(p,"rb") as f: return f.read()
pat=load(PATCHED); pri=load(PRISTINE)

def va2off(va): return va-0x100000+0x80
def off2va(off): return off-0x80+0x100000
def w(buf,off): return struct.unpack_from("<I",buf,off)[0]

REGS=["zero","at","v0","v1","a0","a1","a2","a3","t0","t1","t2","t3","t4","t5","t6","t7",
      "s0","s1","s2","s3","s4","s5","s6","s7","t8","t9","k0","k1","gp","sp","fp","ra"]

def s16(x):
    return x-0x10000 if x&0x8000 else x

def disasm(word, va):
    op=word>>26
    rs=(word>>21)&0x1F; rt=(word>>16)&0x1F; rd=(word>>11)&0x1F
    sa=(word>>6)&0x1F; funct=word&0x3F; imm=word&0xFFFF; tgt=word&0x03FFFFFF
    if word==0: return "nop"
    if op==0:
        if funct==0x20: return f"add {REGS[rd]},{REGS[rs]},{REGS[rt]}"
        if funct==0x21: return f"addu {REGS[rd]},{REGS[rs]},{REGS[rt]}"
        if funct==0x22: return f"sub {REGS[rd]},{REGS[rs]},{REGS[rt]}"
        if funct==0x23: return f"subu {REGS[rd]},{REGS[rs]},{REGS[rt]}"
        if funct==0x24: return f"and {REGS[rd]},{REGS[rs]},{REGS[rt]}"
        if funct==0x25: return f"or {REGS[rd]},{REGS[rs]},{REGS[rt]}"
        if funct==0x2a: return f"slt {REGS[rd]},{REGS[rs]},{REGS[rt]}"
        if funct==0x2b: return f"sltu {REGS[rd]},{REGS[rs]},{REGS[rt]}"
        if funct==0x00: return f"sll {REGS[rd]},{REGS[rt]},{sa}"
        if funct==0x02: return f"srl {REGS[rd]},{REGS[rt]},{sa}"
        if funct==0x03: return f"sra {REGS[rd]},{REGS[rt]},{sa}"
        if funct==0x08: return f"jr {REGS[rs]}"
        if funct==0x09: return f"jalr {REGS[rd]},{REGS[rs]}"
        return f".word 0x{word:08X} (special funct=0x{funct:02X})"
    if op==2: return f"j 0x{((va&0xF0000000)|(tgt<<2)):08X}"
    if op==3: return f"jal 0x{((va&0xF0000000)|(tgt<<2)):08X}"
    if op==4: return f"beq {REGS[rs]},{REGS[rt]},0x{va+4+(s16(imm)<<2):08X}"
    if op==5: return f"bne {REGS[rs]},{REGS[rt]},0x{va+4+(s16(imm)<<2):08X}"
    if op==6: return f"blez {REGS[rs]},0x{va+4+(s16(imm)<<2):08X}"
    if op==7: return f"bgtz {REGS[rs]},0x{va+4+(s16(imm)<<2):08X}"
    if op==1:
        if rt==0: return f"bltz {REGS[rs]},0x{va+4+(s16(imm)<<2):08X}"
        if rt==1: return f"bgez {REGS[rs]},0x{va+4+(s16(imm)<<2):08X}"
        return f"regimm rt={rt}"
    if op==9: return f"addiu {REGS[rt]},{REGS[rs]},0x{imm:04X}({s16(imm)})"
    if op==8: return f"addi {REGS[rt]},{REGS[rs]},0x{imm:04X}({s16(imm)})"
    if op==0x0a: return f"slti {REGS[rt]},{REGS[rs]},0x{imm:04X}"
    if op==0x0b: return f"sltiu {REGS[rt]},{REGS[rs]},0x{imm:04X}"
    if op==0x0c: return f"andi {REGS[rt]},{REGS[rs]},0x{imm:04X}"
    if op==0x0d: return f"ori {REGS[rt]},{REGS[rs]},0x{imm:04X}"
    if op==0x0e: return f"xori {REGS[rt]},{REGS[rs]},0x{imm:04X}"
    if op==0x0f: return f"lui {REGS[rt]},0x{imm:04X}"
    if op==0x20: return f"lb {REGS[rt]},0x{imm:04X}({REGS[rs]}) [{s16(imm)}]"
    if op==0x21: return f"lh {REGS[rt]},0x{imm:04X}({REGS[rs]}) [{s16(imm)}]"
    if op==0x23: return f"lw {REGS[rt]},0x{imm:04X}({REGS[rs]}) [{s16(imm)}]"
    if op==0x24: return f"lbu {REGS[rt]},0x{imm:04X}({REGS[rs]}) [{s16(imm)}]"
    if op==0x25: return f"lhu {REGS[rt]},0x{imm:04X}({REGS[rs]}) [{s16(imm)}]"
    if op==0x28: return f"sb {REGS[rt]},0x{imm:04X}({REGS[rs]}) [{s16(imm)}]"
    if op==0x29: return f"sh {REGS[rt]},0x{imm:04X}({REGS[rs]}) [{s16(imm)}]"
    if op==0x2b: return f"sw {REGS[rt]},0x{imm:04X}({REGS[rs]}) [{s16(imm)}]"
    return f".word 0x{word:08X} (op=0x{op:02X})"

def dump(buf, lo_va, hi_va, label):
    print(f"\n===== {label}  0x{lo_va:06X}..0x{hi_va:06X} =====")
    va=lo_va
    while va<hi_va:
        off=va2off(va); word=w(buf,off)
        print(f"  0x{va:06X}: {word:08X}  {disasm(word,va)}")
        va+=4

import sys
# Disassemble around 0x3079B0 jal and back to prologue
# Scan back from 0x3079B0 for addiu sp,sp,-N prologue
def find_prologue(buf, from_va, limit=0x600):
    va=from_va
    while va > from_va-limit:
        word=w(buf,va2off(va))
        op=word>>26; rt=(word>>16)&0x1F; rs=(word>>21)&0x1F; imm=word&0xFFFF
        if op==9 and rt==29 and rs==29 and (imm&0x8000):  # addiu sp,sp,-N
            return va
        va-=4
    return None

pro = find_prologue(pri, 0x3079B0)
print("prologue for 0x3079B0 region:", hex(pro) if pro else None)

# dump the whole candidate function region pristine
dump(pri, 0x307800, 0x307DA0, "PRISTINE candidate around 0x3079B0")
