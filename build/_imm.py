import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
EXE='extracted/SLPM_653.78'
data=open(EXE,'rb').read()
n=len(data)//4
want=set(int(x,16) for x in sys.argv[1:])
# scan for andi/ori/addiu/slti/sltiu/lui with immediate in want, and beq/bne not relevant
for i in range(n):
    w=struct.unpack_from('<I',data,i*4)[0]
    op=w>>26; imm=w&0xFFFF
    va=(i*4)+0xFFF80
    if imm in want and op in (0x08,0x09,0x0A,0x0B,0x0C,0x0D,0x0E,0x0F):
        # addiu(0x09) addi(0x08) slti(0x0A) sltiu(0x0B) andi(0x0C) ori(0x0D) xori(0x0E) lui(0x0F)
        names={8:'addi',9:'addiu',10:'slti',11:'sltiu',12:'andi',13:'ori',14:'xori',15:'lui'}
        rt=(w>>16)&31; rs=(w>>21)&31
        print('0x%08X  %-6s rt=%d rs=%d imm=0x%04X'%(va,names[op],rt,rs,imm))
