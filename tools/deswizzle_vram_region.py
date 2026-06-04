#!/usr/bin/env python3
"""
Deswizzle PS2 VRAM regions with proper GS memory layout.

PS2 GS VRAM layout (PSMCT32):
- Page = 8192 bytes = 32 blocks = 64x32 pixels
- Block = 256 bytes = 8x8 pixels (in columns)
- Column = 64 bytes = 8x2 pixels
- Pages are arranged in a specific block order within each page

For PSMCT32 (32bpp):
  Page width = 64 pixels, Page height = 32 pixels
  Blocks per page = 32 (arranged 8x4 in a specific pattern)

PSMT4 (4bpp):
  Page width = 128 pixels, Page height = 128 pixels
  Each block = 32x16 pixels
"""

import zipfile
import struct
import numpy as np
from PIL import Image
import os
import sys

OUT_DIR = r"C:\Programmieren\wizardrytranslation\dumps\vram_copy_analysis"

# PS2 PSMCT32 block arrangement within a page (8x4 blocks = 32 blocks per page)
# Each page is 64x32 pixels in PSMCT32
PSMCT32_BLOCK_TABLE = [
     0,  1,  4,  5, 16, 17, 20, 21,
     2,  3,  6,  7, 18, 19, 22, 23,
     8,  9, 12, 13, 24, 25, 28, 29,
    10, 11, 14, 15, 26, 27, 30, 31,
]

# PSMCT32 column arrangement within a block
# Each block is 8x8 pixels, each column is 8x2 pixels = 64 bytes
# Columns within a block: alternating pattern
PSMCT32_COL_TABLE = [0, 1, 4, 5, 8, 9, 12, 13, 2, 3, 6, 7, 10, 11, 14, 15]

# PSMT4 block arrangement within a page
# Page = 128x128 pixels for PSMT4
PSMT4_BLOCK_TABLE = [
     0,  2,  8, 10,
     1,  3,  9, 11,
     4,  6, 12, 14,
     5,  7, 13, 15,
    16, 18, 24, 26,
    17, 19, 25, 27,
    20, 22, 28, 30,
    21, 23, 29, 31,
]

def read_vram_from_p2s(p2s_path):
    """Read flat VRAM from PCSX2 save state."""
    with zipfile.ZipFile(p2s_path, 'r') as z:
        gs = z.read('GS.bin')
    vram = gs[len(gs) - 4*1024*1024:]
    return vram

def deswizzle_psmct32(vram, tbp0, width_pixels, height_pixels):
    """
    Deswizzle a PSMCT32 texture from PS2 VRAM.

    tbp0: base pointer in 256-byte blocks
    width_pixels: texture width
    height_pixels: texture height
    """
    out = np.zeros((height_pixels, width_pixels, 4), dtype=np.uint8)

    page_w = 64   # pixels per page width
    page_h = 32   # pixels per page height
    pages_wide = (width_pixels + page_w - 1) // page_w

    block_w = 8   # pixels per block
    block_h = 8
    blocks_per_page_x = 8  # blocks per page horizontally
    blocks_per_page_y = 4

    for py in range(height_pixels):
        for px in range(width_pixels):
            # Which page?
            page_x = px // page_w
            page_y = py // page_h
            page_idx = page_y * pages_wide + page_x

            # Position within page
            lpx = px % page_w
            lpy = py % page_h

            # Which block within page?
            block_x = lpx // block_w
            block_y = lpy // block_h
            block_in_page = block_y * blocks_per_page_x + block_x

            # Look up the actual block number using the swizzle table
            actual_block_in_page = PSMCT32_BLOCK_TABLE[block_in_page]

            # Global block address
            block_addr = tbp0 + page_idx * 32 + actual_block_in_page

            # Position within block
            col_x = lpx % block_w
            col_y = lpy % block_h

            # Column within block (each column = 8x2 = 64 bytes)
            col_idx = col_y // 2
            col_row = col_y % 2

            # Byte offset within VRAM
            byte_off = block_addr * 256 + col_idx * 64 + col_row * 32 + col_x * 4

            if byte_off + 4 <= len(vram):
                r, g, b, a = vram[byte_off], vram[byte_off+1], vram[byte_off+2], vram[byte_off+3]
                out[py, px] = [r, g, b, a]

    return out

