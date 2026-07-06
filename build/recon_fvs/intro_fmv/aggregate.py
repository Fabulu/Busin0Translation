#!/usr/bin/env python3
"""Aggregate R2880 prologue (TBP0 0x310C) sprite draws by UV-Y band (the 24px
source line). For each band report distinct UV-X windows (detecting split rows
with dead zones) and the destination X extent. uvY band -> page line index."""
import sys, os
import numpy as np
sys.path.insert(0, "C:/programmieren/wizardrytranslation/build/recon_v86/gs-vram-atlas")
import gs_atlas as G
sys.stdout.reconfigure(encoding='utf-8')

SNAPS = G.SNAPS
TARGET = 0x310C

def collect(ts):
    path = os.path.join(SNAPS, f"Busin 0 - Wizardry Alternative Neo_SLPM-65378_{ts}.gs.zst")
    if not os.path.exists(path): return []
    vram, draws, transfers, frames = G.parse_dump(path)
    out = []
    for d in draws:
        if d['tex0']['tbp0'] != TARGET or not d['verts']: continue
        ox, oy = d['xyoff']
        xs = [(v[0]-ox)/16.0 for v in d['verts']]; ys = [(v[1]-oy)/16.0 for v in d['verts']]
        uvs = [u for u in d['uvs'] if u and u[0] != 'st']
        if len(uvs) < 2: continue
        u0 = min(u[0] for u in uvs)/16.0; v0 = min(u[1] for u in uvs)/16.0
        u1 = max(u[0] for u in uvs)/16.0; v1 = max(u[1] for u in uvs)/16.0
        out.append(dict(sx0=min(xs), sx1=max(xs), sy0=min(ys), sy1=max(ys),
                        u0=u0, u1=u1, v0=v0, v1=v1))
    return out

def line_index(v0):
    # page line tops [1,25,49,...] 24px pitch -> band = round((v0-... )/24)?
    # v0 are multiples of 24 (0,24,48,..) shifted; map to nearest 24-grid index.
    return int(round(v0 / 24.0))

if __name__ == "__main__":
    allrecs = []
    for ts in sys.argv[1:]:
        recs = collect(ts)
        allrecs.extend(recs)
    print(f"total 0x310C sprites across {len(sys.argv)-1} dumps: {len(allrecs)}")
    # group by (uvY0 band)
    bands = {}
    for r in allrecs:
        key = (round(r['v0']), round(r['v1']))
        bands.setdefault(key, []).append(r)
    print(f"{'uvY0':>5} {'uvY1':>5} {'lineIdx':>7} {'nDraw':>5} | distinct uvX windows (uvX0..uvX1) [destX0..destX1]")
    for (v0, v1) in sorted(bands):
        rs = bands[(v0, v1)]
        # distinct uvX windows
        wins = {}
        for r in rs:
            wk = (round(r['u0']), round(r['u1']))
            wins.setdefault(wk, []).append(r)
        li = line_index(v0)
        parts = []
        for wk in sorted(wins):
            ws = wins[wk]
            dx0 = min(w['sx0'] for w in ws); dx1 = max(w['sx1'] for w in ws)
            parts.append(f"uv[{wk[0]:>3}..{wk[1]:>3}]w{wk[1]-wk[0]:>3} dest[{dx0:6.1f}..{dx1:6.1f}]w{dx1-dx0:5.1f}")
        print(f"{v0:>5} {v1:>5} {li:>7} {len(rs):>5} | " + "  ||  ".join(parts))
