import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
D=open("C:/programmieren/wizardrytranslation/extracted/SLPM_653.78",'rb').read()
def v2f(va): return va-0x100000+0x80
REG=['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7','s0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra']
lo,hi=int(sys.argv[1],16),int(sys.argv[2],16)
for va in range(lo,hi,4):
    w=struct.unpack_from('<I',D,v2f(va))[0]; op=w>>26
    rs=(w>>21)&31; rt=(w>>16)&31; imm=w&0xffff; simm=imm-0x10000 if imm&0x8000 else imm
    if op==0x1f: print(f"{va:08x}: sq    {REG[rt]}, {simm}({REG[rs]})")
    elif op==0x29: print(f"{va:08x}: sh    {REG[rt]}, {simm}({REG[rs]})")
    elif op==0x2b: print(f"{va:08x}: sw    {REG[rt]}, {simm}({REG[rs]})")
