import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
D=open('extracted/SLPM_653.78','rb').read()
def v2f(va): return va-0x100000+0x80
def f2v(off): return off-0x80+0x100000
TEXT0=v2f(0x100000); TEXT1=v2f(0x100000+0x3fdc80)
# look for sw/sh/sb with offset 0x290 and lw too. opcode sw=0x2b sh=0x29 sb=0x28 lw=0x23
OFF=int(sys.argv[1],16) if len(sys.argv)>1 else 0x290
names={0x2b:'sw',0x29:'sh',0x28:'sb',0x23:'lw',0x21:'lh',0x25:'lhu',0x20:'lb',0x24:'lbu'}
off=TEXT0
while off<TEXT1:
    w=struct.unpack('<I',D[off:off+4])[0]
    op=w>>26
    if op in names:
        imm=w&0xffff
        if imm==OFF:
            isstore = op in (0x2b,0x29,0x28)
            print('%08x  %s rt=%d rs=%d off=0x%x %s'%(f2v(off),names[op],(w>>16)&0x1f,(w>>21)&0x1f,imm,'<-- STORE' if isstore else ''))
    off+=4
