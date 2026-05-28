#!/usr/bin/env python3
"""Render R1192 TextEventImage data with correct PSMT4 32x16 block swizzle."""
import struct, os, sys
sys.stdout.reconfigure(encoding='utf-8')

from PIL import Image
import numpy as np

BASE = 'C:/Programmieren/wizardrytranslation'
OUT = f'{BASE}/dumps/textevent'
os.makedirs(OUT, exist_ok=True)

# PS2 PSMT4 uses 32x16 pixel blocks (also called "columns")
# Within each 32x16 block, there's an internal swizzle pattern
# The block data is 256 bytes (32*16/2 = 256 nibbles = 128 bytes... wait)
# Actually PSMT4: each pixel is 4 bits, so 32x16 = 512 pixels = 256 bytes

# PS2 PSMT4 page is 128x128 pixels = 8192 nibbles = 4096 bytes
# Actually no: PSMT4 page is 128x128 = 16384 pixels / 2 = 8192 bytes

# The standard PS2 PSMT4 block swizzle (32x16 blocks within 128x128 pages):
# Each page has (128/32) * (128/16) = 4 * 8 = 32 blocks
# Block ordering within a page follows a specific pattern

def psmt4_deswizzle_block(raw_data, tex_w, tex_h):
    """
    PSMT4 deswizzle using the standard 32-column layout.
    Each 'column' is 32 pixels wide, stored as 16 bytes per row.
    Pages are 128x128 pixels.
    """
    PAGE_W = 128
    PAGE_H = 128
    BLOCK_W = 32
    BLOCK_H = 16

    # Number of pages
    pages_x = max(1, tex_w // PAGE_W)
    pages_y = max(1, tex_h // PAGE_H)
    total_pages = pages_x * pages_y
    page_size = (PAGE_W * PAGE_H) // 2  # 8192 bytes per PSMT4 page

    out = np.zeros((tex_h, tex_w), dtype=np.uint8)

    # Blocks per page
    blocks_per_row = PAGE_W // BLOCK_W  # 4
    blocks_per_col = PAGE_H // BLOCK_H  # 8
    block_size = (BLOCK_W * BLOCK_H) // 2  # 256 bytes

    # Standard PS2 PSMT4 block order within a page
    # This is the column order for PSMT4
    block_order = [
        0, 2, 4, 6,
        1, 3, 5, 7,
        8, 10, 12, 14,
        9, 11, 13, 15,
        16, 18, 20, 22,
        17, 19, 21, 23,
        24, 26, 28, 30,
        25, 27, 29, 31
    ]

    for py in range(pages_y):
        for px in range(pages_x):
            page_idx = py * pages_x + px
            page_off = page_idx * page_size

            for block_idx in range(32):
                # Source position in raw data
                src_off = page_off + block_idx * block_size

                # Destination position
                # Use block_order to find which block position this data goes to
                dest_block = block_order[block_idx]
                dest_bx = dest_block % blocks_per_row
                dest_by = dest_block // blocks_per_row

                for y in range(BLOCK_H):
                    for x in range(BLOCK_W):
                        pixel_idx = y * BLOCK_W + x
                        byte_idx = src_off + pixel_idx // 2
                        nibble = pixel_idx & 1

                        if byte_idx < len(raw_data):
                            bv = raw_data[byte_idx]
                            pv = (bv & 0x0F) if nibble == 0 else ((bv >> 4) & 0x0F)
                        else:
                            pv = 0

                        ox = px * PAGE_W + dest_bx * BLOCK_W + x
                        oy = py * PAGE_H + dest_by * BLOCK_H + y

                        if ox < tex_w and oy < tex_h:
                            out[oy, ox] = pv * 17

    return out


# Also try simple linear 4bpp (no block swizzle, just page layout)
def psmt4_pages_linear(raw_data, tex_w, tex_h):
    """PSMT4 with page layout but linear within pages."""
    PAGE_W = 128
    PAGE_H = 128
    pages_x = max(1, tex_w // PAGE_W)
    pages_y = max(1, tex_h // PAGE_H)
    page_size = (PAGE_W * PAGE_H) // 2

    out = np.zeros((tex_h, tex_w), dtype=np.uint8)

    for py in range(pages_y):
        for px in range(pages_x):
            page_idx = py * pages_x + px
            page_off = page_idx * page_size

            for y in range(PAGE_H):
                for x in range(PAGE_W):
                    pidx = y * PAGE_W + x
                    byte_idx = page_off + pidx // 2
                    nibble = pidx & 1

                    if byte_idx < len(raw_data):
                        bv = raw_data[byte_idx]
                        pv = (bv & 0x0F) if nibble == 0 else ((bv >> 4) & 0x0F)
                    else:
                        pv = 0

                    ox = px * PAGE_W + x
                    oy = py * PAGE_H + y
                    if ox < tex_w and oy < tex_h:
                        out[oy, ox] = pv * 17

    return out


for idx in [1192, 2361]:
    rawfile = f"{BASE}/extracted/packdata_raw/{idx}_type02.raw"
    data = open(rawfile, 'rb').read()
    s2o = struct.unpack_from('<I', data, 24)[0]
    s2t = struct.unpack_from('<I', data, 20)[0]
    s2 = data[s2o:s2o+s2t]
    count = struct.unpack_from('<H', s2, 6)[0]

    print(f"\n=== R{idx}: {count} entries ===")

    # Use the high-entropy pixel region start
    # For R1192: starts at ~0xFC80 (based on unique > 30 threshold at block level)
    # But actually the interleaving means texture data is mixed throughout

    # Let me try the WHOLE section 2 minus the initial header (first 0xB0 bytes)
    # as PSMT4 data at various widths

    header_end = 0xB0 if idx == 1192 else 0x90
    pixel_data = bytes(s2[header_end:])

    print(f"  Data from +{header_end:03X}, {len(pixel_data)} bytes")

    # Try PSMT4 with block deswizzle
    for tex_w in [128, 256, 384, 512]:
        npix = len(pixel_data) * 2
        tex_h = npix // tex_w
        # Round to page boundary
        tex_h = (tex_h // 128) * 128
        if tex_h < 128:
            tex_h = 128
        if tex_h > 2048:
            tex_h = 2048

        print(f"  Trying PSMT4 block deswizzle {tex_w}x{tex_h}...")
        pixels = psmt4_deswizzle_block(pixel_data, tex_w, tex_h)

        # Save normal
        img = Image.fromarray(pixels, 'L')
        fname = f'{OUT}/R{idx}_psmt4_block_{tex_w}x{tex_h}.png'
        img.save(fname)
        print(f"    Saved {fname}")

        # Save inverted
        img_inv = Image.fromarray(255 - pixels, 'L')
        fname2 = f'{OUT}/R{idx}_psmt4_block_inv_{tex_w}x{tex_h}.png'
        img_inv.save(fname2)
        print(f"    Saved {fname2}")

    # Also try pages_linear
    for tex_w in [128, 256, 384, 512]:
        npix = len(pixel_data) * 2
        tex_h = npix // tex_w
        tex_h = (tex_h // 128) * 128
        if tex_h < 128:
            tex_h = 128
        if tex_h > 2048:
            tex_h = 2048

        pixels = psmt4_pages_linear(pixel_data, tex_w, tex_h)
        img_inv = Image.fromarray(255 - pixels, 'L')
        fname = f'{OUT}/R{idx}_psmt4_linear_inv_{tex_w}x{tex_h}.png'
        img_inv.save(fname)
        print(f"  Linear inv {tex_w}x{tex_h}")

print("\nDone!")
