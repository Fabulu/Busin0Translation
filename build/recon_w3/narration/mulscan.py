import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
data=open("extracted/SLPM_653.78",'rb').read()
def va2off(va): return va-0x100000+0x80
lo,hi=0x301000,0x309000
# find sll by 3,4 and 'mult' with small const, and load of 0x18 via lui/ori
# also: detect x*24 = (x<<3)*3 or (x<<4)+(x<<3). Scan sll sa=3 then sll sa=4 nearby, or sll3 then addu
words=[struct.unpack('<I',data[va2off(va):va2off(va)+4])[0] for va in range(lo,hi,4)]
def sll_sa(w):
    if (w>>26)==0 and (w&0x3f)==0: return (w>>6)&0x1f
    return None
for i,va in enumerate(range(lo,hi,4)):
    w=words[i]
    sa=sll_sa(w)
    if sa in (3,4,):
        rd=(w>>11)&0x1f; rt=(w>>16)&0x1f
        # check next few for addu combining
        ctx=[]
        for j in range(i+1,min(i+4,len(words))):
            ww=words[j]
            op=ww>>26
            if op==0 and (ww&0x3f) in (0x21,0x20,0x2d): ctx.append(('addu',j))
            if op==0 and (ww&0x3f)==0: ctx.append(('sll'+str((ww>>6)&0x1f),j))
        print(f"0x{va:08x}: sll rd={rd} rt={rt} sa={sa}  nxt={ctx}")
