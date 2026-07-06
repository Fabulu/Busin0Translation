import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
from capstone import *
EXE="C:/programmieren/wizardrytranslation/extracted/SLPM_653.78"
data=open(EXE,'rb').read()
def f2v(off): return off-0x80+0x100000
def v2f(va): return va-0x100000+0x80
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
md.detail=True
def dis(va, n=40):
    off=v2f(va)
    for i in range(n):
        a=va+i*4
        o=off+i*4
        word=data[o:o+4]
        got=list(md.disasm(word, a))
        if got:
            ins=got[0]
            print(f"0x{a:08X}: {word.hex():8s} {ins.mnemonic:8s} {ins.op_str}")
        else:
            w=struct.unpack('<I',word)[0]
            print(f"0x{a:08X}: {word.hex():8s} .word    0x{w:08X}")
if __name__=='__main__':
    va=int(sys.argv[1],16)
    n=int(sys.argv[2]) if len(sys.argv)>2 else 40
    dis(va,n)
