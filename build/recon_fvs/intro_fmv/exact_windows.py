import sys, os
import numpy as np
sys.path.insert(0,"C:/programmieren/wizardrytranslation/build/recon_v86/gs-vram-atlas")
import gs_atlas as G
sys.stdout.reconfigure(encoding='utf-8')
TARGET=0x310C
# gather all sprites, group by (lineIdx, uvX0_grid) to get exact distinct windows
allw={}
for ts in sys.argv[1:]:
    path=os.path.join(G.SNAPS,f"Busin 0 - Wizardry Alternative Neo_SLPM-65378_{ts}.gs.zst")
    if not os.path.exists(path): continue
    vram,draws,tr,fr=G.parse_dump(path)
    for d in draws:
        if d['tex0']['tbp0']!=TARGET or not d['verts']: continue
        uvs=[u for u in d['uvs'] if u and u[0]!='st']
        if len(uvs)<2: continue
        u0=min(u[0] for u in uvs)/16.0;u1=max(u[0] for u in uvs)/16.0
        v0=min(u[1] for u in uvs)/16.0;v1=max(u[1] for u in uvs)/16.0
        li=int(round(v0/24.0))
        key=(li,round(u0),round(u1))
        allw.setdefault(key,0); allw[key]+=1
# per line, list windows sorted
lines={}
for (li,u0,u1),c in allw.items():
    lines.setdefault(li,[]).append((u0,u1,c))
for li in sorted(lines):
    ws=sorted(lines[li])
    seg=" ".join(f"[{a}..{b}]w{b-a}(x{c})" for a,b,c in ws)
    # dead zones between consecutive windows
    dz=[]
    for k in range(len(ws)-1):
        gap=ws[k+1][0]-ws[k][1]
        if gap>0: dz.append(f"{ws[k][1]}..{ws[k+1][0]}(w{gap})")
    print(f"line{li:2}: {seg}   DEADZONE: {', '.join(dz) if dz else 'none(single)'}")
