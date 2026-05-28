#!/usr/bin/env python3
"""PS2 PSMT8 unswizzle - correct GS pixel address from PCSX2 source.

The raw file contains GS-internal swizzled pixel data.
To display it, we need to compute the GS byte address for each (x,y)
pixel and read from that address in the raw data.

PSMT8 layout:
- Page: 128x64 pixels (8192 bytes)
- Block: 16x16 pixels (256 bytes)
- Column: 16x2 pixels (32 bytes)

References:
- PCSX2 GSLocalMemory::pixelAddress8
- ps2dev GS documentation
"""
import os
import struct
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(BASE, "build", "textures_to_edit")

# PSMT8 block arrangement within a page (128x64 pixels = 8x4 blocks of 16x16)
# block_table[row][col] = block_number in memory
PSMT8_BLOCK_TABLE = [
    [ 0,  1,  4,  5, 16, 17, 20, 21],
    [ 2,  3,  6,  7, 18, 19, 22, 23],
    [ 8,  9, 12, 13, 24, 25, 28, 29],
    [10, 11, 14, 15, 26, 27, 30, 31],
]

# PSMT8 column table - defines pixel mapping within a 16x16 block
# For PSMT8, each 16x16 block = 256 bytes
# Organized as: 4 columns of 16x4 pixels (64 bytes each)
# Within each column, pixels are interleaved

# From PCSX2 GSLocalMemory.cpp - PSMT8 column table:
# The columnTable8 maps (x, y) within a 16x16 block to byte offset
# Based on the PCSX2 source code:

def make_column_table_8():
    """Generate PSMT8 column table from PCSX2 algorithm."""
    # PSMT8: 16x16 block, column width=16, column height=4
    # 4 columns per block, each 64 bytes

    # From PCSX2: the 8-bit column table for 16x16
    # The pattern repeats every 4 rows with two halves swapping

    table = [[0] * 16 for _ in range(16)]

    for y in range(16):
        col = y // 4  # Column index (0-3)
        row_in_col = y % 4

        for x in range(16):
            # Within each column (16x4), the addressing is:
            # Even row pair (0-1): normal
            # Odd row pair (2-3): halves swapped

            # Actually from PCSX2 source the column table is:
            # For PSMT8, the byte offset within the block is:
            # column * 64 + row_in_column * 16 + x
            # With row interleaving for odd rows

            if row_in_col & 1:  # Odd row within column
                # Swap left and right halves (8 pixels each)
                actual_x = x ^ 8  # XOR with 8 swaps halves
            else:
                actual_x = x

            offset = col * 64 + row_in_col * 16 + actual_x
            table[y][x] = offset

    return table

COLUMN_TABLE_8 = make_column_table_8()


def psmt8_pixel_addr(x, y, bw):
    """Calculate byte address in GS local memory for PSMT8 pixel.

    bw: buffer width in pixels (multiple of 128, from TBW * 64)
    """
    page_w = 128
    page_h = 64
    page_size = 8192  # 128 * 64

    # Page position
    page_x = x // page_w
    page_y = y // page_h
    pages_per_row = bw // page_w
    page_num = page_y * pages_per_row + page_x

    # Block position within page
    lx = x % page_w
    ly = y % page_h
    block_x = lx // 16
    block_y = ly // 16
    block_num = PSMT8_BLOCK_TABLE[block_y][block_x]

    # Pixel position within block
    blx = lx % 16
    bly = ly % 16
    col_offset = COLUMN_TABLE_8[bly][blx]

    return page_num * page_size + block_num * 256 + col_offset


def unswizzle_psmt8(data, width, height, bw=None):
    """Unswizzle PSMT8 data from GS-internal format to linear."""
    if bw is None:
        bw = max(width, 128)
    if bw % 128 != 0:
        bw = ((bw + 127) // 128) * 128

    output = bytearray(width * height)
    for y in range(height):
        for x in range(width):
            addr = psmt8_pixel_addr(x, y, bw)
            if addr < len(data):
                output[y * width + x] = data[addr]
    return bytes(output)


def unswizzle_clut_psmt8(palette_data):
    """Unswizzle PS2 CLUT for PSMT8."""
    colors = []
    for i in range(256):
        off = i * 4
        if off + 3 < len(palette_data):
            r, g, b, a = palette_data[off], palette_data[off+1], palette_data[off+2], palette_data[off+3]
            a = min(a * 2, 255)
            colors.append((r, g, b, a))
        else:
            colors.append((0, 0, 0, 0))
    # CLUT interleave: swap entries 8-15 with 16-23 in each group of 32
    unswizzled = list(colors)
    for grp in range(8):
        base = grp * 32
        for j in range(8):
            unswizzled[base + 8 + j], unswizzled[base + 16 + j] = \
                unswizzled[base + 16 + j], unswizzled[base + 8 + j]
    return unswizzled


def decode_file(raw_name, width, height):
    """Decode a raw texture file."""
    raw_path = os.path.join(TEX_DIR, raw_name)
    data = open(raw_path, 'rb').read()
    tex = data[16:]  # Skip 16-byte sub-header

    pixel_count = width * height
    pal_size = 1024
    header_size = 192

    pixel_data = tex[header_size:header_size + pixel_count]
    pal_data = tex[header_size + pixel_count:header_size + pixel_count + pal_size]

    print(f"\nDecoding {raw_name}: {width}x{height}")
    print(f"  Pixel data: {len(pixel_data)} bytes")
    print(f"  Palette data: {len(pal_data)} bytes")

    palette = unswizzle_clut_psmt8(pal_data)

    # Unswizzle with GS address calculation
    print("  Unswizzling...")
    unswizzled = unswizzle_psmt8(pixel_data, width, height, bw=512)

    # Save
    img = Image.new('RGBA', (width, height))
    pix_out = [palette[unswizzled[i]] for i in range(pixel_count)]
    img.putdata(pix_out)

    out_name = raw_name.replace('.raw', '.png')
    out_path = os.path.join(TEX_DIR, out_name)
    img.save(out_path)
    print(f"  Saved: {out_path}")

    return img


def main():
    decode_file('R2119_tavern_buttons_1.raw', 512, 64)
    decode_file('R2118_tavern_background.raw', 512, 512)


if __name__ == '__main__':
    main()
