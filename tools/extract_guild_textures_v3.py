#!/usr/bin/env python3
"""Extract R2121 and R2122 with correct PS2 PSMT8 deswizzle.

Uses the exact block and column tables from PCSX2's GSTables.h:
  - PSMT8 page: 128x64 pixels
  - Block: 16x16 pixels (256 bytes)
  - Column: 16x2 pixels within a block (two column pairs alternate)

The PSMT8 block table determines how 16x16 blocks are arranged within a 128x64 page.
The column table determines byte ordering within each column.
"""
import struct, sys, os
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(BASE, "build", "textures_to_edit")

# PCSX2 blockTable8 from GSTables.h
# Maps block position (row, col) within a page to block index
# Page is 128x64 pixels = 8 blocks wide x 4 blocks tall
# blockTable8[block_y][block_x] = block_number
BLOCK_TABLE_8 = [
    [ 0,  1,  4,  5, 16, 17, 20, 21],
    [ 2,  3,  6,  7, 18, 19, 22, 23],
    [ 8,  9, 12, 13, 24, 25, 28, 29],
    [10, 11, 14, 15, 26, 27, 30, 31],
]

# PCSX2 columnTable8 from GSTables.h
# Maps pixel position within a 16x16 block to byte offset
# columnTable8[y][x] for a 16x16 block
# From GS documentation, PSMT8 column arrangement:
# Each 16x16 block has 256 bytes
# Organized as 4 columns of 16x4 each
# Within each column, bytes are arranged with a specific interleave

# Standard PCSX2 columnTable8 (16 rows x 16 cols = 256 entries)
# Values 0-255 mapping each (x,y) within a block to its byte offset
COLUMN_TABLE_8 = [
    [  0,   4,   8,  12,  16,  20,  24,  28,   2,   6,  10,  14,  18,  22,  26,  30],  # y=0
    [ 33,  37,  41,  45,  49,  53,  57,  61,  35,  39,  43,  47,  51,  55,  59,  63],  # y=1
    [  1,   5,   9,  13,  17,  21,  25,  29,   3,   7,  11,  15,  19,  23,  27,  31],  # y=2
    [ 32,  36,  40,  44,  48,  52,  56,  60,  34,  38,  42,  46,  50,  54,  58,  62],  # y=3
    [ 64,  68,  72,  76,  80,  84,  88,  92,  66,  70,  74,  78,  82,  86,  90,  94],  # y=4
    [ 97, 101, 105, 109, 113, 117, 121, 125,  99, 103, 107, 111, 115, 119, 123, 127],  # y=5
    [ 65,  69,  73,  77,  81,  85,  89,  93,  67,  71,  75,  79,  83,  87,  91,  95],  # y=6
    [ 96, 100, 104, 108, 112, 116, 120, 124,  98, 102, 106, 110, 114, 118, 122, 126],  # y=7
    [128, 132, 136, 140, 144, 148, 152, 156, 130, 134, 138, 142, 146, 150, 154, 158],  # y=8
    [161, 165, 169, 173, 177, 181, 185, 189, 163, 167, 171, 175, 179, 183, 187, 191],  # y=9
    [129, 133, 137, 141, 145, 149, 153, 157, 131, 135, 139, 143, 147, 151, 155, 159],  # y=10
    [160, 164, 168, 172, 176, 180, 184, 188, 162, 166, 170, 174, 178, 182, 186, 190],  # y=11
    [192, 196, 200, 204, 208, 212, 216, 220, 194, 198, 202, 206, 210, 214, 218, 222],  # y=12
    [225, 229, 233, 237, 241, 245, 249, 253, 227, 231, 235, 239, 243, 247, 251, 255],  # y=13
    [193, 197, 201, 205, 209, 213, 217, 221, 195, 199, 203, 207, 211, 215, 219, 223],  # y=14
    [224, 228, 232, 236, 240, 244, 248, 252, 226, 230, 234, 238, 242, 246, 250, 254],  # y=15
]


