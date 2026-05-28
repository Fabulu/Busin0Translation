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

# Try both nibble orders for page 2
for nibble_order in ["low_first", "high_first"]:
    page = np.zeros((PAGE_H, PAGE_W), dtype=np.uint8)
    po = 2 * 8192  # page 2
    for y in range(PAGE_H):
        for x in range(0, PAGE_W, 2):
            bo = po + y * (PAGE_W // 2) + x // 2
            bv = pixel_data[bo]
            if nibble_order == "low_first":
                page[y, x] = bv & 0x0F
                page[y, x+1] = (bv >> 4) & 0x0F
            else:
                page[y, x] = (bv >> 4) & 0x0F
                page[y, x+1] = bv & 0x0F

    lut = np.zeros(16, dtype=np.uint8)
    for i in range(15):
        lut[i] = 0
    lut[15] = 255

    page_vis = lut[page]
    img = Image.fromarray(page_vis, "L")
    img_scaled = img.resize((PAGE_W * 8, PAGE_H * 8), Image.NEAREST)
    img_scaled.save(os.path.join(OUT_DIR, f"_page2_{nibble_order}.png"))

# Also try treating the data as 8bpp instead of 4bpp
# Maybe each byte is one pixel
page8 = np.zeros((64, 128), dtype=np.uint8)  # 8192 bytes = 64x128
po = 2 * 8192
for y in range(64):
    for x in range(128):
        page8[y, x] = pixel_data[po + y * 128 + x]

# Visualize the 8bpp interpretation
lut8 = np.zeros(256, dtype=np.uint8)
for i in range(256):
    lut8[i] = 255 - i
page8_vis = lut8[page8]
img8 = Image.fromarray(page8_vis, "L")
img8_scaled = img8.resize((128 * 8, 64 * 8), Image.NEAREST)
img8_scaled.save(os.path.join(OUT_DIR, "_page2_8bpp.png"))

# Try interpreting with PS2 PSMT4 block swizzle
# PS2 4bpp textures use a specific block layout within 32-byte columns
# The standard PSMT4 layout arranges pixels in a specific pattern
# Let me try the standard PS2 deswizzle for PSMT4

def deswizzle_psmt4_page(raw_data, width=128, height=128):
    """Deswizzle PS2 PSMT4 texture data"""
    pixels = np.full((height, width), 15, dtype=np.uint8)

    # PSMT4: 32 pixels per "column page" width, blocks of 32x128 columns
    # Actually for 4bpp on PS2:
    # - Each 32-byte block covers an 32x4 pixel area
    # - Block width = 32 pixels (16 bytes per row, 4 rows)

    # Simplified PS2 PSMT4 layout:
    # The texture is divided into 128x32 blocks
    # Within each block, data is stored in a specific zigzag pattern

    block_w = 32  # pixels
    block_h = 16  # pixels (for PSMT4, page size is 128x128, column is 32x16)

    num_blocks_x = width // block_w   # 4
    num_blocks_y = height // block_h  # 8

    for by in range(num_blocks_y):
        for bx in range(num_blocks_x):
            block_idx = by * num_blocks_x + bx
            block_offset = block_idx * (block_w * block_h // 2)  # bytes

            for y in range(block_h):
                for x in range(0, block_w, 2):
                    byte_idx = block_offset + y * (block_w // 2) + x // 2
                    if byte_idx < len(raw_data):
                        bv = raw_data[byte_idx]
                        px = bx * block_w + x
                        py = by * block_h + y
                        if px < width and py < height:
                            pixels[py, px] = bv & 0x0F
                            pixels[py, px+1] = (bv >> 4) & 0x0F

    return pixels

# Try deswizzled version
raw_page2 = pixel_data[2*8192:3*8192]
deswizzled = deswizzle_psmt4_page(raw_page2)
lut = np.zeros(16, dtype=np.uint8)
for i in range(15):
    lut[i] = 0
lut[15] = 255
page_vis = lut[deswizzled]
img = Image.fromarray(page_vis, "L")
img.resize((128*8, 128*8), Image.NEAREST).save(os.path.join(OUT_DIR, "_page2_deswizzle_32x16.png"))

print("Done.")
