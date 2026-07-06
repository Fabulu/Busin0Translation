import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
f=open('extracted/SLPM_653.78','rb').read()
seg=f[0x80:0x80+0x3fdc80]
# find addiu $v0,$v0,imm where imm in {0x12,0x16,0x18,0x1a,0x1e,0x24} immediately followed by sh to same reg (a6420000/a4420000 style) -> Y pitch
for i in range(0,len(seg)-8,4):
    w=struct.unpack_from('<I',seg,i)[0]
    nxt=struct.unpack_from('<I',seg,i+4)[0]
    op=w>>26; rs=(w>>21)&31; rt=(w>>16)&31; imm=w&0xffff
    # addiu rt, rs, imm  with rs==rt (self-increment), imm a small line pitch
    if op==9 and rs==rt and imm in (0x10,0x12,0x14,0x16,0x18,0x1a,0x1c,0x1e,0x20,0x24):
        # next is sh rt, off(base)? sh op=0x29
        if (nxt>>26)==0x29 and ((nxt>>16)&31)==rt:
            va=0x100000+i
            if 0x305000<=va<=0x30a000:
                print('PITCH va=%08x  addiu r%d,r%d,0x%x ; sh r%d'%(va,rt,rs,imm,rt))
