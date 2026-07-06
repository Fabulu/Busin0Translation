import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
EXE='C:/programmieren/wizardrytranslation/extracted/SLPM_653.78'
data=open(EXE,'rb').read()
def f2v(off): return off-0x80+0x100000
def reg(n): return ['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7','s0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra'][n]
# load/store with offset 6 to descriptor, anywhere in draw region. also direct addr 0x55DF06? unlikely.
# The descriptor base 0x55DD20 with index*0x1E0. Code reads ptr+6.
for off in range(0,len(data)-4,4):
    w=struct.unpack_from('<I',data,off)[0]
    op=w>>26; rs=(w>>21)&31; rt=(w>>16)&31; imm=w&0xffff
    simm=imm-0x10000 if imm&0x8000 else imm
    if op in (0x21,0x25,0x29,0x23,0x2B) and simm==6:
        va=f2v(off)
        if 0x1B0000<=va<0x1D0000:
            mn={0x21:'lh',0x25:'lhu',0x29:'sh',0x23:'lw',0x2B:'sw'}[op]
            print(f"  0x{va:08X}: {mn:5} ${reg(rt):4} 6(${reg(rs)})")
