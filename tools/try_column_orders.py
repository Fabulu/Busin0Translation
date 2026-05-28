#!/usr/bin/env python3
"""Try different column table interpretations for PSMT8 deswizzle."""
import sys, os
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

BASE = 'C:/Programmieren/wizardrytranslation/build/textures_to_edit'

blockTable8 = [
    [ 0,  1,  4,  5, 16, 17, 20, 21],
    [ 2,  3,  6,  7, 18, 19, 22, 23],
    [ 8,  9, 12, 13, 24, 25, 28, 29],
    [10, 11, 14, 15, 26, 27, 30, 31],
]

# PCSX2 column table
col_pcsx2 = [
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

# Alternative: simple linear column (no intra-block swizzle)
col_linear = [[y * 16 + x for x in range(16)] for y in range(16)]


def build_lut(col_table):
    lut = [None] * 8192
    for y in range(64):
        for x in range(128):
            bx, by = x // 16, y // 16
            lx, ly = x % 16, y % 16
            addr = blockTable8[by][bx] * 256 + col_table[ly][lx]
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


def decode(filename, width, height, lut, suffix):
    data = open(os.path.join(BASE, filename), 'rb').read()
    tex = data[16:]
    raw = tex[272:]
    pixel_count = width * height
    pal_data = raw[pixel_count:pixel_count + 1024]
    palette = unswizzle_clut(pal_data)

    PAGE_W, PAGE_H, PAGE_BYTES = 128, 64, 8192
    pages_x, pages_y = width // PAGE_W, height // PAGE_H

    out = bytearray(pixel_count)
    for py in range(pages_y):
        for px in range(pages_x):
            page_off = (py * pages_x + px) * PAGE_BYTES
            for i in range(PAGE_BYTES):
                src = page_off + i
                if src < len(raw) and lut[i] is not None:
                    lx, ly = lut[i]
                    ox, oy = px * PAGE_W + lx, py * PAGE_H + ly
                    if ox < width and oy < height:
                        out[oy * width + ox] = raw[src]

    img = Image.new('RGBA', (width, height))
    img.putdata([palette[out[j]] for j in range(pixel_count)])
    out_name = filename.replace('.raw', f'_{suffix}.png')
    img.save(os.path.join(BASE, out_name))
    print(f'Saved: {out_name}')


# Build LUTs
lut_pcsx2 = build_lut(col_pcsx2)
lut_linear = build_lut(col_linear)

# Test on R2118 (where we can see Japanese text)
for label, lut in [('block_pcsx2col', lut_pcsx2), ('block_linearcol', lut_linear)]:
    decode('R2118_tavern_background.raw', 512, 512, lut, label)

# Also test R2121
for label, lut in [('block_linearcol', lut_linear)]:
    decode('R2121_guild_background.raw', 512, 512, lut, label)

print('Done!')
