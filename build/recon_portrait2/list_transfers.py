import sys, struct
import numpy as np
sys.path.insert(0,'build/recon_v86/gs-vram-atlas')
sys.stdout.reconfigure(encoding='utf-8')
import zstandard as zstd, gs_atlas as G

def load_raw_gsdump_to_tmp(path):
    # parse_dump expects zstd. If raw, wrap by writing zstd? Instead replicate parse on raw.
    d=open(path,'rb').read()
    if d[:4]!=b'\x28\xb5\x2f\xfd':
        # recompress to feed parse_dump (it decompresses). Simpler: monkeypatch.
        import io
        cctx=zstd.ZstdCompressor()
        comp=cctx.compress(d)
        tmp=path+'.zst.tmp'
        open(tmp,'wb').write(comp)
        return tmp
    return path

p=load_raw_gsdump_to_tmp(sys.argv[1])
vram,draws,transfers,frames=G.parse_dump(p)
print('total transfers',len(transfers),'draws',len(draws),'frames',frames)
from collections import Counter
c=Counter()
for t in transfers:
    c[(t['dbp'],t['dpsm'],t['dbw'])]+=1
print('--- transfers by (dbp,dpsm,dbw) ---')
for (dbp,dpsm,dbw),n in sorted(c.items()):
    pn=G.PSM_NAMES.get(dpsm,hex(dpsm))
    print(f'  dbp={hex(dbp):>7} psm={pn:8} dbw={dbw} count={n}')
print('--- transfers landing at/near 0x3000 ---')
for t in transfers:
    if 0x2c00 <= t['dbp'] <= 0x3400:
        print(f"  dbp={hex(t['dbp'])} psm={G.PSM_NAMES.get(t['dpsm'],hex(t['dpsm']))} dbw={t['dbw']} rrw={t.get('rrw')} rrh={t.get('rrh')} datalen={len(t['data'])}")
