import sys, struct, re
from capstone import *
sys.stdout.reconfigure(encoding='utf-8')
EXE=r'C:\programmieren\wizardrytranslation\extracted\SLPM_653.78'
def v2f(va): return va - 0x100000 + 0x80
def f2v(off): return off + 0x100000 - 0x80
data=open(EXE,'rb').read()
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS64 | CS_MODE_LITTLE_ENDIAN)
callers=[0x2EEEB4,0x2F08AC,0x2F1D90,0x2F44A4,0x2F4670,0x2F4AE8,0x2F7E5C,0x2F8318,
         0x2FA0A0,0x2FAF00,0x2FAFE0,0x2FD008,0x2FD038,0x2FF660,0x301570,0x301988,
         0x301C50,0x305DE4,0x30B054,0x30C900]
# for each caller, decode the few insns before to find the a0 immediate set (addiu a0,zero,IMM)
for c in callers:
    a0imm=None
    for back in range(4,40,4):
        va=c-back
        ins=list(md.disasm(data[v2f(va):v2f(va)+4],va))
        if not ins: continue
        i=ins[0]
        if i.mnemonic in ('addiu','ori','li','lui') and i.op_str.startswith('$a0'):
            a0imm=i.op_str
            # if it's the delay slot too
            break
    # also check delay slot (c+4)
    dl=list(md.disasm(data[v2f(c+4):v2f(c+4)+4],c+4))
    dls=dl[0].mnemonic+' '+dl[0].op_str if dl else ''
    print(f"caller 0x{c:08X}: a0set='{a0imm}' delay='{dls}'")
