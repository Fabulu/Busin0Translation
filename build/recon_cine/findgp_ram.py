import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
ee=open("RAMdumps/stillbad-5_eeMemory.bin","rb").read()
def u32(a): 
    if a<0 or a+4>len(ee): return None
    return struct.unpack_from("<I",ee,a)[0]
# gp candidate range: program 0x100000..0x579800. gp likely 0x55xxxx..0x57xxxx
# constraint: ptr at gp-26852 is a valid EE pointer (0x00100000..0x02000000), nonzero
# and ptr at gp-26856 valid too
hits=[]
for gp in range(0x500000,0x579800,4):
    p1=u32(gp-26852); p2=u32(gp-26856)
    if p1 is None or p2 is None: continue
    if 0x00100000<=p1<0x02000000 and 0x00100000<=p2<0x02000000:
        hits.append((gp,p1,p2))
print(f"{len(hits)} candidates")
for gp,p1,p2 in hits[:40]:
    print(f"gp=0x{gp:08X} struct_base=0x{p1:08X} pagetbl=0x{p2:08X}")
