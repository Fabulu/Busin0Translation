import sys, struct
from capstone import *
sys.stdout.reconfigure(encoding='utf-8')
EXE=r'C:\programmieren\wizardrytranslation\extracted\SLPM_653.78'
def v2f(va): return va - 0x100000 + 0x80
data=open(EXE,'rb').read()
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS64 | CS_MODE_LITTLE_ENDIAN)
disps=[int(x,16) for x in sys.argv[1:]]  # gp-relative negative displacements as positive hex (e.g. 6960)
# find lbu/lb/lw/lhu reg, -disp(gp)
for va in range(0x100000, 0x3B0000,4):
    o=v2f(va)
    if o+4>len(data): break
    ins=list(md.disasm(data[o:o+4],va))
    if not ins: continue
    i=ins[0]
    if i.mnemonic in ('lbu','lb','lw','lhu','lh') and '($gp)' in i.op_str:
        for d in disps:
            if f"-0x{d:x}($gp)" in i.op_str:
                print(f"READ 0x{va:08X}: {i.mnemonic} {i.op_str}")
