"""
Extract PSMT4 texture from PS2 GS VRAM with CORRECT full swizzle.

The PS2 GS stores PSMT4 textures with three levels of swizzling:
1. Page level: 128x128 pixels per page, pages arranged by TBW
2. Block level: 32 blocks per page, in specific arrangement
3. Column/pixel level: pixels within a block follow a complex pattern

Reference: PS2 GS User's Manual, PSMT4 pixel storage format
"""

import struct
from PIL import Image

GS_HEADER = 509

# ---- PSMT4 full deswizzle tables ----

# Block arrangement within a page (128x128 pixels, blocks are 32x16)
# Index: BLOCK_LAYOUT[block_row][block_col] where
#   block_row = (local_y // 16), block_col = (local_x // 32)
PSMT4_PAGE_BLOCKS = [
    [ 0,  2,  4,  6],
    [ 1,  3,  5,  7],
    [ 8, 10, 12, 14],
    [ 9, 11, 13, 15],
    [16, 18, 20, 22],
    [17, 19, 21, 23],
    [24, 26, 28, 30],
    [25, 27, 29, 31],
]

# PSMT4 pixel-to-byte mapping within a 32x16 block
# Based on the official PS2 documentation
# A PSMT4 block is 32 pixels wide x 16 pixels tall = 512 pixels = 256 bytes
#
# The column structure for PSMT4:
# Each "column" is 32 pixels wide x 4 rows tall = 128 nibbles = 64 bytes
# There are 4 columns per block (16 rows / 4 rows per column)
#
# Within each column, there's a specific pixel arrangement

def build_psmt4_lut():
    """Build lookup table: (px, py) -> (byte_offset_in_block, nibble_shift)
    for a 32x16 PSMT4 block.

    Based on PCSX2's GSLocalMemory implementation.
    """
    # PSMT4 column table from PS2 docs
    # Each column is 32 wide x 4 tall
    # Columns per block: 4 (since block is 16 tall)

    lut = {}

    # The PSMT4 block layout follows this pattern:
    # Column index = y // 4
    # Within each column (32x4 pixels = 128 nibbles = 64 bytes):
    #   The pixels are arranged in a specific interleaved pattern

    # From PCSX2 source and PS2 docs, the PSMT4 column word table:
    # For even columns (0, 2):
    COLUMN_WORD_EVEN = [
        [ 0,  1,  4,  5,  8,  9, 12, 13],
        [ 2,  3,  6,  7, 10, 11, 14, 15],
    ]
    # For odd columns (1, 3):
    COLUMN_WORD_ODD = [
        [ 8,  9, 12, 13,  0,  1,  4,  5],
        [10, 11, 14, 15,  2,  3,  6,  7],
    ]

    # Within each 32-bit word: 8 nibbles
    # PSMT4 nibble arrangement within a word:
    # Each 32-bit word holds 8 pixels (4 bits each)
    # Pixel order within word: nibble 0 (bits 0-3), nibble 1 (bits 4-7), ... nibble 7 (bits 28-31)

    for py in range(16):
        col_idx = py // 4        # Which column (0-3)
        row_in_col = py % 4      # Row within column (0-3)

        # Within a column, rows 0-1 use one word pattern, rows 2-3 use another
        word_row = row_in_col // 2  # 0 or 1
        sub_row = row_in_col % 2    # 0 or 1

        if col_idx % 2 == 0:
            word_table = COLUMN_WORD_EVEN
        else:
            word_table = COLUMN_WORD_ODD

        for px in range(32):
            # Which word within the row (each word = 4 pixels wide for PSMT4...
            # actually 8 nibbles = 8 pixels per 32-bit word)
            # But layout: 32 pixels / 8 pixels per word = 4 words per row
            word_in_row = px // 8
            nibble_in_word = px % 8

            # Word index in the column
            word_idx = word_table[word_row][word_in_row + sub_row * 4]

            # Byte offset: column_base + word_index * 4 + nibble byte offset
            col_base = col_idx * 64  # 64 bytes per column
            byte_in_word = nibble_in_word // 2
            nibble_pos = nibble_in_word % 2  # 0=low, 1=high

            byte_offset = col_base + word_idx * 4 + byte_in_word

            lut[(px, py)] = (byte_offset, nibble_pos * 4)  # shift amount

    return lut


def build_psmt4_lut_v2():
    """Alternative: use direct coordinate-to-offset formula from PS2 docs.

    For PSMT4, each block is 32x16 = 256 bytes.
    The pixel address formula from the GS manual:

    page = (bp + (y/128) * bw + (x/128))
    In the block: use block table and column swizzle.
    """
    # Let me try a different approach - use the known PSMT4 column offsets
    # from actual PS2 documentation / GSTex plugin sources

    # PSMT4 column table - maps (x, y) within a 32x16 block to byte offset
    # This is from the GSdx / PCSX2 pixel storage tables

    lut = {}

    for y in range(16):
        for x in range(32):
            # Column number within block
            col = y >> 2  # 0-3, each column is 4 rows

            # Within the column (32x4 pixels = 64 bytes)
            cy = y & 3  # 0-3 row within column

            # The PSMT4 word layout within a column:
            # Each column has 16 32-bit words (64 bytes)
            # Arranged as 8 words per "half-row", 2 half-rows per row...
            # It's complex. Let me use the actual formulas.

            # From PCSX2's GSBlock.h for PSMT4:
            # The nibble address within a block:

            # Word address within column
            # Each 32-bit word = 8 nibbles (8 PSMT4 pixels)

            # PSMT4 uses a specific interleaving pattern
            # Let's use a simpler empirical approach

            pass

    return None


