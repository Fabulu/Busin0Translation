#!/usr/bin/env python3
"""PS2 PSMT8 unswizzle - try multiple column interleave patterns."""
import struct
import os
import array
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(BASE, "build", "textures_to_edit")

# PSMT8 block layout
PSMT8_BLOCK_LAYOUT = [
    [ 0,  1,  4,  5, 16, 17, 20, 21],
    [ 2,  3,  6,  7, 18, 19, 22, 23],
    [ 8,  9, 12, 13, 24, 25, 28, 29],
    [10, 11, 14, 15, 26, 27, 30, 31],
]

# Build reverse block layout (block_num -> (bx, by))
BLOCK_POS = {}
for by in range(4):
    for bx in range(8):
        BLOCK_POS[PSMT8_BLOCK_LAYOUT[by][bx]] = (bx, by)


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


def try_unswizzle_variant(data, width, height, variant):
    """Try different unswizzle approaches."""
    output = bytearray(width * height)
    bw = max(width, 128)  # buffer width, at least 128

    page_w = 128
    page_h = 64
    page_size = 8192

    pages_per_row = bw // page_w

    for y in range(height):
        for x in range(width):
            # Page
            px = x // page_w
            py = y // page_h
            page_num = py * pages_per_row + px

            # Within page
            lx = x % page_w
            ly = y % page_h

            # Block within page
            block_x = lx // 16
            block_y = ly // 16
            block_num = PSMT8_BLOCK_LAYOUT[block_y][block_x]

            # Within block (16x16)
            blx = lx % 16
            bly = ly % 16

            if variant == 0:
                # No column interleave - just linear within block
                block_off = bly * 16 + blx
            elif variant == 1:
                # Column with odd-row half swap
                col = bly // 4
                row_in_col = bly % 4
                if row_in_col % 2 == 1:
                    actual_px = (blx + 8) % 16
                else:
                    actual_px = blx
                block_off = col * 64 + row_in_col * 16 + actual_px
            elif variant == 2:
                # Column with every-other-row half swap (different pattern)
                col = bly // 4
                row_in_col = bly % 4
                if bly % 2 == 1:
                    actual_px = (blx + 8) % 16
                else:
                    actual_px = blx
                block_off = col * 64 + row_in_col * 16 + actual_px
            elif variant == 3:
                # No column structure, no swap
                block_off = bly * 16 + blx
            elif variant == 4:
                # Try: blocks are correct but stored linearly (no block rearrangement)
                # Just the block table is different
                block_num = block_y * 8 + block_x  # linear
                block_off = bly * 16 + blx
            elif variant == 5:
                # Reverse mapping: output address -> source address
                # Maybe the data is swizzled and we need to map differently
                addr = (page_num * page_size +
                       block_num * 256 +
                       bly * 16 + blx)
                if addr < len(data):
                    output[y * width + x] = data[addr]
                continue
            elif variant == 6:
                # Only block swizzle, no column interleave
                addr = (page_num * page_size +
                       block_num * 256 +
                       bly * 16 + blx)
                if addr < len(data):
                    output[y * width + x] = data[addr]
                continue

            if variant <= 4:
                addr = (page_num * page_size +
                       block_num * 256 +
                       block_off)
                if addr < len(data):
                    output[y * width + x] = data[addr]

    return bytes(output)


def main():
    # Use R2119 for faster testing (512x64 vs 512x512)
    data = open(os.path.join(TEX_DIR, 'R2119_tavern_buttons_1.raw'), 'rb').read()
    tex = data[16:]
    w, h = 512, 64
    pixel_count = w * h
    pal_size = 1024

    pixel_data = tex[192:192 + pixel_count]
    pal_data = tex[192 + pixel_count:192 + pixel_count + pal_size]
    palette = unswizzle_clut_psmt8(pal_data)

    for v in range(7):
        print(f"Variant {v}...")
        unswizzled = try_unswizzle_variant(pixel_data, w, h, v)
        img = Image.new('RGBA', (w, h))
        pix_out = [palette[unswizzled[i]] for i in range(pixel_count)]
        img.putdata(pix_out)
        out_path = os.path.join(TEX_DIR, f'R2119_v{v}.png')
        img.save(out_path)
        print(f"  Saved: {out_path}")

    # Also try: maybe the data is NOT swizzled and needs no unswizzle
    # (it was uploaded linearly via IMAGE mode, PS2 GS stores it swizzled
    # internally, but what we have might be the pre-swizzle data)
    print("Linear (no unswizzle)...")
    img_lin = Image.new('RGBA', (w, h))
    pix_lin = [palette[pixel_data[i]] for i in range(pixel_count)]
    img_lin.putdata(pix_lin)
    out_path_lin = os.path.join(TEX_DIR, 'R2119_noswizzle.png')
    img_lin.save(out_path_lin)
    print(f"  Saved: {out_path_lin}")


if __name__ == '__main__':
    main()
