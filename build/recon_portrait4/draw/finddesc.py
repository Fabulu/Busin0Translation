import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
EXE='C:/programmieren/wizardrytranslation/extracted/SLPM_653.78'
data=open(EXE,'rb').read()
def f2v(off): return off-0x80+0x100000
def reg(n): return ['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7','s0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra'][n]
# find loads/stores with offset 0xDE, 0x02, 0x40, 0xBA (descriptor field accesses anywhere)
targets=[int(x,16) for x in sys.argv[1:]] if len(sys.argv)>1 else [0xDE]
for off in range(0,len(data)-4,4):
    w=struct.unpack_from('<I',data,off)[0]
    op=w>>26; rs=(w>>21)&31; rt=(w>>16)&31; imm=w&0xffff
    simm=imm-0x10000 if imm&0x8000 else imm
    if op in (0x29,0x2B,0x28,0x21,0x23,0x25,0x24,0x27,0x20) and simm in targets:
        mn={0x09:'addiu',0x29:'sh',0x2B:'sw',0x28:'sb',0x21:'lh',0x23:'lw',0x25:'lhu',0x24:'lbu',0x27:'lwu',0x20:'lb'}[op]
        va=f2v(off)
        # only show those in the sprite/draw region 0x1B0000-0x1D0000
        if 0x1B0000<=va<0x1D0000:
            print(f"  0x{va:08X}: {mn:5} ${reg(rt):4} 0x{simm:X}(${reg(rs)})")
