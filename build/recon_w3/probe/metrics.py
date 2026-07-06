import sys, os
sys.path.insert(0, "C:/programmieren/wizardrytranslation/build/recon_v86/gs-vram-atlas")
sys.stdout.reconfigure(encoding='utf-8')
import gs_atlas as G
import numpy as np
ts="20260616173046"
path=os.path.join(G.SNAPS, f"Busin 0 - Wizardry Alternative Neo_SLPM-65378_{ts}.gs.zst")
vram,draws,transfers,frames=G.parse_dump(path)
TBP0=0x3000; bw_px=1024
def cell(gid):
    row=gid//42; col=gid%42
    return G.sample_pixels(vram, TBP0, bw_px, 0x14, 24,24, col*24, row*24)
rows=[]
for gid in range(95):
    c=cell(gid)
    ink = c!=0
    cols_with_ink = np.where(ink.any(axis=0))[0]
    ch=chr(gid+32)
    if len(cols_with_ink)==0:
        rows.append((gid,ch,-1,-1,0))
    else:
        il=int(cols_with_ink.min()); ir=int(cols_with_ink.max())
        rows.append((gid,ch,il,ir,ir-il+1))
print("gid char ink_left ink_right ink_width")
for r in rows:
    print("%3d %r  L=%2d R=%2d W=%2d"%(r[0],r[1],r[2],r[3],r[4]))
# save
import json
json.dump(rows, open("C:/programmieren/wizardrytranslation/build/recon_w3/probe/metrics.json","w"))
