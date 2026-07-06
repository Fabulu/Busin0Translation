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
vg=gwords("C:/programmieren/wizardrytranslation/build/patched_type2/1197_type02.raw")
# v96 RAM
import struct as st
ee=open(r"C:/programmieren/wizardrytranslation/build/recon_tri/extract/requestbroken__ee.bin","rb").read()
res=0x011C3D00; so=st.unpack_from("<I",ee,res+0x18)[0]; ss=st.unpack_from("<I",ee,res+0x14)[0]
s=ee[res+so:res+so+ss]; w=[st.unpack_from(">H",s,i*2)[0] for i in range(len(s)//2)]
v96g=[]; g=[]
for x in w:
    g.append(x)
    if x==0xFFFF: v96g.append(g); g=[]
print("group counts orig/v99/v96:",len(og),len(vg),len(v96g))
# group 1 comparison
print("\nGROUP 1 (structural list):")
print("  orig len=%d  v99 len=%d  v96 len=%d"%(len(og[1]),len(vg[1]),len(v96g[1])))
print("  v99==orig (PRISTINE)?", og[1]==vg[1])
print("  v96==orig?", og[1]==v96g[1])
print("  v96 has FFD2?", 0xFFD2 in v96g[1], " v99 has FFD2?", 0xFFD2 in vg[1])
# Find ALL groups that use 0x0001 separators (structural lists) in original
print("\nStructural groups (containing 0x0001 separators) in ORIGINAL:")
struct_g=[i for i,g in enumerate(og) if 0x0001 in g]
print("  indices:", struct_g[:40], "...n=",len(struct_g))
# For each structural group, is v99 pristine?
notprist=[i for i in struct_g if i<len(vg) and og[i]!=vg[i]]
print("  structural groups MODIFIED in v99 (NOT pristine):", notprist)
