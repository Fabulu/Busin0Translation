import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
ee = open(r"C:/programmieren/wizardrytranslation/build/recon_tri/extract/requestbroken__ee.bin","rb").read()
# disassemble MIPS at given VA range using a tiny decoder for the instructions we need (lw/sw/lui/addiu/jal/jr/beq/...)
def u32(a): return struct.unpack_from("<I", ee, a)[0]
regs=["zero","at","v0","v1","a0","a1","a2","a3","t0","t1","t2","t3","t4","t5","t6","t7",
      "s0","s1","s2","s3","s4","s5","s6","s7","t8","t9","k0","k1","gp","sp","fp","ra"]
def dis(va):
    w=u32(va)
    op=w>>26; rs=(w>>21)&31; rt=(w>>16)&31; rd=(w>>11)&31; sh=(w>>6)&31; fn=w&63
    imm=w&0xffff; simm=imm-0x10000 if imm&0x8000 else imm
    tgt=(w&0x3ffffff)<<2
    R=regs
    if w==0: return "nop"
    if op==0:
        if fn==0x20: return f"add {R[rd]},{R[rs]},{R[rt]}"
        if fn==0x21: return f"addu {R[rd]},{R[rs]},{R[rt]}"
        if fn==0x23: return f"subu {R[rd]},{R[rs]},{R[rt]}"
        if fn==8: return f"jr {R[rs]}"
        if fn==9: return f"jalr {R[rs]}"
        if fn==0: return f"sll {R[rd]},{R[rt]},{sh}"
        return f".word {w:08x} (special fn={fn:#x})"
    if op==2: return f"j {((va+4)&0xf0000000)|tgt:08x}"
    if op==3: return f"jal {((va+4)&0xf0000000)|tgt:08x}"
    if op==4: return f"beq {R[rs]},{R[rt]},{va+4+(simm<<2):08x}"
    if op==5: return f"bne {R[rs]},{R[rt]},{va+4+(simm<<2):08x}"
    if op==1:
        if rt==0: return f"bltz {R[rs]},{va+4+(simm<<2):08x}"
        if rt==1: return f"bgez {R[rs]},{va+4+(simm<<2):08x}"
    if op==9: return f"addiu {R[rt]},{R[rs]},{simm}"
    if op==0xf: return f"lui {R[rt]},{imm:#x}"
    if op==0x23: return f"lw {R[rt]},{simm}({R[rs]})"
    if op==0x2b: return f"sw {R[rt]},{simm}({R[rs]})"
    if op==0x24: return f"lbu {R[rt]},{simm}({R[rs]})"
    if op==0x20: return f"lb {R[rt]},{simm}({R[rs]})"
    if op==0x25: return f"lhu {R[rt]},{simm}({R[rs]})"
    if op==0x28: return f"sb {R[rt]},{simm}({R[rs]})"
    if op==0xd: return f"ori {R[rt]},{R[rs]},{imm:#x}"
    if op==0xc: return f"andi {R[rt]},{R[rs]},{imm:#x}"
    if op==0xa: return f"slti {R[rt]},{R[rs]},{simm}"
    return f".word {w:08x} (op={op:#x})"
import sys
start=int(sys.argv[1],16); n=int(sys.argv[2])
for i in range(n):
    va=start+i*4
    print(f"{va:08X}: {dis(va)}")
