#!/usr/bin/env python3
"""Try proper PS2 PSMT8 unswizzle using the exact GS memory layout."""
import struct
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


def ps2_psmt8_addr(x, y, bw):
    """Calculate the byte offset in GS memory for a PSMT8 pixel at (x,y).

    bw = buffer width in pixels (must be multiple of 128).

    PS2 GS PSMT8 memory layout:
    - Page: 128x64 pixels = 8192 bytes
    - Block: 16x16 pixels = 256 bytes
    - Column: 16x4 pixels = 64 bytes (stored as two 16x2 halves)
    """
    # Page dimensions
    page_w = 128
    page_h = 64
    page_size = page_w * page_h  # 8192 bytes

    # Block dimensions
    block_w = 16
    block_h = 16
    block_size = block_w * block_h  # 256 bytes

    # Column dimensions
    col_w = 16
    col_h = 4  # Actually 2 interleaved
    col_size = 64

    # Page coordinates
    px = x // page_w
    py = y // page_h
    bw_pages = bw // page_w
    page_num = py * bw_pages + px

    # Position within page
    lx = x % page_w
    ly = y % page_h

    # Block position within page (8 x 4 blocks)
    bx = lx // block_w
    by = ly // block_h

    # PSMT8 block table (maps block position to block number in memory)
    block_table = [
        [ 0,  1,  4,  5, 16, 17, 20, 21],
        [ 2,  3,  6,  7, 18, 19, 22, 23],
        [ 8,  9, 12, 13, 24, 25, 28, 29],
        [10, 11, 14, 15, 26, 27, 30, 31],
    ]
    block_num = block_table[by][bx]

    # Position within block
    blx = lx % block_w
    bly = ly % block_h

    # PSMT8 column within block
    # Each column is 16 pixels wide, 4 rows tall
    # But interleaved: even and odd columns alternate
    col_idx = bly // 4  # Which column group (0-3)

    # Position within column
    cy = bly % 4
    cx = blx

    # Column table for PSMT8
    # Within each 16x4 column, pixels are stored in a specific order
    # The column number depends on the block position

    # PSMT8 column layout within block:
    # Columns are 64 bytes each (16x4 pixels)
    # Column order: alternates based on row
    #   Rows 0-3: column 0
    #   Rows 4-7: column 1
    #   Rows 8-11: column 2
    #   Rows 12-15: column 3

    # Within each column:
    # PS2 GS interleaves even/odd rows
    # Row 0,2 use one addressing, row 1,3 use another

    # The 64 bytes of a column:
    # Bytes 0-15: row 0 (16 pixels)
    # Bytes 16-31: row 1 (16 pixels)
    # Bytes 32-47: row 2 (16 pixels)
    # Bytes 48-63: row 3 (16 pixels)
    # BUT with possible interleaving

    # Simple approach: within a block, offset = row * 16 + col
    # But with column interleaving applied

    # PSMT8 has this column interleave pattern:
    # Even rows (0,2,4,...): pixels are at their natural position
    # Odd rows (1,3,5,...): pixels are shifted by 8

    # Actually let me try a simpler approach first.
    # Within the 16x16 block, the byte offset considering columns:

    # Column index (0-3) = bly // 4
    # Row within column (0-3) = bly % 4
    # But interleaving swaps some columns based on row parity

    # For PSMT8, the interleaving within a column is:
    # Row 0: bytes 0-15 (pixels 0-15, left to right)
    # Row 1: bytes 16-31 (pixels 0-15, but shifted)
    # Row 2: bytes 32-47
    # Row 3: bytes 48-63

    # The shift for odd rows is: pixels 8-15 come first, then 0-7
    # i.e., odd rows have the two 8-pixel halves swapped

    # Let me try this interpretation:
    if cy % 2 == 1:  # Odd row within column
        cx = (cx + 8) % 16  # Swap left/right halves

    col_offset = cy * 16 + cx
    block_offset = col_idx * 64 + col_offset

    byte_addr = page_num * page_size + block_num * block_size + block_offset

    return byte_addr


