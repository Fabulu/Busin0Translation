import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
ee=open("RAMdumps/stillbad-5_eeMemory.bin","rb").read()
def u32(a): return struct.unpack_from("<I",ee,a)[0]
# page-table runtime array: 671 entries x 8 bytes = (data_ptr u32, refcount u16, pad).
# A loaded entry: data_ptr in EE heap (0x100000..0x2000000), refcount small (1..50).
# Many entries zero (unloaded). Find region with several valid (ptr, small refcount) and rest zero.
N=671; ST=8
best=[]
step=4
for base in range(0x100000,0x02000000,step):
    if base+N*ST>len(ee): break
    # quick: first entry
    p0=u32(base); 
    # sample 60 entries
    valid=zero=bad=0
    for i in range(0,80):
        p=u32(base+i*ST); rc=struct.unpack_from("<H",ee,base+i*ST+4)[0]
        if p==0 and rc==0: zero+=1
        elif 0x100000<=p<0x02000000 and 1<=rc<=200: valid+=1
        else: bad+=1
        if bad>3: break
    if bad<=3 and valid>=3 and zero>=20:
        best.append((base,valid,zero,bad))
print(len(best),"candidates")
for b,v,z,bad in best[:25]:
    print(f"0x{b:08X} valid={v} zero={z} bad={bad}")
