import sys
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
import numpy as np
im=Image.open('build/recon_portrait4/extract/Toolongspaces__shot.png').convert('RGB')
a=np.array(im).astype(np.int32); lum=a.mean(axis=2)
bright=lum>150
# "sound, not even" is the widest line. find text rows in center
rowsum=bright.sum(axis=1)
rows=np.where(rowsum>5)[0]
print("text rows:",rows.min() if len(rows) else None, rows.max() if len(rows) else None)
# per line, find leftmost/rightmost
for y0,y1 in [(150,168),(168,186),(186,204),(204,222)]:
    band=bright[y0:y1,:]
    cols=np.where(band.sum(axis=0)>0)[0]
    if len(cols)>3:
        print(f"  y[{y0}:{y1}] x=[{cols.min()},{cols.max()}] span={cols.max()-cols.min()} center={(cols.min()+cols.max())/2:.0f}")
# screen center is 320. A line "sound, not even" (15 chars incl spaces) spanning to ~? 
# If narration could fit 19, it'd span 19*pitch. pitch from dialogue=23.4 but narration may differ.
