import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
EXE='C:/programmieren/wizardrytranslation/extracted/SLPM_653.78'
data=open(EXE,'rb').read()
def f2v(off): return off-0x80+0x100000
def reg(n): return ['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7','s0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra'][n]
GP=0x504FF0
target=int(sys.argv[1],16) if len(sys.argv)>1 else 0x509F80
# gp-relative: any op with rs=28(gp), addr = GP+simm
for off in range(0,len(data)-4,4):
    w=struct.unpack_from('<I',data,off)[0]
    op=w>>26; rs=(w>>21)&31; rt=(w>>16)&31; imm=w&0xffff
    simm=imm-0x10000 if imm&0x8000 else imm
    if rs==28 and op in (0x09,0x29,0x2B,0x28,0x21,0x23,0x25,0x24,0x27,0x20,0x22):
        addr=GP+simm
        if abs(addr-target)<0x40:
            mn={0x09:'addiu',0x29:'sh',0x2B:'sw',0x28:'sb',0x21:'lh',0x23:'lw',0x25:'lhu',0x24:'lbu',0x27:'lwu',0x20:'lb',0x22:'lwl'}.get(op,f'op{op:#x}')
            print(f"  0x{f2v(off):08X}: {mn:5} ${reg(rt):4} {simm}($gp)   -> 0x{addr:08X}")
