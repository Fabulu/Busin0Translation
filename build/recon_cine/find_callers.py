import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
exe=open("extracted/SLPM_653.78","rb").read()
def f(va): return va-0x100000+0x80
# find JAL to 0x30B120 (FontDispSet) and writes to gp-0x68D0 (glyph_id) / gp-0x68C8 / gp-0x68CC
TARGET=0x30B120
jaltgt=(0x30B120>>2)&0x3FFFFFF
g68D0=(-0x68D0)&0xFFFF
g68C8=(-0x68C8)&0xFFFF
g68CC=(-0x68CC)&0xFFFF
jals=[]; w68D0=[]; w68C8=[]
for off in range(0x80,len(exe)-4,4):
    w=struct.unpack_from("<I",exe,off)[0]
    va=0x100000+off-0x80
    op=w>>26
    if op==3 and (w&0x3FFFFFF)==jaltgt: jals.append(va)
    if op in (0x29,) and ((w>>21)&31)==28:  # sh to gp
        imm=w&0xFFFF
        if imm==g68D0: w68D0.append(va)
        if imm==g68C8: w68C8.append(va)
print("JAL FontDispSet(0x30B120):"); [print(f"  0x{v:08X}") for v in jals]
print("sh -> gp-0x68D0 (glyph_id):"); [print(f"  0x{v:08X}") for v in w68D0]
print("sh -> gp-0x68C8 (mode):"); [print(f"  0x{v:08X}") for v in w68C8]
