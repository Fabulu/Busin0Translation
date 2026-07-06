import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
EXE='C:/programmieren/wizardrytranslation/extracted/SLPM_653.78'
data=open(EXE,'rb').read()
def f2v(off): return off-0x80+0x100000
def reg(n): return ['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7','s0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra'][n]
LO=0x509F00; HI=0x50A000
for off in range(0,len(data)-4,4):
    w=struct.unpack_from('<I',data,off)[0]
    if (w>>26)==0x0F:
        rt=(w>>16)&31; hi=(w&0xffff)<<16
        for j in range(1,6):
            o2=off+j*4
            w2=struct.unpack_from('<I',data,o2)[0]
            op2=w2>>26; rs2=(w2>>21)&31; rt2=(w2>>16)&31; imm2=w2&0xffff
            simm=imm2-0x10000 if imm2&0x8000 else imm2
            if rs2==rt:
                addr=hi+simm
                if LO<=addr<HI:
                    mn={0x09:'addiu',0x29:'sh',0x2B:'sw',0x28:'sb',0x21:'lh',0x23:'lw',0x25:'lhu',0x24:'lbu',0x27:'lwu'}.get(op2,f'op{op2:#x}')
                    print(f"  ins@0x{f2v(o2):08X}: {mn:5} ${reg(rt2):4} <- 0x{addr:08X}  (lui@0x{f2v(off):08X})")
                    break
