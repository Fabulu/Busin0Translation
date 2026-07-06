import sys
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
sys.stdout.reconfigure(encoding='utf-8')
EXE="extracted/SLPM_653.78"
data=open(EXE,'rb').read()
def fo(va): return va - 0x100000 + 0x80
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 + CS_MODE_LITTLE_ENDIAN)
md.skipdata=True
def dis(va, n):
    off=fo(va); code=data[off:off+n*4]
    for ins in md.disasm(code, va):
        print("0x%08x: %-9s %s" % (ins.address, ins.mnemonic, ins.op_str))
va=int(sys.argv[1],16); n=int(sys.argv[2]) if len(sys.argv)>2 else 80
dis(va,n)
