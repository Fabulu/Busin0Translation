#!/usr/bin/env python3
"""Extract PS2 CockpitImg PSMT8 textures to PNG using linear pixel layout.

These textures have a 192-byte header (12 QWs of GS register config)
followed by pixel data and a 256-color RGBA palette.

The pixel data has some horizontal interlace artifacts from PS2 GS
memory swizzle that is not yet fully decoded. The palette and content
are correct, making the textures usable for reference/translation work.

Layout:
  bytes 0-15:   Sub-header (type, payload_size, data_offset, pad)
  bytes 16-207: GS register config (TEX0, CLAMP, MIPTBP, etc.)
  bytes 208+:   Pixel data (width * height bytes, PSMT8 indices)
                Palette (1024 bytes, 256 RGBA32 entries)
                Padding to file size

TEX0 register at QW[5] provides PSM (0x13=PSMT8), TW/TH (dimensions),
and TBW (buffer width in 64-pixel units).
"""
import sys
import os
import struct
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(BASE, "build", "textures_to_edit")

HEADER_SIZE = 192  # 12 quadwords of GS register config


def unswizzle_clut(pal_data):
    """Parse PS2 PSMT8 CLUT and apply palette entry swizzle."""
    colors = []
    for i in range(256):
        off = i * 4
        if off + 3 < len(pal_data):
            r, g, b, a = pal_data[off], pal_data[off+1], pal_data[off+2], pal_data[off+3]
            colors.append((r, g, b, min(a * 2, 255)))  # PS2 alpha 0-128 -> 0-255
        else:
            colors.append((0, 0, 0, 0))
    # PS2 CLUT swizzle: swap entries 8-15 with 16-23 in each group of 32
    for grp in range(8):
        base = grp * 32
        for j in range(8):
            colors[base + 8 + j], colors[base + 16 + j] = \
                colors[base + 16 + j], colors[base + 8 + j]
    return colors


def read_tex0(tex):
    """Read TEX0 register from the 192-byte header."""
    for qi in range(12):
        hi = struct.unpack_from('<Q', tex, qi * 16 + 8)[0]
        if (hi & 0xFF) == 0x06:  # TEX0_1
            lo = struct.unpack_from('<Q', tex, qi * 16)[0]
            psm = (lo >> 20) & 0x3F
            tw = (lo >> 26) & 0xF
            th = (lo >> 30) & 0xF
            return 1 << tw, 1 << th, psm
    return None, None, None


def decode(filename):
    """Decode a CockpitImg texture to PNG."""
    filepath = os.path.join(TEX_DIR, filename)
    if not os.path.exists(filepath):
        print(f"Not found: {filepath}")
        return

    data = open(filepath, 'rb').read()
    tex = data[16:]  # skip 16-byte sub-header

    # Read dimensions from TEX0
    width, height, psm = read_tex0(tex)
    if width is None:
        print(f"Could not read TEX0 from {filename}")
        return

    print(f"Decoding {filename}: {width}x{height} PSM=0x{psm:02x}")

    raw = tex[HEADER_SIZE:]
    pixel_count = width * height
    pal_size = 1024

    # Verify data availability
    if len(raw) < pixel_count + pal_size:
        print(f"  WARNING: not enough data ({len(raw)} < {pixel_count + pal_size})")
        return

    pixel_data = raw[:pixel_count]
    pal_data = raw[pixel_count:pixel_count + pal_size]
    palette = unswizzle_clut(pal_data)

    # Linear decode
    img = Image.new('RGBA', (width, height))
    pixels = [palette[pixel_data[j]] for j in range(pixel_count)]
    img.putdata(pixels)

    out_path = os.path.join(TEX_DIR, filename.replace('.raw', '.png'))
    img.save(out_path)
    print(f"  Saved: {out_path}")


if __name__ == '__main__':
    files = [
        'R2118_tavern_background.raw',
        'R2119_tavern_buttons_1.raw',
        'R2120_tavern_buttons_2.raw',
        'R2121_guild_background.raw',
        'R2122_guild_buttons.raw',
        'R2124_menu_overlay.raw',
    ]
    for f in files:
        decode(f)
