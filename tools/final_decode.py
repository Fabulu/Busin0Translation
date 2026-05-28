#!/usr/bin/env python3
"""Final PS2 PSMT8 decode combining column layout with PCSX2 table.

Data structure in GS memory:
- The data is stored in pages of 128x64 pixels (8192 bytes)
- Each page has 32 blocks of 16x16 pixels (256 bytes each)
- Within each block, bytes are ordered according to columnTable8

For each pixel (x,y), the byte address is:
  page = (y // 64) * pages_per_row + (x // 128)
  block = blockTable8[(y%64) // 16][(x%128) // 16]
  offset = columnTable8[y%16][x%16]
  address = page * 8192 + block * 256 + offset

To unswizzle: for each output pixel (x,y), read data[address].
"""
import os
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(BASE, "build", "textures_to_edit")

# PCSX2 exact tables
blockTable8 = [
    [ 0,  1,  4,  5, 16, 17, 20, 21],
    [ 2,  3,  6,  7, 18, 19, 22, 23],
    [ 8,  9, 12, 13, 24, 25, 28, 29],
    [10, 11, 14, 15, 26, 27, 30, 31],
]

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


def build_lut(width, height, bw):
    """Build lookup table: for each output pixel (x,y), return source byte offset."""
    if bw < 128:
        bw = 128
    pages_per_row = bw // 128

    lut = [0] * (width * height)
    for y in range(height):
        for x in range(width):
            page = (y // 64) * pages_per_row + (x // 128)
            block = blockTable8[(y % 64) // 16][(x % 128) // 16]
            col_off = columnTable8[y % 16][x % 16]
            lut[y * width + x] = page * 8192 + block * 256 + col_off
    return lut


def decode_file(filename, width, height, header_offset=192):
    filepath = os.path.join(TEX_DIR, filename)
    data = open(filepath, 'rb').read()
    tex = data[16:]  # skip sub-header
    raw = tex[header_offset:]

    pixel_count = width * height
    pal_start = pixel_count
    pal_data = raw[pal_start:pal_start + 1024]
    palette = unswizzle_clut(pal_data)

    print(f"Decoding {filename}: {width}x{height}, header={header_offset}")
    print(f"  Pixel data: {len(raw)} bytes available, need {pixel_count}")
    print(f"  Palette: bytes {pal_start}-{pal_start+1024}")

    # Build LUT with bw = 512 (from TEX0 TBW=8)
    lut = build_lut(width, height, bw=512)

    # Check max LUT address
    max_addr = max(lut)
    print(f"  LUT max address: {max_addr} (data available: {len(raw)})")

    if max_addr >= len(raw):
        print(f"  WARNING: LUT addresses exceed data! Max={max_addr}, available={len(raw)}")

    # Unswizzle
    out = bytearray(pixel_count)
    for i in range(pixel_count):
        addr = lut[i]
        if addr < pixel_count:  # Only read from pixel region, not palette
            out[i] = raw[addr]

    img = Image.new('RGBA', (width, height))
    img.putdata([palette[out[j]] for j in range(pixel_count)])

    out_name = filename.replace('.raw', '.png')
    out_path = os.path.join(TEX_DIR, out_name)
    img.save(out_path)
    print(f"  Saved: {out_path}")

    # Save zoomed version
    if height <= 128:
        crop_box = (60, max(0, 15), min(400, width), min(50, height))
    else:
        crop_box = (0, height // 4, width, height * 3 // 4)
    crop = img.crop(crop_box)
    zoom_factor = 4 if height <= 128 else 2
    zoomed = crop.resize((crop.width * zoom_factor, crop.height * zoom_factor), Image.NEAREST)
    zoom_path = out_path.replace('.png', '_zoom.png')
    zoomed.save(zoom_path)
    print(f"  Saved zoom: {zoom_path}")

    return img


def main():
    # Test with R2119 first (smaller)
    decode_file('R2119_tavern_buttons_1.raw', 512, 64, header_offset=192)
    decode_file('R2118_tavern_background.raw', 512, 512, header_offset=192)

    # Also try with all other textures
    for f in ['R2120_tavern_buttons_2.raw', 'R2121_guild_background.raw',
              'R2122_guild_buttons.raw', 'R2124_menu_overlay.raw']:
        try:
            # Determine dimensions from TEX0
            data = open(os.path.join(TEX_DIR, f), 'rb').read()
            tex = data[16:]
            import struct
            for qi in range(12):
                lo = struct.unpack_from('<Q', tex, qi * 16)[0]
                hi = struct.unpack_from('<Q', tex, qi * 16 + 8)[0]
                if (hi & 0xFF) == 0x06:
                    tw = (lo >> 26) & 0xF
                    th = (lo >> 30) & 0xF
                    w = 1 << tw
                    h = 1 << th
                    decode_file(f, w, h, header_offset=192)
                    break
        except Exception as e:
            print(f"Error processing {f}: {e}")


if __name__ == '__main__':
    main()
