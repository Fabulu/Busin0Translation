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

# PS2 PSMT4 deswizzle
# The PSMT4 format stores data in 128-bit (16 byte) words
# Each 128-bit word = 32 pixels at 4bpp
# The page layout for PSMT4 is:
# - Page size: 128x128
# - Block size: 128x32 (a "page" has 4 blocks vertically)
# - Column size: 128x4 (each block has 8 columns)
# Actually the proper PS2 GS PSMT4 layout is complex.
# Let me implement the standard deswizzle table approach.

# PSMT4 block arrangement within a page (128x128):
# - Blocks are 32x16 pixels
# - 4 blocks wide (128/32) x 8 blocks tall (128/16)
# - Block index mapping:
#   Row 0: blocks 0,2,4,6
#   Row 1: blocks 1,3,5,7
#   Row 2: blocks 8,10,12,14
#   etc.

# Actually, let me try the simplest correct PS2 4bpp deswizzle.
# Key insight: PS2 PSMT4 stores 128x128 textures using:
# - 32-pixel wide columns
# - Within each column, 4-pixel tall rows
# - Pixels within a row use interleaved nibble order

# Standard PS2 PSMT4 deswizzle for a 128x128 page
def psmt4_deswizzle(raw_bytes, width=128, height=128):
    """Standard PS2 PSMT4 deswizzle"""
    result = np.full((height, width), 15, dtype=np.uint8)

    # PSMT4 parameters
    # Each "page" = 128x128 pixels
    # Block = 32x16 pixels
    # Column = 32x4 pixels
    # Within column, pixels are stored linearly but with specific ordering

    # For PSMT4, the block layout within a page:
    # blocks_per_row = width / 32 = 4
    # blocks_per_col = height / 16 = 8

    # Each block = 32*16/2 = 256 bytes
    # Total = 32 blocks * 256 bytes = 8192 bytes (matches!)

    blocks_w = width // 32   # 4
    blocks_h = height // 16  # 8

    for block_y in range(blocks_h):
        for block_x in range(blocks_w):
            # Block order in PSMT4:
            # Row 0 of blocks: left to right
            # Row 1: left to right
            # etc.
            block_idx = block_y * blocks_w + block_x
            block_base = block_idx * 256  # 256 bytes per block

            for cy in range(16):
                for cx in range(0, 32, 2):
                    byte_off = block_base + cy * 16 + cx // 2
                    if byte_off < len(raw_bytes):
                        bv = raw_bytes[byte_off]
                        px = block_x * 32 + cx
                        py = block_y * 16 + cy
                        if px < width and py < height:
                            result[py, px] = bv & 0x0F
                            result[py, px + 1] = (bv >> 4) & 0x0F

    return result

# Try on page 0
raw_page0 = pixel_data[0:8192]
page0_ds = psmt4_deswizzle(raw_page0)
lut = np.zeros(16, dtype=np.uint8)
for i in range(15):
    lut[i] = 0
lut[15] = 255
vis = lut[page0_ds]
Image.fromarray(vis, "L").resize((128*8, 128*8), Image.NEAREST).save(
    os.path.join(OUT_DIR, "_page0_ds_32x16.png"))

# Try on page 2
raw_page2 = pixel_data[2*8192:3*8192]
page2_ds = psmt4_deswizzle(raw_page2)
vis2 = lut[page2_ds]
Image.fromarray(vis2, "L").resize((128*8, 128*8), Image.NEAREST).save(
    os.path.join(OUT_DIR, "_page2_ds_32x16.png"))

# Also try 32x32 blocks (another common PS2 layout)
def psmt4_deswizzle_32x32(raw_bytes, width=128, height=128):
    result = np.full((height, width), 15, dtype=np.uint8)
    blocks_w = width // 32   # 4
    blocks_h = height // 32  # 4
    bytes_per_block = 32 * 32 // 2  # 512

    for block_y in range(blocks_h):
        for block_x in range(blocks_w):
            block_idx = block_y * blocks_w + block_x
            block_base = block_idx * bytes_per_block

            for cy in range(32):
                for cx in range(0, 32, 2):
                    byte_off = block_base + cy * 16 + cx // 2
                    if byte_off < len(raw_bytes):
                        bv = raw_bytes[byte_off]
                        px = block_x * 32 + cx
                        py = block_y * 32 + cy
                        if px < width and py < height:
                            result[py, px] = bv & 0x0F
                            result[py, px + 1] = (bv >> 4) & 0x0F
    return result

page2_ds2 = psmt4_deswizzle_32x32(raw_page2)
vis3 = lut[page2_ds2]
Image.fromarray(vis3, "L").resize((128*8, 128*8), Image.NEAREST).save(
    os.path.join(OUT_DIR, "_page2_ds_32x32.png"))

# Try completely different: maybe the data isn't organized by pages at all
# Maybe it's one continuous 256-wide texture (at 4bpp, 128 bytes per row)
# Total data = 65536 bytes, at 128 bytes/row = 512 rows
# So 256x512 at 4bpp = 256*512/2 = 65536 bytes

atlas_linear = np.zeros((512, 256), dtype=np.uint8)
for y in range(512):
    for x in range(0, 256, 2):
        byte_off = y * 128 + x // 2
        if byte_off < len(pixel_data):
            bv = pixel_data[byte_off]
            atlas_linear[y, x] = bv & 0x0F
            atlas_linear[y, x+1] = (bv >> 4) & 0x0F

vis4 = lut[atlas_linear]
Image.fromarray(vis4, "L").resize((256*4, 512*4), Image.NEAREST).save(
    os.path.join(OUT_DIR, "_atlas_linear_256x512.png"))

print("Done.")
