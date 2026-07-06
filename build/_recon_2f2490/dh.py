import sys
sys.stdout.reconfigure(encoding='utf-8')
from capstone import *
import struct
EXE=r"C:\programmieren\wizardrytranslation\extracted\SLPM_653.78"
VA_BASE=0xFFF80
def va2fo(va): return va-VA_BASE
exe=open(EXE,'rb').read()
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS32+CS_MODE_LITTLE_ENDIAN)
start=int(sys.argv[1],16) if len(sys.argv)>1 else 0x2F2490
maxlen=int(sys.argv[2],16) if len(sys.argv)>2 else 0x600
va=start
end=start+maxlen
sawjr=False
while va<end:
    fo=va2fo(va)
    w=exe[fo:fo+4]
    try:
        ins=next(md.disasm(w, va))
        txt=f"{ins.mnemonic:8} {ins.op_str}"
    except StopIteration:
        word=struct.unpack('<I',w)[0]
        txt=f".word 0x{word:08X}"
    print(f"{va:08X}  {w.hex()}  {txt}")
    if sawjr:
        break
    if 'jr' in txt.split()[0:1][0:1] and 'ra' in txt:
        sawjr=True
    va+=4
