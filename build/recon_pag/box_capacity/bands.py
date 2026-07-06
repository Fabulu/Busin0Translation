import sys
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
im=Image.open('build/recon_cine/extract/overflowbartalk__shot.png').convert('L')
w,h=im.size
px=im.load()
# count bright (text) pixels per row in left dialogue region x in [20,400]
counts=[]
for y in range(h):
    c=0
    for x in range(20,420):
        if px[x,y]>150: c+=1
    counts.append(c)
for y in range(350,h):
    print('%3d %4d %s'%(y, counts[y], '#'*(counts[y]//3)))
