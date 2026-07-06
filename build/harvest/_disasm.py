import struct
# Minimal MIPS-LE disassembler for the few opcodes we care about
exe=open("C:/programmieren/wizardrytranslation/extracted/SLPM_653.78","rb").read()
def fo(va): return va-0x100000+0x80
REG=["zero","at","v0","v1","a0","a1","a2","a3","t0","t1","t2","t3","t4","t5","t6","t7",
     "s0","s1","s2","s3","s4","s5","s6","s7","t8","t9","k0","k1","gp","sp","fp","ra"]
def dis(va):
    w=struct.unpack_from("<I",exe,fo(va))[0]
    op=w>>26; rs=(w>>21)&31; rt=(w>>16)&31; rd=(w>>11)&31; sh=(w>>6)&31; fn=w&63
    imm=w&0xffff; simm=imm-0x10000 if imm&0x8000 else imm
    s=f"0x{va:06X}: {w:08X}  "
    if w==0: return s+"nop"
    if op==0:
        if fn==0x20: return s+f"add {REG[rd]},{REG[rs]},{REG[rt]}"
        if fn==0x21: return s+f"addu {REG[rd]},{REG[rs]},{REG[rt]}"
        if fn==0x22: return s+f"sub {REG[rd]},{REG[rs]},{REG[rt]}"
        if fn==0x23: return s+f"subu {REG[rd]},{REG[rs]},{REG[rt]}"
        if fn==0x00: return s+f"sll {REG[rd]},{REG[rt]},{sh}"
        if fn==0x02: return s+f"srl {REG[rd]},{REG[rt]},{sh}"
        if fn==0x03: return s+f"sra {REG[rd]},{REG[rt]},{sh}"
        if fn==0x08: return s+f"jr {REG[rs]}"
        if fn==0x09: return s+f"jalr {REG[rd]},{REG[rs]}"
        if fn==0x25: return s+f"or {REG[rd]},{REG[rs]},{REG[rt]}"
        if fn==0x2a: return s+f"slt {REG[rd]},{REG[rs]},{REG[rt]}"
        if fn==0x2b: return s+f"sltu {REG[rd]},{REG[rs]},{REG[rt]}"
        return s+f".word(special fn=0x{fn:02X})"
    if op==2: return s+f"j 0x{((va+4)&0xF0000000)|((w&0x3ffffff)<<2):X}"
    if op==3: return s+f"jal 0x{((va+4)&0xF0000000)|((w&0x3ffffff)<<2):X}"
    if op==4: return s+f"beq {REG[rs]},{REG[rt]},0x{va+4+(simm<<2):06X}"
    if op==5: return s+f"bne {REG[rs]},{REG[rt]},0x{va+4+(simm<<2):06X}"
    if op==1: 
        if rt==0: return s+f"bltz {REG[rs]},0x{va+4+(simm<<2):06X}"
        if rt==1: return s+f"bgez {REG[rs]},0x{va+4+(simm<<2):06X}"
    if op==6: return s+f"blez {REG[rs]},0x{va+4+(simm<<2):06X}"
    if op==7: return s+f"bgtz {REG[rs]},0x{va+4+(simm<<2):06X}"
    if op==8: return s+f"addi {REG[rt]},{REG[rs]},{simm}"
    if op==9: return s+f"addiu {REG[rt]},{REG[rs]},{simm}"
    if op==0x0a: return s+f"slti {REG[rt]},{REG[rs]},{simm}"
    if op==0x0b: return s+f"sltiu {REG[rt]},{REG[rs]},{simm}"
    if op==0x0c: return s+f"andi {REG[rt]},{REG[rs]},0x{imm:X}"
    if op==0x0d: return s+f"ori {REG[rt]},{REG[rs]},0x{imm:X}"
    if op==0x0f: return s+f"lui {REG[rt]},0x{imm:X}"
    if op==0x20: return s+f"lb {REG[rt]},{simm}({REG[rs]})"
    if op==0x21: return s+f"lh {REG[rt]},{simm}({REG[rs]})"
    if op==0x23: return s+f"lw {REG[rt]},{simm}({REG[rs]})"
    if op==0x24: return s+f"lbu {REG[rt]},{simm}({REG[rs]})"
    if op==0x25: return s+f"lhu {REG[rt]},{simm}({REG[rs]})"
    if op==0x28: return s+f"sb {REG[rt]},{simm}({REG[rs]})"
    if op==0x29: return s+f"sh {REG[rt]},{simm}({REG[rs]})"
    if op==0x2b: return s+f"sw {REG[rt]},{simm}({REG[rs]})"
    if op==0x31: return s+f"lwc1 f{rt},{simm}({REG[rs]})"
    if op==0x39: return s+f"swc1 f{rt},{simm}({REG[rs]})"
    if op==0x11: return s+f"COP1 {w:08X}"
    return s+f".word 0x{w:08X} (op=0x{op:02X})"
import sys
start=int(sys.argv[1],16); n=int(sys.argv[2])
for i in range(n):
    print(dis(start+i*4))
