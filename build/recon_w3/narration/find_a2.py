#!/usr/bin/env python3
"""Find instructions that load/store byte offset 0xA2 (the cell cursor) and 0x40 (cell array)
within the font/narration code region, to locate the descriptor-draw routine."""
import sys, struct
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
sys.stdout.reconfigure(encoding='utf-8')
d=open('extracted/SLPM_653.78','rb').read()
def v2f(va): return va-0x100000+0x80
md=Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
# scan region 0x2e0000 - 0x310000 for lbu/lb/sb with disp 0xa2, and multiply-by-24 idioms
start=0x2e0000; end=0x310000
fo=v2f(start)
code=d[fo:fo+(end-start)]
for ins in md.disasm(code,start):
    op=ins.op_str
    if ins.mnemonic in ('lbu','lb','sb','lhu','lh','sh') and ('0xa2(' in op):
        print(f"{ins.address:08x}  {ins.mnemonic:6s} {op}")
