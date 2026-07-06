import sys
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
import numpy as np
im=Image.open('build/recon_portrait4/extract/ladyknightnoportrait__shot.png').convert('RGB')
a=np.array(im).astype(np.int32)
lum=a.mean(axis=2)
# line2 = "break the spirit" at y~425-445
band=lum[424:446,60:600]
prof=(band>140).sum(axis=0)
# find glyph ink columns -> cluster into glyphs
cols=np.where(prof>0)[0]
clusters=[]
cur=[]
prev=None
for c in cols:
    if prev is None or c-prev<=4:
        cur.append(c)
    else:
        clusters.append((cur[0]+60,cur[-1]+60))
        cur=[c]
    prev=c
if cur: clusters.append((cur[0]+60,cur[-1]+60))
print("line2 'break the spirit' glyph ink clusters:")
centers=[]
for cl in clusters:
    ctr=(cl[0]+cl[1])/2
    centers.append(ctr)
    print(f"  x[{cl[0]}-{cl[1]}] center={ctr:.0f}")
# Char positions in "break the spirit": b r e a k _ t h e _ s p i r i t
# spaces produce gaps. compute advance between consecutive letters
print("\ndeltas between consecutive ink-cluster centers:")
for i in range(1,len(centers)):
    print(f"  {centers[i]-centers[i-1]:.1f}")
