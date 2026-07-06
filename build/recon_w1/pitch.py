from PIL import Image
import numpy as np, sys
sys.stdout.reconfigure(encoding='utf-8')

def measure(name, ytop, ybot, thr=110, xlo=0, xhi=640):
    im=Image.open(f'build/recon_tri2/{name}__shot.png').convert('RGB')
    a=np.array(im).astype(np.int32)
    lum=a.mean(axis=2)
    prof=np.array([(lum[y,xlo:xhi]>thr).sum() for y in range(ytop,ybot)])
    # smooth
    k=np.ones(3)/3
    s=np.convolve(prof,k,mode='same')
    # find local maxima clusters: rows where s exceeds half its local span
    return prof,s,ytop

for name,(yt,yb,xlo,xhi) in {
    'shady4':(380,478,40,360),
    'BarkeepOverflow':(380,478,40,360),
}.items():
    prof,s,ytop=measure(name,yt,yb,xlo=xlo,xhi=xhi)
    print(f'=== {name} (text band x {xlo}-{xhi}) ===')
    # weighted centroid peak detection: split into bands by zero-ish gaps
    thr_line=prof.max()*0.30
    in_line=prof>thr_line
    centers=[]
    y=0
    while y<len(prof):
        if in_line[y]:
            y0=y
            while y<len(prof) and in_line[y]: y+=1
            y1=y
            ys=np.arange(y0,y1)
            w=prof[y0:y1]
            c=(ys*w).sum()/w.sum()
            centers.append(ytop+c)
        else:
            y+=1
    centers=[round(c,1) for c in centers]
    print('line centers:',centers)
    if len(centers)>=2:
        diffs=[round(centers[i+1]-centers[i],1) for i in range(len(centers)-1)]
        print('pitches:',diffs)
    print()
