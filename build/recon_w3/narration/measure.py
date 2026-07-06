import sys, os, glob
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, "build/recon_v86/gs-vram-atlas")
import gs_atlas as G
SNAPS = "C:/Users/Fabian Trunz/OneDrive - Berner Fachhochschule/Dokumente/PCSX2/snaps"

def gchar(u, v):
    col=(u//16)//24; row=(v//16)//24; gid=row*42+col; ch=gid+32
    return chr(ch) if 32<=ch<127 else '?'

target = sys.argv[1]
f = glob.glob(os.path.join(SNAPS, f"*{target}*.gs.zst"))[0]
print("FILE", os.path.basename(f))
vram, draws, transfers, frames = G.parse_dump(f)
# only last vsync frame's R1188 T4 draws
maxv = max(d['vsync'] for d in draws) if draws else 0
rows=[]
for d in draws:
    t0=d['tex0']
    if t0['tbp0']==0x3000 and t0['psm']==0x14 and d['verts'] and d['uvs']:
        # sprite: 2 verts. coords are 12.4 fixed, xyoff subtracted
        offx,offy = d['xyoff']
        vs = d['verts']
        # take min x of the two verts
        xs=[(vx-offx)/16.0 for vx,vy in vs]
        ys=[(vy-offy)/16.0 for vx,vy in vs]
        u,v = d['uvs'][0][:2] if d['uvs'][0][0]!='st' else (0,0)
        rows.append((d['vsync'], d['seq'], min(xs), min(ys), gchar(u,v)))
# group by vsync, print last vsync
from collections import defaultdict
byv=defaultdict(list)
for r in rows: byv[r[0]].append(r)
vs_sorted=sorted(byv)
print("vsyncs with R1188T4:", vs_sorted[-5:], "total", len(vs_sorted))
v=vs_sorted[-1]
grp=sorted(byv[v], key=lambda r:r[1])
print(f"--- vsync {v}: {len(grp)} glyphs ---")
# group into lines by y
lines=defaultdict(list)
for vsy,seq,x,y,ch in grp:
    lines[round(y)].append((x,ch))
for y in sorted(lines):
    pts=sorted(lines[y])
    xs=[p[0] for p in pts]
    txt=''.join(p[1] for p in pts)
    steps=[round(xs[i+1]-xs[i],2) for i in range(len(xs)-1)]
    print(f"Y={y:6.1f} n={len(pts):2d} x0={xs[0]:6.1f} xN={xs[-1]:6.1f} txt={txt!r}")
    print(f"        steps={steps}")
