import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
def groups(path):
    b=open(path,"rb").read()
    so=struct.unpack_from("<I",b,0x18)[0]; ss=struct.unpack_from("<I",b,0x14)[0]
    sec2=b[so:so+ss]
    nw=len(sec2)//2
    words=[struct.unpack_from(">H",sec2,i*2)[0] for i in range(nw)]
    # split on FFFF
    grps=[]; cur=[]
    for w in words:
        cur.append(w)
        if w==0xFFFF:
            grps.append(cur); cur=[]
    if cur: grps.append(cur)
    return grps,words
ot="C:/programmieren/wizardrytranslation/build/recon_w2/parked/orig1197.raw"
og,ow=groups(ot)
vg,vw=groups("C:/programmieren/wizardrytranslation/build/patched_type2/1197_type02.raw")
print("orig groups:",len(og)," v99 groups:",len(vg))
def g2c(w):
    if w==0x0000: return '_'
    if w==0xFFFE: return '|'
    if w==0xFFFF: return ''
    if w<0x80: 
        c=w+32; return chr(c) if 32<=c<127 else "{%02X}"%w
    return "{%04X}"%w
# print first 8 groups both
for i in range(0,10):
    oc="".join(g2c(w) for w in og[i]) if i<len(og) else "<none>"
    vc="".join(g2c(w) for w in vg[i]) if i<len(vg) else "<none>"
    print(f"\n--- group {i} ---")
    print(f"  orig[{len(og[i]) if i<len(og) else 0}]: {og[i][:30] if i<len(og) else ''}")
    print(f"  ORIG text: {oc[:90]}")
    print(f"  V99  text: {vc[:90]}")
