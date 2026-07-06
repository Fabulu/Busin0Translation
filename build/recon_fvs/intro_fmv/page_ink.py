#!/usr/bin/env python3
"""Decode pristine R2880 sub7 page; for each 24px line band, report ink columns
and segment them into ink runs separated by >= GAP px of bg, to correlate with
the GS-observed UV windows (split rows)."""
import sys
import numpy as np
sys.path.insert(0, "C:/programmieren/wizardrytranslation/tools")
from psmt4_deswizzle import deswizzle_psmt4
sys.stdout.reconfigure(encoding='utf-8')

SRC = "C:/programmieren/wizardrytranslation/extracted/packdata_raw/2880_type11.raw"
OFF=1962944; SZ=131072; W=H=512; BW=512; DBW=256; BG=15
blob=open(SRC,'rb').read()[OFF:OFF+SZ]
lin=np.frombuffer(bytes(deswizzle_psmt4(blob,W,H,bw_psmt4=BW,dbw_ct32=DBW)),dtype=np.uint8).reshape(H,W)
ink=(lin!=BG)
# uvY bands are 0,24,48,... so line band top = i*24, height 24
GAP=10
for i in range(18):
    top=i*24
    band=ink[top:top+24]
    colmask=band.any(axis=0)
    cols=np.where(colmask)[0]
    if not len(cols):
        print(f"line{i:2} y[{top:3}..{top+24}] BLANK"); continue
    # segment into runs separated by >=GAP bg cols
    runs=[]
    start=cols[0]; prev=cols[0]
    for c in cols[1:]:
        if c-prev>GAP:
            runs.append((start,prev)); start=c
        prev=c
    runs.append((start,prev))
    rs=" ".join(f"[{a}..{b}]w{b-a+1}" for a,b in runs)
    print(f"line{i:2} y[{top:3}..{top+24}] inkX[{cols.min()}..{cols.max()}] totW={cols.max()-cols.min()+1}  runs(gap>={GAP}): {rs}")