def build_page_lut():
    """Build forward LUT: for each byte in a 8192-byte page, what (x,y) does it map to?"""
    PAGE_W, PAGE_H = 128, 64
    BLOCK_W, BLOCK_H = 16, 16
    BLOCKS_X = PAGE_W // BLOCK_W  # 8
    BLOCKS_Y = PAGE_H // BLOCK_H  # 4
    BLOCK_BYTES = BLOCK_W * BLOCK_H  # 256

    # Forward: byte_offset -> (x, y) within page
    lut = [(0, 0)] * (PAGE_W * PAGE_H)

    # Inverse block table: block_number -> (bx, by)
    inv_block = {}
    for by in range(BLOCKS_Y):
        for bx in range(BLOCKS_X):
            bn = BLOCK_TABLE_8[by][bx]
            inv_block[bn] = (bx, by)

    # Inverse column table: byte_offset_in_block -> (lx, ly)
    inv_column = {}
    for ly in range(BLOCK_H):
        for lx in range(BLOCK_W):
            bo = COLUMN_TABLE_8[ly][lx]
            inv_column[bo] = (lx, ly)

    for bn in range(32):
        bx, by = inv_block[bn]
        block_start = bn * BLOCK_BYTES

        for byte_in_block in range(BLOCK_BYTES):
            lx, ly = inv_column[byte_in_block]
            page_byte = block_start + byte_in_block
            px = bx * BLOCK_W + lx
            py = by * BLOCK_H + ly

            if page_byte < len(lut):
                lut[page_byte] = (px, py)

    return lut


def deswizzle_psmt8(raw_data, tex_w, tex_h, lut):
    """Deswizzle PSMT8 texture using page/block/column tables."""
    PAGE_W, PAGE_H = 128, 64
    PAGE_BYTES = PAGE_W * PAGE_H
    pages_x = max(1, tex_w // PAGE_W)
    pages_y = max(1, tex_h // PAGE_H)

    out = bytearray(tex_w * tex_h)

    for py in range(pages_y):
        for px_page in range(pages_x):
            page_idx = py * pages_x + px_page
            page_off = page_idx * PAGE_BYTES

            for i in range(PAGE_BYTES):
                src = page_off + i
                if src >= len(raw_data):
                    continue
                lx, ly = lut[i]
                ox = px_page * PAGE_W + lx
                oy = py * PAGE_H + ly
                if ox < tex_w and oy < tex_h:
                    out[oy * tex_w + ox] = raw_data[src]

    return bytes(out)


def unswizzle_clut(palette_data):
    """Unswizzle PS2 PSMT8 CLUT."""
    colors = []
    for i in range(256):
        off = i * 4
        if off + 3 < len(palette_data):
            r, g, b, a = palette_data[off], palette_data[off+1], palette_data[off+2], palette_data[off+3]
            colors.append((r, g, b, min(a * 2, 255)))
        else:
            colors.append((0, 0, 0, 0))

    for grp in range(8):
        base = grp * 32
        for j in range(8):
            colors[base + 8 + j], colors[base + 16 + j] = \
                colors[base + 16 + j], colors[base + 8 + j]
    return colors


def decode_resource(filename, width, height, lut):
    filepath = os.path.join(TEX_DIR, filename)
    data = open(filepath, 'rb').read()
    tex = data[16:]
    raw = tex[272:]  # skip GIF header (17 QWs)

    pixel_count = width * height
    pal_size = 1024

    pixel_bytes = raw[:pixel_count]
    pal_bytes = raw[pixel_count:pixel_count + pal_size]
    palette = unswizzle_clut(pal_bytes)

    # Deswizzled version
    px_desw = deswizzle_psmt8(pixel_bytes, width, height, lut)
    img = Image.new('RGBA', (width, height))
    img.putdata([palette[px_desw[j]] for j in range(pixel_count)])
    out_path = os.path.join(TEX_DIR, filename.replace('.raw', '.png'))
    img.save(out_path)
    print(f"Saved: {out_path}")

    # Linear version for comparison
    img_lin = Image.new('RGBA', (width, height))
    img_lin.putdata([palette[pixel_bytes[j]] for j in range(min(pixel_count, len(pixel_bytes)))])
    out_lin = os.path.join(TEX_DIR, filename.replace('.raw', '_linear_ref.png'))
    img_lin.save(out_lin)
    print(f"Saved: {out_lin}")


if __name__ == '__main__':
    print("Building PSMT8 page LUT...")
    lut = build_page_lut()

    # Verify LUT completeness
    coords = set(lut)
    print(f"  {len(coords)} unique coordinates")

    # Verify all coords are valid
    max_x = max(c[0] for c in lut)
    max_y = max(c[1] for c in lut)
    print(f"  Coord range: x=0..{max_x}, y=0..{max_y}")

    decode_resource('R2121_guild_background.raw', 512, 512, lut)
    decode_resource('R2122_guild_buttons.raw', 512, 64, lut)

    # Also decode R2118 for validation
    decode_resource('R2118_tavern_background.raw', 512, 512, lut)

    print("\nDone!")
