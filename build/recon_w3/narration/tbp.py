import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
data=open("extracted/SLPM_653.78",'rb').read()
def va2off(va): return va-0x100000+0x80
# find immediate 0x3000 (TBP0 for R1188) or 0x30 (tbp0 in pages? 0x3000 page) in 0x3060b0 and 0x307da0 region
for lo,hi,nm in [(0x3060b0,0x3062b0,'emit-3060b0'),(0x307da0,0x3098e0,'narr-307da0')]:
    for va in range(lo,hi,4):
        o=va2off(va); w=struct.unpack('<I',data[o:o+4])[0]
        op=w>>26; imm=w&0xffff
        if op in (0x09,0x0d,0x0f) and imm in (0x3000,0x30,0xc0,):
            print(f"{nm} 0x{va:08x}: op={op:#x} imm={imm:#x}")
