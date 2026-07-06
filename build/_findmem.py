import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
EXE='extracted/SLPM_653.78'
data=open(EXE,'rb').read()
n=len(data)//4
LO=0x2F0000; HI=0x310000
# loads/stores with given offset: lbu(0x24) lb(0x20) lhu(0x25) lh(0x21) lw(0x23) sb(0x28) sh(0x29) sw(0x2b)
ops={0x20:'lb',0x21:'lh',0x23:'lw',0x24:'lbu',0x25:'lhu',0x28:'sb',0x29:'sh',0x2b:'sw'}
targets=set(int(x,16) for x in sys.argv[1:])
for i in range(n):
    w=struct.unpack_from('<I',data,i*4)[0]
    op=w>>26; imm=w&0xFFFF; rs=(w>>21)&31; rt=(w>>16)&31
    va=(i*4)+0xFFF80
    if va<LO or va>HI: continue
    if op in ops and imm in targets:
        print('0x%08X  %-4s rt=%d %d(rs=%d)'%(va,ops[op],rt,imm,rs))
