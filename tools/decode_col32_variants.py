#!/usr/bin/env python3
"""Try different pixel orderings within the 32-byte column."""
import os
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(BASE, "build", "textures_to_edit")


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


def decode_with_col_map(raw, w, h, palette, col_map, name):
    """Decode using a 32-byte column with custom pixel mapping.

    col_map: list of 32 (dx, dy) pairs mapping byte index -> pixel offset within column.
    """
    img = Image.new('RGBA', (w, h))
    pixels = [(0, 0, 0, 0)] * (w * h)

    col_w = 16
    col_h = 2
    cols_per_row = w // col_w  # 512/16 = 32

    for i in range(min(len(raw), w * h)):
        col_idx = i // 32
        byte_in_col = i % 32

        col_row = col_idx // cols_per_row
        col_col = col_idx % cols_per_row

        dx, dy = col_map[byte_in_col]

        x = col_col * col_w + dx
        y = col_row * col_h + dy

        if 0 <= x < w and 0 <= y < h:
            pixels[y * w + x] = palette[raw[i]]

    img.putdata(pixels)
    out_path = os.path.join(TEX_DIR, name)
    img.save(out_path)

    # Zoom
    crop = img.crop((60, 15, 400, 50))
    zoomed = crop.resize((crop.width * 4, crop.height * 4), Image.NEAREST)
    zoomed.save(out_path.replace('.png', '_zoom.png'))
    print(f"Saved: {name}")


