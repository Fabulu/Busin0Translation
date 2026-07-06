import sys, struct
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
ee=np.fromfile("RAMdumps/stillbad-5_eeMemory.bin",dtype=np.uint8)
# struct array signature via numpy: view field0 (int16) at stride 50 over 679 entries.
# Build for each candidate base the count of -1 and (0..678). Vectorize over bases is hard with stride.
# Instead: locate the array by the page-table runtime array which has 8-byte stride pairs.
# Faster: read whole as int16, find windows. We'll test bases mod 2 only, using strided slicing per base is O(n*679).
# Compromise: the array base is a malloc result -> typically 16-byte aligned. Scan bases step 16.
u16=ee.view(np.uint16)
n=len(ee)
ST=50; N=679
best=[]
for base in range(0x100000,0x02000000,16):
    end=base+N*ST
    if end>n: break
    # field0 int16 at base, base+50, ... -> indices base//2, +25, ...
    idx0=base//2
    f0=u16[idx0:idx0+N*25:25]  # stride 25 u16 = 50 bytes
    if len(f0)<N: continue
    # count 0xFFFF and <=678
    neg=int(np.count_nonzero(f0==0xFFFF))
    val=int(np.count_nonzero(f0<=678))
    if neg>=600 and 1<=(val-0)<=60:
        # val includes those <=678 (incl 0). active = val (excluding ffff which is 65535>678)
        active=val
        if 1<=active<=60:
            best.append((base,active,neg))
print(len(best))
for b,a,ng in best[:30]:
    print(f"0x{b:08X} active<=678={a} ffff={ng}")
