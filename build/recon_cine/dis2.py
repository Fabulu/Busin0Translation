import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
EXE="extracted/SLPM_653.78"
data=open(EXE,"rb").read()
def f(va): return va-0x100000+0x80
REG=["zero","at","v0","v1","a0","a1","a2","a3","t0","t1","t2","t3","t4","t5","t6","t7",
     "s0","s1","s2","s3","s4","s5","s6","s7","t8","t9","k0","k1","gp","sp","fp","ra"]
def dec(va):
    w=struct.unpack_from("<I",data,f(va))[0]
    op=w>>26; rs=(w>>21)&31; rt=(w>>16)&31; rd=(w>>11)&31; sh=(w>>6)&31; fn=w&63
    imm=w&0xFFFF; simm=imm-0x10000 if imm&0x8000 else imm
    tgt=((va+4)&0xF0000000)|((w&0x3FFFFFF)<<2)
    R=REG
    if w==0: return "nop"
    if op==0:
        if fn==0x20 or fn==0x21: return f"addu {R[rd]},{R[rs]},{R[rt]}"
        if fn==0x24: return f"and {R[rd]},{R[rs]},{R[rt]}"
        if fn==0x25: return f"or {R[rd]},{R[rs]},{R[rt]}"
        if fn==0x08: return f"jr {R[rs]}"
        if fn==0x09: return f"jalr {R[rd]},{R[rs]}"
        if fn==0x00: return f"sll {R[rd]},{R[rt]},{sh}"
        if fn==0x02: return f"srl {R[rd]},{R[rt]},{sh}"
        if fn==0x03: return f"sra {R[rd]},{R[rt]},{sh}"
        if fn==0x2A: return f"slt {R[rd]},{R[rs]},{R[rt]}"
        if fn==0x2B: return f"sltu {R[rd]},{R[rs]},{R[rt]}"
        if fn==0x22 or fn==0x23: return f"subu {R[rd]},{R[rs]},{R[rt]}"
        return f".word 0x{w:08X} (special fn=0x{fn:02X})"
    if op==2: return f"j 0x{tgt:08X}"
    if op==3: return f"jal 0x{tgt:08X}"
    if op==4: return f"beq {R[rs]},{R[rt]},0x{va+4+(simm<<2):08X}"
    if op==5: return f"bne {R[rs]},{R[rt]},0x{va+4+(simm<<2):08X}"
    if op==6: return f"blez {R[rs]},0x{va+4+(simm<<2):08X}"
    if op==7: return f"bgtz {R[rs]},0x{va+4+(simm<<2):08X}"
    if op==1:
        if rt==0: return f"bltz {R[rs]},0x{va+4+(simm<<2):08X}"
        if rt==1: return f"bgez {R[rs]},0x{va+4+(simm<<2):08X}"
    if op==9: return f"addiu {R[rt]},{R[rs]},{simm}"
    if op==0x0C: return f"andi {R[rt]},{R[rs]},0x{imm:X}"
    if op==0x0D: return f"ori {R[rt]},{R[rs]},0x{imm:X}"
    if op==0x0F: return f"lui {R[rt]},0x{imm:X}"
    if op==0x0A: return f"slti {R[rt]},{R[rs]},{simm}"
    if op==0x0B: return f"sltiu {R[rt]},{R[rs]},{simm}"
    if op==0x20: return f"lb {R[rt]},{simm}({R[rs]})"
    if op==0x21: return f"lh {R[rt]},{simm}({R[rs]})"
    if op==0x23: return f"lw {R[rt]},{simm}({R[rs]})"
    if op==0x24: return f"lbu {R[rt]},{simm}({R[rs]})"
    if op==0x25: return f"lhu {R[rt]},{simm}({R[rs]})"
    if op==0x28: return f"sb {R[rt]},{simm}({R[rs]})"
    if op==0x29: return f"sh {R[rt]},{simm}({R[rs]})"
    if op==0x2B: return f"sw {R[rt]},{simm}({R[rs]})"
    if op==0x37: return f"ld {R[rt]},{simm}({R[rs]})"
    if op==0x3F: return f"sd {R[rt]},{simm}({R[rs]})"
    return f".word 0x{w:08X} (op=0x{op:02X})"
def dump(va,n):
    for i in range(n):
        a=va+i*4
        print(f"0x{a:08X}: {dec(a)}")
import sys as _s
if __name__=="__main__":
    va=int(_s.argv[1],16); n=int(_s.argv[2]) if len(_s.argv)>2 else 60
    dump(va,n)

def find_gp():
    # gp is set in _start typically via lui/ori or addiu. Search for lui gp / ori gp pattern
    import struct as st
    for off in range(0x80, 0x4000, 4):
        w=st.unpack_from("<I",data,off)[0]
        op=w>>26; rt=(w>>16)&31
        if op==0x0F and rt==28:  # lui gp
            hi=w&0xFFFF
            w2=st.unpack_from("<I",data,off+4)[0]
            if (w2>>26)==0x0D and ((w2>>16)&31)==28:
                lo=w2&0xFFFF
                print(f"gp candidate @ file 0x{off:X}: 0x{(hi<<16)+lo:08X}")
            if (w2>>26)==0x09 and ((w2>>16)&31)==28:
                lo=w2&0xFFFF; simm=lo-0x10000 if lo&0x8000 else lo
                print(f"gp candidate @ file 0x{off:X}: 0x{(hi<<16)+simm:08X}")
