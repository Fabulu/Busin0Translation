import sys
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
sys.stdout.reconfigure(encoding='utf-8')
exe=open('extracted/SLPM_653.78','rb').read()
def va2off(va): return va-0x100000+0x80
md=Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN); md.skipdata=True
def dis(va,n):
    o=va2off(va)
    for ins in md.disasm(exe[o:o+n*4],va):
        print("0x%08x: %-10s %s"%(ins.address,ins.mnemonic,ins.op_str))
print("=== 0x1A handler 0x2F4450 ===")
dis(0x2F4450,40)
