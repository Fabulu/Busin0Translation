import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
from capstone import *

EXE=open('extracted/SLPM_653.78','rb').read()
def v2f(va): return va-0x100000+0x80
def f2v(fo): return fo-0x80+0x100000
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS64+CS_MODE_LITTLE_ENDIAN); md.skipdata=True; md.detail=True

def rd32(va): return struct.unpack_from('<I',EXE,v2f(va))[0]

def disasm(va,n=40):
    fo=v2f(va); return list(md.disasm(EXE[fo:fo+n*4], va))

def show(va,n=40):
    for ins in disasm(va,n):
        print(f"  {ins.address:08X}: {ins.mnemonic:9s} {ins.op_str}")

if __name__=='__main__':
    va=int(sys.argv[1],16); n=int(sys.argv[2]) if len(sys.argv)>2 else 40
    show(va,n)
