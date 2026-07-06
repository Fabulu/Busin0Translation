import sys, json, os
import numpy as np
from PIL import Image
sys.stdout.reconfigure(encoding='utf-8')
BASE="C:/programmieren/wizardrytranslation"
sys.path.insert(0, os.path.join(BASE,"tools"))
from psmt4_deswizzle import deswizzle_psmt4

# Decode the v93 PATCHED page if present, else pristine, to get actual ink
PATCHED=os.path.join(BASE,"build/packdata_resources/2880_type11.raw")
SRC=PATCHED if os.path.exists(PATCHED) else os.path.join(BASE,"extracted/packdata_raw/2880_type11.raw")
OFF=1962944;SZ=131072;W=H=512;BW=512;DBW=256;BG=15
print("source:",SRC)
blob=open(SRC,'rb').read()[OFF:OFF+SZ]
lin=np.frombuffer(bytes(deswizzle_psmt4(blob,W,H,bw_psmt4=BW,dbw_ct32=DBW)),dtype=np.uint8).reshape(H,W)
ink=(BG-lin.astype(int))  # ink intensity 0..15

gs={
 0:[((0,72),(217.6,300.7)),((96,384),(82.4,436.0))],
 3:[((0,144),(177.9,340.3)),((168,456),(106.4,427.2))],
 4:[((0,192),(138.7,374.9)),((216,336),(116.0,277.0)),((336,432),(276.9,406.6))],
 14:[((0,216),(140.6,382.1)),((240,384),(140.6,302.9)),((384,464),(296.7,388.7))],
 16:[((0,192),(149.4,364.5)),((216,504),(105.4,426.1))],
}
# Render an approximate 512-wide "screen" for each special line: each uv window
# stretched to its dest rect. Show where ink lands.
SCRW=512
canvas=np.zeros((len(gs)*28, SCRW),dtype=float)
for row,(li,wins) in enumerate(sorted(gs.items())):
    band=ink[li*24:li*24+24]  # 24x512
    for (u0,u1),(d0,d1) in wins:
        sw=int(round(d1-d0))
        seg=band[:, u0:u1]  # 24 x (u1-u0)
        if seg.shape[1]==0: continue
        segimg=Image.fromarray((seg*17).clip(0,255).astype('uint8'))
        segimg=segimg.resize((max(1,sw),24), Image.BILINEAR)
        sa=np.asarray(segimg,dtype=float)/17
        x0=int(round(d0))
        for yy in range(24):
            for xx in range(sa.shape[1]):
                sx=x0+xx
                if 0<=sx<SCRW:
                    canvas[row*28+yy, sx]=max(canvas[row*28+yy,sx], sa[yy,xx])
    # report ink extent on screen for this line
    rb=canvas[row*28:row*28+24]
    cols=np.where(rb.max(axis=0)>1)[0]
    if len(cols):
        print(f"line{li:2}: screen ink X[{cols.min()}..{cols.max()}] center={(cols.min()+cols.max())//2} "
              f"(screen mid=256; gap_left={cols.min()} gap_right={SCRW-cols.max()})")

out=Image.fromarray((canvas*17).clip(0,255).astype('uint8'))
out=out.resize((SCRW,canvas.shape[0]),Image.NEAREST)
op=os.path.join(BASE,"build/recon_cine/r2880_glitch/screen_sim.png")
# invert for readability (ink dark on light)
Image.fromarray((255-(canvas*17).clip(0,255)).astype('uint8')).save(op)
print("wrote",op)
