import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
# Decode GS.bin to find dialogue box sprite extents. GS dump: find sprites (PRIM)
# We use a simpler approach: the GS.bin from PCSX2 savestate. Let's find the text
# draw primitives at tbp0=0x3000 (R1188 font) and measure min/max screen X of glyphs.
# GS.bin format in PCSX2 savestate is the raw GS privileged regs + local mem (4MB).
# The first 0x2000 bytes are GS regs/internal; the 4MB VRAM follows.
# Instead, measure text extent from the eeMemory render descriptor isn't possible
# (no live pen). Fall back: measure from Screenshot.png.
from PIL import Image
img=Image.open(sys.argv[1]).convert('RGB')
W,Hh=img.size
print(f"screenshot {W}x{Hh}")
px=img.load()
# The dialogue box is a darker panel in lower portion. Find its horizontal extent
# by scanning a row in the box region for the panel border (brighter frame).
# Scan rows in lower third.
for y in range(int(Hh*0.62), int(Hh*0.95), 4):
    row=[px[x,y] for x in range(W)]
    # brightness
    br=[ (r+g+b)//3 for (r,g,b) in row ]
    # find leftmost/rightmost where brightness > 60 (text/frame vs dark bg)
    pass
# Simpler: print brightness profile of a row through the text and through frame
def profile(y):
    vals=[(r+g+b)//3 for (r,g,b) in (px[x,y] for x in range(W))]
    return vals
# Detect the box frame: the ornate frame is bright. Find columns where a vertical
# strip in the box region is consistently mid-bright (frame).
import statistics
ys=range(int(Hh*0.65),int(Hh*0.92))
colbright=[]
for x in range(W):
    v=statistics.mean((sum(px[x,y])/3) for y in ys)
    colbright.append(v)
# print where brightness jumps (box edges)
print("col brightness sampled every 8 px:")
s=""
for x in range(0,W,8):
    s+=f"{x}:{colbright[x]:.0f} "
print(s)
