#!/usr/bin/env python3
"""
Summary identification of all characters in R2138 sub25.
Cross-reference with Wizardry game context for level-up notification screen.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from psmt4_deswizzle import deswizzle_psmt4
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PATH = os.path.join(BASE, "extracted", "packdata_raw", "2138_type29.raw")
DUMP_DIR = os.path.join(BASE, "dumps")

SUB_OFFSET = 0x15C4D0
HEADER_SIZE = 0x6E0
PIXEL_OFFSET = SUB_OFFSET + HEADER_SIZE
PIXEL_SIZE = 32768
TEX_W, TEX_H = 256, 256
DBW_CT32 = 128

data = open(RAW_PATH, 'rb').read()
pixel_data = data[PIXEL_OFFSET:PIXEL_OFFSET + PIXEL_SIZE]
pixels = deswizzle_psmt4(pixel_data, TEX_W, TEX_H, dbw_ct32=DBW_CT32)

# Let me look at the COMPLETE texture at threshold=5 to understand full layout
print("=" * 80)
print("FULL TEXTURE MAP at threshold >= 3")
print("=" * 80)

charmap = '.' + '123456789ABCDEF'
for y in range(TEX_H):
    line = ''
    has_content = False
    for x in range(TEX_W):
        v = pixels[y * TEX_W + x]
        if v >= 3:
            line += '#'
            has_content = True
        else:
            line += '.'
    if has_content:
        # Compress: show only first 200 chars
        print(f"y{y:3d}:{line[:200]}")

# Now extract individual annotations on the full 2x overview image
from PIL import ImageDraw, ImageFont

full_pixels = pixels
img = Image.new('L', (TEX_W * 4, TEX_H * 4))
for y in range(TEX_H):
    for x in range(TEX_W):
        v = full_pixels[y * TEX_W + x] * 17
        for zy in range(4):
            for zx in range(4):
                img.putpixel((x*4+zx, y*4+zy), v)

# Convert to RGB and add annotations
img_rgb = img.convert('RGB')
draw = ImageDraw.Draw(img_rgb)

annotations = [
    ((0, 0, 256, 50), "Region 1: top area"),
    ((0, 55, 80, 80), "Region 2: small shapes"),
    ((0, 120, 256, 170), "Region 3: banner text"),
    ((4, 176, 122, 217), "Region 4: large text"),
    ((144, 176, 188, 217), "Region 5: small text"),
    ((5, 224, 121, 254), "Region 6: large text"),
]

for (x1, y1, x2, y2), label in annotations:
    draw.rectangle([x1*4, y1*4, x2*4, y2*4], outline=(255, 0, 0))
    draw.text((x1*4, y1*4 - 12), label, fill=(255, 0, 0))

img_rgb.save(os.path.join(DUMP_DIR, "r2138_sub25_annotated_4x.png"))
print("\nSaved annotated overview.")

# Now let's specifically look at the top regions that haven't been analyzed
print("\n" + "=" * 80)
print("TOP AREA (y=0-50) analysis")
print("=" * 80)

for y in range(0, 50):
    line = ''
    has = False
    for x in range(TEX_W):
        v = pixels[y * TEX_W + x]
        if v >= 3:
            line += charmap[min(v, 15)]
            has = True
        else:
            line += '.'
    if has:
        print(f"y{y:3d}:{line[:200]}")

print("\n" + "=" * 80)
print("MID AREA (y=55-80) analysis")
print("=" * 80)

for y in range(55, 80):
    line = ''
    has = False
    for x in range(TEX_W):
        v = pixels[y * TEX_W + x]
        if v >= 3:
            line += charmap[min(v, 15)]
            has = True
        else:
            line += '.'
    if has:
        print(f"y{y:3d}:{line[:200]}")
