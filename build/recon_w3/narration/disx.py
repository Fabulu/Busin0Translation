import sys, struct
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
sys.stdout.reconfigure(encoding='utf-8')
disc=open('C:/programmieren/wizardrytranslation/extracted/SLPM_653.78','rb').read()
def v2f(va): return va-0x100000+0x80
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
def disasm(va, n=120):
    fo=v2f(va)
    for i in range(n):
        a=va+i*4
        word=disc[fo+i*4:fo+i*4+4]
        gen=md.disasm(word, a)
        ins=next(gen, None)
        if ins is None:
            w=struct.unpack('<I',word)[0]
            print(f"0x{a:08X}: .word 0x{w:08X}")
        else:
            print(f"0x{a:08X}: {ins.mnemonic:9s} {ins.op_str}")
if __name__=="__main__":
    va=int(sys.argv[1],16); n=int(sys.argv[2]) if len(sys.argv)>2 else 120
    disasm(va,n)
