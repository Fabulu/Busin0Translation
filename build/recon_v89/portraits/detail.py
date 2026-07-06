import sys, os
sys.path.insert(0,'build/recon_v86/gs-vram-atlas'); import gs_atlas as G
sys.stdout.reconfigure(encoding='utf-8')

def dump(ts,label,maxframe1=True):
    path=G.SNAPS+f'/Busin 0 - Wizardry Alternative Neo_SLPM-65378_{ts}.gs.zst'
    if not os.path.exists(path): print(f'MISSING {ts}'); return
    v,draws,transfers,frames=G.parse_dump(path)
    print(f'\n===== {label} {ts}: {len(transfers)} transfers =====')
    # print ALL transfers in first ~32 (one frame)
    for i,t in enumerate(transfers[:34]):
        psm=G.PSM_NAMES.get(t['dpsm'],hex(t['dpsm']))
        print(f'  [{i:3d}] dbp=0x{t["dbp"]:05X} dpsm={psm:8s} {t["rrw"]:>4}x{t["rrh"]:<4} dbw={t.get("dbw","?")}')

dump('20260611203408','JP-REF Simzon(0611)')
dump('20260613134123','v89 ShadyMan(speaker)')
