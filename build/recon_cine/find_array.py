import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
ee=open("RAMdumps/stillbad-5_eeMemory.bin","rb").read()
def s16(a): return struct.unpack_from("<h",ee,a)[0]
# Search for region where, over 679 entries stride 50, field0 is mostly -1 with a few 0..99
N=679; ST=50
best=[]
# step by 2 for alignment
for base in range(0x100000, 0x02000000, 2):
    if base+N*ST>len(ee): break
    # quick reject: check first, and a sample
    neg=0; val=0; bad=0
    # sample first 100 entries fast
    ok=True
    for i in range(0,100):
        pi=s16(base+i*ST)
        if pi==-1: neg+=1
        elif 0<=pi<=99: val+=1
        else: bad+=1; 
        if bad>3: ok=False; break
    if not ok: continue
    if neg>=80 and val>=1:
        # full check
        neg=val=bad=0
        for i in range(N):
            pi=s16(base+i*ST)
            if pi==-1: neg+=1
            elif 0<=pi<=99: val+=1
            else: bad+=1
        if neg>=600 and 1<=val<=40 and bad<5:
            best.append((base,val,neg,bad))
print(f"{len(best)} regions")
for b,v,n,bad in best[:30]:
    print(f"array@0x{b:08X} active={v} neg={n} bad={bad}")
