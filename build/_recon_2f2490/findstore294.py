import struct
EXE=r"C:\programmieren\wizardrytranslation\extracted\SLPM_653.78"
VA_BASE=0xFFF80
exe=open(EXE,'rb').read()
# find sh rt,0x294(rs) : op=0x29 (sh), imm=0x294
# also lh 0x294 (op=0x21? no, lh=0x21). We want stores: sh op=0x29
n=len(exe)//4
for i in range(n):
    w=struct.unpack('<I',exe[i*4:i*4+4])[0]
    va=VA_BASE+i*4
    op=(w>>26)&0x3F; rs=(w>>21)&0x1F; rt=(w>>16)&0x1F
    imm=w&0xFFFF; s=imm-0x10000 if imm&0x8000 else imm
    if op==0x29 and s==0x294:  # sh ...,0x294(rs)
        print(f"{va:08X}  sh r{rt}, 0x294(r{rs})")
