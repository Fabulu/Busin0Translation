#!/usr/bin/env python3
"""Find the actual data stride by analyzing R2121 pixel patterns.

R2121 has color content, making banding patterns easier to analyze.
If the data is linear but with wrong stride, the bands will repeat
at intervals = stride / display_width * display_width pixels.
"""
import os
import struct
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


def main():
    # Try rendering R2121 at various strides (display width = 512)
    data = open(os.path.join(TEX_DIR, 'R2121_guild_background.raw'), 'rb').read()
    tex = data[16:]

    # Use offset 192 (exact payload match) and 272 (17 QW header)
    for header in [192, 272]:
        raw = tex[header:]

        # Palette at offset pixel_count
        for stride in [512, 640, 768, 1024]:
            # Use stride as the actual memory width
            total_pixels = stride * (len(raw) // stride)
            actual_height = total_pixels // stride

            # Palette: after all pixel data
            pal_start = stride * (512 * 512 // stride)  # Approximate
            if header == 192:
                pal_start = 512 * 512  # Exact for 192 header
            elif header == 272:
                pal_start = 512 * 512  # Might be wrong

            if pal_start + 1024 > len(raw):
                continue

            pal = unswizzle_clut(raw[pal_start:pal_start + 1024])

            # Render as stride-wide image, then show only the first 512 columns
            display_w = min(512, stride)
            display_h = min(512, actual_height)

            img = Image.new('RGBA', (display_w, display_h))
            pixels = []
            for y in range(display_h):
                for x in range(display_w):
                    off = y * stride + x
                    if off < len(raw) and off < pal_start:
                        pixels.append(pal[raw[off]])
                    else:
                        pixels.append((0, 0, 0, 0))
            img.putdata(pixels)

            out_path = os.path.join(TEX_DIR, f'R2121_h{header}_s{stride}.png')
            img.save(out_path)
            print(f"Saved: {out_path}")


if __name__ == '__main__':
    main()
