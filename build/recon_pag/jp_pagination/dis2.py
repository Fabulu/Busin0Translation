import struct,sys
sys.stdout.reconfigure(encoding='utf-8')
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
md.skipdata=True
exe=open('extracted/SLPM_653.78','rb').read()
def f2o(va): return va-0xFFF80
def dump(va,end):
    o=f2o(va); code=exe[o:f2o(end)]
    for i in md.disasm(code, va):
        tgt=''
        if i.mnemonic in ('jal','j','bal') or i.mnemonic.startswith('b'):
            tgt=''
        print(f"  {i.address:06X}: {i.mnemonic:8s} {i.op_str}")
        va2=i.address+i.size
    # handle if disasm stalls
print("=== 0x305A60 .. 0x305C00 ===")
dump(0x305A60, 0x305C00)
