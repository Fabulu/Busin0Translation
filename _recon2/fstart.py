import sys, struct
from capstone import *
sys.stdout.reconfigure(encoding='utf-8')
EXE=r'C:\programmieren\wizardrytranslation\extracted\SLPM_653.78'
def v2f(va): return va - 0x100000 + 0x80
data=open(EXE,'rb').read()
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS64 | CS_MODE_LITTLE_ENDIAN)
target=int(sys.argv[1],16)
# scan backward for 'addiu sp,sp,-imm' as prologue
va=target
for _ in range(2000):
    va-=4
    ins=list(md.disasm(data[v2f(va):v2f(va)+4],va))
    if ins and ins[0].mnemonic=='addiu' and ins[0].op_str.startswith('$sp, $sp, -'):
        print(f"function start: 0x{va:08X}  ({ins[0].op_str})")
        break
