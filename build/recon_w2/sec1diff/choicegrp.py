import struct,sys,os
sys.stdout.reconfigure(encoding='utf-8')
def groups(d):
    o=struct.unpack_from("<I",d,0x18)[0]; s2=d[o:]
    g=[]; cur=[]
    for i in range(0,len(s2)-1,2):
        w=(s2[i]<<8)|s2[i+1]; cur.append(w)
        if w==0xFFFF: g.append(cur); cur=[]
    if cur: g.append(cur)
    return g
v99=open('build/patched_type2/1197_type02.raw','rb').read()
pri=open('extracted/packdata_raw/1197_type02.raw','rb').read()
gv=groups(v99); gp=groups(pri)
# Find groups containing choice markers 0xFFC0-0xFFCF
def markers(g): return [w for w in g if 0xFFC0<=w<=0xFFCF]
def seg_counts(g):
    # count 0xFFFE separators (segments) and choice markers
    fe=sum(1 for w in g if w==0xFFFE)
    cm=markers(g)
    return fe,cm
print("groups with choice markers:")
for i in range(min(len(gv),len(gp))):
    mv=markers(gv[i]); mp=markers(gp[i])
    if mv or mp:
        fev,_=seg_counts(gv[i]); fep,_=seg_counts(gp[i])
        flag = "" if (mv==mp and fev==fep) else "  <<< MISMATCH"
        print("  g%d: pri markers=%s FFFE=%d | v99 markers=%s FFFE=%d%s"%(i,[hex(x) for x in mp],fep,[hex(x) for x in mv],fev,flag))
