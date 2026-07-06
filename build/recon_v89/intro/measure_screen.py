import sys
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
import numpy as np

# Frame 165751: 3 lines "Long ago...", "a war plunged the Kingdc", "into bloo"
p="C:/Users/Fabian Trunz/OneDrive - Berner Fachhochschule/Dokumente/PCSX2/snaps/Busin 0 - Wizardry Alternative Neo_SLPM-65378_20260613165751.png"
img=np.array(Image.open(p).convert('L'))
H,W=img.shape
print(f'screenshot {W}x{H}')
# text is WHITE (~255) on dark movie. Threshold high.
mask = img>200
# find rows with substantial white text
rowsum=mask.sum(axis=1)
print('rows with >5 white px:')
band=None
for y in range(H):
    if rowsum[y]>5:
        cols=np.where(mask[y])[0]
        # only print band starts
        pass
# group into line bands
ys=np.where(rowsum>8)[0]
if len(ys):
    # cluster
    bands=[]; s=ys[0]; prev=ys[0]
    for y in ys[1:]:
        if y-prev>4:
            bands.append((s,prev)); s=y
        prev=y
    bands.append((s,prev))
    for (a,b) in bands:
        sub=mask[a:b+1]
        cols=np.where(sub.any(axis=0))[0]
        if len(cols):
            print(f'  band y={a:3d}..{b:3d}  x={cols.min():3d}..{cols.max():3d}  cx={(cols.min()+cols.max())//2}')
