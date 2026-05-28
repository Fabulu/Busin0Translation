#!/usr/bin/env python3
import os
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(BASE, "build", "textures_to_edit")

for name in ['R2119_2row_interleave', 'R2119_shift128', 'R2119_shift131',
             'R2119_noswizzle', 'R2119_4row_interleave']:
    try:
        img = Image.open(os.path.join(TEX_DIR, f'{name}.png'))
        crop = img.crop((80, 20, 350, 48))
        zoomed = crop.resize((crop.width * 4, crop.height * 4), Image.NEAREST)
        zoomed.save(os.path.join(TEX_DIR, f'{name}_zoom.png'))
        print(f"Saved zoom: {name}")
    except:
        pass
