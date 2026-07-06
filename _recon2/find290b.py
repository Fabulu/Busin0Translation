import sys, struct, re
from capstone import *
sys.stdout.reconfigure(encoding='utf-8')
EXE=r'C:\programmieren\wizardrytranslation\extracted\SLPM_653.78'
def v2f(va): return va - 0x100000 + 0x80
data=open(EXE,'rb').read()
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS64 | CS_MODE_LITTLE_ENDIAN)
start=0x2E0000; end=0x310000
fo=v2f(start)
for va in range(start,end,4):
    o=v2f(va)
    insns=list(md.disasm(data[o:o+4], va))
    if not insns: continue
    ins=insns[0]
    if ins.mnemonic in ('lw','lh','lhu','lb','lbu','sw','sh','sb'):
        m=re.search(r'(0x[0-9a-fA-F]+)\(\$', ins.op_str)
        if m:
            disp=int(m.group(1),16)
            if 0x290<=disp<=0x29f:
                print(f"{va:08X}: {ins.mnemonic:5s} {ins.op_str}")
