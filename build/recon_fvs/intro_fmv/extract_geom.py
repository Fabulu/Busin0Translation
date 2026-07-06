#!/usr/bin/env python3
"""Extract per-sprite UV+dest geometry for the R2880 prologue page (TBP0 0x310C)
from cinematic GS .zst dumps. Reports EACH sprite draw (not just band aggregate)
so single-vs-split windows and dead zones are visible."""
import sys, os, glob
import numpy as np
sys.path.insert(0, "C:/programmieren/wizardrytranslation/build/recon_v86/gs-vram-atlas")
import gs_atlas as G
sys.stdout.reconfigure(encoding='utf-8')

SNAPS = G.SNAPS
TARGET = 0x310C

def dump(ts):
    path = os.path.join(SNAPS, f"Busin 0 - Wizardry Alternative Neo_SLPM-65378_{ts}.gs.zst")
    if not os.path.exists(path):
        return None
    vram, draws, transfers, frames = G.parse_dump(path)
    sprites = []
    tbps = {}
    for d in draws:
        tbp = d['tex0']['tbp0']
        tbps[tbp] = tbps.get(tbp, 0) + 1
        if tbp != TARGET: continue
        if not d['verts']: continue
        ox, oy = d['xyoff']
        xs = [(v[0]-ox)/16.0 for v in d['verts']]
        ys = [(v[1]-oy)/16.0 for v in d['verts']]
        sx0, sy0, sx1, sy1 = min(xs), min(ys), max(xs), max(ys)
        uvs = [u for u in d['uvs'] if u and u[0] != 'st']
        if len(uvs) < 2:
            continue
        u0 = min(u[0] for u in uvs)/16.0; v0 = min(u[1] for u in uvs)/16.0
        u1 = max(u[0] for u in uvs)/16.0; v1 = max(u[1] for u in uvs)/16.0
        sprites.append(dict(sx0=sx0, sy0=sy0, sx1=sx1, sy1=sy1,
                            u0=u0, v0=v0, u1=u1, v1=v1,
                            psm=d['tex0']['psm'], tbw=d['tex0']['tbw'],
                            tw=d['tex0']['tw'], th=d['tex0']['th']))
    return sprites, tbps, draws

if __name__ == "__main__":
    tss = sys.argv[1:]
    for ts in tss:
        r = dump(ts)
        if r is None:
            print(f"{ts}: MISSING"); continue
        sprites, tbps, draws = r
        print(f"\n=== {ts}: total_draws={len(draws)}  TBP0_hist(top)="
              f"{sorted(tbps.items(), key=lambda kv:-kv[1])[:6]}")
        if not sprites:
            print("  no 0x310C sprite draws"); continue
        s0 = sprites[0]
        print(f"  TEX0: psm={s0['psm']:#x} tbw={s0['tbw']} tw={s0['tw']} th={s0['th']}")
        # sort by dest Y then dest X
        sprites.sort(key=lambda s: (round(s['sy0']), round(s['sx0'])))
        print(f"  {'#':>2} {'destX0':>6} {'destX1':>6} {'destW':>5} {'destY0':>6} {'destY1':>6} "
              f"| {'uvX0':>6} {'uvX1':>6} {'uvW':>5} {'uvY0':>5} {'uvY1':>5}")
        for i, s in enumerate(sprites):
            print(f"  {i:>2} {s['sx0']:>6.1f} {s['sx1']:>6.1f} {s['sx1']-s['sx0']:>5.1f} "
                  f"{s['sy0']:>6.1f} {s['sy1']:>6.1f} | "
                  f"{s['u0']:>6.1f} {s['u1']:>6.1f} {s['u1']-s['u0']:>5.1f} "
                  f"{s['v0']:>5.1f} {s['v1']:>5.1f}")
