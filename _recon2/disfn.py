import sys
from capstone import *
sys.stdout.reconfigure(encoding='utf-8')
EXE=r'C:\programmieren\wizardrytranslation\extracted\SLPM_653.78'
def v2f(va): return va - 0x100000 + 0x80
data=open(EXE,'rb').read()
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS64 | CS_MODE_LITTLE_ENDIAN)
start_va = int(sys.argv[1],16)
nbytes = int(sys.argv[2],0) if len(sys.argv)>2 else 0x400
fo = v2f(start_va)
code = data[fo:fo+nbytes]
for ins in md.disasm(code, start_va):
    print(f"{ins.address:08X}: {ins.mnemonic:8s} {ins.op_str}")
