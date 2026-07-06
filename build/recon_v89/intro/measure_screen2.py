import sys
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
import numpy as np

p="C:/Users/Fabian Trunz/OneDrive - Berner Fachhochschule/Dokumente/PCSX2/snaps/Busin 0 - Wizardry Alternative Neo_SLPM-65378_20260613165751.png"
rgb=np.array(Image.open(p).convert('RGB')).astype(int)
H,W,_=rgb.shape
# text is near-white & low saturation; movie is green/brown.
r,g,b=rgb[:,:,0],rgb[:,:,1],rgb[:,:,2]
mn=np.minimum(np.minimum(r,g),b); mx=np.maximum(np.maximum(r,g),b)
mask=(mn>130)&((mx-mn)<40)  # bright + low saturation = white text
rowsum=mask.sum(axis=1)
ys=np.where(rowsum>15)[0]
print(f'{W}x{H}, text rows: {len(ys)}')
if len(ys):
    bands=[]; s=ys[0]; prev=ys[0]
    for y in ys[1:]:
        if y-prev>8: bands.append((s,prev)); s=y
        prev=y
    bands.append((s,prev))
    for (a,bb) in bands:
        sub=mask[a:bb+1]
        cols=np.where(sub.sum(axis=0)>2)[0]
        if len(cols):
            print(f'  band y={a:3d}..{bb:3d} x={cols.min():4d}..{cols.max():4d} cx={(cols.min()+cols.max())//2} width={cols.max()-cols.min()}')
print(f'screen center x={W//2}')
