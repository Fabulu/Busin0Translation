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
# For choice groups, the # of 0xFFFE BEFORE the first choice marker = the option-intro segment count.
# Dispatcher maps segment index -> option. Mismatch = desync.
def pre_marker_fffe(g):
    n=0
    for w in g:
        if 0xFFC0<=w<=0xFFCF: return n
        if w==0xFFFE: n+=1
    return None  # no marker
bad=[]
for i in range(min(len(gv),len(gp))):
    pmv=pre_marker_fffe(gv[i]); pmp=pre_marker_fffe(gp[i])
    if pmp is not None and pmv!=pmp:
        bad.append((i,pmp,pmv))
print("CHOICE groups with desynced pre-marker FFFE count (segment->option desync):")
for i,p,v in bad: print("  g%d: pristine=%d v99=%d"%(i,p,v))
print("total desynced choice groups:",len(bad))
