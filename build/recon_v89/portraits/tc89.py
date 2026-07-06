import sys, os, hashlib
sys.path.insert(0,'build/recon_v86/gs-vram-atlas'); import gs_atlas as G
sys.stdout.reconfigure(encoding='utf-8')

def load(name):
    try: return open(f'extracted/packdata_raw/{name}_type01.raw','rb').read()
    except FileNotFoundError: return b''

BLOBS={n:load(n) for n in ['1251','1250','1252','1253','1188','1191','1252','1240','1241','1242','1243','1244','1245']}

def match_src(data):
    if len(data)<64: return None
    needle=bytes(data[:256])
    for name,blob in BLOBS.items():
        if not blob: continue
        idx=blob.find(needle)
        if idx>=0: return (name, idx)
    return None

def analyze(ts,label):
    path=G.SNAPS+f'/Busin 0 - Wizardry Alternative Neo_SLPM-65378_{ts}.gs.zst'
    if not os.path.exists(path):
        print(f'\n##### {label} {ts}: MISSING DUMP'); return
    v,draws,transfers,frames=G.parse_dump(path)
    print(f'\n===== {label} {ts}: {len(transfers)} transfers, {len(draws)} draws =====')
    hits=[]
    for i,t in enumerate(transfers):
        big = t['rrw']*t['rrh']>= 128*128
        psm=G.PSM_NAMES.get(t['dpsm'],hex(t['dpsm']))
        src=match_src(t['data'])
        if src and src[0]=='1251': hits.append(i)
        if (src and src[0] in ('1251','1250','1252','1253')) or t['dbp']==0x3000 and big:
            flag = '  <== R1251 PORTRAIT' if (src and src[0]=='1251') else ''
            print(f'  [{i:3d}] dbp=0x{t["dbp"]:05X} dpsm={psm:8s} {t["rrw"]}x{t["rrh"]} src={src}{flag}')
    print(f'  >>> R1251-sourced transfers: {len(hits)} (indices {hits})')
    return len(hits)

for ts,lbl in sys.argv[1:] and [] or []:
    pass
pairs=[
 ('20260611203408','JP-REF Simzon(0611)'),
 ('20260613134204','v89 Simzon(narr)'),
 ('20260613134123','v89 ShadyMan(speaker)'),
 ('20260613134118','v89 ShadyMan-2'),
 ('20260613134126','v89 ShadyMan-3'),
 ('20260613134130','v89 ShadyMan-4'),
 ('20260613134133','v89 dlg'),
 ('20260613134135','v89 dlg2'),
 ('20260613134139','v89 dlg3'),
]
for ts,lbl in pairs: analyze(ts,lbl)
