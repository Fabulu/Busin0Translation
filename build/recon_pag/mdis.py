import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
from capstone import *
D=open('extracted/SLPM_653.78','rb').read()
def v2f(va): return va-0x100000+0x80
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS64|CS_MODE_LITTLE_ENDIAN)
md.detail=True
md.skipdata=True
def word(va):
    return struct.unpack('<I',D[v2f(va):v2f(va)+4])[0]
def disasm(va, n=60):
    addr=va
    end=va+n*4
    while addr < end:
        chunk=D[v2f(addr):v2f(end)]
        got=False
        for ins in md.disasm(chunk, addr):
            print('%08x  %08x  %-9s %s'%(ins.address, word(ins.address), ins.mnemonic, ins.op_str))
            addr=ins.address+ins.size
            got=True
            if addr>=end: break
        if not got:
            print('%08x  %08x  .word'%(addr,word(addr)))
            addr+=4
if __name__=='__main__':
    va=int(sys.argv[1],16)
    n=int(sys.argv[2]) if len(sys.argv)>2 else 60
    disasm(va,n)