def deswizzle_psmct32_fast(vram, tbp0, width_pixels, height_pixels):
    """
    Fast deswizzle - read block-by-block and place pixels.
    Still somewhat slow but better than per-pixel.
    """
    out = np.zeros((height_pixels, width_pixels, 4), dtype=np.uint8)

    page_w = 64
    page_h = 32
    pages_wide = (width_pixels + page_w - 1) // page_w
    pages_high = (height_pixels + page_h - 1) // page_h

    # Build inverse block table
    inv_block = [0] * 32
    for i, b in enumerate(PSMCT32_BLOCK_TABLE):
        inv_block[b] = i

    for page_y in range(pages_high):
        for page_x in range(pages_wide):
            page_idx = page_y * pages_wide + page_x

            for block_in_page in range(32):
                actual_block = PSMCT32_BLOCK_TABLE[block_in_page]
                block_addr = tbp0 + page_idx * 32 + actual_block

                # This block's position in the page
                bx = block_in_page % 8
                by = block_in_page // 8

                base_x = page_x * page_w + bx * 8
                base_y = page_y * page_h + by * 8

                # Read 256 bytes for this block
                off = block_addr * 256
                if off + 256 > len(vram):
                    continue

                block_data = vram[off:off+256]

                # Parse columns (4 columns of 8x2 pixels each)
                block_arr = np.frombuffer(block_data, dtype=np.uint8)
                for col in range(4):
                    for row in range(2):
                        for x in range(8):
                            byte_idx = col * 64 + row * 32 + x * 4
                            px_x = base_x + x
                            px_y = base_y + col * 2 + row

                            if px_x < width_pixels and px_y < height_pixels:
                                out[px_y, px_x, 0] = block_arr[byte_idx]
                                out[px_y, px_x, 1] = block_arr[byte_idx+1]
                                out[px_y, px_x, 2] = block_arr[byte_idx+2]
                                out[px_y, px_x, 3] = block_arr[byte_idx+3]

    return out


def simple_framebuffer_render(vram, fbp, fbw, height):
    """
    Render a framebuffer region from VRAM.
    FBP = frame buffer base pointer (in 2048-byte pages... actually in 32-word units = 2048/8 = 256 byte blocks)
    FBW = frame buffer width in 64-pixel units

    Actually, PS2 framebuffer is stored with page swizzling too.
    Let's try a simpler approach: just use the deswizzle function.
    """
    width = fbw * 64
    return deswizzle_psmct32_fast(vram, fbp, width, height)


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
        print(f"VRAM: {len(vram)} bytes")

        # Deswizzle SBP=0x1800 as PSMCT32
        # 0x1800 blocks. If this is framebuffer, FBW is typically 10 (=640 pixels) or 8 (=512)
        # The copy is 0x380 blocks = 229376 bytes
        # As PSMCT32 at 512 wide: 229376 / (512*4) = 112 rows
        # As PSMCT32 at 640 wide: 229376 / (640*4) = 89.6 rows

        # Try different widths
        for fw in [512, 640]:
            # Calculate height from available blocks
            # pages_wide = fw // 64
            pages_wide = fw // 64
            blocks_per_row_of_pages = pages_wide * 32  # blocks per page-row
            page_rows = 0x380 // blocks_per_row_of_pages
            h = page_rows * 32

            print(f"\n  Deswizzling SBP=0x1800 as PSMCT32 {fw}x{h}...")
            try:
                img_arr = deswizzle_psmct32_fast(vram, 0x1800, fw, h)

                rgb = img_arr[:,:,:3]
                alpha = img_arr[:,:,3]

                img = Image.fromarray(rgb, 'RGB')
                path_out = os.path.join(OUT_DIR, f"{name}_src0x1800_deswiz_{fw}x{h}.png")
                img.save(path_out)
                print(f"  Saved: {path_out}")

                img_a = Image.fromarray(alpha, 'L')
                path_a = os.path.join(OUT_DIR, f"{name}_src0x1800_deswiz_{fw}x{h}_alpha.png")
                img_a.save(path_a)
                print(f"  Saved: {path_a}")
            except Exception as e:
                print(f"  Error: {e}")
                import traceback
                traceback.print_exc()

        # Also deswizzle DBP=0x3000 as PSMCT32 (same dimensions)
        for fw in [512]:
            pages_wide = fw // 64
            blocks_per_row_of_pages = pages_wide * 32
            page_rows = 0x380 // blocks_per_row_of_pages
            h = page_rows * 32

            print(f"\n  Deswizzling DBP=0x3000 as PSMCT32 {fw}x{h}...")
            try:
                img_arr = deswizzle_psmct32_fast(vram, 0x3000, fw, h)

                rgb = img_arr[:,:,:3]
                img = Image.fromarray(rgb, 'RGB')
                path_out = os.path.join(OUT_DIR, f"{name}_dst0x3000_deswiz_{fw}x{h}.png")
                img.save(path_out)
                print(f"  Saved: {path_out}")
            except Exception as e:
                print(f"  Error: {e}")
                import traceback
                traceback.print_exc()

        # Also render the main framebuffer at 0x0000 for reference
        print(f"\n  Deswizzling framebuffer at 0x0000 as PSMCT32 640x448...")
        try:
            img_arr = deswizzle_psmct32_fast(vram, 0x0000, 640, 448)
            rgb = img_arr[:,:,:3]
            img = Image.fromarray(rgb, 'RGB')
            path_out = os.path.join(OUT_DIR, f"{name}_fb0x0000_deswiz_640x448.png")
            img.save(path_out)
            print(f"  Saved: {path_out}")
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == '__main__':
    main()
