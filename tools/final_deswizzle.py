#!/usr/bin/env python3
"""Final PSMT8 deswizzle using verified PCSX2 tables.

The PS2 GS stores texture data uploaded via GIF IMAGE mode in swizzled format.
This script uses the exact blockTable8 and columnTable8 from PCSX2's GSTables.cpp
to reverse the swizzle and produce a correctly ordered image.

The pixel address formula for PSMT8 is:
  page = (y // 64) * pages_per_row + (x // 128)
  block = blockTable8[y%64 // 16][x%128 // 16]
  column_byte = columnTable8[y%16][x%16]
  byte_address = page * 8192 + block * 256 + column_byte
"""
import sys, os
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(BASE, "build", "textures_to_edit")

blockTable8 = [
    [ 0,  1,  4,  5, 16, 17, 20, 21],
    [ 2,  3,  6,  7, 18, 19, 22, 23],
    [ 8,  9, 12, 13, 24, 25, 28, 29],
    [10, 11, 14, 15, 26, 27, 30, 31],
]

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


def build_inverse_lut():
    """Build inverse LUT: for each byte position in a page, what pixel (x,y) does it map to?"""
    lut = [None] * 8192
    for y in range(64):
        for x in range(128):
            bx, by = x // 16, y // 16
            lx, ly = x % 16, y % 16
            addr = blockTable8[by][bx] * 256 + columnTable8[ly][lx]
            lut[addr] = (x, y)
    return lut


def unswizzle_clut(pal_data):
    colors = []
    for i in range(256):
        off = i * 4
        if off + 3 < len(pal_data):
            r, g, b, a = pal_data[off], pal_data[off+1], pal_data[off+2], pal_data[off+3]
            colors.append((r, g, b, min(a * 2, 255)))
        else:
            colors.append((0, 0, 0, 0))
    for grp in range(8):
        base = grp * 32
        for j in range(8):
            colors[base + 8 + j], colors[base + 16 + j] = \
                colors[base + 16 + j], colors[base + 8 + j]
    return colors


def decode(filename, width, height, lut):
    filepath = os.path.join(TEX_DIR, filename)
    data = open(filepath, 'rb').read()
    tex = data[16:]
    raw = tex[192:]

    pixel_count = width * height
    pal_data = raw[pixel_count:pixel_count + 1024]
    palette = unswizzle_clut(pal_data)

    PAGE_W, PAGE_H = 128, 64
    PAGE_BYTES = 8192
    pages_x = width // PAGE_W
    pages_y = height // PAGE_H

    # Deswizzle
    out = bytearray(pixel_count)
    for py in range(pages_y):
        for px in range(pages_x):
            page_idx = py * pages_x + px
            page_off = page_idx * PAGE_BYTES
            for i in range(PAGE_BYTES):
                src = page_off + i
                if src < len(raw) and lut[i] is not None:
                    lx, ly = lut[i]
                    ox = px * PAGE_W + lx
                    oy = py * PAGE_H + ly
                    if ox < width and oy < height:
                        out[oy * width + ox] = raw[src]

    img = Image.new('RGBA', (width, height))
    img.putdata([palette[out[j]] for j in range(pixel_count)])
    out_path = os.path.join(TEX_DIR, filename.replace('.raw', '.png'))
    img.save(out_path)
    print(f'Saved: {out_path}')


if __name__ == '__main__':
    lut = build_inverse_lut()
    assert all(e is not None for e in lut), "LUT has None entries!"
    print(f"LUT built: {len(set(lut))} unique coords")

    decode('R2119_tavern_buttons_1.raw', 512, 64, lut)
    decode('R2118_tavern_background.raw', 512, 512, lut)
    decode('R2121_guild_background.raw', 512, 512, lut)
    decode('R2122_guild_buttons.raw', 512, 64, lut)
    decode('R2120_tavern_buttons_2.raw', 512, 64, lut)
    decode('R2124_menu_overlay.raw', 512, 64, lut)
    print('Done!')
