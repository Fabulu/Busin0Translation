import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
def gwords(path):
    b=open(path,"rb").read()
    so=struct.unpack_from("<I",b,0x18)[0]; ss=struct.unpack_from("<I",b,0x14)[0]
    s=b[so:so+ss]; w=[struct.unpack_from(">H",s,i*2)[0] for i in range(len(s)//2)]
    grps=[]; g=[]
    for x in w:
        g.append(x)
        if x==0xFFFF: grps.append(g); g=[]
    return grps
og=gwords("C:/programmieren/wizardrytranslation/build/recon_w2/parked/orig1197.raw")
# group 1 structure: split on 0x0001
g1=og[1]
items=[]; cur=[]
for w in g1:
    if w==0x0001:
        items.append(cur); cur=[]
    elif w==0xFFFF:
        items.append(cur); cur=[]
    else:
        cur.append(w)
print("GROUP 1: %d items (0x0001-separated)"%len(items))
for i,it in enumerate(items):
    # decode glyphs
    txt="".join((' ' if w==0 else ('|' if w==0xFFFE else (chr(w+32) if w<0x80 else '{%04X}'%w))) for w in it)
    print("  item %2d [%2d words]: %s"%(i,len(it),txt[:60]))
