#!/usr/bin/env python3
"""PS2 PSMT8 exact deswizzle using the GS pixel address calculation.

Reference: PCSX2 GS documentation and GSLocalMemory.cpp
The PS2 GS stores PSMT8 textures using a multi-level addressing:
  1. Page level: 128x64 pixels per page (8192 bytes)
  2. Block level: 16x16 pixels per block (256 bytes), 32 blocks per page
  3. Column level: 16x4 pixels per column, 4 columns per block
  4. Pixel level: specific byte interleave within columns
"""
import sys, os
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(BASE, "build", "textures_to_edit")

# PCSX2-derived PSMT8 tables
# blockTable8[by][bx] - block number for position (bx, by) within a page
blockTable8 = [
    [ 0,  1,  4,  5, 16, 17, 20, 21],
    [ 2,  3,  6,  7, 18, 19, 22, 23],
    [ 8,  9, 12, 13, 24, 25, 28, 29],
    [10, 11, 14, 15, 26, 27, 30, 31],
]

# columnTable8[cy][cx] - byte position within 16x4 column for pixel (cx, cy)
# From PCSX2 GSTables.h
columnTable8 = [
    [  0,   4,   8,  12,  16,  20,  24,  28,   2,   6,  10,  14,  18,  22,  26,  30],
    [ 33,  37,  41,  45,  49,  53,  57,  61,  35,  39,  43,  47,  51,  55,  59,  63],
    [  1,   5,   9,  13,  17,  21,  25,  29,   3,   7,  11,  15,  19,  23,  27,  31],
    [ 32,  36,  40,  44,  48,  52,  56,  60,  34,  38,  42,  46,  50,  54,  58,  62],
]


def pixelAddress8(x, y, bp, bw):
    """Calculate the byte address of a PSMT8 pixel at (x, y).
    bp = base pointer (in 256-byte units), bw = buffer width (in 64-pixel units).
    Returns byte offset in VRAM."""
    PAGE_W = 128
    PAGE_H = 64
    BLOCK_W = 16
    BLOCK_H = 16
    COL_H = 4

    # Page coordinates
    page_x = x // PAGE_W
    page_y = y // PAGE_H
    page = page_y * bw + page_x  # bw is in 64-pixel units = number of page-widths/2

    # Actually bw for PSMT8 means: number of 64-pixel units of buffer width
    # For width=512: bw = 512/64 = 8, and pages_per_row = 512/128 = 4
    # So page = page_y * (bw/2) + page_x  ???
    # No: in PCSX2, for PSMT8: page = (bp + page_y * bw * 2 + page_x) * 8192
    # Let me use the simpler formula: linear page within the texture data

    # For our case (reading from linear data, not VRAM), we can simplify:
    # page index = page_y * pages_per_row + page_x
    pages_per_row = bw * 64 // PAGE_W  # This depends on interpretation of bw
    # Actually for PSMT8 in PCSX2: bw is already in 64-pixel columns
    # page width in pixels = 128, so pages_per_row = (bw * 64) / 128 = bw / 2
    # But that can be fractional... let's use bw directly
    # For a 512-wide texture with bw=8: pages_per_row = 8*64/128 = 4

    page = page_y * (bw * 64 // PAGE_W) + page_x

    # Block within page
    bx = (x % PAGE_W) // BLOCK_W
    by = (y % PAGE_H) // BLOCK_H
    block = blockTable8[by][bx]

    # Column within block
    cy = (y % BLOCK_H) // COL_H
    cx = x % BLOCK_W
    col_y = y % COL_H

    # Byte offset within column
    col_offset = columnTable8[col_y][cx]

    # Total byte address
    byte_addr = page * 8192 + block * 256 + cy * 64 + col_offset

    return byte_addr


def deswizzle_psmt8_exact(raw_data, tex_w, tex_h, bw):
    """Deswizzle PSMT8 texture using exact address calculation."""
    out = bytearray(tex_w * tex_h)

    for y in range(tex_h):
        for x in range(tex_w):
            addr = pixelAddress8(x, y, 0, bw)
            if addr < len(raw_data):
                out[y * tex_w + x] = raw_data[addr]

    return bytes(out)


def unswizzle_clut(palette_data):
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


def decode_resource(filename, width, height, bw):
    filepath = os.path.join(TEX_DIR, filename)
    data = open(filepath, 'rb').read()
    tex = data[16:]
    raw = tex[272:]  # after GIF header

    pixel_count = width * height
    pal_size = 1024

    pixel_bytes = raw[:pixel_count]
    pal_bytes = raw[pixel_count:pixel_count + pal_size]
    palette = unswizzle_clut(pal_bytes)

    print(f"\nProcessing {filename} ({width}x{height}, bw={bw})")

    # Exact deswizzle
    px = deswizzle_psmt8_exact(pixel_bytes, width, height, bw)
    img = Image.new('RGBA', (width, height))
    img.putdata([palette[px[j]] for j in range(pixel_count)])
    out = os.path.join(TEX_DIR, filename.replace('.raw', '.png'))
    img.save(out)
    print(f"  Saved: {out}")

    # Also try with different bw values
    for test_bw in [4, 8, 16]:
        if test_bw == bw:
            continue
        px2 = deswizzle_psmt8_exact(pixel_bytes, width, height, test_bw)
        img2 = Image.new('RGBA', (width, height))
        img2.putdata([palette[px2[j]] for j in range(pixel_count)])
        out2 = os.path.join(TEX_DIR, filename.replace('.raw', f'_bw{test_bw}.png'))
        img2.save(out2)
        print(f"  Saved: {out2}")


if __name__ == '__main__':
    # TEX0 says TBW=8 for both R2121 and R2122
    # TBW for PSMT8: buffer width in 64-pixel units
    # TBW=8 -> 8*64 = 512 pixels wide (matches)
    decode_resource('R2121_guild_background.raw', 512, 512, 8)
    decode_resource('R2122_guild_buttons.raw', 512, 64, 8)
    decode_resource('R2118_tavern_background.raw', 512, 512, 8)
    print("\nDone!")
