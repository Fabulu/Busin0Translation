import sys
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
ee=np.fromfile("RAMdumps/stillbad-5_eeMemory.bin",dtype=np.uint8)
u32=ee.view(np.uint32); u16=ee.view(np.uint16)
n=len(ee)//4
# page array: 671 entries x 8 bytes. entry=(ptr u32, refcount u16, pad u16).
# ptr field at u32 index even (0,2,4,...); refcount at u16 index (2*ptr_idx+2)... 
# Let's index by base in bytes step 8 (8-aligned typical for malloc array).
N=671
best=[]
ptrs=u32  # every 4 bytes
for base8 in range(0x100000,0x02000000,8):
    bi=base8//4
    if base8+N*8>len(ee): break
    p=u32[bi:bi+N*2:2]  # ptr fields
    rc=u16[(base8//2)+2 : (base8//2)+2 + N*4 : 4]  # refcount fields
    if len(p)<N or len(rc)<N: continue
    validptr=(p>=0x100000)&(p<0x02000000)
    zero=(p==0)
    smallrc=(rc<=200)
    nvalid=int(np.count_nonzero(validptr & smallrc))
    nzero=int(np.count_nonzero(zero))
    nbad=N-nvalid-nzero
    if nvalid>=4 and nzero>=200 and nbad<10:
        best.append((base8,nvalid,nzero,nbad))
print(len(best),"candidates")
for b,v,z,bad in best[:25]:
    print(f"0x{b:08X} valid={v} zero={z} bad={bad}")
