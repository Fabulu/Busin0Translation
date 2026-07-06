import sys
from capstone import *
sys.stdout.reconfigure(encoding='utf-8')
d=open('build/recon_tri2/shady4__ee.bin','rb').read()
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
md.skipdata=True
va=int(sys.argv[1],16)
n=int(sys.argv[2]) if len(sys.argv)>2 else 90
code=d[va:va+n*4]
for ins in md.disasm(code, va):
    print(f'0x{ins.address:06X}: {ins.bytes.hex()}  {ins.mnemonic:9s} {ins.op_str}')
