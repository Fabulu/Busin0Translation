import sys, numpy as np
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
im=np.asarray(Image.open('build/recon_portrait4/extract/ladyknightnoportrait__shot.png').convert('L')).astype(np.float32)
H,W=im.shape
rs=np.array([(im[y,:]>150).sum() for y in range(H)])
# measure ink band heights for the 4 dialogue lines (tops ~387,413,440,465)
sy=480/448
for top in [387,413,440,465]:
    band=[y for y in range(top-3,top+24) if rs[y]>8]
    if band:
        h=band[-1]-band[0]+1
        print(f"line top~{top}: ink band y={band[0]}-{band[-1]} height_ss={h} native={h/sy:.1f}")
# Conclusion: ink height vs 24px cell
