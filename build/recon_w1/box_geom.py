from PIL import Image
import numpy as np, sys
sys.stdout.reconfigure(encoding='utf-8')

# Find dialogue box top/bottom edges in shady4. The box is a dark panel with a
# lighter border, occupying bottom portion. Measure box inner top (below name banner)
# and box bottom edge.
for name in ['shady4','BarkeepOverflow']:
    im=Image.open(f'build/recon_tri2/{name}__shot.png').convert('RGB')
    a=np.array(im).astype(np.int32)
    H,W,_=a.shape
    lum=a.mean(axis=2)
    # The box border: scan column x=320 (center) from y=350..479 for the bottom border (bright line)
    col=lum[:,300:340].mean(axis=1)
    print(f'=== {name} center-column luminance y=340..479 ===')
    for y in range(355,479):
        print(f'{y:3d} {col[y]:6.1f} '+ '#'*int(col[y]/3))
    print()
