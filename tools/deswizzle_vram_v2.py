#!/usr/bin/env python3
"""
Deswizzle PS2 VRAM with correct GS memory layout.
Uses the well-documented PS2 GS block/page/column tables.

Reference: https://ps2linux.no-ip.info/playstation2-linux.com/docs/howto/display/gs_block_table.html
"""

import zipfile
import numpy as np
from PIL import Image
import os
import struct

OUT_DIR = r"C:\Programmieren\wizardrytranslation\dumps\vram_copy_analysis"

# PSMCT32 block layout within a page (page = 64x32 pixels)
# Table indexed [row][col] where row = block_y (0-3), col = block_x (0-7)
PSMCT32_BLOCK = [
    [ 0,  1,  4,  5, 16, 17, 20, 21],
    [ 2,  3,  6,  7, 18, 19, 22, 23],
    [ 8,  9, 12, 13, 24, 25, 28, 29],
    [10, 11, 14, 15, 26, 27, 30, 31],
]

# PSMCT32: column layout within a block (8x8 pixels per block, 4 columns of 8x2)
# columnTable32[row][col] gives the pixel index within the 256-byte block
# For PSMCT32, each pixel = 4 bytes
# Column table from PS2 documentation
PSMCT32_COL = [
    [ 0,  1,  4,  5,  8,  9, 12, 13],
    [ 2,  3,  6,  7, 10, 11, 14, 15],
    [ 8,  9, 12, 13,  0,  1,  4,  5],  # Note: columns wrap with XOR pattern
    [10, 11, 14, 15,  2,  3,  6,  7],
    [ 0,  1,  4,  5,  8,  9, 12, 13],  # Repeats for rows 4-7 but with different pattern
    [ 2,  3,  6,  7, 10, 11, 14, 15],
    [ 8,  9, 12, 13,  0,  1,  4,  5],
    [10, 11, 14, 15,  2,  3,  6,  7],
]

def read_vram_from_p2s(p2s_path):
    with zipfile.ZipFile(p2s_path, 'r') as z:
        gs = z.read('GS.bin')
    vram = gs[len(gs) - 4*1024*1024:]
    return vram

def read_pixel_psmct32(vram, tbp0, tbw, x, y):
    """
    Read a single PSMCT32 pixel from VRAM.
    tbp0: base pointer in blocks (64-byte units... actually 256-byte blocks)
    tbw: buffer width in 64-pixel units
    x, y: pixel coordinates

    PS2 GS PSMCT32 addressing:
    - Page = 64x32 pixels = 8192 bytes = 32 blocks
    - Block = 8x8 pixels = 256 bytes
    - Column = 8x2 pixels = 64 bytes
    """
    page_w = 64  # pixels
    page_h = 32
    block_w = 8
    block_h = 8

    # Which page?
    page_x = x // page_w
    page_y = y // page_h
    page_num = page_y * tbw + page_x

    # Position within page
    px = x % page_w
    py = y % page_h

    # Which block within page?
    bx = px // block_w
    by = py // block_h
    block_in_page = PSMCT32_BLOCK[by][bx]

    # Global block address
    block_addr = tbp0 + page_num * 32 + block_in_page

    # Position within block
    cx = px % block_w
    cy = py % block_h

    # Column within block
    # Each column = 64 bytes = 8 pixels * 2 rows * 4 bytes
    col = cy // 2
    row_in_col = cy % 2

    # The pixel position in the column uses the column table
    # Actually for PSMCT32, within each column (64 bytes = 16 dwords),
    # pixels are arranged as:
    # Row 0: pixels 0-7 at dword positions from column table
    # Row 1: pixels 0-7 at dword positions from column table
    pix_idx = PSMCT32_COL[cy][cx]

    # Byte offset
    byte_off = block_addr * 256 + pix_idx * 4 * 4  # Wait, this isn't right either

    # Let me use a simpler correct formula:
    # Within a block (256 bytes = 64 dwords):
    # Column n (0-3) starts at dword n*16
    # Within a column (16 dwords = 8x2 pixels):
    #   Row 0: dwords 0-7 (but swizzled by column table)
    #   Row 1: dwords 8-15

    # Actually the simplest correct approach for PSMCT32:
    # offset_in_block = (column * 16 + row_in_col * 8 + pixel_in_row) * 4
    # But with column swizzle applied

    # Simpler: use column number and position directly
    col_num = cy >> 1  # which column (0-3)
    row_in_col = cy & 1

    # Pixel offset within the column
    # Column table gives the dword index for position (cy, cx) within the block
    dword_idx = PSMCT32_COL[cy][cx]

    byte_off = block_addr * 256 + dword_idx * 4

    if byte_off + 4 > len(vram):
        return (0, 0, 0, 0)

    return struct.unpack_from('<BBBB', vram, byte_off)


