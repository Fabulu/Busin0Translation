import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS64, CS_MODE_LITTLE_ENDIAN
f=open('extracted/SLPM_653.78','rb').read()
def off(va): return va-0x100000+0x80
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS64|CS_MODE_LITTLE_ENDIAN)
va=int(sys.argv[1],16); n=int(sys.argv[2]) if len(sys.argv)>2 else 80
o=off(va); code=f[o:o+n*4]
# manual stepping: decode each 4 bytes; if capstone fails, print raw
addr=va
i=0
while i < len(code):
    chunk=code[i:i+4]
    if len(chunk)<4: break
    decoded=list(md.disasm(chunk, addr))
    if decoded:
        ins=decoded[0]
        print('%08x  %08x  %-9s %s'%(addr, struct.unpack('<I',chunk)[0], ins.mnemonic, ins.op_str))
    else:
        print('%08x  %08x  .word'%(addr, struct.unpack('<I',chunk)[0]))
    addr+=4; i+=4
