import struct,sys
sys.stdout.reconfigure(encoding='utf-8')
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN); md.skipdata=True
exe=open('extracted/SLPM_653.78','rb').read()
def f2o(va): return va-0xFFF80
def dump(va,end,tag=''):
    print(f"--- {tag} ---")
    for i in md.disasm(exe[f2o(va):f2o(end)], va):
        print(f"  {i.address:06X}: {i.mnemonic:8s} {i.op_str}")
dump(0x2F4700,0x2F47C0,'op 0x21 handler head')
