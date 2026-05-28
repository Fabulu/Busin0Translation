#!/usr/bin/env python3
"""Extract R2121 and R2122 CockpitImg textures with proper PS2 PSMT8 deswizzle."""
import struct, sys, os
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(BASE, "build", "textures_to_edit")

# PS2 GS PSMT8 block arrangement within a 128x64 page
# 8 blocks wide (16px) x 4 blocks tall (16px) = 32 blocks per page
# This table maps linear block index to block position in page
# From PCSX2's GSClut.cpp / blockTable8
PSMT8_BLOCK_TABLE = [
     0,  1,  4,  5, 16, 17, 20, 21,
     2,  3,  6,  7, 18, 19, 22, 23,
     8,  9, 12, 13, 24, 25, 28, 29,
    10, 11, 14, 15, 26, 27, 30, 31,
]

# PSMT8 column table within a 16x4 column
# From PCSX2: columnTable8
# Each column is 16 pixels wide, 4 rows tall = 64 bytes
# The column table maps (row, col) within the 16x4 column to byte offset
PSMT8_COLUMN_TABLE = [
    # Row 0
    [ 0,  4,  8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60],
    # Row 1
    [ 2,  6, 10, 14, 18, 22, 26, 30, 34, 38, 42, 46, 50, 54, 58, 62],
    # Row 2
    [ 1,  5,  9, 13, 17, 21, 25, 29, 33, 37, 41, 45, 49, 53, 57, 61],
    # Row 3
    [ 3,  7, 11, 15, 19, 23, 27, 31, 35, 39, 43, 47, 51, 55, 59, 63],
]


def build_psmt8_page_lut():
    """Build a forward lookup table: page_lut[linear_byte_offset] = (local_x, local_y)
    for a single 128x64 PSMT8 page (8192 bytes)."""
    PAGE_W, PAGE_H = 128, 64
    BLOCK_W, BLOCK_H = 16, 16
    COL_H = 4
    BLOCKS_X = PAGE_W // BLOCK_W  # 8
    BLOCKS_Y = PAGE_H // BLOCK_H  # 4

    # Build inverse block table: block_number -> (bx, by)
    inv_block = {}
    for idx in range(32):
        by = idx // BLOCKS_X
        bx = idx % BLOCKS_X
        blk_num = PSMT8_BLOCK_TABLE[idx]
        inv_block[blk_num] = (bx, by)

    lut = [(0, 0)] * (PAGE_W * PAGE_H)

    for blk_num in range(32):
        bx, by = inv_block[blk_num]
        blk_offset = blk_num * (BLOCK_W * BLOCK_H)  # 256 bytes per block

        for col_idx in range(4):  # 4 columns per block
            col_offset = blk_offset + col_idx * 64  # 64 bytes per column

            for row in range(COL_H):
                for px in range(BLOCK_W):
                    # Byte offset within column using column table
                    byte_in_col = PSMT8_COLUMN_TABLE[row][px]
                    linear_pos = col_offset + byte_in_col

                    local_x = bx * BLOCK_W + px
                    local_y = by * BLOCK_H + col_idx * COL_H + row

                    if linear_pos < len(lut):
                        lut[linear_pos] = (local_x, local_y)

    return lut


def deswizzle_psmt8(raw_data, tex_w, tex_h, lut):
    """Deswizzle PSMT8 texture data using page + block + column tables."""
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
                src_idx = page_off + i
                if src_idx >= len(raw_data):
                    continue

                local_x, local_y = lut[i]
                ox = px_page * PAGE_W + local_x
                oy = py * PAGE_H + local_y

                if ox < tex_w and oy < tex_h:
                    out[oy * tex_w + ox] = raw_data[src_idx]

    return bytes(out)


def unswizzle_clut_psmt8(palette_data):
    """Unswizzle PS2 CLUT for PSMT8: swap entries 8-15 with 16-23 in each group of 32."""
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
    """Decode a PSMT8 CockpitImg resource to PNG."""
    filepath = os.path.join(TEX_DIR, filename)
    data = open(filepath, 'rb').read()
    print(f"\n{'=' * 60}")
    print(f"Processing: {filename} ({len(data)} bytes)")

    tex = data[16:]  # skip sub-header
    data_start = 272  # first GIF tag is PACKED nloop=1 nreg=16 = 17 QWs = 272 bytes
    raw = tex[data_start:]

    pixel_count = width * height
    pal_size = 1024

    print(f"  {width}x{height} PSMT8, data at +{data_start}, avail={len(raw)}, need={pixel_count + pal_size}")

    pixel_bytes = raw[:pixel_count]
    pal_bytes = raw[pixel_count:pixel_count + pal_size]

    palette = unswizzle_clut_psmt8(pal_bytes)

    # Try both linear and deswizzled pixel layout
    for label, do_desw in [('linear', False), ('deswizzled', True)]:
        if do_desw:
            px = deswizzle_psmt8(pixel_bytes, width, height, lut)
        else:
            px = pixel_bytes

        img = Image.new('RGBA', (width, height))
        pixels_out = []
        for j in range(pixel_count):
            if j < len(px):
                pixels_out.append(palette[px[j]])
            else:
                pixels_out.append((0, 0, 0, 0))
        img.putdata(pixels_out)

        out_name = filename.replace('.raw', f'_{label}.png')
        out_path = os.path.join(TEX_DIR, out_name)
        img.save(out_path)
        print(f"  Saved: {out_path}")


if __name__ == '__main__':
    print("Building PSMT8 page lookup table...")
    lut = build_psmt8_page_lut()

    # Verify LUT
    coords = set(lut)
    print(f"  LUT has {len(coords)} unique coordinate pairs")

    decode_resource('R2121_guild_background.raw', 512, 512, lut)
    decode_resource('R2122_guild_buttons.raw', 512, 64, lut)
    print("\nDone!")
