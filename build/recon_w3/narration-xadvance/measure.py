import sys, os
sys.path.insert(0, "C:/programmieren/wizardrytranslation/build/recon_v86/gs-vram-atlas")
sys.stdout.reconfigure(encoding='utf-8')
import gs_atlas as G

SNAPS = G.SNAPS
ts = "20260612061701"
path = os.path.join(SNAPS, f"Busin 0 - Wizardry Alternative Neo_SLPM-65378_{ts}.gs.zst")
vram, draws, transfers, frames = G.parse_dump(path)
print(f"draws={len(draws)} transfers={len(transfers)} frames={sorted(frames)}")

# Find R1188 font draws: TBP0=0x3000, PSMT4
font = [d for d in draws if d['tex0']['tbp0']==0x3000 and d['tex0']['psm']==0x14]
print(f"font draws (tbp0=0x3000 PSMT4) = {len(font)}")

# Also any small textured draws that look like glyph sprites (24x24 cells)
# Print each font draw's screen rect and uv
for d in font:
    ox, oy = d['xyoff']
    xs = [(v[0]-ox)/16.0 for v in d['verts']]
    ys = [(v[1]-oy)/16.0 for v in d['verts']]
    uvs = [(u[0]/16.0, u[1]/16.0) for u in d['uvs'] if u and u[0]!='st']
    print(f"seq={d['seq']} vsync={d['vsync']} x=[{min(xs):.1f},{max(xs):.1f}] y=[{min(ys):.1f},{max(ys):.1f}] uv={uvs} tbw={d['tex0']['tbw']}")
