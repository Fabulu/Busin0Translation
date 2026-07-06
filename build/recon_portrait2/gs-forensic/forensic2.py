#!/usr/bin/env python3
"""Refined portrait forensic. Focus on the UNIQUE portrait signature:
   a textured draw sampling TBP0=0x3000 with CBP=0x3200 (the R1251 portrait CLUT),
   PSM PSMT8, 256x512. This CLUT is unique to the portrait. Track draw rects
   properly (sprite = 2 verts -> bounding box) and correlate to transfers by seq.
"""
import sys, os, hashlib
sys.path.insert(0, 'C:/programmieren/wizardrytranslation/build/recon_v86/gs-vram-atlas')
import gs_atlas as G
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')

RAW = 'C:/programmieren/wizardrytranslation/extracted/packdata_raw'
R1251 = open(f'{RAW}/1251_type01.raw', 'rb').read()

def src1251(data):
    if len(data) < 256: return None
    return R1251.find(bytes(data[:256]))

def rect_of(d):
    t = d['tex0']; ox, oy = d['xyoff']
    xs = [(v[0]-ox)/16.0 for v in d['verts']]
    ys = [(v[1]-oy)/16.0 for v in d['verts']]
    if not xs: return None
    return (round(min(xs)), round(min(ys)), round(max(xs)), round(max(ys)))

def analyze(ts, label):
    path = G.SNAPS + f'/Busin 0 - Wizardry Alternative Neo_SLPM-65378_{ts}.gs.zst'
    if not os.path.exists(path):
        print(f"\n##### MISSING {label} {ts}"); return
    vram, draws, transfers, frames = G.parse_dump(path)
    print(f"\n================ {label}  {ts} ================")
    # R1251 transfers w/ vsync
    r1251 = [(i,t['vsync'],t['dbp'],t['rrw'],t['rrh']) for i,t in enumerate(transfers)
             if (src1251(t['data']) or -1) >= 0]
    print(f"  R1251 transfers: {len(r1251)} -> {[(i,'v%d'%v,'0x%04X'%dbp,'%dx%d'%(w,h)) for i,v,dbp,w,h in r1251]}")

    # PORTRAIT DRAW signature: samples TBP0=0x3000 AND CBP=0x3200 (portrait CLUT)
    portr_draws = [d for d in draws if d['tex0']['tbp0']==0x3000 and d['tex0']['cbp']==0x3200]
    # broader: any draw whose CBP==0x3200 regardless of tbp
    cbp3200 = [d for d in draws if d['tex0']['cbp']==0x3200]
    print(f"  DRAWS sampling TBP0=0x3000 & CBP=0x3200 (portrait sig): {len(portr_draws)}")
    print(f"  DRAWS with CBP=0x3200 (any tbp): {len(cbp3200)}")
    # show distinct (psm,tw,th,tbp,rect,vsync) for portrait-sig draws
    seen = {}
    for d in cbp3200:
        t=d['tex0']; r=rect_of(d)
        k=(t['tbp0'],G.PSM_NAMES.get(t['psm'],hex(t['psm'])),t['tw'],t['th'],r,d['vsync'])
        seen[k]=seen.get(k,0)+1
    for (tbp,psm,tw,th,r,vs),c in sorted(seen.items()):
        print(f"       tbp=0x{tbp:04X} {psm} {tw}x{th} vsync={vs} rect={r} x{c}")

    # Also: any sprite draw to the portrait SCREEN rect. From PRESENT we will learn the rect.
    # Collect all sprite (prim==6) draws with non-degenerate bbox, tally rects.
    rects={}
    for d in draws:
        if d['prim'] not in (6,):  # sprite
            pass
        r=rect_of(d)
        if not r: continue
        w=r[2]-r[0]; h=r[3]-r[1]
        if w<=0 or h<=0: continue
        if 50<=w<=180 and 120<=h<=300:
            e=rects.setdefault(r,{'c':0,'tex':set()})
            e['c']+=1
            t=d['tex0']
            e['tex'].add((t['tbp0'],G.PSM_NAMES.get(t['psm'],hex(t['psm'])),t['cbp']))
    print(f"  portrait-sized NON-degenerate sprite rects: {len(rects)}")
    for r,e in sorted(rects.items(),key=lambda kv:-kv[1]['c'])[:8]:
        texs=", ".join(f"0x{a:04X}/{p}/cbp0x{c:04X}" for a,p,c in sorted(e['tex']))
        print(f"       rect={r} (w={r[2]-r[0]} h={r[3]-r[1]}) count={e['c']} tex=[{texs}]")

for ts,lab in [('20260611203408','PRESENT JP-ref Simzon'),
               ('20260613170106','ABSENT v89 dialogue A'),
               ('20260613171306','ABSENT v89 dialogue B'),
               ('20260613103826','ABSENT v86 Simzon')]:
    analyze(ts,lab)
