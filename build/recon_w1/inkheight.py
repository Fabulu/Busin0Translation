from PIL import Image
import numpy as np, sys
sys.stdout.reconfigure(encoding='utf-8')

# Measure ink height per line in shady4. Lines centered ~392,418,444,469 (screen).
# For each line, find the vertical extent of bright glyph pixels.
im=Image.open('build/recon_tri2/shady4__shot.png').convert('RGB')
a=np.array(im).astype(np.int32)
lum=a.mean(axis=2)
thr=120
xlo,xhi=45,360
for cy in [392,418,444,469]:
    rows=range(cy-13,cy+13)
    cnts=[(lum[y,xlo:xhi]>thr).sum() for y in rows]
    ys=[y for y in rows]
    active=[y for y,c in zip(ys,cnts) if c>4]
    if active:
        top,bot=min(active),max(active)
        print(f'line cy~{cy}: ink rows {top}..{bot} height_screen={bot-top+1} height_internal={(bot-top+1)*448/480:.1f}')
    # detail profile
    #for y,c in zip(ys,cnts): print(' ',y,c)
