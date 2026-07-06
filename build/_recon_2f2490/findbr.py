import sys,struct
EXE=r"C:\programmieren\wizardrytranslation\extracted\SLPM_653.78"
exe=open(EXE,'rb').read()
def fo(va): return va-0x100000+0x80
targets=[int(x,16) for x in sys.argv[1:]]
# scan a window for branches/jumps to targets
lo,hi=0x307000,0x30A000
for va in range(lo,hi,4):
    w=struct.unpack_from('<I',exe,fo(va))[0]
    op=(w>>26)&0x3F
    imm=w&0xFFFF; s=imm-0x10000 if imm&0x8000 else imm
    bt=va+4+s*4
    jt=((w&0x03FFFFFF)<<2)|(va&0xF0000000)
    if op in (4,5,6,7,1) and bt in targets:
        print("BR  %08X -> %08X  w=%08X"%(va,bt,w))
    if op in (2,3) and jt in targets:
        print("JMP %08X -> %08X  w=%08X"%(va,jt,w))
