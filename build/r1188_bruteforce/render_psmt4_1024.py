"""
Render R1188 as PSMT4 1024x1024 with proper PS2 GS swizzle.
Based on TEX0 register: PSM=PSMT4, 1024x1024, TBW=16.
"""
import struct, os
import numpy as np
from PIL import Image

SRC = r"C:\Programmieren\wizardrytranslation\extracted\packdata_raw\1188_type01.raw"
OUT = r"C:\Programmieren\wizardrytranslation\build\r1188_bruteforce"

raw = open(SRC, "rb").read()

# PS2 PSMT4 memory layout constants
# A PSMT4 page is 128x128 pixels = 8192 bytes (128*128/2)
# A block within a page is 32x16 pixels = 256 bytes (32*16/2)
# A column within a block is 32x2 pixels = 32 bytes
# Pages are arranged in 128-pixel wide columns

# Block arrangement within a page (128x128 px = 4x8 blocks of 32x16)
# PS2 GS block order for PSMT4:
PSMT4_BLOCK_TABLE = [
    [ 0,  2,  8, 10],
    [ 1,  3,  9, 11],
    [ 4,  6, 12, 14],
    [ 5,  7, 13, 15],
    [16, 18, 24, 26],
    [17, 19, 25, 27],
    [20, 22, 28, 30],
    [21, 23, 29, 31],
]

# Column layout within a block for PSMT4
# Each column is 32 pixels wide, 2 pixels tall = 32 bytes
# A block has 8 columns (16 rows / 2 rows per column)

def psmt4_page_column_block_unswizzle(data, width, height):
    """Full PS2 PSMT4 unswizzle using page/block/column layout."""
    out = np.zeros((height, width), dtype=np.uint8)
    src = np.frombuffer(data, dtype=np.uint8)

    page_w = 128  # pixels
    page_h = 128  # pixels
    block_w = 32   # pixels
    block_h = 16   # pixels

    pages_x = width // page_w
    pages_y = height // page_h

    for py in range(pages_y):
        for px in range(pages_x):
            page_idx = py * pages_x + px
            page_base = page_idx * (page_w * page_h // 2)  # bytes per page

            for by in range(8):  # 8 block rows per page
                for bx in range(4):  # 4 block cols per page
                    block_num = PSMT4_BLOCK_TABLE[by][bx]
                    block_offset = page_base + block_num * (block_w * block_h // 2)

                    for row in range(block_h):
                        for col in range(0, block_w, 2):
                            byte_idx = block_offset + row * (block_w // 2) + col // 2
                            if byte_idx >= len(src):
                                continue
                            byte = src[byte_idx]

                            ox = px * page_w + bx * block_w + col
                            oy = py * page_h + by * block_h + row

                            if ox < width and oy < height:
                                out[oy, ox] = (byte & 0x0F) * 17
                            if ox + 1 < width and oy < height:
                                out[oy, ox + 1] = ((byte >> 4) & 0x0F) * 17

    return out


def simple_linear_4bpp(data, width, height):
    """Simple linear 4bpp, lo nibble first."""
    needed = (width * height) // 2
    d = data[:needed]
    arr = np.frombuffer(d, dtype=np.uint8)
    lo = (arr & 0x0F) * 17
    hi = ((arr >> 4) & 0x0F) * 17
    pixels = np.empty(len(arr) * 2, dtype=np.uint8)
    pixels[0::2] = lo
    pixels[1::2] = hi
    return pixels[:width*height].reshape((height, width))


# Try several header offsets with proper PSMT4 swizzle at 1024x1024
for hdr in [0x800, 0x850, 0xC00, 0x1000]:
    data = raw[hdr:]
    data_len = len(data)

    # 4bpp 1024x1024 needs 524288 bytes
    needed = 524288
    if data_len < needed:
        print(f"hdr=0x{hdr:x}: only {data_len} bytes, need {needed}")
        # Pad
        data = data + b'\x00' * (needed - data_len)

    print(f"\n=== Header offset 0x{hdr:x} ({hdr}) ===")

    # Linear 4bpp 1024x1024
    pixels = simple_linear_4bpp(data, 1024, 1024)
    name = f"r1188_4bpp_linear_1024x1024_hdr{hdr}.png"
    Image.fromarray(pixels, 'L').save(os.path.join(OUT, name))
    print(f"  Saved {name}")

    # PSMT4 swizzled 1024x1024
    pixels = psmt4_page_column_block_unswizzle(data, 1024, 1024)
    name = f"r1188_psmt4_swizzle_1024x1024_hdr{hdr}.png"
    Image.fromarray(pixels, 'L').save(os.path.join(OUT, name))
    print(f"  Saved {name}")

# Also try with the header at exactly the computed 4096 but treating
# the sparse structure of the data (zero rows every ~0xA0 bytes)
# Maybe those zero rows are part of the data (transparent strips)

# Let's also try: what if we strip the 2-row zeros from the pattern?
# The pattern from 0x850 is: 6 rows of data, 2 rows of zeros, repeat
# That looks like 128-byte blocks with 32 bytes of padding = 160 byte stride

print("\n=== Checking data structure pattern ===")
data_start = 0x850
# Check if data follows pattern: N bytes data, M bytes zeros
for i in range(5):
    off = data_start + i * 0x150  # try 0x150 = 336 byte stride
    chunk = raw[off:off+0x150]
    nz_count = sum(1 for b in chunk if b != 0)
    print(f"  Block {i} at 0x{off:04x}: {nz_count}/{len(chunk)} non-zero")

# Try 0xA0 stride (160 bytes)
print("\nStride 0xA0:")
for i in range(8):
    off = data_start + i * 0xA0
    chunk = raw[off:off+0xA0]
    nz_count = sum(1 for b in chunk if b != 0)
    z_tail = sum(1 for b in chunk[-32:] if b == 0)
    print(f"  Block {i} at 0x{off:04x}: {nz_count}/{len(chunk)} non-zero, last 32: {z_tail} zeros")

print("\nDone!")
