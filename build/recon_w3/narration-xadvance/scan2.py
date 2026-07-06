import sys, struct
from capstone import *
sys.stdout.reconfigure(encoding='utf-8')
EXE="C:/programmieren/wizardrytranslation/extracted/SLPM_653.78"
D=open(EXE,'rb').read()
def v2f(va): return va-0x100000+0x80
def f2v(off): return off-0x80+0x100000
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS32+CS_MODE_LITTLE_ENDIAN); md.detail=True
lo,hi=0x300000,0x320000
for off in range(v2f(lo),v2f(hi),4):
    a=f2v(off); ins=next(md.disasm(D[off:off+4],a,1),None)
    if ins is None: continue
    s=ins.mnemonic+" "+ins.op_str
    if any(x in s for x in ["0xa0(","0xa2(","0xa3(","0xa1("]) and ins.mnemonic.startswith(("lbu","lb","lhu","lh","lw")):
        print(f"{a:08x}: {s}")
