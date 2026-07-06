import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
from capstone import *
EXE=open('extracted/SLPM_653.78','rb').read()
def v2f(va): return va-0x100000+0x80
def f2v(fo): return fo-0x80+0x100000
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS64+CS_MODE_LITTLE_ENDIAN); md.skipdata=True; md.detail=True
# Look in text-render region 0x302000-0x309000 for the per-line pixel-Y multiply.
# Patterns: line*24 = (line<<1+line)<<3 ; line*12=(line*3)<<2 ; or addiu base; multiply.
# Easiest: disasm whole region and flag 'sll Rd,Rs,3' or 'sll ...,1' followed by addu (x3 then shift) -> x24/x12.
fo0=v2f(0x301E00); fo1=v2f(0x309000)
ins=list(md.disasm(EXE[fo0:fo1], 0x301E00))
# find sequences: sll a, x, 1 ; addu a, a, x ; sll a, a, K  => x * (3<<K)
for i in range(len(ins)-2):
    a,b,c=ins[i],ins[i+1],ins[i+2]
    if a.mnemonic=='sll' and b.mnemonic=='addu' and c.mnemonic=='sll':
        # parse
        try:
            ao=a.op_str.split(', '); bo=b.op_str.split(', '); co=c.op_str.split(', ')
            if ao[2]=='1' and ao[0]==bo[0] and ao[1]==bo[2] and bo[0]==co[1]:
                k=int(co[2],0); mult=3*(1<<k)
                print(f"0x{a.address:08X}: x*{mult}  [{a.mnemonic} {a.op_str} ; {b.mnemonic} {b.op_str} ; {c.mnemonic} {c.op_str}]")
        except: pass
