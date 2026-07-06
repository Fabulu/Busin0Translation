import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
data=open("extracted/SLPM_653.78",'rb').read()
def va2off(va): return va-0x100000+0x80
# Find functions that read descriptor +0x3c (lh) and have a *24 idiom nearby -> per-glyph X
lo,hi=0x301000,0x309000
words=[struct.unpack('<I',data[va2off(va):va2off(va)+4])[0] for va in range(lo,hi,4)]
def is_x24(i):
    # pattern: sll rX,rY,1 ; addu rX,rX,rY ; sll rX,rX,3   -> *24
    if i+2>=len(words): return False
    a,b,c=words[i],words[i+1],words[i+2]
    if (a>>26)==0 and (a&0x3f)==0 and ((a>>6)&0x1f)==1:
        if (b>>26)==0 and (b&0x3f) in (0x21,0x20):
            if (c>>26)==0 and (c&0x3f)==0 and ((c>>6)&0x1f)==3:
                return True
    return False
for i,va in enumerate(range(lo,hi,4)):
    if is_x24(i):
        print(f"x24 idiom @ 0x{va:08x}")
