import sys, os
sys.path.insert(0, "C:/programmieren/wizardrytranslation/build/recon_v86/gs-vram-atlas")
sys.stdout.reconfigure(encoding='utf-8')
import gs_atlas as G
import numpy as np

ts="20260616173046"
path=os.path.join(G.SNAPS, f"Busin 0 - Wizardry Alternative Neo_SLPM-65378_{ts}.gs.zst")
vram,draws,transfers,frames=G.parse_dump(path)

# Sample whole 1024x1024 PSMT4 atlas at TBP0=0x3000, TBW: tbw in tex0 was 16 (units of 64 px) => bw_px=16*64=1024
TBP0=0x3000; bw_px=1024
# sample index values for entire atlas is huge; sample per glyph cell
# glyph grid: 24x24 cells, 42 cols, rows up to 42
# We care about ASCII gid 0..94 -> row=gid//42, col=gid%42
def cell_idx(gid):
    row=gid//42; col=gid%42
    x0=col*24; y0=row*24
    return G.sample_pixels(vram, TBP0, bw_px, 0x14, 24,24, x0,y0)

# Determine background index. Sample a known-empty area & the space glyph(gid0)
sp=cell_idx(0)
from collections import Counter
print("space gid0 value histogram:", Counter(sp.ravel().tolist()).most_common(5))
A=cell_idx(33)  # 'A'
print("A gid33 histogram:", Counter(A.ravel().tolist()).most_common(6))
# Print A as ascii art using nonzero-index = ink
bg = Counter(sp.ravel().tolist()).most_common(1)[0][0]
print("bg index =",bg)
for y in range(24):
    print(''.join('#' if A[y,x]!=bg else '.' for x in range(24)))
