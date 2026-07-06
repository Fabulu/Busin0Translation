import struct, sys
sys.stdout.reconfigure(encoding='utf-8')
ee = open("C:/programmieren/wizardrytranslation/build/recon_tri2/99spacetest__ee.bin","rb").read()
print("ee size", len(ee))
# Search for XYZ values. Glyph raw X for the 99 test may differ (it's the patched/test build).
# First, search the narration dump's known X step: look for consecutive u16 X values 384 apart at same Y.
# But ee.bin is from a DIFFERENT save (99spacetest) than the 0612 gs dump. So measure from 99's own gs if available.
# 99 has no gs.bin. Use 98spacetest__gs.bin instead? That's a GS.bin (final VRAM). Not GIF.
# Strategy: search ee.bin for a run of XYZ2 packet words: low32 = (Y<<16)|X with X increasing by 0x180 (384).
# XYZF2/XYZ2 stored as 64-bit; X in [0:16], Y in [16:32].
import numpy as np
a = np.frombuffer(ee, dtype="<u4")
# find positions where a[i] and a[i+k] (some stride) have same high16 (Y) and low16 differ by 0x180
lo = a & 0xFFFF
hi = (a >> 16) & 0xFFFF
# candidate: many entries with Y around 0x80B0 (32944) won't match (that's the dump's Y). 
# Instead look generically: sequences of >=8 words where consecutive (stride s) have constant Y-hi and X-lo step 0x180.
hits=[]
N=len(a)
for s in [1,2,3,4]:
    i=0
    while i < N-8*s:
        # check run
        y0=hi[i]; x0=lo[i]
        if y0==0 or y0>0x2000:  # plausible screen Y in subpixel < 0x2000(=512px)... actually Y subpixel up to ~512*16=8192=0x2000
            i+=1; continue
        run=1
        j=i+s
        while j<N and hi[j]==y0 and (lo[j]-lo[j-s])&0xFFFF==0x180:
            run+=1; j+=s
        if run>=6:
            hits.append((i*4, s, run, x0, y0))
            i=j
        else:
            i+=1
print("candidate XYZ runs (offset, stride_words, runlen, x0, y0):")
for h in hits[:40]:
    print(f"  off=0x{h[0]:08X} stride={h[1]}w run={h[2]} x0=0x{h[3]:X} y0=0x{h[4]:X} ({h[3]/16.0:.1f},{h[4]/16.0:.1f})")
print("total hits", len(hits))
