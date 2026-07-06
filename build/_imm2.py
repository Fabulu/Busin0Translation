import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
EXE='extracted/SLPM_653.78'
data=open(EXE,'rb').read()
n=len(data)//4
want=set(int(x,16) for x in sys.argv[1:])
LO=0x2C0000; HI=0x320000
names={8:'addi',9:'addiu',10:'slti',11:'sltiu',12:'andi',13:'ori',14:'xori',15:'lui'}
for i in range(n):
    w=struct.unpack_from('<I',data,i*4)[0]
    op=w>>26; imm=w&0xFFFF
    va=(i*4)+0xFFF80
    if va<LO or va>HI: continue
    if imm not in want: continue
    if op not in names: continue
    rt=(w>>16)&31; rs=(w>>21)&31
    if op==9 and rs==29: continue  # stack frame
    print('0x%08X  %-6s rt=%d rs=%d imm=0x%04X'%(va,names[op],rt,rs,imm))
