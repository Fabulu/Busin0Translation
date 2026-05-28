#!/usr/bin/env python3
"""Extract PS2 CockpitImg textures (R2121, R2122) to PNG.

These resources store PSMT8 (8-bit indexed) texture data in HOST (linear) format.
The data layout is:
  - 16-byte sub-header (type=0, payload_size, offset=16, pad=0)
  - 272 bytes of GIF register setup (PACKED nloop=1 nreg=16 with TEX0 etc.)
  - width * height bytes of linear pixel data (palette indices)
  - 1024 bytes of RGBA palette (256 entries, 4 bytes each)
  - PS2 palette has alpha 0-128 (scale *2 to get 0-255)
  - PS2 PSMT8 CLUT has entries 8-15 and 16-23 swapped in each group of 32
"""
import sys, os
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(BASE, "build", "textures_to_edit")


def unswizzle_clut(pal_data):
    """Parse and unswizzle PS2 PSMT8 CLUT palette."""
    colors = []
    for i in range(256):
        off = i * 4
        if off + 3 < len(pal_data):
            r, g, b, a = pal_data[off], pal_data[off + 1], pal_data[off + 2], pal_data[off + 3]
            colors.append((r, g, b, min(a * 2, 255)))
        else:
            colors.append((0, 0, 0, 0))
    # CLUT swizzle: swap entries 8-15 with 16-23 in each group of 32
    for grp in range(8):
        base = grp * 32
        for j in range(8):
            colors[base + 8 + j], colors[base + 16 + j] = \
                colors[base + 16 + j], colors[base + 8 + j]
    return colors


def decode(filename, width, height):
    """Decode a CockpitImg PSMT8 resource to RGBA PNG."""
    filepath = os.path.join(TEX_DIR, filename)
    data = open(filepath, 'rb').read()
    tex = data[16:]       # skip sub-header
    raw = tex[272:]        # skip GIF register setup (17 quadwords)

    pixel_count = width * height
    pal_size = 1024

    pixel_data = raw[:pixel_count]
    pal_data = raw[pixel_count:pixel_count + pal_size]
    palette = unswizzle_clut(pal_data)

    # Linear read - data is in HOST format (not GS VRAM swizzled)
    img = Image.new('RGBA', (width, height))
    pixels = [palette[pixel_data[j]] for j in range(pixel_count)]
    img.putdata(pixels)

    out_path = os.path.join(TEX_DIR, filename.replace('.raw', '.png'))
    img.save(out_path)
    print(f'Saved: {out_path}')
    return out_path


if __name__ == '__main__':
    decode('R2121_guild_background.raw', 512, 512)
    decode('R2122_guild_buttons.raw', 512, 64)
    print('Done!')
