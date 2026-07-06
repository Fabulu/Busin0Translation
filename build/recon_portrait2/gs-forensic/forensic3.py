#!/usr/bin/env python3
"""Dump raw verts/uvs of the portrait-signature draws (PRESENT) to get the true
screen rect, then in ABSENT search for ANY draw landing in that screen rect.
Also verify the dbp=0x3000 region content in ABSENT (what is there instead)."""
import sys, os, hashlib
sys.path.insert(0, 'C:/programmieren/wizardrytranslation/build/recon_v86/gs-vram-atlas')
import gs_atlas as G
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')

def analyze(ts, label, show_portrait=False):
    path = G.SNAPS + f'/Busin 0 - Wizardry Alternative Neo_SLPM-65378_{ts}.gs.zst'
    vram, draws, transfers, frames = G.parse_dump(path)
    print(f"\n==== {label} {ts} : draws={len(draws)} tx={len(transfers)} ====")
    if show_portrait:
        ps = [d for d in draws if d['tex0']['cbp']==0x3200][:6]
        for d in ps:
            print(f"  seq={d['seq']} v{d['vsync']} prim={d['prim']} xyoff={d['xyoff']}")
            print(f"     verts={d['verts']}")
            print(f"     uvs={d['uvs'][:6]}")
    # dbp=0x3000 region: read native portrait view (PSMT8 256x512) -> nonzero & md5
    base = 0x3000*256
    reg = vram[base:base+0x20000]
    print(f"  dbp=0x3000 raw bytes nonzero={int(np.count_nonzero(reg))}/{len(reg)} "
          f"md5={hashlib.md5(reg.tobytes()).hexdigest()[:12]}")
    # what textures DO sample tbp0=0x3000 here?
    from collections import Counter
    c=Counter()
    for d in draws:
        t=d['tex0']
        if t['tbp0']==0x3000:
            c[(G.PSM_NAMES.get(t['psm'],hex(t['psm'])),t['tw'],t['th'],'cbp0x%04X'%t['cbp'])]+=1
    print(f"  textures sampling TBP0=0x3000: {len(c)} distinct")
    for k,n in c.most_common(10):
        print(f"     {k} x{n}")

analyze('20260611203408','PRESENT JP-ref Simzon', show_portrait=True)
analyze('20260613170106','ABSENT v89 dialogue A')
analyze('20260613171306','ABSENT v89 dialogue B')
analyze('20260613103826','ABSENT v86 Simzon')
