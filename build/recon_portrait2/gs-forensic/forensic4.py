#!/usr/bin/env python3
"""Final: (a) full portrait screen rect from all sub-sprite verts in PRESENT.
   (b) confirm NO draw lands in that screen region in ABSENT (sampling anything).
   (c) check v89 dialogue B (171306) parse issue (0 draws)."""
import sys, os, struct
sys.path.insert(0, 'C:/programmieren/wizardrytranslation/build/recon_v86/gs-vram-atlas')
import gs_atlas as G
import zstandard as zstd
sys.stdout.reconfigure(encoding='utf-8')

def portrait_screen_rect(ts):
    path = G.SNAPS + f'/Busin 0 - Wizardry Alternative Neo_SLPM-65378_{ts}.gs.zst'
    v,draws,tx,fr = G.parse_dump(path)
    pts=[]
    for d in draws:
        if d['tex0']['cbp']==0x3200 and d['vsync']==0:
            ox,oy=d['xyoff']
            for vv in d['verts']:
                pts.append(((vv[0]-ox)/16.0,(vv[1]-oy)/16.0))
    if pts:
        xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
        print(f"  PRESENT portrait sprite vertices (frame0): {pts}")
        print(f"  -> screen bbox X[{min(xs):.0f}..{max(xs):.0f}] Y[{min(ys):.0f}..{max(ys):.0f}]")
        return (min(xs),min(ys),max(xs),max(ys))
    return None

def draws_in_region(ts, rx0,ry0,rx1,ry1):
    path = G.SNAPS + f'/Busin 0 - Wizardry Alternative Neo_SLPM-65378_{ts}.gs.zst'
    v,draws,tx,fr = G.parse_dump(path)
    hits={}
    for d in draws:
        ox,oy=d['xyoff']
        for vv in d['verts']:
            sx=(vv[0]-ox)/16.0; sy=(vv[1]-oy)/16.0
            if rx0-8<=sx<=rx1+8 and ry0-8<=sy<=ry1+8:
                t=d['tex0']
                k=(t['tbp0'],G.PSM_NAMES.get(t['psm'],hex(t['psm'])),t['cbp'])
                hits[k]=hits.get(k,0)+1
                break
    return hits, len(draws)

print("=== PRESENT portrait screen rect ===")
rect = portrait_screen_rect('20260611203408')
# expand to expected portrait box (~128x256 sprite split into 5). Use a generous box.
RX0,RY0,RX1,RY1 = 350,360,420,520
print(f"\n=== searching ABSENT dumps for ANY draw in portrait screen region X[{RX0}..{RX1}] Y[{RY0}..{RY1}] ===")
for ts,lab in [('20260613170106','v89 dialogue A'),('20260613103826','v86 Simzon')]:
    try:
        hits,nd = draws_in_region(ts,RX0,RY0,RX1,RY1)
        print(f"  {lab} {ts}: draws={nd} draws-touching-region={sum(hits.values())}")
        for k,n in sorted(hits.items(),key=lambda kv:-kv[1])[:8]:
            print(f"      tbp=0x{k[0]:04X} {k[1]} cbp=0x{k[2]:04X} x{n}")
    except Exception as e:
        print(f"  {lab}: ERR {e}")

# check 171306 header (why 0 draws)
print("\n=== v89 dialogue B 171306 header check ===")
p='20260613171306'
path=G.SNAPS+f'/Busin 0 - Wizardry Alternative Neo_SLPM-65378_{p}.gs.zst'
data=zstd.ZstdDecompressor().decompress(open(path,'rb').read(),max_output_size=512*1024*1024)
print(f"  decompressed={len(data)} magic={data[:4]} state_version={struct.unpack_from('<I',data,8)[0]}")
