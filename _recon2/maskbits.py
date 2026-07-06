import sys, struct
from capstone import *
sys.stdout.reconfigure(encoding='utf-8')
EXE=r'C:\programmieren\wizardrytranslation\extracted\SLPM_653.78'
def v2f(va): return va - 0x100000 + 0x80
data=open(EXE,'rb').read()
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS64 | CS_MODE_LITTLE_ENDIAN)
callers=[0x2EEEB4,0x2F08AC,0x2F1D90,0x2F44A4,0x2F4670,0x2F4AE8,0x2F7E5C,0x2F8318,
         0x2FA0A0,0x2FAF00,0x2FAFE0,0x2FD008,0x2FD038,0x2FF660,0x301570,0x301988,
         0x301C50,0x305DE4,0x30B054,0x30C900]
# emulate a0 across ~8 insns before the jal (lui/ori/addiu on a0)
for c in callers:
    a0=None; hi=0
    # include delay slot at c+4 (executes before jal target)
    seq=[c-16,c-12,c-8,c-4,c+4]
    for va in seq:
        ins=list(md.disasm(data[v2f(va):v2f(va)+4],va))
        if not ins: continue
        i=ins[0]
        if not i.op_str.startswith('$a0'): continue
        if i.mnemonic=='lui':
            hi=int(i.op_str.split(',')[1],16)<<16; a0=hi
        elif i.mnemonic=='ori':
            imm=int(i.op_str.split(',')[-1],16); a0=(a0 or 0)|imm
        elif i.mnemonic=='addiu':
            parts=i.op_str.split(',')
            imm=int(parts[-1],16)
            if '$a0, $a0' in i.op_str: a0=(a0 or 0)+imm
            else: a0=imm
    print(f"caller 0x{c:08X}: posts mask=0x{(a0 or 0):X}")
