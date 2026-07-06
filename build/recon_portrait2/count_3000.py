import sys
sys.path.insert(0,'build/recon_v86/gs-vram-atlas')
sys.stdout.reconfigure(encoding='utf-8')
import gs_atlas as G
from collections import Counter
p=sys.argv[1]
vram,draws,transfers,frames=G.parse_dump(p)
c=Counter()
for t in transfers: c[t['dbp']]+=1
n3000=sum(1 for t in transfers if 0x2c00<=t['dbp']<=0x3c00)
# draws sampling from tbp in portrait range
tbps=Counter()
for d in draws:
    tbps[d.get('tbp')]+=1
draw3000=sum(v for k,v in tbps.items() if k is not None and 0x2c00<=k<=0x3c00)
print(f'{p.split(chr(92))[-1].split("/")[-1]}: transfers={len(transfers)} draws={len(draws)}')
print(f'  transfers into 0x2c00-0x3c00 = {n3000}')
print(f'  textured draws sampling tbp 0x2c00-0x3c00 = {draw3000}')
print('  transfer dbp histogram (portrait region):', {hex(k):v for k,v in sorted(c.items()) if 0x2c00<=k<=0x3c00})
print('  draw tbp histogram (portrait region):', {hex(k):v for k,v in sorted(tbps.items()) if k is not None and 0x2c00<=k<=0x3c00})
