import sys, struct
from capstone import *
sys.stdout.reconfigure(encoding='utf-8')
EXE="C:/programmieren/wizardrytranslation/extracted/SLPM_653.78"
D=open(EXE,'rb').read()
def f2v(off): return off-0x80+0x100000
def v2f(va): return va-0x100000+0x80
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS32+CS_MODE_LITTLE_ENDIAN)
md.detail=True
def disasm(va, n=60):
    off=v2f(va)
    for i in range(n):
        a=va+i*4
        code=D[v2f(a):v2f(a)+4]
        ins=next(md.disasm(code, a, 1), None)
        if ins is None:
            w=struct.unpack('<I',code)[0]
            print(f"{a:08x}: .word    0x{w:08x}")
        else:
            print(f"{a:08x}: {ins.mnemonic:8s} {ins.op_str}")
def word(va):
    return struct.unpack_from('<I', D, v2f(va))[0]
if __name__=="__main__":
    va=int(sys.argv[1],16)
    n=int(sys.argv[2]) if len(sys.argv)>2 else 60
    disasm(va,n)
