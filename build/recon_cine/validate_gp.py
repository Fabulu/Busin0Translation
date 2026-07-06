import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
ee=open("RAMdumps/stillbad-5_eeMemory.bin","rb").read()
def u32(a): return struct.unpack_from("<I",ee,a)[0] if 0<=a<len(ee)-4 else None
def s16(a): 
    v=struct.unpack_from("<h",ee,a)[0]; return v
# struct array: 679 entries * 50 bytes. field0 = page_index (-1 or 0..678)
# A valid base: scan first 200 entries, count how many are -1 vs valid(0..99) vs garbage
def score(base):
    if base<0x100000 or base+679*50>len(ee): return -1,0,0
    valid=neg=garbage=0
    for i in range(679):
        pi=s16(base+i*50)
        if pi==-1: neg+=1
        elif 0<=pi<=99: valid+=1
        else: garbage+=1
    return valid,neg,garbage
cands=[0x00500958,0x005009A8,0x00502C08,0x00503628]
# Instead scan all candidate gp from prior, score struct_base
seen=set()
best=[]
for gp in range(0x500000,0x579800,4):
    p1=u32(gp-26852)
    if p1 is None or not(0x100000<=p1<0x02000000): continue
    if p1 in seen: continue
    seen.add(p1)
    v,n,g=score(p1)
    if v+n>650 and g<30 and v>=1:  # mostly -1/valid, few garbage, at least 1 active
        best.append((gp,p1,v,n,g))
best.sort(key=lambda x:-x[2])
for gp,p1,v,n,g in best[:25]:
    print(f"gp=0x{gp:08X} sbase=0x{p1:08X} valid={v} neg={n} garb={g}")
