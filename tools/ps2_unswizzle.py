#!/usr/bin/env python3
"""PS2 GS PSMT8 unswizzle - exact memory layout from GS documentation."""
import struct
import os
import array
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(BASE, "build", "textures_to_edit")


# PSMT8 block layout in page (8 columns x 4 rows of 16x16 blocks)
# This maps (block_col, block_row) -> block_number
PSMT8_BLOCK_LAYOUT = [
    [ 0,  1,  4,  5, 16, 17, 20, 21],
    [ 2,  3,  6,  7, 18, 19, 22, 23],
    [ 8,  9, 12, 13, 24, 25, 28, 29],
    [10, 11, 14, 15, 26, 27, 30, 31],
]

# PSMT8 column table - maps position within 16x16 block to byte offset
# Each block has 4 columns (each 16x4 pixels = 64 bytes)
# The PS2 GS has a specific interleave pattern within each column

# For PSMT8, the pixel within a 16x16 block at (px, py) maps to:
# column = py // 4 (0-3)
# row_in_column = py % 4 (0-3)
# The two halves (0-7 and 8-15) swap on odd rows within the column

def psmt8_block_offset(px, py):
    """Get byte offset within a 16x16 PSMT8 block for pixel (px, py)."""
    col = py // 4  # Which column (0-3)
    row_in_col = py % 4

    # PS2 PSMT8 interleave within column:
    # Even rows (0, 2): normal order left-to-right
    # Odd rows (1, 3): left/right halves swapped

    if row_in_col % 2 == 1:
        # Odd row - swap halves
        actual_px = (px + 8) % 16
    else:
        actual_px = px

    return col * 64 + row_in_col * 16 + actual_px


def psmt8_byte_address(x, y, buffer_width):
    """Calculate byte address in GS local memory for PSMT8 pixel at (x,y).

    buffer_width: texture buffer width in pixels (must be multiple of 128).
    Returns: byte offset in GS memory.
    """
    # Page: 128x64 pixels = 8192 bytes
    # Block: 16x16 pixels = 256 bytes
    page_w = 128
    page_h = 64
    page_size = 8192  # bytes
    block_size = 256  # bytes

    # Page position
    page_x = x // page_w
    page_y = y // page_h
    pages_per_row = buffer_width // page_w
    page_num = page_y * pages_per_row + page_x

    # Position within page
    lx = x % page_w
    ly = y % page_h

    # Block position within page
    bx = lx // 16
    by = ly // 16
    block_num = PSMT8_BLOCK_LAYOUT[by][bx]

    # Position within block
    blx = lx % 16
    bly = ly % 16

    block_off = psmt8_block_offset(blx, bly)

    return page_num * page_size + block_num * block_size + block_off


def build_lookup_table(width, height, buffer_width):
    """Build a lookup table mapping linear (y*width+x) to GS memory address."""
    table = array.array('I', [0] * (width * height))
    for y in range(height):
        for x in range(width):
            addr = psmt8_byte_address(x, y, buffer_width)
            table[y * width + x] = addr
    return table


def unswizzle_psmt8(data, width, height, buffer_width=None):
    """Unswizzle PSMT8 pixel data from GS memory layout to linear."""
    if buffer_width is None:
        buffer_width = width
    # Round up to multiple of 128
    if buffer_width % 128 != 0:
        buffer_width = ((buffer_width + 127) // 128) * 128

    output = bytearray(width * height)
    lut = build_lookup_table(width, height, buffer_width)

    for i in range(width * height):
        addr = lut[i]
        if addr < len(data):
            output[i] = data[addr]

    return bytes(output)


def unswizzle_clut_psmt8(palette_data):
    """Unswizzle PS2 CLUT for PSMT8 (256 colors, PSMCT32 format)."""
    colors = []
    for i in range(256):
        off = i * 4
        if off + 3 < len(palette_data):
            r, g, b, a = palette_data[off], palette_data[off+1], palette_data[off+2], palette_data[off+3]
            # PS2 alpha: 0-128 maps to 0-255
            a = min(a * 2, 255)
            colors.append((r, g, b, a))
        else:
            colors.append((0, 0, 0, 0))

    # CLUT swizzle for PSMT8: within each group of 32, swap entries 8-15 with 16-23
    unswizzled = list(colors)
    for grp in range(8):
        base = grp * 32
        for j in range(8):
            unswizzled[base + 8 + j], unswizzled[base + 16 + j] = \
                unswizzled[base + 16 + j], unswizzled[base + 8 + j]

    return unswizzled


def decode_texture(raw_path, width, height, header_size, out_path):
    """Decode a PSMT8 texture from a raw resource file."""
    data = open(raw_path, 'rb').read()
    tex = data[16:]  # Skip 16-byte sub-header

    pixel_count = width * height
    pal_size = 1024  # 256 * 4

    pixel_data = tex[header_size:header_size + pixel_count]
    pal_data = tex[header_size + pixel_count:header_size + pixel_count + pal_size]

    print(f"Decoding {os.path.basename(raw_path)}: {width}x{height}")
    print(f"  Header: {header_size} bytes")
    print(f"  Pixels: offset {header_size}, {len(pixel_data)} bytes")
    print(f"  Palette: offset {header_size + pixel_count}, {len(pal_data)} bytes")

    # Check if palette looks valid
    if len(pal_data) >= 4:
        print(f"  Palette[0]: {pal_data[:4].hex()}")

    # Unswizzle pixels
    print("  Unswizzling pixels...")
    unswizzled = unswizzle_psmt8(pixel_data, width, height)

    # Unswizzle palette
    palette = unswizzle_clut_psmt8(pal_data)

    # Build image
    img = Image.new('RGBA', (width, height))
    pix_out = [palette[unswizzled[i]] for i in range(pixel_count)]
    img.putdata(pix_out)

    img.save(out_path)
    print(f"  Saved: {out_path}")

    # Also save without unswizzle for comparison
    out_linear = out_path.replace('.png', '_linear.png')
    img_lin = Image.new('RGBA', (width, height))
    pix_lin = [palette[pixel_data[i]] for i in range(pixel_count)]
    img_lin.putdata(pix_lin)
    img_lin.save(out_linear)
    print(f"  Saved (linear): {out_linear}")

    return img


def main():
    # R2118: 512x512, header = 192 bytes (12 QWs)
    # Payload = 263360, header = 192, pixel+pal = 263168 -> exact match
    decode_texture(
        os.path.join(TEX_DIR, 'R2118_tavern_background.raw'),
        512, 512, 192,
        os.path.join(TEX_DIR, 'R2118_tavern_background.png')
    )

    # R2119: 512x64, header = 192 bytes
    # Payload = 33984, header = 192, 512*64+1024 = 33792 -> 33984-192=33792 exact!
    decode_texture(
        os.path.join(TEX_DIR, 'R2119_tavern_buttons_1.raw'),
        512, 64, 192,
        os.path.join(TEX_DIR, 'R2119_tavern_buttons_1.png')
    )


if __name__ == '__main__':
    main()
