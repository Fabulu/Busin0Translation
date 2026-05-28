import struct, os
import numpy as np
from PIL import Image

ATLAS_PATH = r"C:\Programmieren\wizardrytranslation\extracted\packdata_resources\1272_type01.bin"
OUT_DIR = r"C:\Programmieren\wizardrytranslation\dumps\glyphs"
HEADER_SIZE = 192
PAGE_W = 128
PAGE_H = 128

with open(ATLAS_PATH, "rb") as f:
    data = f.read()

pixel_data = data[HEADER_SIZE:HEADER_SIZE + 65536]

# Decode all 8 pages
pages = []
for pi in range(8):
    po = pi * 8192
    page = np.zeros((PAGE_H, PAGE_W), dtype=np.uint8)
    for y in range(PAGE_H):
        for x in range(0, PAGE_W, 2):
            bo = po + y * (PAGE_W // 2) + x // 2
            bv = pixel_data[bo]
            page[y, x] = bv & 0x0F
            page[y, x+1] = (bv >> 4) & 0x0F
    pages.append(page)

# Save all 8 pages as separate images
for pi in range(8):
    lut = np.zeros(16, dtype=np.uint8)
    for i in range(15):
        lut[i] = 0
    lut[15] = 255
    page_vis = lut[pages[pi]]
    img = Image.fromarray(page_vis, "L")
    img_scaled = img.resize((PAGE_W * 4, PAGE_H * 4), Image.NEAREST)
    img_scaled.save(os.path.join(OUT_DIR, f"_debug_page{pi}.png"))

    # Count non-bg pixels
    nbg = np.sum(pages[pi] != 15)
    print(f"Page {pi}: {nbg} non-bg pixels")

# Look at the full atlas as one image with 16x16 glyph grid
# Maybe the grid is 16 cols x 16 rows per page = 256 glyphs per page
# with 8x8 glyphs
for glyph_size in [8, 10, 12, 14, 16]:
    cols = PAGE_W // glyph_size
    rows = PAGE_H // glyph_size
    print(f"\nGlyph size {glyph_size}: {cols}x{rows} = {cols*rows} per page, {cols*rows*8} total")

# Let's try different glyph sizes and see which grid aligns with the data
# Check page 0 at 8x8 grid
print("\n\nPage 0 - checking glyph boundaries at 8px grid:")
for gy in range(16):
    for gx in range(16):
        x0 = gx * 8
        y0 = gy * 8
        cell = pages[0][y0:y0+8, x0:x0+8]
        nbg = np.sum(cell != 15)
        if nbg > 0:
            print(f"  Grid ({gx},{gy}) = glyph {gy*16+gx}: {nbg} non-bg pixels")

print("\n\nPage 2 - checking glyph boundaries at 8px grid:")
for gy in range(16):
    for gx in range(16):
        x0 = gx * 8
        y0 = gy * 8
        cell = pages[2][y0:y0+8, x0:x0+8]
        nbg = np.sum(cell != 15)
        if nbg > 0:
            print(f"  Grid ({gx},{gy}) = glyph {gy*16+gx}: {nbg} non-bg pixels")

# Also try 12x12
print("\n\nPage 0 - checking at 12px grid:")
cols12 = PAGE_W // 12  # 10
rows12 = PAGE_H // 12  # 10
for gy in range(rows12):
    for gx in range(cols12):
        x0 = gx * 12
        y0 = gy * 12
        cell = pages[0][y0:y0+12, x0:x0+12]
        nbg = np.sum(cell != 15)
        if nbg > 0:
            print(f"  Grid ({gx},{gy}): {nbg} non-bg pixels")

print("Done.")
