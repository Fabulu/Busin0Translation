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
def show(name,g):
    print("=== %s (len %d words) ==="%(name,len(g)))
    seg=[];cur=[]
    for w in g:
        if w in (0xFFFE,0xFFFF) or 0xFFC0<=w<=0xFFCF:
            print("  SEG:", " ".join("%04x"%x for x in cur), " <%04x>"%w)
            cur=[]
        else: cur.append(w)
for i in [652,916]:
    print("\n########## GROUP %d ##########"%i)
    show("PRISTINE g%d"%i,gp[i])
    show("V99 g%d"%i,gv[i])
