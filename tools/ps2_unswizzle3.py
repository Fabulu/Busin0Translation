#!/usr/bin/env python3
"""Try fine-grained PS2 PSMT8 column interleave patterns without block rearrangement."""
import os
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(BASE, "build", "textures_to_edit")


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


def try_column_only(data, width, height, pattern_name, swap_fn):
    """Apply only column-level interleave, no block rearrangement."""
    output = bytearray(width * height)
    for y in range(height):
        for x in range(width):
            src_x = swap_fn(x, y)
            src_off = y * width + src_x
            if src_off < len(data):
                output[y * width + x] = data[src_off]
    return bytes(output)


def main():
    data = open(os.path.join(TEX_DIR, 'R2119_tavern_buttons_1.raw'), 'rb').read()
    tex = data[16:]
    w, h = 512, 64
    pixel_count = w * h
    pal_size = 1024

    pixel_data = tex[192:192 + pixel_count]
    pal_data = tex[192 + pixel_count:192 + pixel_count + pal_size]
    palette = unswizzle_clut_psmt8(pal_data)

    # Try various column swap patterns
    patterns = {
        'swap8_odd': lambda x, y: ((x + 8) % 16 + (x // 16) * 16) if y % 2 == 1 else x,
        'swap8_every2': lambda x, y: ((x + 8) % 16 + (x // 16) * 16) if (y // 2) % 2 == 1 else x,
        'swap8_col4': lambda x, y: ((x + 8) % 16 + (x // 16) * 16) if (y % 4) in (1, 3) else x,
        'swap8_col4v2': lambda x, y: ((x + 8) % 16 + (x // 16) * 16) if (y % 4) in (2, 3) else x,
        'swap8_row2of4': lambda x, y: ((x + 8) % 16 + (x // 16) * 16) if (y % 4) in (1, 2) else x,
        'swap128_odd': lambda x, y: ((x + 128) % 256 + (x // 256) * 256) if y % 2 == 1 else x,
        'swap64_odd': lambda x, y: ((x + 64) % 128 + (x // 128) * 128) if y % 2 == 1 else x,
        'swap32_odd': lambda x, y: ((x + 32) % 64 + (x // 64) * 64) if y % 2 == 1 else x,
        'swap16_odd': lambda x, y: ((x + 16) % 32 + (x // 32) * 32) if y % 2 == 1 else x,
    }

    for name, fn in patterns.items():
        unswizzled = try_column_only(pixel_data, w, h, name, fn)
        img = Image.new('RGBA', (w, h))
        pix_out = [palette[unswizzled[i]] for i in range(pixel_count)]
        img.putdata(pix_out)
        out_path = os.path.join(TEX_DIR, f'R2119_col_{name}.png')
        img.save(out_path)
        print(f"Saved: {name}")


if __name__ == '__main__':
    main()
