import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
EXE='extracted/SLPM_653.78'
BASE=0x100000; FOFF=0x80
def v2f(v): return v-BASE+FOFF
data=open(EXE,'rb').read()
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
def dis_full(va, n=60):
    off=v2f(va); code=data[off:off+n*4]
    for i in range(0,len(code),4):
        w=struct.unpack_from('<I',code,i)[0]
        addr=va+i
        out=list(md.disasm(code[i:i+4], addr, count=1))
        if out:
            ins=out[0]
            print("0x%08x: %08x  %-9s %s"%(addr,w,ins.mnemonic,ins.op_str))
        else:
            print("0x%08x: %08x  .word"%(addr,w))
if __name__=='__main__':
    va=int(sys.argv[1],16); n=int(sys.argv[2]) if len(sys.argv)>2 else 60
    dis_full(va,n)
