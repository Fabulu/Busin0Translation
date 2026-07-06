import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools')
sys.path.insert(0,'build/recon_v86/tavern-submenu')
from psmt4_deswizzle import _psmt4_nibble_addr
from PIL import Image

def deswz(win, w, h, dbw):
    out=[[0]*w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            addr=_psmt4_nibble_addr(x,y,dbw)
            byte=win[addr>>1]
            nib=(byte>>4) if (addr&1) else (byte&0xF)
            out[y][x]=nib
    return out

d=open('build/recon_v89/tavern/R2147_v89.raw','rb').read()
win=d[0x560:0x560+32768]
px=deswz(win,256,256,128)
# grayscale by nibble value
img=Image.new('L',(256,256))
for y in range(256):
    for x in range(256):
        img.putpixel((x,y), px[y][x]*16)
img.save('build/recon_v89/tavern/r2147_win1_v89.png')
# count distinct nibble histogram
from collections import Counter
c=Counter()
for row in px:
    c.update(row)
print('nibble histogram win1 v89:', dict(c))
print('saved r2147_win1_v89.png')
