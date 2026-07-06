import sys, os
sys.path.insert(0, "C:/programmieren/wizardrytranslation/build/recon_v86/gs-vram-atlas")
sys.stdout.reconfigure(encoding='utf-8')
import gs_atlas as G
import numpy as np

ts="20260616173046"
path=os.path.join(G.SNAPS, f"Busin 0 - Wizardry Alternative Neo_SLPM-65378_{ts}.gs.zst")
vram,draws,transfers,frames=G.parse_dump(path)
print("draws",len(draws),"transfers",len(transfers))
font=[d for d in draws if d['tex0']['tbp0']==0x3000 and d['tex0']['psm']==0x14]
print("font draws tbp0=0x3000 PSMT4:",len(font))
# also list distinct tbp0/psm to find the font if not exactly 0x3000/0x14
from collections import Counter
c=Counter((d['tex0']['tbp0'],d['tex0']['psm'],d['tex0']['tbw'],d['tex0']['cbp'],d['tex0']['cpsm']) for d in draws)
for k,v in c.most_common(20):
    print("tbp0=0x%x psm=0x%x tbw=%d cbp=0x%x cpsm=%d  count=%d"%(k[0],k[1],k[2],k[3],k[4],v))
