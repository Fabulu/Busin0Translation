import sys, os
sys.path.insert(0, "C:/programmieren/wizardrytranslation/build/recon_v86/gs-vram-atlas")
sys.stdout.reconfigure(encoding='utf-8')
import gs_atlas as G
import numpy as np

ts="20260616173046"
path=os.path.join(G.SNAPS, f"Busin 0 - Wizardry Alternative Neo_SLPM-65378_{ts}.gs.zst")
vram,draws,transfers,frames=G.parse_dump(path)
font=[d for d in draws if d['tex0']['tbp0']==0x3000 and d['tex0']['psm']==0x14 and d['tex0']['tbw']==16]

recs=[]
for d in font:
    ox,oy=d['xyoff']
    vx=d['verts'][0][0]; vy=d['verts'][0][1]
    sx=(vx-ox)/16.0; sy=(vy-oy)/16.0
    uv=d['uvs']
    u0=min(uv[0][0],uv[1][0])/16.0; v0=min(uv[0][1],uv[1][1])/16.0
    u1=max(uv[0][0],uv[1][0])/16.0; v1=max(uv[0][1],uv[1][1])/16.0
    col=round(u0/24.0); row=round(v0/24.0)
    gid=row*42+col
    ch = chr(gid+32) if 0<=gid<=94 else '?'
    recs.append((d['seq'],sx,sy,u0,v0,u1-u0,v1-v0,col,row,gid,ch))

# group by line (sy) and sort by seq
recs.sort(key=lambda r:r[0])
# print lines: group by sy rounded
from collections import defaultdict
lines=defaultdict(list)
for r in recs:
    lines[round(r[2])].append(r)
for sy in sorted(lines):
    rr=sorted(lines[sy], key=lambda r:r[1])
    txt=''.join(r[10] for r in rr)
    print(f"y={sy}: '{txt}'")