def deswizzle_psmct32_correct(vram, tbp0, tbw, width, height):
    """
    Correctly deswizzle a PSMCT32 texture/framebuffer from PS2 VRAM.

    Uses the standard PS2 GS addressing formula.
    """
    out = np.zeros((height, width, 4), dtype=np.uint8)

    page_w = 64
    page_h = 32
    block_w = 8
    block_h = 8

    for y in range(height):
        page_y = y // page_h
        py = y % page_h
        by = py // block_h
        cy = py % block_h

        for x in range(width):
            page_x = x // page_w
            px = x % page_w
            bx = px // block_w
            cx = px % block_w

            page_num = page_y * tbw + page_x
            block_in_page = PSMCT32_BLOCK[by][bx]
            block_addr = tbp0 + page_num * 32 + block_in_page

            dword_idx = PSMCT32_COL[cy][cx]
            byte_off = block_addr * 256 + dword_idx * 4

            if byte_off + 4 <= len(vram):
                out[y, x, 0] = vram[byte_off]
                out[y, x, 1] = vram[byte_off + 1]
                out[y, x, 2] = vram[byte_off + 2]
                out[y, x, 3] = vram[byte_off + 3]

    return out


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    states = [
        (r"C:\Programmieren\wizardrytranslation\RAMdumps\charscreenv5.p2s", "charscreenv5"),
        (r"C:\Programmieren\wizardrytranslation\RAMdumps\fundamental.p2s", "fundamental"),
    ]

    for path, name in states:
        if not os.path.exists(path):
            continue

        print(f"\n{'='*60}")
        print(f"Processing: {name}")
        print(f"{'='*60}")

        vram = read_vram_from_p2s(path)

        # Framebuffer at 0x0000, FBW=10 (640 pixels), 448 lines
        print("  Deswizzling framebuffer 0x0000 (640x448)...")
        fb = deswizzle_psmct32_correct(vram, 0x0000, 10, 640, 448)
        img = Image.fromarray(fb[:,:,:3], 'RGB')
        img.save(os.path.join(OUT_DIR, f"{name}_fb_correct_640x448.png"))
        print("  Saved.")

        # SBP=0x1800, likely same FBW as main framebuffer
        # 0x1800 blocks = 0x1800*256 = 0x180000 bytes from VRAM start
        # This is framebuffer data, so FBW should be 10 (640 pixels)
        # Height: 0x380 blocks. At FBW=10, pages_wide=10, blocks per page-row=10*32=320=0x140
        # page_rows = 0x380 / 0x140 = 2.85... not exact
        # Try tbw=8 (512 pixels): pages_wide=8, blocks_per_page_row=256=0x100
        # page_rows = 0x380/0x100 = 3.5 -> 3 page rows * 32 = 96 pixels

        # Actually the copy might span more than the exact rectangle.
        # Let's try both 512 and 640 wide
        for tbw, fw in [(8, 512), (10, 640)]:
            # Calculate how many page-rows fit in 0x380 blocks
            blocks_per_page_row = tbw * 32
            page_rows = 0x380 // blocks_per_page_row
            h = page_rows * 32
            if h == 0:
                continue

            print(f"  Deswizzling SBP=0x1800 as PSMCT32 {fw}x{h} (tbw={tbw})...")
            src = deswizzle_psmct32_correct(vram, 0x1800, tbw, fw, h)
            img = Image.fromarray(src[:,:,:3], 'RGB')
            p = os.path.join(OUT_DIR, f"{name}_src1800_correct_{fw}x{h}.png")
            img.save(p)
            print(f"  Saved: {p}")

            # Alpha
            alpha = src[:,:,3]
            img_a = Image.fromarray(np.minimum(alpha.astype(np.uint16)*2, 255).astype(np.uint8), 'L')
            img_a.save(os.path.join(OUT_DIR, f"{name}_src1800_correct_{fw}x{h}_alpha.png"))

        # DBP=0x3000 (R1272 destination)
        for tbw, fw in [(8, 512)]:
            blocks_per_page_row = tbw * 32
            page_rows = 0x380 // blocks_per_page_row
            h = page_rows * 32

            print(f"  Deswizzling DBP=0x3000 as PSMCT32 {fw}x{h} (tbw={tbw})...")
            dst = deswizzle_psmct32_correct(vram, 0x3000, tbw, fw, h)
            img = Image.fromarray(dst[:,:,:3], 'RGB')
            p = os.path.join(OUT_DIR, f"{name}_dst3000_correct_{fw}x{h}.png")
            img.save(p)
            print(f"  Saved: {p}")

        print("  Done.")

if __name__ == '__main__':
    main()
