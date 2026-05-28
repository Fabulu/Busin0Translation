#!/usr/bin/env python3
"""Try PSMCT32-based block table with PSMT8 pixel format.

The PS2 GS can upload texture data using PSMCT32 BITBLTBUF setting
even for PSMT8 textures. In this case, the block layout used for
storage is the PSMCT32 block table, not the PSMT8 one.

PSMCT32 layout:
- Page: 64x32 pixels (at 32bpp) = 8192 bytes
- Block: 8x8 pixels (at 32bpp) = 256 bytes

But for 8bpp data stored using PSMCT32 layout:
- Page: 64*4 x 32 = 256x32 pixels (treating 4 bytes as 4 pixels)
- Block: 8*4 x 8 = 32x8 pixels

Or we can just use PSMCT32's block table with byte-level addressing.
"""
import os
import struct
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(BASE, "build", "textures_to_edit")

# PSMCT32 block table (8x4 blocks of 8x8 pixels within a 64x32 page)
PSMCT32_BLOCK_TABLE = [
    [ 0,  1,  4,  5, 16, 17, 20, 21],
    [ 2,  3,  6,  7, 18, 19, 22, 23],
    [ 8,  9, 12, 13, 24, 25, 28, 29],
    [10, 11, 14, 15, 26, 27, 30, 31],
]


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


def psmct32_as_psmt8_addr(x, y, bw):
    """Calculate address for PSMT8 data stored with PSMCT32 block layout.

    When data is uploaded as PSMCT32, each 32-bit word holds 4 consecutive 8-bit pixels.
    The PSMCT32 page is 64x32 words = 256x32 pixels (at 8bpp) = 8192 bytes.
    """
    # Treat data as PSMCT32: each "pixel" is 4 bytes (4 actual 8-bit pixels)
    word_x = x // 4  # Which 32-bit word
    byte_in_word = x % 4  # Which byte within the word

    # PSMCT32 page: 64x32 words
    page_w = 64  # words
    page_h = 32  # rows
    page_size = page_w * page_h * 4  # 8192 bytes

    # PSMCT32 block: 8x8 words
    block_w = 8  # words
    block_h = 8  # rows
    block_size = block_w * block_h * 4  # 256 bytes

    bw_words = bw // 4  # buffer width in 32-bit words

    # Page position
    page_x = word_x // page_w
    page_y = y // page_h
    pages_per_row = bw_words // page_w
    page_num = page_y * pages_per_row + page_x

    # Block position within page
    lx = word_x % page_w
    ly = y % page_h
    block_x = lx // block_w
    block_y = ly // block_h
    block_num = PSMCT32_BLOCK_TABLE[block_y][block_x]

    # Within block
    blx = lx % block_w
    bly = ly % block_h

    # PSMCT32 column interleave within 8x8 block
    # From PCSX2: columnTable32[y][x]
    # For PSMCT32, within an 8x8 block, the addressing is:
    # Each row is 8 words = 32 bytes
    # Even rows: words 0-7 in order
    # Odd rows: words 0-3 swap with words 4-7
    if bly & 1:
        actual_blx = blx ^ 4  # Swap left/right halves on odd rows
    else:
        actual_blx = blx

    word_offset = bly * block_w + actual_blx
    byte_addr = page_num * page_size + block_num * block_size + word_offset * 4 + byte_in_word

    return byte_addr


def try_psmct32_layout(data, width, height, bw):
    """Unswizzle assuming PSMCT32 block layout."""
    output = bytearray(width * height)
    for y in range(height):
        for x in range(width):
            addr = psmct32_as_psmt8_addr(x, y, bw)
            if addr < len(data):
                output[y * width + x] = data[addr]
    return bytes(output)


def try_psmct32_no_column(data, width, height, bw):
    """PSMCT32 block layout without column interleave."""
    output = bytearray(width * height)

    page_w = 256  # pixels at 8bpp
    page_h = 32
    page_size = 8192

    for y in range(height):
        for x in range(width):
            word_x = x // 4
            byte_in_word = x % 4

            page_x = word_x // 64
            page_y = y // 32
            pages_per_row = (bw // 4) // 64
            page_num = page_y * pages_per_row + page_x

            lx = word_x % 64
            ly = y % 32
            block_x = lx // 8
            block_y = ly // 8
            block_num = PSMCT32_BLOCK_TABLE[block_y][block_x]

            blx = lx % 8
            bly = ly % 8

            word_offset = bly * 8 + blx
            addr = page_num * page_size + block_num * 256 + word_offset * 4 + byte_in_word

            if addr < len(data):
                output[y * width + x] = data[addr]

    return bytes(output)


def try_simple_32bit_interleave(data, width, height):
    """Maybe the data is just interleaved in 32-bit words (4 bytes at a time)."""
    output = bytearray(width * height)

    # Try: read 4 pixels at a time, but from different row pattern
    # Maybe the rows alternate between two sets?

    # Simple 2x2 deinterlace
    for y in range(height):
        for x in range(width):
            # Try byte-to-pixel mapping where bytes are grouped in 4s
            # from a 32-bit write pattern
            output[y * width + x] = data[y * width + x] if y * width + x < len(data) else 0

    return bytes(output)


def decode_file(raw_name, width, height, method='psmct32'):
    """Decode a raw texture file."""
    raw_path = os.path.join(TEX_DIR, raw_name)
    data = open(raw_path, 'rb').read()
    tex = data[16:]

    pixel_count = width * height
    pal_size = 1024
    header_size = 192

    pixel_data = tex[header_size:header_size + pixel_count]
    pal_data = tex[header_size + pixel_count:header_size + pixel_count + pal_size]

    palette = unswizzle_clut_psmt8(pal_data)

    print(f"\nDecoding {raw_name}: {width}x{height} ({method})")

    if method == 'psmct32':
        unswizzled = try_psmct32_layout(pixel_data, width, height, bw=512)
    elif method == 'psmct32_nocol':
        unswizzled = try_psmct32_no_column(pixel_data, width, height, bw=512)
    elif method == 'linear':
        unswizzled = pixel_data
    else:
        unswizzled = pixel_data

    img = Image.new('RGBA', (width, height))
    pix_out = [palette[unswizzled[i]] for i in range(pixel_count)]
    img.putdata(pix_out)

    out_name = raw_name.replace('.raw', f'_{method}.png')
    out_path = os.path.join(TEX_DIR, out_name)
    img.save(out_path)
    print(f"  Saved: {out_path}")
    return img


def main():
    for method in ['psmct32', 'psmct32_nocol', 'linear']:
        decode_file('R2119_tavern_buttons_1.raw', 512, 64, method)

    # Only do psmct32 for R2118 (it's slow for 512x512)
    decode_file('R2118_tavern_background.raw', 512, 512, 'psmct32')


if __name__ == '__main__':
    main()
