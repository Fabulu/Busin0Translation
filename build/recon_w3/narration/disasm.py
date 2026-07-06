import sys
sys.stdout.reconfigure(encoding='utf-8')
from capstone import *
EXE="extracted/SLPM_653.78"
data=open(EXE,'rb').read()
def va2off(va): return va-0x100000+0x80
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS32+CS_MODE_LITTLE_ENDIAN)
start=int(sys.argv[1],16); n=int(sys.argv[2]) if len(sys.argv)>2 else 40
off=va2off(start)
code=data[off:off+n*4]
va=start
for i in range(n):
    chunk=code[i*4:i*4+4]
    g=list(md.disasm(chunk, va))
    if g:
        ins=g[0]
        print(f"0x{va:08x}: {ins.bytes.hex()} {ins.mnemonic:9s} {ins.op_str}")
    else:
        import struct
        w=struct.unpack('<I',chunk)[0]
        print(f"0x{va:08x}: {chunk.hex()} .word 0x{w:08x}")
    va+=4
