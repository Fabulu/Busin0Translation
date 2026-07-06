import sys
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
import numpy as np
im=Image.open('build/recon_portrait4/extract/ladyknightnoportrait__shot.png').convert('RGB')
a=np.array(im).astype(np.int32)
lum=a.mean(axis=2)
h,w,_=a.shape
# Box frame: the ornate ornaments are bright. Find the box top edge.
# Scan column-brightness profile in the box band to find frame verticals.
# The box spans roughly y 385-470. Find the left & right inner content boundary.
# The frame ornaments: print col profile of max-lum over box rows
band=lum[388:468,:]
colmax=band.max(axis=0)
# frame ornaments are bright tall structures at edges. Find them.
bright_cols=np.where(colmax>180)[0]
print("brightest cols (>180):", bright_cols.min(), bright_cols.max())
# left ornament cluster and right ornament cluster
# print gaps
prev=None
clusters=[]
cur=[]
for c in np.where(colmax>160)[0]:
    if prev is None or c-prev<=3:
        cur.append(c)
    else:
        clusters.append((cur[0],cur[-1]))
        cur=[c]
    prev=c
if cur: clusters.append((cur[0],cur[-1]))
print("ornament/text clusters (>160):")
for cl in clusters:
    print(f"  x[{cl[0]}-{cl[1]}] w={cl[1]-cl[0]}")
