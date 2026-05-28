#!/usr/bin/env python3
"""Extract R2121 and R2122 CockpitImg textures with correct PCSX2 PSMT8 deswizzle.

Uses exact tables from PCSX2 GSTables.cpp.
"""
import struct, sys, os
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(BASE, "build", "textures_to_edit")

# From PCSX2 GSTables.cpp - blockTable8[4][8]
blockTable8 = [
    [ 0,  1,  4,  5, 16, 17, 20, 21],
    [ 2,  3,  6,  7, 18, 19, 22, 23],
    [ 8,  9, 12, 13, 24, 25, 28, 29],
    [10, 11, 14, 15, 26, 27, 30, 31],
]

# From PCSX2 GSTables.cpp - columnTable8[16][16]
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


def build_page_lut():
    """Build forward LUT: page_lut[linear_byte] = (x, y) within a 128x64 page."""
    PAGE_W, PAGE_H = 128, 64
    BLOCK_W, BLOCK_H = 16, 16
    BLOCKS_X = PAGE_W // BLOCK_W  # 8
    BLOCKS_Y = PAGE_H // BLOCK_H  # 4

    # Invert block table: block_number -> (bx, by)
    inv_block = {}
    for by in range(4):
        for bx in range(8):
            inv_block[blockTable8[by][bx]] = (bx, by)

    # Invert column table: byte_offset_in_block -> (lx, ly)
    inv_column = {}
    for ly in range(16):
        for lx in range(16):
            inv_column[columnTable8[ly][lx]] = (lx, ly)

    # Verify completeness
    assert len(inv_block) == 32, f"Expected 32 blocks, got {len(inv_block)}"
    assert len(inv_column) == 256, f"Expected 256 column entries, got {len(inv_column)}"

    lut = [(0, 0)] * (PAGE_W * PAGE_H)

    for bn in range(32):
        bx, by = inv_block[bn]
        block_start = bn * 256  # 256 bytes per block

        for byte_in_block in range(256):
            lx, ly = inv_column[byte_in_block]
            page_byte = block_start + byte_in_block
            px = bx * BLOCK_W + lx
            py = by * BLOCK_H + ly

            if page_byte < len(lut):
                lut[page_byte] = (px, py)

    return lut


def deswizzle_psmt8(raw_data, tex_w, tex_h, lut):
    """Deswizzle PSMT8 texture using the page LUT."""
    PAGE_W, PAGE_H = 128, 64
    PAGE_BYTES = PAGE_W * PAGE_H  # 8192
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
    """Unswizzle PS2 PSMT8 CLUT: swap entries 8-15 with 16-23 in each group of 32."""
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
    """Decode a PSMT8 CockpitImg resource."""
    filepath = os.path.join(TEX_DIR, filename)
    data = open(filepath, 'rb').read()
    tex = data[16:]  # skip sub-header
    raw = tex[272:]  # skip first PACKED GIF tag (17 QWs)

    pixel_count = width * height
    pal_size = 1024

    pixel_bytes = raw[:pixel_count]
    pal_bytes = raw[pixel_count:pixel_count + pal_size]
    palette = unswizzle_clut(pal_bytes)

    print(f"\n{filename}: {width}x{height} PSMT8")

    # Deswizzled
    px = deswizzle_psmt8(pixel_bytes, width, height, lut)
    img = Image.new('RGBA', (width, height))
    img.putdata([palette[px[j]] for j in range(pixel_count)])
    out = os.path.join(TEX_DIR, filename.replace('.raw', '.png'))
    img.save(out)
    print(f"  Saved: {out}")

    # Also save linear for reference
    img_lin = Image.new('RGBA', (width, height))
    img_lin.putdata([palette[pixel_bytes[j]] for j in range(min(pixel_count, len(pixel_bytes)))])
    out_lin = os.path.join(TEX_DIR, filename.replace('.raw', '_linear_ref.png'))
    img_lin.save(out_lin)
    print(f"  Saved: {out_lin}")


if __name__ == '__main__':
    print("Building PSMT8 page LUT from PCSX2 tables...")
    lut = build_page_lut()
    coords = set(lut)
    print(f"  {len(coords)} unique coordinates, range x=0..{max(c[0] for c in lut)}, y=0..{max(c[1] for c in lut)}")

    decode_resource('R2121_guild_background.raw', 512, 512, lut)
    decode_resource('R2122_guild_buttons.raw', 512, 64, lut)
    # R2118 for validation
    decode_resource('R2118_tavern_background.raw', 512, 512, lut)

    print("\nDone!")
