import sys, os, glob, re
sys.path.insert(0,'build/recon_v86/gs-vram-atlas'); import gs_atlas as G
sys.stdout.reconfigure(encoding='utf-8')

R1251=open('extracted/packdata_raw/1251_type01.raw','rb').read()
needle=R1251[0xA1:0xA1+256]  # documented portrait payload start

def scan(ts):
    path=G.SNAPS+f'/Busin 0 - Wizardry Alternative Neo_SLPM-65378_{ts}.gs.zst'
    try:
        v,draws,transfers,frames=G.parse_dump(path)
    except Exception as e:
        return None
    hits=[]
    box64=0
    for i,t in enumerate(transfers):
        d=t['data']
        if len(d)>=256 and bytes(d[:256])==bytes(needle):
            hits.append((t['rrw'],t['rrh']))
        if t['dbp']==0x3000 and t['rrw']==256 and t['rrh']==64:
            box64+=1
    return (len(transfers),len(hits),hits[:2],box64)

# all Jun13 13:xx dumps (the v89 playtest session)
allz=sorted(glob.glob(G.SNAPS+'/*SLPM-65378_20260613*.gs.zst'))
print(f'Total Jun13 dumps: {len(allz)}')
for p in allz:
    ts=re.search(r'_(\d{14})\.gs\.zst',p).group(1)
    # focus on 13:33-13:45 (the dialogue session)
    if not (ts.startswith('20260613133') or ts.startswith('20260613134')): continue
    r=scan(ts)
    if r is None: continue
    nt,nh,szs,box=r
    mark = ' <== PORTRAIT' if nh>0 else (' (namebox256x64)' if box>0 else '')
    print(f'  {ts}: xfr={nt:3d} R1251hits={nh} sizes={szs} box256x64={box}{mark}')
