import sys
from capstone import *
sys.stdout.reconfigure(encoding='utf-8')
EXE=r'C:\programmieren\wizardrytranslation\extracted\SLPM_653.78'
def v2f(va): return va - 0x100000 + 0x80
def f2v(off): return off + 0x100000 - 0x80
data=open(EXE,'rb').read()
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS64 | CS_MODE_LITTLE_ENDIAN)
md.detail=True
targets=[int(x,16) for x in sys.argv[1:]]
# scan whole text for jal to targets
import struct
# text region rough: VA 0x100000.. up to file end
base_va=f2v(0)
n=len(data)
for off in range(0,n-4,4):
    w=struct.unpack('<I',data[off:off+4])[0]
    op=w>>26
    if op==3: # jal
        tgt=((f2v(off)& 0xF0000000) | ((w&0x3FFFFFF)<<2))
        if tgt in targets:
            print(f"jal at {f2v(off):08X} -> {tgt:08X}")
