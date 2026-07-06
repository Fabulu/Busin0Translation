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
# For each group, count 0x0001 separators in orig vs v99. A DIFFERENCE => structural desync.
print("Groups where 0x0001-separator COUNT differs (structural desync risk):")
bad=[]
for i in range(min(len(og),len(vg))):
    o=og[i].count(0x0001); v=vg[i].count(0x0001)
    if o!=v:
        bad.append((i,o,v))
        print("  group %d: orig %d seps -> v99 %d seps"%(i,o,v))
print("total groups with separator-count change:",len(bad))
