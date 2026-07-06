import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
EXE='C:/programmieren/wizardrytranslation/extracted/SLPM_653.78'
data=open(EXE,'rb').read()
def f2v(off): return off-0x80+0x100000
def reg(n): return ['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7','s0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra'][n]
# find 'sh rt, 6(rs)' where rt was just loaded with an immediate (addiu rt,zero,N) within prev 3 instrs, N>0
for off in range(12,len(data)-4,4):
    w=struct.unpack_from('<I',data,off)[0]
    op=w>>26; rs=(w>>21)&31; rt=(w>>16)&31; imm=w&0xffff
    simm=imm-0x10000 if imm&0x8000 else imm
    if op==0x29 and simm==6:  # sh rt,6(rs)
        va=f2v(off)
        if not (0x1B0000<=va<0x1D0000): continue
        # look back for addiu rt,zero,N
        for j in range(1,5):
            w2=struct.unpack_from('<I',data,off-j*4)[0]
            if (w2>>26)==0x09 and ((w2>>21)&31)==0 and ((w2>>16)&31)==rt:
                n=w2&0xffff
                print(f"  0x{va:08X}: sh ${reg(rt)},6(${reg(rs)})  <- addiu ${reg(rt)},zero,{n if n<0x8000 else n-0x10000} (0x{n:X})")
                break
