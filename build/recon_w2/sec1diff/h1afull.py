import sys
from capstone import Cs,CS_ARCH_MIPS,CS_MODE_MIPS32,CS_MODE_LITTLE_ENDIAN
sys.stdout.reconfigure(encoding='utf-8')
exe=open('extracted/SLPM_653.78','rb').read()
def va2off(va): return va-0x100000+0x80
md=Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN); md.skipdata=True
def dis(va,n):
    for ins in md.disasm(exe[va2off(va):va2off(va)+n*4],va):
        print("0x%08x: %-9s %s"%(ins.address,ins.mnemonic,ins.op_str))
# 0x2F15C0 / 0x2F15D0 / 0x2F15E0 - the wait helpers called by 0x1A
print("=== 0x2F15C0 (called by 0x1A, gates the wait) ===")
dis(0x2F15C0,16)
print("\n=== 0x2F2CE0 (0x1A entry helper - 'is box active'?) ===")
dis(0x2F2CE0,20)
