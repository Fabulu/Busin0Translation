import sys
sys.stdout.reconfigure(encoding='utf-8')
from capstone import *

EXE="extracted/SLPM_653.78"
data=open(EXE,"rb").read()
# EXE file = vaddr-0x100000+0x80
def f(va): return va-0x100000+0x80

md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS64|CS_MODE_LITTLE_ENDIAN)

def dis(va, n):
    off=f(va)
    code=data[off:off+n*4]
    for ins in md.disasm(code, va):
        print(f"0x{ins.address:08X}: {ins.mnemonic:8s} {ins.op_str}")

print("=== RenderAllTiles 0x30B840 (first 90 ins) ===")
dis(0x30B840, 90)
