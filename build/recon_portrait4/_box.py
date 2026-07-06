import sys, numpy as np
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
# Detect dialogue box vertical extent: the box is a semi-opaque dark panel over the scene.
# Measure per-row mean luma in lower third; box region = darker uniform band, text=bright.
def box(path,label):
    im=np.asarray(Image.open(path).convert('L')).astype(np.float32)
    H,W=im.shape
    # use central columns to avoid frame ornaments
    col=im[:, W//4:3*W//4]
    rowmean=col.mean(axis=1)
    rowstd=col.std(axis=1)
    print(f"=== {label} ({W}x{H}) lower region rows 300-479 (mean,std) ===")
    for y in range(300,H,2):
        print(f"  y={y:3d} mean={rowmean[y]:6.1f} std={rowstd[y]:6.1f}")
box('build/recon_portrait4/extract/ladyknightnoportrait__shot.png','ladyknight')