def extract_psmt4_direct(vram, tbp0, tbw, width, height):
    """Extract using the GS addressing formula directly.

    For PSMT4:
    - Page: 128x128 pixels
    - Block: 32x16 pixels
    - Column: 32x4 pixels (but internal layout varies by even/odd column)

    The approach: compute the VRAM byte address for each pixel.
    """
    base = tbp0 * 256
    bw_pages = tbw  # TBW for PSMT4 in pages (each page = 128 pixels wide...
                     # actually TBW is in units of 64-pixel-widths)
    # For PSMT4: TBW value * 64 = buffer width in pixels
    # Pages per row = (TBW * 64) / 128 = TBW / 2
    # Wait, TBW for PSMT4: the manual says TBW is (buffer_width_pixels / 64)
    # So TBW=4 means 256 pixels wide
    # Pages per row for PSMT4 = 256/128 = 2
    pages_per_row = (tbw * 64) // 128

    pixels = bytearray(width * height)

    # Build a simple per-pixel extractor using the block table
    # and a straightforward column layout

    for py in range(height):
        for px in range(width):
            # Page coordinates
            page_x = px // 128
            page_y = py // 128
            page_idx = page_y * pages_per_row + page_x
            page_base = base + page_idx * 8192  # 8192 bytes per page

            # Local coordinates within page
            lx = px % 128
            ly = py % 128

            # Block coordinates within page
            bx = lx // 32
            by = ly // 16
            block_idx = PSMT4_PAGE_BLOCKS[by][bx]
            block_base = page_base + block_idx * 256

            # Pixel coordinates within block
            blk_x = lx % 32
            blk_y = ly % 16

            # Column within block
            col = blk_y // 4
            col_y = blk_y % 4

            # Column base offset in block
            col_base = col * 64  # 64 bytes per column

            # Within column: PSMT4 uses a specific word arrangement
            # From the PS2 GS documentation, PSMT4 column word layout:
            #
            # For even columns: words arranged as:
            #   Row 0: w0  w1  w4  w5  w8  w9  w12 w13
            #   Row 1: w2  w3  w6  w7  w10 w11 w14 w15
            # For odd columns:
            #   Row 0: w8  w9  w12 w13 w0  w1  w4  w5
            #   Row 1: w10 w11 w14 w15 w2  w3  w6  w7
            #
            # Each word = 4 bytes = 8 nibbles (8 PSMT4 pixels)
            # Row 0 = col_y 0,1  Row 1 = col_y 2,3
            # Within each row: sub_row = col_y % 2

            # Word column (0-3) from x: each word covers 8 pixels
            wcol = blk_x // 8
            nibble_in_word = blk_x % 8

            row_pair = col_y // 2  # 0 or 1
            sub_row = col_y % 2    # 0 or 1

            # Word index selection based on column parity
            if col % 2 == 0:
                # Even column word layout
                even_words = [
                    [0, 1, 4, 5, 8, 9, 12, 13],
                    [2, 3, 6, 7, 10, 11, 14, 15],
                ]
                word_idx = even_words[row_pair][wcol * 2 + sub_row]
            else:
                # Odd column word layout
                odd_words = [
                    [8, 9, 12, 13, 0, 1, 4, 5],
                    [10, 11, 14, 15, 2, 3, 6, 7],
                ]
                word_idx = odd_words[row_pair][wcol * 2 + sub_row]

            # Byte offset within column
            byte_in_word = nibble_in_word // 2
            nibble_low = nibble_in_word % 2

            addr = block_base + col_base + word_idx * 4 + byte_in_word

            if addr < len(vram):
                bval = vram[addr]
                if nibble_low == 0:
                    pixels[py * width + px] = bval & 0x0F
                else:
                    pixels[py * width + px] = (bval >> 4) & 0x0F

    return pixels


def main():
    with open('RAMdumps/GS.bin', 'rb') as f:
        data = f.read()
    vram = data[GS_HEADER:]
    print(f"VRAM: {len(vram)} bytes")

    TBP0 = 0x2A68
    TBW = 4
    W, H = 256, 256
    CBP = 0x2AE9

    print(f"Extracting PSMT4 at TBP0=0x{TBP0:X}, {W}x{H}, TBW={TBW}")
    pixels = extract_psmt4_direct(vram, TBP0, TBW, W, H)

    # Save grayscale
    img = Image.new('L', (W, H))
    for y in range(H):
        for x in range(W):
            img.putpixel((x, y), pixels[y * W + x] * 17)
    img.save('RAMdumps/tbp0_2A68_v2.png')
    print("Saved: RAMdumps/tbp0_2A68_v2.png")

    # Also try with a standard CLUT gradient for visibility
    # Index 0 = white (background), higher = darker
    img2 = Image.new('L', (W, H))
    for y in range(H):
        for x in range(W):
            val = pixels[y * W + x]
            # Invert: 0=white, 15=black
            img2.putpixel((x, y), 255 - val * 17)
    img2.save('RAMdumps/tbp0_2A68_v2_inv.png')
    print("Saved: RAMdumps/tbp0_2A68_v2_inv.png")

    # Save raw
    with open('RAMdumps/tbp0_2A68_v2.bin', 'wb') as f:
        f.write(pixels)

    used = set(pixels)
    print(f"Used indices: {sorted(used)}")
    print(f"Non-zero pixels: {sum(1 for p in pixels if p != 0)}/{len(pixels)}")


if __name__ == '__main__':
    main()
