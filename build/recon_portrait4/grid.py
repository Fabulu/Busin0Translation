import sys
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
import numpy as np
im=Image.open('build/recon_portrait4/extract/ladyknightnoportrait__shot.png').convert('RGB')
a=np.array(im).astype(np.int32)
lum=a.mean(axis=2)
# "But what could" line1 y~405-425. text: B u t _ w h a t _ c o u l d  = 14 cells
band=lum[404:424,60:600]
prof=(band>140).sum(axis=0)
cols=np.where(prof>0)[0]+60
print("line1 ink x range:",cols.min(),cols.max())
# If 14 cells, leftmost cell-left ~ first ink; rightmost cell ('d') right edge
# Assume cell pitch P, first cell left edge L. B at cell0, d at cell13.
# B ink starts ~L, d ink ends ~ L+13*P + glyphwidth
# Use line2 spirit: 16 cells. b starts 85. Let me fit a grid to line2.
# Known string line2 = "break the spirit": cells: b0 r1 e2 a3 k4 sp5 t6 h7 e8 sp9 s10 p11 i12 r13 i14 t15
# ink centers we found map to non-space cells. Fit center = L + cell*P + offset
centers_cells = [(88,0),(139,1),(164,2),(172,3),  # b r e a (k merged? ) 
                 ]
# Simpler: cell0 'b' center 88, cell15 't' center 439. 15 cells span = 439-88=351 => P=351/15=23.4
print("approx pitch from b(cell0=88) to t(cell15=439):", (439-88)/15)
# verify with line1 "But what could": B center? 
band1=lum[404:424,60:600]
prof1=(band1>140).sum(axis=0)
cols1=np.where(prof1>2)[0]
clusters=[]
cur=[];prev=None
for c in cols1:
    if prev is None or c-prev<=4: cur.append(c)
    else: clusters.append((cur[0]+60,cur[-1]+60)); cur=[c]
    prev=c
if cur: clusters.append((cur[0]+60,cur[-1]+60))
print("line1 clusters:",[ (c[0]+c[1])//2 for c in clusters])
