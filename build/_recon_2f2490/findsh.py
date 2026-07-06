import sys,struct
EXE=r"C:\programmieren\wizardrytranslation\extracted\SLPM_653.78"
exe=open(EXE,'rb').read()
def fo(va): return va-0x100000+0x80
off=int(sys.argv[1],16)
for va in range(0x307DA0,0x3097E0,4):
    w=struct.unpack_from('<I',exe,fo(va))[0]
    op=(w>>26)&0x3F; imm=w&0xFFFF; rs=(w>>21)&0x1F; rt=(w>>16)&0x1F
    if op==0x29 and imm==off:  # sh rt, off(rs)
        print("SH  %08X  rs=%d rt=%d  %08X"%(va,rs,rt,w))
