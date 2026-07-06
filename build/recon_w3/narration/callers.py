import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
data=open("extracted/SLPM_653.78",'rb').read()
def va2off(va): return va-0x100000+0x80
targets=[int(x,16) for x in sys.argv[1:]]
lo,hi=0x100000,0x500000
for va in range(lo,hi,4):
    o=va2off(va)
    if o+4>len(data): break
    w=struct.unpack('<I',data[o:o+4])[0]
    op=w>>26
    if op==3: # jal
        tgt=((va+4)&0xf0000000)|((w&0x3ffffff)<<2)
        if tgt in targets:
            print(f"0x{va:08x}: jal 0x{tgt:08x}")
