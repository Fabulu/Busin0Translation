import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
import rabbitizer
exe=open("extracted/SLPM_653.78","rb").read()
def f(va): return va-0x100000+0x80
# scan whole exe; find 'sh $x, 0($y)' instructions; report context. Also find funcs that load gp-0x68E4 then sh 0.
# imm for -0x68E4 = 0x971C
TARG=0x971C
hits=[]
for off in range(0x80,len(exe)-4,4):
    w=struct.unpack_from("<I",exe,off)[0]
    op=w>>26; rs=(w>>21)&31; imm=w&0xFFFF
    if op==0x23 and rs==28 and imm==TARG:  # lw from gp-0x68E4 (struct base)
        va=0x100000+off-0x80
        hits.append(va)
print("lw struct_base (gp-0x68E4) sites:")
for va in hits: print(f"  0x{va:08X}")
