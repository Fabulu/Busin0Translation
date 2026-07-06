import sys, os
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
import numpy as np

# Measure text horizontal extent per row in the decoded v89 R2880 (left-align baseline=v86)
for v in ['v86','v89']:
    img = np.array(Image.open(f'build/recon_v89/intro/r2880s7_{v}.png').convert('L'))
    print(f'=== {v} R2880 decoded (512x512) ===')
    # text is dark (ink~0) on white(bg~255). Find dark pixels.
    line_tops=[1,25,49,73,97,121,145,169,194,218,241,265,290,313,337,361,385,409]
    for i,top in enumerate(line_tops[:6]):
        band = img[top:top+23,:]
        dark = np.where(band.min(axis=0) < 128)[0]
        if len(dark):
            print(f'  line {i}: x {dark.min():3d}..{dark.max():3d}  width={dark.max()-dark.min():3d}')
        else:
            print(f'  line {i}: (empty)')
