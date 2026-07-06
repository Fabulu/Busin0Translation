import struct,sys,os
sys.stdout.reconfigure(encoding='utf-8')
# Parse sec2 into groups separated by 0xFFFF. Compare per-group 0xFFD2 presence v99 vs pristine.
def groups(d):
    o=struct.unpack_from("<I",d,0x18)[0]; s2=d[o:]
    g=[]; cur=[]
    for i in range(0,len(s2)-1,2):
        w=(s2[i]<<8)|s2[i+1]
        cur.append(w)
        if w==0xFFFF:
            g.append(cur); cur=[]
    if cur: g.append(cur)
    return g
v99=open('build/patched_type2/1197_type02.raw','rb').read()
pri=open('extracted/packdata_raw/1197_type02.raw','rb').read()
gv=groups(v99); gp=groups(pri)
print("v99 groups=%d pri groups=%d"%(len(gv),len(gp)))
# count groups with 0xFFD2
def hasffd2(g): return sum(1 for x in g if x==0xFFD2)
pv=[i for i,g in enumerate(gv) if 0xFFD2 in g]
pp=[i for i,g in enumerate(gp) if 0xFFD2 in g]
print("v99 groups w/ FFD2:",pv)
print("pri groups w/ FFD2 (count):",len(pp),"first 20:",pp[:20])
# For the pristine groups with FFD2, what's the v99 equivalent group's FFD2 count?
print("\nper-group FFD2: pri vs v99 (groups where they differ, first 25):")
diff=0
for i in range(min(len(gv),len(gp))):
    a=hasffd2(gv[i]); b=hasffd2(gp[i])
    if a!=b:
        diff+=1
        if diff<=25: print("  group %d: pri_ffd2=%d v99_ffd2=%d  pri_len=%d v99_len=%d"%(i,b,a,len(gp[i]),len(gv[i])))
print("total groups with differing FFD2 count:",diff)
