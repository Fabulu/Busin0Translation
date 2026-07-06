import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
DATA=open('extracted/SLPM_653.78','rb').read()
BASE_VA=0x100000; BASE_OFF=0x80
def va2off(va): return va-BASE_VA+BASE_OFF
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
start=int(sys.argv[1],16); end=int(sys.argv[2],16)
va=start
while va<end:
    off=va2off(va)
    word=DATA[off:off+4]
    got=list(md.disasm(word, va))
    if got:
        ins=got[0]
        print(f"0x{va:08x}: {struct.unpack('<I',word)[0]:08x}  {ins.mnemonic:9s} {ins.op_str}")
    else:
        print(f"0x{va:08x}: {struct.unpack('<I',word)[0]:08x}  .word")
    va+=4
