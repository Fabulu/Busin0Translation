import sys, struct
from capstone import *
sys.stdout.reconfigure(encoding='utf-8')
EXE="C:/programmieren/wizardrytranslation/extracted/SLPM_653.78"
D=open(EXE,'rb').read()
def v2f(va): return va-0x100000+0x80
def f2v(off): return off-0x80+0x100000
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS32+CS_MODE_LITTLE_ENDIAN)
md.detail=True

# Scan a VA range for instructions referencing offset 0xA2 (lbu/lhu/sb at +0xA2)
# and for multiply-by-24 idioms (sll/sll+add giving *24, or mult with 24, or addiu 24)
lo=int(sys.argv[1],16) if len(sys.argv)>1 else 0x302000
hi=int(sys.argv[2],16) if len(sys.argv)>2 else 0x306000
mode=sys.argv[3] if len(sys.argv)>3 else "a2"

off_lo=v2f(lo); off_hi=v2f(hi)
for off in range(off_lo, off_hi, 4):
    code=D[off:off+4]
    a=f2v(off)
    ins=next(md.disasm(code,a,1),None)
    if ins is None: continue
    s=ins.mnemonic+" "+ins.op_str
    if mode=="a2":
        if "0xa2(" in s or "0xa2 (" in s:
            print(f"{a:08x}: {s}")
    elif mode=="24":
        # look for immediate 24 / 0x18 in addiu, or multiply by 24
        if ("addiu" in ins.mnemonic and (", 0x18" in s or ", 24" in s)) or \
           ("mul" in ins.mnemonic) or \
           ("0x18" == ins.op_str.split(', ')[-1] if ',' in ins.op_str else False):
            print(f"{a:08x}: {s}")
    elif mode=="li24":
        # any immediate exactly 24
        for op in ins.operands:
            if op.type==CS_OP_IMM and op.imm==24:
                print(f"{a:08x}: {s}")
                break
