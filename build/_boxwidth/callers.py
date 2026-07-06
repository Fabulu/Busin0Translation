import struct,sys
EXE=r"C:\programmieren\wizardrytranslation\extracted\SLPM_653.78"
VA_BASE=0xFFF80
exe=open(EXE,'rb').read()
targets=[int(x,16) for x in sys.argv[1:]]
for fo in range(0,len(exe)-4,4):
    w=struct.unpack('<I',exe[fo:fo+4])[0]
    op=(w>>26)&0x3F
    if op in (0x02,0x03): # j/jal
        tgt=((w&0x03FFFFFF)<<2)|((fo+VA_BASE)&0xF0000000)
        if tgt in targets:
            va=fo+VA_BASE
            print(f"{va:08X} {'jal' if op==3 else 'j'} 0x{tgt:X}")
