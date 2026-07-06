import sys, numpy as np
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
def box(path,label):
    im=np.asarray(Image.open(path).convert('L')).astype(np.float32)
    H,W=im.shape
    col=im[:, W//4:3*W//4]
    rm=col.mean(axis=1)
    # find box top/bottom bright border lines in lower third
    print(f"=== {label} bright border rows (mean>55) in 355-479 ===")
    for y in range(355,H):
        if rm[y]>55: print(f"   y={y} mean={rm[y]:.0f}")
box('build/recon_portrait4/extract/nshadymanand4linesinsteadof3__shot.png','nshadyman(5line)')
box('build/recon_portrait4/extract/ladyknightnoportrait__shot.png','ladyknight(4line)')
