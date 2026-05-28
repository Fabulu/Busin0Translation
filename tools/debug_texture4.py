#!/usr/bin/env python3
"""Investigate the exact pixel layout and try PSMT8 unswizzle."""
import struct
import os
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(BASE, "build", "textures_to_edit")


def unswizzle_clut_psmt8(palette_data):
    colors = []
    for i in range(256):
        off = i * 4
        if off + 3 < len(palette_data):
            r, g, b, a = palette_data[off], palette_data[off+1], palette_data[off+2], palette_data[off+3]
            a = min(a * 2, 255)
            colors.append((r, g, b, a))
        else:
            colors.append((0, 0, 0, 0))
    unswizzled = list(colors)
    for grp in range(8):
        base = grp * 32
        for j in range(8):
            unswizzled[base + 8 + j], unswizzled[base + 16 + j] = \
                unswizzled[base + 16 + j], unswizzled[base + 8 + j]
    return unswizzled


# PS2 GS PSMT8 swizzle tables
# The GS stores PSMT8 in pages of 128x64 pixels
# Each page is divided into blocks of 16x16 pixels
# Within each block, pixels are stored in a specific pattern

# PSMT8 page: 128x64 pixels
# Block: 16x16 pixels
# Blocks per page: 8x4 = 32 blocks

# Block arrangement within a page (column/row of blocks):
PSMT8_BLOCK_TABLE = [
    # Row 0: blocks 0-7 (x: 0..7)
    [ 0,  1,  4,  5, 16, 17, 20, 21],
    # Row 1: blocks 8-15
    [ 2,  3,  6,  7, 18, 19, 22, 23],
    # Row 2: blocks 16-23
    [ 8,  9, 12, 13, 24, 25, 28, 29],
    # Row 3: blocks 24-31
    [10, 11, 14, 15, 26, 27, 30, 31],
]

# Column table within a block for PSMT8 (16x16 -> 256 bytes, 4 columns of 4x16 bytes)
PSMT8_COL_TABLE = [
    [0, 1, 4, 5, 8, 9, 12, 13],   # even row
    [2, 3, 6, 7, 10, 11, 14, 15],  # odd row
]


def psmt8_unswizzle(data, width, height):
    """Unswizzle PSMT8 pixel data.

    PS2 GS PSMT8 memory layout:
    - Pages are 128x64 pixels (8192 bytes each)
    - Each page has 32 blocks of 16x16 pixels
    - Blocks are arranged in a specific order within the page
    - Within blocks, columns of 16x2 bytes
    """
    output = bytearray(width * height)

    page_w = 128  # pixels per page width
    page_h = 64   # pixels per page height
    block_w = 16
    block_h = 16

    pages_x = (width + page_w - 1) // page_w
    pages_y = (height + page_h - 1) // page_h

    # Buffer width in pages (BW from BITBLTBUF, in 64-pixel units)
    # For 512 wide: BW = 512/64 = 8 -> that's page_stride
    bw_pixels = width  # Actual width

    src_idx = 0

    for page_y in range(pages_y):
        for page_x in range(pages_x):
            page_base_x = page_x * page_w
            page_base_y = page_y * page_h

            for block_idx in range(32):
                # Find block position within page
                block_row = -1
                block_col = -1
                for r in range(4):
                    for c in range(8):
                        if PSMT8_BLOCK_TABLE[r][c] == block_idx:
                            block_row = r
                            block_col = c
                            break
                    if block_row >= 0:
                        break

                bx = page_base_x + block_col * block_w
                by = page_base_y + block_row * block_h

                # Read 256 bytes for this 16x16 block
                for row in range(block_h):
                    for col in range(block_w):
                        if src_idx < len(data):
                            x = bx + col
                            y = by + row
                            if x < width and y < height:
                                output[y * width + x] = data[src_idx]
                        src_idx += 1

    return bytes(output)


def psmt8_unswizzle_v2(data, width, height):
    """Unswizzle PSMT8 using the known column/block layout.

    Based on the PS2 GS memory mapping documentation.
    PSMT8: page=128x64, block=16x16
    """
    output = bytearray(width * height)

    # PSMT8 block layout within a page (8 columns x 4 rows of 16x16 blocks)
    block_layout = [
        [ 0,  1,  4,  5, 16, 17, 20, 21],
        [ 2,  3,  6,  7, 18, 19, 22, 23],
        [ 8,  9, 12, 13, 24, 25, 28, 29],
        [10, 11, 14, 15, 26, 27, 30, 31],
    ]

    # PSMT8 column layout within a block
    # Each block is 16x16 = 256 bytes, organized as 4 columns of 16x4 bytes
    # Column layout (2 rows, 4 columns per row):
    # Even row: 0, 4, 8, 12 (column indices)
    # Odd row:  2, 6, 10, 14
    # But within each column: 2 sub-columns of 8 bytes wide

    # Actually, for PSMT8 within a block, the layout is:
    # The 16x16 block is divided into 16 columns of 16x1
    # stored in groups based on the column table

    # Simpler approach: just use the known pixel address formula
    # For PSMT8:
    # page_width = 128, page_height = 64
    # block_width = 16, block_height = 16
    # column_width = 16, column_height = 4

    page_w = 128
    page_h = 64
    block_w = 16
    block_h = 16

    # Buffer width in pages
    bw_pages = (width + page_w - 1) // page_w

    for dst_y in range(height):
        for dst_x in range(width):
            # Which page?
            px = dst_x // page_w
            py = dst_y // page_h
            page_num = py * bw_pages + px

            # Position within page
            lx = dst_x % page_w
            ly = dst_y % page_h

            # Which block within the page?
            bx = lx // block_w
            by = ly // block_h
            block_num = block_layout[by][bx]

            # Position within block
            blx = lx % block_w
            bly = ly % block_h

            # Column within block (4 rows per column group)
            col_y = bly // 4
            col_x = blx

            # Within the 16x4 column:
            # Even columns (0,2): normal order
            # Odd columns (1,3): reversed?

            # Linear offset within block: row * 16 + col
            block_offset = bly * block_w + blx

            # Total source offset
            src = (page_num * page_w * page_h +
                   block_num * block_w * block_h +
                   block_offset)

            if src < len(data):
                output[dst_y * width + dst_x] = data[src]

    return bytes(output)


