import sys, os
sys.path.insert(0, "C:/programmieren/wizardrytranslation/build/recon_v86/gs-vram-atlas")
sys.stdout.reconfigure(encoding='utf-8')
import gs_atlas as G
import numpy as np

ts="20260616173046"
path=os.path.join(G.SNAPS, f"Busin 0 - Wizardry Alternative Neo_SLPM-65378_{ts}.gs.zst")
vram,draws,transfers,frames=G.parse_dump(path)
font=[d for d in draws if d['tex0']['tbp0']==0x3000 and d['tex0']['psm']==0x14 and d['tex0']['tbw']==16]
print("narration font draws:",len(font))
d=font[0]
print("keys:",list(d.keys()))
print("tex0:",d['tex0'])
print("xyoff:",d.get('xyoff'))
print("verts:",d['verts'][:4])
print("uvs:",d['uvs'][:4])
