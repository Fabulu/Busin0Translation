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
    return grps,w
vg,vw=gwords("C:/programmieren/wizardrytranslation/build/patched_type2/1197_type02.raw")
og,ow=gwords("C:/programmieren/wizardrytranslation/build/recon_w2/parked/orig1197.raw")
# find FFD2 in v99
idxs=[i for i,x in enumerate(vw) if x==0xFFD2]
print("FFD2 word indices in v99:",idxs)
# which group
gi=0; gstart=[0]
for i,x in enumerate(vw):
    if x==0xFFFF and i+1<len(vw): gstart.append(i+1)
import bisect
for ix in idxs:
    g=bisect.bisect_right(gstart,ix)-1
    print("FFD2 at word %d -> group %d"%(ix,g))
    # decode group g v99 and orig
    def dec(grp):
        return "".join((' ' if w==0 else ('|' if w==0xFFFE else ('#C#' if w==0xFFD2 else (chr(w+32) if w<0x80 else '{%04X}'%w)))) for w in grp)
    print("  v99 g%d (len %d): %s"%(g,len(vg[g]),dec(vg[g])[:120]))
    if g<len(og): print("  orig g%d (len %d): same-as-orig? %s"%(g,len(og[g]), og[g]==vg[g]))
# Is this FFD2 present in ORIGINAL too?
oidxs=[i for i,x in enumerate(ow) if x==0xFFD2]
print("\nFFD2 in ORIGINAL?:", len(oidxs), "(if >0, FFD2 is a legit original control code)")