def psmt8_unswizzle_correct(data, width, height, bw=None):
    """Unswizzle PSMT8 using exact GS address calculation."""
    if bw is None:
        bw = width
    # Round bw up to multiple of 128
    if bw % 128 != 0:
        bw = ((bw + 127) // 128) * 128

    output = bytearray(width * height)

    for y in range(height):
        for x in range(width):
            src_addr = ps2_psmt8_addr(x, y, bw)
            if src_addr < len(data):
                output[y * width + x] = data[src_addr]

    return bytes(output)


def collect_image_data_r2118():
    data = open(os.path.join(TEX_DIR, 'R2118_tavern_background.raw'), 'rb').read()
    tex = data[16:]
    total_qw = len(tex) // 16

    image_blocks = []
    i = 17
    while i < total_qw:
        lo = struct.unpack_from('<Q', tex, i * 16)[0]
        nloop = lo & 0x7FFF
        flg = (lo >> 46) & 3

        if flg == 2 and nloop > 0:
            data_start = (i + 1) * 16
            data_size = min(nloop * 16, len(tex) - data_start)
            if data_size > 0:
                image_blocks.append((data_start, data_size))
            i += 1 + nloop
        else:
            found = False
            for j in range(i + 1, min(i + 5, total_qw)):
                lo2 = struct.unpack_from('<Q', tex, j * 16)[0]
                flg2 = (lo2 >> 46) & 3
                nloop2 = lo2 & 0x7FFF
                if flg2 == 2 and nloop2 > 0:
                    i = j
                    found = True
                    break
            if not found:
                remaining = len(tex) - i * 16
                if remaining > 0:
                    image_blocks.append((i * 16, remaining))
                break

    all_data = bytearray()
    for offset, size in image_blocks:
        all_data.extend(tex[offset:offset + size])
    return all_data


def main():
    # ===== R2118 =====
    print("R2118 with correct PSMT8 unswizzle:")
    all_data = collect_image_data_r2118()
    pixel_count = 512 * 512
    pal_size = 1024

    print(f"  Total IMAGE data: {len(all_data)}")

    pixels = bytes(all_data[:pixel_count])
    pal_raw = bytes(all_data[pixel_count:pixel_count + pal_size])
    palette = unswizzle_clut_psmt8(pal_raw)

    # Try different column interleaving options
    for variant in range(4):
        unswizzled = psmt8_unswizzle_correct(pixels, 512, 512)
        img = Image.new('RGBA', (512, 512))
        pix_out = [palette[unswizzled[i]] for i in range(pixel_count)]
        img.putdata(pix_out)
        out_path = os.path.join(TEX_DIR, f'R2118_correct_v{variant}.png')
        img.save(out_path)
        print(f"  Saved: {out_path}")
        break  # Only one variant for now

    # Also try: maybe the data is NOT swizzled at all, just the GIF tag bytes
    # are corrupting the stream. Let me check how many "gap" bytes there are.
    # From the debug: 26 IMAGE blocks, each preceded by a 16-byte GIF tag
    # First IMAGE at QW[17] means 17 QWs (272 bytes) of header
    # Then 26 GIF tags = 26*16 = 416 bytes
    # Plus the gap at QW[5044-5046] = 3 QWs = 48 bytes
    # Total overhead = 272 + 416 + 48 = 736 bytes
    # Total file = 264176, data = 264176 - 736 = 263440
    # Need 263168, difference = 272 bytes

    # But actually 263728 bytes of IMAGE data was collected (from debug_texture3)
    # That's 263728 - 263168 = 560 extra bytes
    # This suggests some of the "IMAGE" data includes non-pixel bytes

    # Let me try without unswizzle, just straight linear
    img_linear = Image.new('RGBA', (512, 512))
    pix_linear = [palette[pixels[i]] for i in range(pixel_count)]
    img_linear.putdata(pix_linear)
    out_path_linear = os.path.join(TEX_DIR, 'R2118_linear.png')
    img_linear.save(out_path_linear)
    print(f"  Saved (linear): {out_path_linear}")

    # ===== R2119 =====
    print("\nR2119 with correct PSMT8 unswizzle:")
    data = open(os.path.join(TEX_DIR, 'R2119_tavern_buttons_1.raw'), 'rb').read()
    tex = data[16:]

    w, h = 512, 64
    pixel_count2 = w * h
    pixels2 = tex[192:192 + pixel_count2]
    pal_raw2 = tex[192 + pixel_count2:192 + pixel_count2 + pal_size]
    palette2 = unswizzle_clut_psmt8(pal_raw2)

    unswizzled2 = psmt8_unswizzle_correct(pixels2, w, h)
    img2 = Image.new('RGBA', (w, h))
    pix_out2 = [palette2[unswizzled2[i]] for i in range(pixel_count2)]
    img2.putdata(pix_out2)
    out_path2 = os.path.join(TEX_DIR, 'R2119_correct.png')
    img2.save(out_path2)
    print(f"  Saved: {out_path2}")

    # Linear version for comparison
    img_lin2 = Image.new('RGBA', (w, h))
    pix_lin2 = [palette2[pixels2[i]] for i in range(pixel_count2)]
    img_lin2.putdata(pix_lin2)
    out_path_lin2 = os.path.join(TEX_DIR, 'R2119_linear.png')
    img_lin2.save(out_path_lin2)
    print(f"  Saved (linear): {out_path_lin2}")


if __name__ == '__main__':
    main()
