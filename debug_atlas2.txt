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

# Decode page 0 fully
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

# Check page 0: find non-15 pixel positions
page0 = pages[0]
print("Page 0 non-background rows:")
for y in range(PAGE_H):
    non_bg = np.where(page0[y] != 15)[0]
    if len(non_bg) > 0:
        print(f"  y={y}: cols {non_bg[0]}-{non_bg[-1]} ({len(non_bg)} pixels)")

print("\nPage 0 non-background cols:")
for x in range(PAGE_W):
    non_bg = np.where(page0[:, x] != 15)[0]
    if len(non_bg) > 0:
        print(f"  x={x}: rows {non_bg[0]}-{non_bg[-1]} ({len(non_bg)} pixels)")

# Print more detail for the first few glyph rows
print("\nPage 0 rows 0-30 raw hex (x=0..31):")
for y in range(30):
    vals = [f"{page0[y,x]:x}" for x in range(32)]
    print(f"  y={y:2d}: {' '.join(vals)}")

# Check page 1 similarly
page1 = pages[1]
print("\nPage 1 non-background rows:")
for y in range(PAGE_H):
    non_bg = np.where(page1[y] != 15)[0]
    if len(non_bg) > 0:
        print(f"  y={y}: cols {non_bg[0]}-{non_bg[-1]} ({len(non_bg)} pixels)")
