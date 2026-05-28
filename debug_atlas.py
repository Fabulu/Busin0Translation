import struct, os
import numpy as np
from PIL import Image

ATLAS_PATH = r"C:\Programmieren\wizardrytranslation\extracted\packdata_resources\1272_type01.bin"
OUT_DIR = r"C:\Programmieren\wizardrytranslation\dumps\glyphs"
HEADER_SIZE = 192
PAGE_W = 128
PAGE_H = 128
GLYPH_W = 12
GLYPH_H = 12
COLS = 21

with open(ATLAS_PATH, "rb") as f:
    data = f.read()

pixel_data = data[HEADER_SIZE:HEADER_SIZE + 65536]

# Check what glyph 37 maps to
gi = 37  # Should be 'A'
col = gi % COLS  # 37 % 21 = 16
row = gi // COLS  # 37 // 21 = 1

px = col * GLYPH_W  # 16 * 12 = 192
py = row * GLYPH_H  # 1 * 12 = 12

print(f"Glyph {gi}: col={col}, row={row}, px={px}, py={py}")
print(f"Atlas position: ({px}, {py}) to ({px+12}, {py+12})")

# px=192 means we're in the second page column (192 >= 128)
page_col = px // 128  # = 1
page_row = py // 128  # = 0
page_idx = page_row * 2 + page_col  # = 1
local_x = px % 128  # = 64
local_y = py % 128  # = 12

print(f"Page {page_idx}, local ({local_x}, {local_y})")

# Read raw pixel data for this location
page_offset = page_idx * 8192
for y in range(local_y, local_y + GLYPH_H):
    row_data = []
    for x in range(local_x, local_x + GLYPH_W):
        byte_offset = page_offset + y * (PAGE_W // 2) + x // 2
        bv = pixel_data[byte_offset]
        if x % 2 == 0:
            pix = bv & 0x0F
        else:
            pix = (bv >> 4) & 0x0F
        row_data.append(pix)
    print(f"  y={y}: {row_data}")

# Now let's check what's actually in the atlas visually
# Dump the first 2 pages as images to understand the layout
for pi in range(2):
    po = pi * 8192
    page = np.zeros((PAGE_H, PAGE_W), dtype=np.uint8)
    for y in range(PAGE_H):
        for x in range(0, PAGE_W, 2):
            bo = po + y * (PAGE_W // 2) + x // 2
            bv = pixel_data[bo]
            page[y, x] = bv & 0x0F
            page[y, x+1] = (bv >> 4) & 0x0F

    # Map to visible: 15=white(bg), 0-14=dark
    lut = np.zeros(16, dtype=np.uint8)
    for i in range(15):
        lut[i] = 0
    lut[15] = 255
    page_vis = lut[page]

    img = Image.fromarray(page_vis, "L")
    img_scaled = img.resize((PAGE_W * 4, PAGE_H * 4), Image.NEAREST)
    img_scaled.save(os.path.join(OUT_DIR, f"_debug_page{pi}.png"))

    print(f"\nPage {pi} - unique values: {np.unique(page)}")
    # Print first 24x24 region
    print(f"Page {pi} top-left 24x24:")
    for y in range(min(24, PAGE_H)):
        vals = [f"{page[y,x]:x}" for x in range(min(24, PAGE_W))]
        print("  " + " ".join(vals))

print("\nDone.")