def main():
    data = open(os.path.join(TEX_DIR, 'R2119_tavern_buttons_1.raw'), 'rb').read()
    tex = data[16:]
    w, h = 512, 64
    raw = tex[192:192 + w * h]
    pal = unswizzle_clut(tex[192 + w * h:192 + w * h + 1024])

    # From the PCSX2 columnTable8, the first 2 rows (32 bytes) of a block:
    # Row 0: [0, 4, 16, 20, 32, 36, 48, 52, 2, 6, 18, 22, 34, 38, 50, 54]
    # Row 1: [8, 12, 24, 28, 40, 44, 56, 60, 10, 14, 26, 30, 42, 46, 58, 62]

    # This means byte 0 of a column is at pixel (0,0)
    # byte 4 is at pixel (1,0), byte 16 at (2,0), etc.
    # But bytes 8,12,24,28,... are at row 1

    # Within a 32-byte column (bytes 0-31), the mapping would be:
    # Extract from columnTable8 for y=0 and y=1:
    ct_row0 = [0, 4, 16, 20, 32, 36, 48, 52, 2, 6, 18, 22, 34, 38, 50, 54]
    ct_row1 = [8, 12, 24, 28, 40, 44, 56, 60, 10, 14, 26, 30, 42, 46, 58, 62]

    # Build inverse: for each byte offset 0-63 (in the block), find (x, y) within first 2 rows
    inv = {}
    for x in range(16):
        inv[ct_row0[x]] = (x, 0)
        inv[ct_row1[x]] = (x, 1)

    # Extract just the bytes 0-31 mapping (first column of the block)
    col_map = []
    for byte_idx in range(32):
        if byte_idx in inv:
            col_map.append(inv[byte_idx])
        else:
            col_map.append((byte_idx % 16, byte_idx // 16))

    # But wait, the first column is bytes 0-63 (all bytes 0-63 in the block with offset < 64)
    # The columnTable8 row 0 gives byte offsets for pixels (0-15, y=0)
    # These byte offsets range from 0 to 54
    # Row 1 offsets range from 8 to 62
    # So both rows use bytes in the range 0-62 -> 63 bytes? That's a 16x4 column actually...

    # Let me reconsider. The PCSX2 columnTable8 is for a 16x16 BLOCK not a COLUMN.
    # A column within the block is 16x4 pixels = 64 bytes.
    # The table gives the BYTE OFFSET WITHIN THE BLOCK for each pixel.

    # For pixels at (x, y=0): offsets are [0,4,16,20,32,36,48,52,2,6,18,22,34,38,50,54]
    # For pixels at (x, y=1): offsets are [8,12,24,28,40,44,56,60,10,14,26,30,42,46,58,62]
    # For pixels at (x, y=2): offsets are [33,37,49,53,1,5,17,21,35,39,51,55,3,7,19,23]
    # For pixels at (x, y=3): offsets are [41,45,57,61,9,13,25,29,43,47,59,63,11,15,27,31]

    # All byte offsets 0-63 are used for the first 4 rows (column 0 of the block)
    # Column 1 uses offsets 64-127, etc.

    # So within a 64-byte column (16x4 pixels), the mapping is:
    col64_map = {}
    for y in range(4):
        for x in range(16):
            byte_off = [
                [0, 4, 16, 20, 32, 36, 48, 52, 2, 6, 18, 22, 34, 38, 50, 54],
                [8, 12, 24, 28, 40, 44, 56, 60, 10, 14, 26, 30, 42, 46, 58, 62],
                [33, 37, 49, 53, 1, 5, 17, 21, 35, 39, 51, 55, 3, 7, 19, 23],
                [41, 45, 57, 61, 9, 13, 25, 29, 43, 47, 59, 63, 11, 15, 27, 31],
            ][y][x]
            col64_map[byte_off] = (x, y)

    # Build col64 map as a list
    col64_list = [(0, 0)] * 64
    for byte_off, (x, y) in col64_map.items():
        col64_list[byte_off] = (x, y)

    # Now decode using 64-byte columns (16x4 pixels)
    # Columns are arranged left-to-right, top-to-bottom
    col_w = 16
    col_h = 4
    cols_per_row = w // col_w  # 32

    img = Image.new('RGBA', (w, h))
    pixels = [(0, 0, 0, 0)] * (w * h)

    for i in range(min(len(raw), w * h)):
        col_idx = i // 64
        byte_in_col = i % 64

        col_row = col_idx // cols_per_row
        col_col = col_idx % cols_per_row

        dx, dy = col64_list[byte_in_col]

        x = col_col * col_w + dx
        y = col_row * col_h + dy

        if 0 <= x < w and 0 <= y < h:
            pixels[y * w + x] = pal[raw[i]]

    img.putdata(pixels)
    out_path = os.path.join(TEX_DIR, 'R2119_col64_pcsx2.png')
    img.save(out_path)

    crop = img.crop((60, 15, 400, 50))
    zoomed = crop.resize((crop.width * 4, crop.height * 4), Image.NEAREST)
    zoomed.save(os.path.join(TEX_DIR, 'R2119_col64_pcsx2_zoom.png'))
    print(f"Saved: R2119_col64_pcsx2.png")

    # Now try with FULL block layout: 256 bytes per block (16x16), with block table
    # Blocks arranged within pages using blockTable8
    blockTable8 = [
        [0, 1, 4, 5, 16, 17, 20, 21],
        [2, 3, 6, 7, 18, 19, 22, 23],
        [8, 9, 12, 13, 24, 25, 28, 29],
        [10, 11, 14, 15, 26, 27, 30, 31],
    ]

    # Build full block pixel map (256 bytes -> 16x16 pixels)
    ct8 = [
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
    block_map = [(0, 0)] * 256
    for y in range(16):
        for x in range(16):
            byte_off = ct8[y][x]
            block_map[byte_off] = (x, y)

    # Build inverse block table (block_num -> block_x, block_y within page)
    inv_block = {}
    for by in range(4):
        for bx in range(8):
            inv_block[blockTable8[by][bx]] = (bx, by)

    page_w = 128
    page_h = 64
    page_bytes = 8192
    pages_per_row = w // page_w  # 512/128 = 4

    img2 = Image.new('RGBA', (w, h))
    pixels2 = [(0, 0, 0, 0)] * (w * h)

    for i in range(min(len(raw), w * h)):
        # Which page?
        page_idx = i // page_bytes
        byte_in_page = i % page_bytes

        page_y = page_idx // pages_per_row
        page_x = page_idx % pages_per_row

        # Which block within page?
        block_idx = byte_in_page // 256
        byte_in_block = byte_in_page % 256

        if block_idx not in inv_block:
            continue

        bx, by = inv_block[block_idx]
        dx, dy = block_map[byte_in_block]

        x = page_x * page_w + bx * 16 + dx
        y = page_y * page_h + by * 16 + dy

        if 0 <= x < w and 0 <= y < h:
            pixels2[y * w + x] = pal[raw[i]]

    img2.putdata(pixels2)
    out_path2 = os.path.join(TEX_DIR, 'R2119_full_block.png')
    img2.save(out_path2)

    crop2 = img2.crop((60, 15, 400, 50))
    zoomed2 = crop2.resize((crop2.width * 4, crop2.height * 4), Image.NEAREST)
    zoomed2.save(os.path.join(TEX_DIR, 'R2119_full_block_zoom.png'))
    print(f"Saved: R2119_full_block.png")


if __name__ == '__main__':
    main()
