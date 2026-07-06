import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
ee=open("RAMdumps/stillbad-5_eeMemory.bin","rb").read()
def s16(a): return struct.unpack_from("<h",ee,a)[0]
def u16(a): return struct.unpack_from("<H",ee,a)[0]
# 32-entry render list, stride 50. field0=page_index in {-1, 0..99}.
# At least a few active (0..99). Position fields (+4 Y) reasonable (-256..512).
best=[]
for base in range(0x100000,0x02000000,2):
    if base+32*50>len(ee): break
    pis=[s16(base+i*50) for i in range(32)]
    # all must be -1 or 0..678
    ok=all(p==-1 or 0<=p<=678 for p in pis)
    if not ok: continue
    active=[p for p in pis if p!=-1]
    if not (1<=len(active)<=32): continue
    # require at least 4 active and at least one in kanji page range and positions sane
    if len(active)<4: continue
    # check +4 (Y) of active entries within -300..600
    ys=[s16(base+i*50+4) for i,p in enumerate(pis) if p!=-1]
    if not all(-400<=y<=700 for y in ys): continue
    best.append((base,len(active),pis[:8]))
print(f"{len(best)} candidates")
for b,a,p in best[:30]:
    print(f"0x{b:08X} active={a} first8={p}")
