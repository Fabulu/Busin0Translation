#!/usr/bin/env python3
"""Extract textured sprite draws from a PCSX2 .gs.zst dump, focus on dialogue glyphs.
Reuse the gs_atlas parser but emit per-draw screen coords + UV so we can measure
the per-glyph X advance and per-line Y pitch AS DRAWN."""
import sys, os, struct, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r"C:\programmieren\wizardrytranslation\build\recon_v86\gs-vram-atlas")
import gs_atlas as G

SNAPS = r"C:\Users\Fabian Trunz\OneDrive - Berner Fachhochschule\Dokumente\PCSX2\snaps"

def run(ts):
    path = os.path.join(SNAPS, f"Busin 0 - Wizardry Alternative Neo_SLPM-65378_{ts}.gs.zst")
    vram, draws, transfers, frames = G.parse_dump(path)
    print(f"# {ts}: draws={len(draws)} transfers={len(transfers)} frames={sorted(frames)}")
    # Each draw: prim, tex0(tbp0,tbw,psm,tw,th,cbp), verts list, uvs list, xyoff
    # For sprite (prim==6), verts come in pairs (top-left, bottom-right).
    # Compute screen rect and uv rect per draw.
    rows = []
    for d in draws:
        t = d['tex0']
        ox, oy = d['xyoff']
        vs = d['verts']
        if len(vs) < 2:
            continue
        xs = [(v[0]-ox)/16.0 for v in vs]
        ys = [(v[1]-oy)/16.0 for v in vs]
        x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
        # uv
        uvs = [u for u in d['uvs'] if u and u[0] != 'st']
        if uvs:
            us = [u[0]/16.0 for u in uvs]
            vsv = [u[1]/16.0 for u in uvs]
            u0,u1,v0,v1 = min(us),max(us),min(vsv),max(vsv)
        else:
            u0=u1=v0=v1=-1
        rows.append({'seq':d['seq'],'vsync':d['vsync'],'prim':d['prim'],
                     'tbp':t['tbp0'],'tbw':t['tbw'],'psm':t['psm'],
                     'tw':t['tw'],'th':t['th'],'cbp':t['cbp'],
                     'x0':round(x0,1),'y0':round(y0,1),'x1':round(x1,1),'y1':round(y1,1),
                     'w':round(x1-x0,1),'h':round(y1-y0,1),
                     'u0':round(u0,1),'v0':round(v0,1),'u1':round(u1,1),'v1':round(v1,1)})
    return rows

if __name__ == "__main__":
    ts = sys.argv[1] if len(sys.argv)>1 else "20260612061801"
    rows = run(ts)
    out = os.path.join(r"C:\programmieren\wizardrytranslation\build\recon_w1\renderer", f"draws_{ts}.json")
    json.dump(rows, open(out,'w'), indent=0)
    print(f"# wrote {out} ({len(rows)} textured draws)")
    # quick tex histogram
    from collections import Counter
    c = Counter((r['tbp'],r['tbw'],r['psm'],r['tw'],r['th']) for r in rows)
    print("# tex (tbp,tbw,psm,tw,th) : count")
    for k,v in c.most_common(20):
        print(f"#   tbp=0x{k[0]:04X} tbw={k[1]} psm=0x{k[2]:02X} {k[3]}x{k[4]} : {v}")
