import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
EXE=r"C:\programmieren\wizardrytranslation\extracted\SLPM_653.78"
VA_BASE=0xFFF80
exe=open(EXE,'rb').read()
REG=["zero","at","v0","v1","a0","a1","a2","a3","t0","t1","t2","t3","t4","t5","t6","t7","s0","s1","s2","s3","s4","s5","s6","s7","t8","t9","k0","k1","gp","sp","s8","ra"]
def dec(w,pc):
    op=(w>>26)&0x3F; rs=(w>>21)&0x1F; rt=(w>>16)&0x1F; rd=(w>>11)&0x1F; sa=(w>>6)&0x1F; f=w&0x3F
    imm=w&0xFFFF; s=imm-0x10000 if imm&0x8000 else imm
    tgt=((w&0x03FFFFFF)<<2)|(pc&0xF0000000)
    bt=pc+4+s*4
    R=REG
    if w==0: return "nop"
    if op==0:
        if f==0x2D:
            if rt==0: return f"move ${R[rd]}, ${R[rs]}"
            return f"daddu ${R[rd]}, ${R[rs]}, ${R[rt]}"
        if f==0x2B: return f"sltu ${R[rd]}, ${R[rs]}, ${R[rt]}"
        if f==0x2A: return f"slt ${R[rd]}, ${R[rs]}, ${R[rt]}"
        if f==0x21:
            if rt==0: return f"move ${R[rd]}, ${R[rs]}"
            return f"addu ${R[rd]}, ${R[rs]}, ${R[rt]}"
        if f==0x20: return f"add ${R[rd]}, ${R[rs]}, ${R[rt]}"
        if f==0x23: return f"subu ${R[rd]}, ${R[rs]}, ${R[rt]}"
        if f==0x22: return f"sub ${R[rd]}, ${R[rs]}, ${R[rt]}"
        if f==0x08: return f"jr ${R[rs]}"
        if f==0x09: return f"jalr ${R[rd]}, ${R[rs]}" if rd!=31 else f"jalr ${R[rs]}"
        if f==0x00: return f"sll ${R[rd]}, ${R[rt]}, {sa}" if w!=0 else "nop"
        if f==0x02: return f"srl ${R[rd]}, ${R[rt]}, {sa}"
        if f==0x03: return f"sra ${R[rd]}, ${R[rt]}, {sa}"
        if f==0x04: return f"sllv ${R[rd]}, ${R[rt]}, ${R[rs]}"
        if f==0x06: return f"srlv ${R[rd]}, ${R[rt]}, ${R[rs]}"
        if f==0x24: return f"and ${R[rd]}, ${R[rs]}, ${R[rt]}"
        if f==0x25:
            if rt==0: return f"move ${R[rd]}, ${R[rs]}"
            return f"or ${R[rd]}, ${R[rs]}, ${R[rt]}"
        if f==0x27: return f"nor ${R[rd]}, ${R[rs]}, ${R[rt]}"
        if f==0x26: return f"xor ${R[rd]}, ${R[rs]}, ${R[rt]}"
        if f==0x18: return f"mult ${R[rs]}, ${R[rt]}"
        if f==0x19: return f"multu ${R[rs]}, ${R[rt]}"
        if f==0x1A: return f"div ${R[rs]}, ${R[rt]}"
        if f==0x1B: return f"divu ${R[rs]}, ${R[rt]}"
        if f==0x10: return f"mfhi ${R[rd]}"
        if f==0x12: return f"mflo ${R[rd]}"
        return f"R funct={f:#x} rd={R[rd]} rs={R[rs]} rt={R[rt]}"
    if op==0x02: return f"j 0x{tgt:X}"
    if op==0x03: return f"jal 0x{tgt:X}"
    if op==0x04: return ("b 0x%X"%bt) if rs==0 and rt==0 else f"beq ${R[rs]}, ${R[rt]}, 0x{bt:X}"
    if op==0x05: return f"bne ${R[rs]}, ${R[rt]}, 0x{bt:X}"
    if op==0x06: return f"blez ${R[rs]}, 0x{bt:X}"
    if op==0x07: return f"bgtz ${R[rs]}, 0x{bt:X}"
    if op==0x14: return f"beql ${R[rs]}, ${R[rt]}, 0x{bt:X}"
    if op==0x15: return f"bnel ${R[rs]}, ${R[rt]}, 0x{bt:X}"
    if op==0x01:
        if rt==0: return f"bltz ${R[rs]}, 0x{bt:X}"
        if rt==1: return f"bgez ${R[rs]}, 0x{bt:X}"
        if rt==0x11: return f"bgezal ${R[rs]}, 0x{bt:X}"
        return f"regimm rt={rt}"
    if op==0x09: return f"addiu ${R[rt]}, ${R[rs]}, {s:#x}" if rs!=0 else f"li ${R[rt]}, {s:#x}"
    if op==0x0A: return f"slti ${R[rt]}, ${R[rs]}, {s:#x}"
    if op==0x0B: return f"sltiu ${R[rt]}, ${R[rs]}, {s:#x}"
    if op==0x0C: return f"andi ${R[rt]}, ${R[rs]}, {imm:#x}"
    if op==0x0D: return f"ori ${R[rt]}, ${R[rs]}, {imm:#x}"
    if op==0x0E: return f"xori ${R[rt]}, ${R[rs]}, {imm:#x}"
    if op==0x0F: return f"lui ${R[rt]}, {imm:#x}"
    if op==0x23: return f"lw ${R[rt]}, {s:#x}(${R[rs]})"
    if op==0x25: return f"lhu ${R[rt]}, {s:#x}(${R[rs]})"
    if op==0x21: return f"lh ${R[rt]}, {s:#x}(${R[rs]})"
    if op==0x20: return f"lb ${R[rt]}, {s:#x}(${R[rs]})"
    if op==0x24: return f"lbu ${R[rt]}, {s:#x}(${R[rs]})"
    if op==0x2B: return f"sw ${R[rt]}, {s:#x}(${R[rs]})"
    if op==0x29: return f"sh ${R[rt]}, {s:#x}(${R[rs]})"
    if op==0x28: return f"sb ${R[rt]}, {s:#x}(${R[rs]})"
    if op==0x37: return f"ld ${R[rt]}, {s:#x}(${R[rs]})"
    if op==0x3F: return f"sd ${R[rt]}, {s:#x}(${R[rs]})"
    if op==0x1E: return f"lq ${R[rt]}, {s:#x}(${R[rs]})"
    if op==0x1F: return f"sq ${R[rt]}, {s:#x}(${R[rs]})"
    return f".word 0x{w:08X} (op={op:#x})"
def disrange(start,end):
    va=start
    while va<end:
        w=struct.unpack('<I',exe[va-VA_BASE:va-VA_BASE+4])[0]
        print(f"{va:08X}  {dec(w,va)}")
        va+=4
if __name__=='__main__':
    s=int(sys.argv[1],16); e=int(sys.argv[2],16)
    disrange(s,e)
