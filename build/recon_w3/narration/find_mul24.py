#!/usr/bin/env python3
"""Find *24 idioms and explicit 24/0x18 immediates in the font/text code region."""
import sys
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
sys.stdout.reconfigure(encoding='utf-8')
d=open('extracted/SLPM_653.78','rb').read()
def v2f(va): return va-0x100000+0x80
md=Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
md.detail=False
start=0x2e0000; end=0x310000
fo=v2f(start)
code=d[fo:fo+(end-start)]
ins_list=list(md.disasm(code,start))
# index by addr
# pattern A: sll t,r,k ; addu t,t,r ; sll t,t,m  => r*( (2^k+1) * 2^m ). *24 = 3*8 -> sll1, addu, sll3
# pattern B: explicit addiu/ori reg, 0x18 then mult; or "mul reg, ?, reg" with 24
# Simpler: report any instruction with immediate 0x18 (24) AND any 'mul'/'mult' nearby
for i,ins in enumerate(ins_list):
    op=ins.op_str
    m=ins.mnemonic
    # *24 via (x*3)<<3 : look for sll Rd,Rs,1 ; addu Rd,Rd,Rs ; sll Rd,Rd,3
    if m=='sll' and op.endswith(', 1'):
        if i+2<len(ins_list):
            a=ins_list[i+1]; b=ins_list[i+2]
            if a.mnemonic=='addu' and b.mnemonic=='sll' and b.op_str.endswith(', 3'):
                print(f"{ins.address:08x}  MUL24((x*3)<<3): {ins.mnemonic} {ins.op_str} | {a.mnemonic} {a.op_str} | {b.mnemonic} {b.op_str}")
    # *24 via (x<<3)*3 alt
    if m=='sll' and op.endswith(', 3'):
        if i+2<len(ins_list):
            a=ins_list[i+1]; b=ins_list[i+2]
            if a.mnemonic=='sll' and a.op_str.endswith(', 1') and b.mnemonic=='addu':
                print(f"{ins.address:08x}  MUL24alt: {ins.mnemonic} {ins.op_str} | {a.mnemonic} {a.op_str} | {b.mnemonic} {b.op_str}")
    # explicit 0x18 immediate in addiu/ori/li used as multiplier candidate
    if m in ('addiu','ori','li','addi') and (', 0x18' in op):
        print(f"{ins.address:08x}  IMM24: {m} {op}")
    if m in ('mul','mult','multu') and 'mul' in m:
        # report mul with following/preceding 24
        print(f"{ins.address:08x}  {m} {op}")
