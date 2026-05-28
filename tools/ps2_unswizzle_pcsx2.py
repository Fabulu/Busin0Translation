#!/usr/bin/env python3
"""PS2 PSMT8 unswizzle using exact PCSX2 lookup tables.

From PCSX2 GSLocalMemory.cpp, the pixel address calculation for PSMT8
uses pre-computed tables: blockTable8, columnTable8.

These tables are well-documented in the PCSX2 source code.
"""
import os
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(BASE, "build", "textures_to_edit")

# PCSX2 blockTable8[4][8] - block number within a 128x64 page
# Rows: 4 block rows (each 16 pixels tall), Cols: 8 block columns (each 16 pixels wide)
blockTable8 = [
    [ 0,  1,  4,  5, 16, 17, 20, 21],
    [ 2,  3,  6,  7, 18, 19, 22, 23],
    [ 8,  9, 12, 13, 24, 25, 28, 29],
    [10, 11, 14, 15, 26, 27, 30, 31],
]

# PCSX2 columnTable8[16][16] - byte offset within a 16x16 block
# This is the EXACT table from PCSX2 source
# From: https://github.com/PCSX2/pcsx2/blob/master/pcsx2/GS/GSLocalMemory.cpp
# The columnTable8 is a 16x16 table where [y][x] gives the byte offset
# within the 256-byte block for the pixel at position (x, y).

# PCSX2 uses two column tables that alternate based on the block column
# For even columns:
columnTable8 = [
    [  0,   4,  16,  20,  32,  36,  48,  52,   2,   6,  18,  22,  34,  38,  50,  54],
    [  8,  12,  24,  28,  40,  44,  56,  60,  10,  14,  26,  30,  42,  46,  58,  62],
    [ 33,  37,  49,  53,   1,   5,  17,  21,  35,  39,  51,  55,   3,   7,  19,  23],
    [ 41,  45,  57,  61,   9,  13,  25,  29,  43,  47,  59,  63,  11,  15,  27,  31],
    [ 96, 100, 112, 116,  64,  68,  80,  84,  98, 102, 114, 118,  66,  70,  82,  86],
    [104, 108, 120, 124,  72,  76,  88,  92, 106, 110, 122, 126,  74,  78,  90,  94],
    [ 65,  69,  81,  85,  97, 101, 113, 117,  67,  71,  83,  87,  99, 103, 115, 119],
    [ 73,  77,  89,  93, 105, 109, 121, 125,  75,  79,  91,  95, 107, 111, 123, 127],
    [128, 132, 144, 148, 160, 164, 176, 180, 130, 134, 146, 150, 162, 166, 178, 182],
    [136, 140, 152, 156, 168, 172, 184, 188, 138, 142, 154, 158, 170, 174, 186, 190],
    [161, 165, 177, 181, 129, 133, 145, 149, 163, 167, 179, 183, 131, 135, 147, 151],
    [169, 173, 185, 189, 137, 141, 153, 157, 171, 175, 187, 191, 139, 143, 155, 159],
    [224, 228, 240, 244, 192, 196, 208, 212, 226, 230, 242, 246, 194, 198, 210, 214],
    [232, 236, 248, 252, 200, 204, 216, 220, 234, 238, 250, 254, 202, 206, 218, 222],
    [193, 197, 209, 213, 225, 229, 241, 245, 195, 199, 211, 215, 227, 231, 243, 247],
    [201, 205, 217, 221, 233, 237, 249, 253, 203, 207, 219, 223, 235, 239, 251, 255],
]


def psmt8_addr(x, y, bw):
    """Calculate exact GS memory byte address for PSMT8 pixel at (x, y).

    bw: buffer width in pixels (must be multiple of 128).
    Returns: byte offset in GS local memory.
    """
    # Page: 128x64
    page_x = x >> 7  # x // 128
    page_y = y >> 6  # y // 64
    page = page_y * (bw >> 7) + page_x  # page_y * pages_per_row + page_x

    # Block within page: 16x16
    lx = x & 127  # x % 128
    ly = y & 63   # y % 64
    block = blockTable8[ly >> 4][lx >> 4]

    # Byte within block
    bx = lx & 15  # x % 16
    by = ly & 15  # y % 16
    col_off = columnTable8[by][bx]

    return (page * 8192 + block * 256 + col_off)


def unswizzle_psmt8(data, width, height, bw=None):
    """Unswizzle PSMT8 pixel data using PCSX2 address calculation."""
    if bw is None:
        bw = max(width, 128)
    if bw & 127:
        bw = (bw + 127) & ~127

    output = bytearray(width * height)
    for y in range(height):
        for x in range(width):
            addr = psmt8_addr(x, y, bw)
            if addr < len(data):
                output[y * width + x] = data[addr]
    return bytes(output)


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


def decode_file(raw_name, width, height):
    raw_path = os.path.join(TEX_DIR, raw_name)
    data = open(raw_path, 'rb').read()
    tex = data[16:]

    pixel_count = width * height
    pal_size = 1024
    header_size = 192

    pixel_data = tex[header_size:header_size + pixel_count]
    pal_data = tex[header_size + pixel_count:header_size + pixel_count + pal_size]

    print(f"Decoding {raw_name}: {width}x{height}")

    palette = unswizzle_clut_psmt8(pal_data)

    # Unswizzle
    print("  Unswizzling with PCSX2 tables...")
    unswizzled = unswizzle_psmt8(pixel_data, width, height, bw=512)

    img = Image.new('RGBA', (width, height))
    pix_out = [palette[unswizzled[i]] for i in range(pixel_count)]
    img.putdata(pix_out)

    out_name = raw_name.replace('.raw', '.png')
    out_path = os.path.join(TEX_DIR, out_name)
    img.save(out_path)
    print(f"  Saved: {out_path}")

    # Save zoomed version
    if height <= 128:
        crop = img.crop((60, max(0, height//4), min(400, width), min(height, height*3//4)))
    else:
        crop = img.crop((0, height//4, width, height//2))
    zoomed = crop.resize((crop.width * 3, crop.height * 3), Image.NEAREST)
    zoom_path = out_path.replace('.png', '_zoom.png')
    zoomed.save(zoom_path)
    print(f"  Saved zoom: {zoom_path}")


def main():
    decode_file('R2119_tavern_buttons_1.raw', 512, 64)
    decode_file('R2118_tavern_background.raw', 512, 512)


if __name__ == '__main__':
    main()
