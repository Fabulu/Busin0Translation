import sys
sys.path.insert(0,'build/recon_v86/gs-vram-atlas')
sys.stdout.reconfigure(encoding='utf-8')
import gs_atlas as G
p=sys.argv[1]
vram,draws,transfers,frames=G.parse_dump(p)
print(p.split('/')[-1])
seen={}
for i,t in enumerate(transfers):
    if t['dbp'] in (0x3000,0x3200,0x3002):
        key=(t['dbp'],t['dpsm'],t['dbw'],t.get('rrw'),t.get('rrh'),len(t['data']))
        seen.setdefault(key,0); seen[key]+=1
for k,v in sorted(seen.items()):
    dbp,dpsm,dbw,rrw,rrh,dl=k
    print(f'  dbp={hex(dbp)} psm={G.PSM_NAMES.get(dpsm,hex(dpsm))} dbw={dbw} rrw={rrw} rrh={rrh} datalen={dl} count={v}')
