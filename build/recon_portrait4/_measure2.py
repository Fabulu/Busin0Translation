import sys, numpy as np
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image

def band_centers(path,label):
    im=np.asarray(Image.open(path).convert('L')).astype(np.float32)
    H,W=im.shape
    rs=np.array([(im[y]>140).sum() for y in range(H)])
    # smooth
    # find contiguous bands where rs> threshold
    thr=10
    bands=[]
    y=0
    while y<H:
        if rs[y]>thr:
            y0=y
            while y<H and rs[y]>thr: y+=1
            y1=y-1
            # weighted center
            ys=np.arange(y0,y1+1)
            w=rs[y0:y1+1]
            c=(ys*w).sum()/w.sum()
            bands.append((y0,y1,round(c,1),int(w.sum())))
        else:
            y+=1
    print(f"=== {label} ({W}x{H}) bands (y0,y1,center,mass) ===")
    prev=None
    for b in bands:
        d= '' if prev is None else f"  Δcenter={b[2]-prev:.1f}"
        print(f"  y={b[0]:3d}-{b[1]:3d} center={b[2]:6.1f} mass={b[3]:5d}{d}")
        prev=b[2]

for p,l in [
 ('build/recon_portrait4/extract/nshadymanand4linesinsteadof3__shot.png','nshadyman 5-line overflow'),
 ('build/recon_portrait4/extract/ladyknightnoportrait__shot.png','ladyknight 4-line'),
 ('build/recon_portrait4/extract/Toolongspaces__shot.png','narration 2-line'),
 ('build/recon_portrait4/extract/Ithinkguyshouldshowuphere__shot.png','narration'),
]:
    band_centers(p,l)
