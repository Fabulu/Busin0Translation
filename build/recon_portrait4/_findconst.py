import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
from capstone import *
EXE=open('extracted/SLPM_653.78','rb').read()
def v2f(va): return va-0x100000+0x80
def f2v(fo): return fo-0x80+0x100000
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS64+CS_MODE_LITTLE_ENDIAN); md.skipdata=True; md.detail=True
# search for immediate 0xFFD2 / 0xFFFE / 0xFFFF compares in code segment
seg=EXE[0x80:0x80+0x3FDC80]
# Look for li/ori/sltiu with these constants. Encoded as halfword immediate in instruction low 16 bits.
import re
targets={0xFFD2:'PB 0xFFD2',0xFFFE:'LB 0xFFFE',0x0FFFF:'0xFFFF'}
hits={t:[] for t in targets}
# scan word-aligned
for fo in range(0,len(seg),4):
    w=struct.unpack_from('<I',seg,fo)[0]
    imm=w&0xFFFF
    op=(w>>26)&0x3F
    if imm in targets and op in (0x08,0x09,0x0A,0x0B,0x0C,0x0D,0x0E,0x0F):  # addi/addiu/slti/sltiu/andi/ori/xori/lui
        va=f2v(0x80+fo)
        hits[imm].append((va,op,w))
for t,name in targets.items():
    print(f"=== {name}: {len(hits[t])} hits ===")
    for va,op,w in hits[t][:40]:
        print(f"   va=0x{va:08X} op=0x{op:02X} word=0x{w:08X}")
