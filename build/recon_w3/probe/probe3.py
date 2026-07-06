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
    # sprite: 1 vert in verts plus implicit? verts had 1 entry. Need 2 verts for a sprite.
    vs=d['verts']; uv=d['uvs']
    if len(vs)<1 or len(uv)<2: continue
    # screen coords (subpixel /16), relative to xyoff
    # uvs: list of (u,v) in /16
    us=[u[0]/16.0 for u in uv]; vsv=[u[1]/16.0 for u in uv]
    xs=[(v[0]-ox)/16.0 for v in vs]; ys=[(v[1]-oy)/16.0 for v in vs]
    recs.append((min(xs),min(ys),min(us),min(vsv),max(us),max(vsv)))
# Hmm only 1 vert. Print raw a few
print("sample raw:")
for d in font[:6]:
    print("verts",d['verts'],"uvs",d['uvs'])