def collect_image_data_r2118():
    """Collect IMAGE transfer data from R2118."""
    data = open(os.path.join(TEX_DIR, 'R2118_tavern_background.raw'), 'rb').read()
    tex = data[16:]
    total_qw = len(tex) // 16

    image_blocks = []
    i = 17  # Skip header QWs
    while i < total_qw:
        lo = struct.unpack_from('<Q', tex, i * 16)[0]
        nloop = lo & 0x7FFF
        flg = (lo >> 46) & 3

        if flg == 2 and nloop > 0:
            data_start = (i + 1) * 16
            data_size = min(nloop * 16, len(tex) - data_start)
            if data_size > 0:
                image_blocks.append((data_start, data_size))
            i += 1 + nloop
        else:
            # Try next few QWs for IMAGE tag
            found = False
            for j in range(i + 1, min(i + 5, total_qw)):
                lo2 = struct.unpack_from('<Q', tex, j * 16)[0]
                flg2 = (lo2 >> 46) & 3
                nloop2 = lo2 & 0x7FFF
                if flg2 == 2 and nloop2 > 0:
                    i = j
                    found = True
                    break
            if not found:
                remaining = len(tex) - i * 16
                if remaining > 0:
                    image_blocks.append((i * 16, remaining))
                break

    all_data = bytearray()
    for offset, size in image_blocks:
        all_data.extend(tex[offset:offset + size])

    return all_data


def main():
    # ===== R2118 with unswizzle =====
    print("R2118 with PSMT8 unswizzle:")
    all_data = collect_image_data_r2118()
    pixel_count = 512 * 512
    pal_size = 1024

    print(f"  Total IMAGE data: {len(all_data)}")

    pixels = bytes(all_data[:pixel_count])
    pal_raw = bytes(all_data[pixel_count:pixel_count + pal_size])

    palette = unswizzle_clut_psmt8(pal_raw)

    # Try with unswizzle v2
    unswizzled = psmt8_unswizzle_v2(pixels, 512, 512)

    img = Image.new('RGBA', (512, 512))
    pix_out = [palette[unswizzled[i]] for i in range(pixel_count)]
    img.putdata(pix_out)
    out_path = os.path.join(TEX_DIR, 'R2118_unswizzled.png')
    img.save(out_path)
    print(f"  Saved: {out_path}")

    # Also try without unswizzle but different block ordering
    # Try v1 unswizzle
    unswizzled_v1 = psmt8_unswizzle(pixels, 512, 512)
    img_v1 = Image.new('RGBA', (512, 512))
    pix_out_v1 = [palette[unswizzled_v1[i]] for i in range(pixel_count)]
    img_v1.putdata(pix_out_v1)
    out_path_v1 = os.path.join(TEX_DIR, 'R2118_unswizzle_v1.png')
    img_v1.save(out_path_v1)
    print(f"  Saved: {out_path_v1}")

    # ===== R2119 with unswizzle =====
    print("\nR2119 with PSMT8 unswizzle:")
    data = open(os.path.join(TEX_DIR, 'R2119_tavern_buttons_1.raw'), 'rb').read()
    tex = data[16:]

    w, h = 512, 64
    pixel_count2 = w * h
    pixels2 = tex[192:192 + pixel_count2]
    pal_raw2 = tex[192 + pixel_count2:192 + pixel_count2 + pal_size]
    palette2 = unswizzle_clut_psmt8(pal_raw2)

    unswizzled2 = psmt8_unswizzle_v2(pixels2, w, h)
    img2 = Image.new('RGBA', (w, h))
    pix_out2 = [palette2[unswizzled2[i]] for i in range(pixel_count2)]
    img2.putdata(pix_out2)
    out_path2 = os.path.join(TEX_DIR, 'R2119_unswizzled.png')
    img2.save(out_path2)
    print(f"  Saved: {out_path2}")


if __name__ == '__main__':
    main()
