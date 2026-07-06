import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
ee=open("RAMdumps/stillbad-5_eeMemory.bin","rb").read()
def u32(a): return struct.unpack_from("<I",ee,a)[0] if 0<=a<len(ee)-4 else None
def s16(a): return struct.unpack_from("<h",ee,a)[0]
def score(base):
    if base<0x100000 or base+679*50>len(ee): return -1,-1,-1
    valid=neg=garbage=0
    for i in range(679):
        pi=s16(base+i*50)
        if pi==-1: neg+=1
        elif 0<=pi<=99: valid+=1
        else: garbage+=1
    return valid,neg,garbage
seen=set(); best=[]
for gp in range(0x500000,0x579800,4):
    p1=u32(gp-26852)
    if p1 is None or not(0x100000<=p1<0x02000000): continue
    if p1 in seen: continue
    seen.add(p1)
    v,n,g=score(p1)
    if n>=550 and v>=1 and v<=40 and g<10:  # mostly inactive, 1..40 active, few garbage
        best.append((gp,p1,v,n,g))
best.sort(key=lambda x:-x[1])
for gp,p1,v,n,g in best[:25]:
    print(f"gp=0x{gp:08X} sbase=0x{p1:08X} active={v} inactive(-1)={n} garb={g}")
