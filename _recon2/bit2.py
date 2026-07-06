import sys, struct, re
from capstone import *
sys.stdout.reconfigure(encoding='utf-8')
EXE=r'C:\programmieren\wizardrytranslation\extracted\SLPM_653.78'
def v2f(va): return va - 0x100000 + 0x80
data=open(EXE,'rb').read()
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS64 | CS_MODE_LITTLE_ENDIAN)
# Find all sites that load 0x290(reg) then within a few insns ori/andi with 4, then store 0x290
# Simpler: dump windows around each 0x290 store in 0x2E0000-0x310000 and print 7 insns
stores=[0x2F2A9C,0x2F4810,0x2F4A38,0x2F96D4,0x2F9734,0x2F97A4,0x2F97B4,0x2F97C4,0x2F9888,
        0x2FA4F0,0x2FA504,0x2FC6D0,0x2FC6E4,0x2FD780,0x2FD794,0x2FDF2C,0x2FDF74,0x2FE0FC,
        0x2FE20C,0x2FE254,0x2FE3DC,0x2FE4FC,0x2FE54C,0x2FE6DC,0x2FE9CC,0x2FEB4C,0x2FEBA0]
for st in stores:
    win=range(st-0x10,st+8,4)
    parts=[]
    for va in win:
        ins=list(md.disasm(data[v2f(va):v2f(va)+4],va))
        if ins: parts.append(f"{ins[0].mnemonic} {ins[0].op_str}")
    j=' | '.join(parts)
    # flag ones touching bit 4
    flag=' <== BIT4' if re.search(r'(ori|andi|xori).*, 4\b', j) or ', 0x4\b' in j else ''
    print(f"{st:08X}: {j}{flag}")
