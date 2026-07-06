import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
EXE='extracted/SLPM_653.78'
data=open(EXE,'rb').read(); n=len(data)//4
ops={0x21:'lh',0x25:'lhu',0x29:'sh'}
for i in range(n):
    w=struct.unpack_from('<I',data,i*4)[0]; op=w>>26; imm=w&0xFFFF
    va=(i*4)+0xFFF80
    if 0x2F0000<=va<=0x310000 and op in ops and imm==0x5e:
        rt=(w>>16)&31; rs=(w>>21)&31
        print('0x%08X %-4s rt=%d 0x5e(rs=%d)'%(va,ops[op],rt,rs))
