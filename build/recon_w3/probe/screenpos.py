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
    ox,oy=d['xyoff']; vx=d['verts'][0][0]; vy=d['verts'][0][1]
    sx=(vx-ox)/16.0; sy=(vy-oy)/16.0
    uv=d['uvs']; u0=min(uv[0][0],uv[1][0])/16.0; v0=min(uv[0][1],uv[1][1])/16.0
    col=round(u0/24.0); row=round(v0/24.0); gid=row*42+col
    ch=chr(gid+32) if 0<=gid<=94 else '?'
    recs.append((d['seq'],sx,sy,gid,ch))
recs.sort(key=lambda r:r[0])
# Line 1 (y~199). The 4x duplication: dedup by (sx,gid)
seen=set(); uniq=[]
for r in recs:
    if round(r[2])!=199: continue
    k=(round(r[1]),r[3])
    if k in seen: continue
    seen.add(k); uniq.append(r)
uniq.sort(key=lambda r:r[1])
print("Line1 unique glyph draws (screen x is bottom-right vertex):")
prev=None
for r in uniq:
    d = r[1]-prev if prev is not None else 0
    print("  x=%.1f gid=%2d '%s'  delta_from_prev=%.1f"%(r[1],r[3],r[4],d))
    prev=r[1]
