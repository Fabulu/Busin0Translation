import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
EXE="C:/programmieren/wizardrytranslation/extracted/SLPM_653.78"
D=open(EXE,'rb').read()
def v2f(va): return va-0x100000+0x80
REG=['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7',
     's0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra']
def dec(va):
    w=struct.unpack_from('<I',D,v2f(va))[0]
    op=w>>26; rs=(w>>21)&31; rt=(w>>16)&31; rd=(w>>11)&31; sa=(w>>6)&31; fn=w&0x3f
    imm=w&0xffff; simm=imm-0x10000 if imm&0x8000 else imm
    # EE specific: lq=0x1e, sq=0x1f, mmi ops op=0x1c
    name=None
    if op==0x1e: name=f"lq    {REG[rt]}, {simm}({REG[rs]})"
    elif op==0x1f: name=f"sq    {REG[rt]}, {simm}({REG[rs]})"
    elif op==0x0f: name=f"lui   {REG[rt]}, 0x{imm:x}"
    elif op==0x09: name=f"addiu {REG[rt]}, {REG[rs]}, {simm}"
    elif op==0x0d: name=f"ori   {REG[rt]}, {REG[rs]}, 0x{imm:x}"
    elif op==0x23: name=f"lw    {REG[rt]}, {simm}({REG[rs]})"
    elif op==0x2b: name=f"sw    {REG[rt]}, {simm}({REG[rs]})"
    elif op==0x24: name=f"lbu   {REG[rt]}, {simm}({REG[rs]})"
    elif op==0x25: name=f"lhu   {REG[rt]}, {simm}({REG[rs]})"
    elif op==0x28: name=f"sb    {REG[rt]}, {simm}({REG[rs]})"
    elif op==0x29: name=f"sh    {REG[rt]}, {simm}({REG[rs]})"
    elif op==0x00:
        if fn==0x00: name=f"sll   {REG[rd]}, {REG[rt]}, {sa}"
        elif fn==0x21: name=f"addu  {REG[rd]}, {REG[rs]}, {REG[rt]}"
        elif fn==0x23: name=f"subu  {REG[rd]}, {REG[rs]}, {REG[rt]}"
        else: name=f"R fn=0x{fn:02x} rd={REG[rd]} rs={REG[rs]} rt={REG[rt]} sa={sa}"
    if name is None: name=f".word 0x{w:08x} (op=0x{op:02x})"
    return f"{va:08x}: {name}"
lo=int(sys.argv[1],16); n=int(sys.argv[2]) if len(sys.argv)>2 else 40
for i in range(n):
    print(dec(lo+i*4))
