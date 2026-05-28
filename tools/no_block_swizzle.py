#!/usr/bin/env python3
"""Try PCSX2 column table WITHOUT block swizzle."""
import os
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(BASE, "build", "textures_to_edit")

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


def decode_file(filename, width, height):
    data = open(os.path.join(TEX_DIR, filename), 'rb').read()
    tex = data[16:]
    raw = tex[192:]

    pixel_count = width * height
    pal = unswizzle_clut(raw[pixel_count:pixel_count + 1024])

    # Build block map (byte offset in block -> pixel position in block)
    block_map = [(0, 0)] * 256
    for y in range(16):
        for x in range(16):
            block_map[columnTable8[y][x]] = (x, y)

    # Use LINEAR block ordering (no blockTable8)
    # Blocks are 16x16 pixels, arranged left-to-right, top-to-bottom
    # Page is 128x64 pixels = 8 blocks wide x 4 blocks tall

    block_w = 16
    block_h = 16
    blocks_per_row = width // block_w  # 512/16 = 32

    img = Image.new('RGBA', (width, height))
    pixels = [(0, 0, 0, 0)] * pixel_count

    for i in range(min(len(raw), pixel_count)):
        block_idx = i // 256
        byte_in_block = i % 256

        block_row = block_idx // blocks_per_row
        block_col = block_idx % blocks_per_row

        dx, dy = block_map[byte_in_block]

        x = block_col * block_w + dx
        y = block_row * block_h + dy

        if 0 <= x < width and 0 <= y < height:
            pixels[y * width + x] = pal[raw[i]]

    img.putdata(pixels)
    out_path = os.path.join(TEX_DIR, filename.replace('.raw', '.png'))
    img.save(out_path)
    print(f"Saved: {out_path}")

    # Zoom
    if height <= 128:
        crop = img.crop((60, 15, 400, min(50, height)))
        zoom = 4
    else:
        crop = img.crop((0, height//4, width, height*3//4))
        zoom = 2
    zoomed = crop.resize((crop.width * zoom, crop.height * zoom), Image.NEAREST)
    zoomed.save(out_path.replace('.png', '_zoom.png'))


if __name__ == '__main__':
    decode_file('R2119_tavern_buttons_1.raw', 512, 64)
    decode_file('R2118_tavern_background.raw', 512, 512)
