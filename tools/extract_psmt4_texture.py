"""
Extract a PSMT4 texture from PS2 GS VRAM dump.

PS2 GS PSMT4 memory layout:
- 1 page = 128x128 pixels = 4096 bytes (4bpp)
- 1 block = 32x16 pixels = 256 bytes
- 32 blocks per page, arranged in specific pattern
"""

import struct
import sys
import os

GS_HEADER = 509
VRAM_SIZE = 4 * 1024 * 1024
BLOCK_SIZE_BYTES = 256  # bytes per block
PAGE_SIZE_BYTES = 8192  # 32 blocks * 256 bytes

# PSMT4 block arrangement within a 128x128 page
# block_row = y // 16, block_col = x // 32
# Index into this table: PSMT4_BLOCK_TABLE[block_row][block_col]
PSMT4_BLOCK_TABLE = [
    [ 0,  2,  4,  6],
    [ 1,  3,  5,  7],
    [ 8, 10, 12, 14],
    [ 9, 11, 13, 15],
    [16, 18, 20, 22],
    [17, 19, 21, 23],
    [24, 26, 28, 30],
    [25, 27, 29, 31],
]


def read_psmt4_pixel(vram, page_base, block_idx, bpx, bpy):
    """Read a single 4-bit pixel from a PSMT4 block in VRAM.
    bpx: 0-31 (x within block), bpy: 0-15 (y within block)
    Returns 0-15 palette index.
    """
    block_addr = page_base + block_idx * BLOCK_SIZE_BYTES

    # Standard PSMT4 column addressing within a 32x16 block
    col = bpy // 2
    row_in_col = bpy % 2
    byte_offset = col * 32 + row_in_col * 16 + bpx // 2

    addr = block_addr + byte_offset
    if addr >= len(vram):
        return 0

    byte_val = vram[addr]
    if bpx % 2 == 0:
        return byte_val & 0x0F
    else:
        return (byte_val >> 4) & 0x0F


def extract_psmt4(vram, tbp0, tbw, width, height):
    """Extract PSMT4 texture with proper PS2 GS swizzling."""
    base_offset = tbp0 * 256
    buf_width_pixels = tbw * 64  # TBW=4 -> 256 pixels
    pages_per_row = buf_width_pixels // 128

    print(f"TBP0=0x{tbp0:X}, base=0x{base_offset:X}, buf_w={buf_width_pixels}, pages/row={pages_per_row}")

    if base_offset >= len(vram):
        print(f"ERROR: base offset beyond VRAM!")
        return None

    pixels = bytearray(width * height)

    for py in range(height):
        for px in range(width):
            page_col = px // 128
            page_row = py // 128
            page_idx = page_row * pages_per_row + page_col
            page_base = base_offset + page_idx * PAGE_SIZE_BYTES

            lpx = px % 128
            lpy = py % 128

            block_col = lpx // 32
            block_row = lpy // 16
            block_idx = PSMT4_BLOCK_TABLE[block_row][block_col]

            bpx = lpx % 32
            bpy = lpy % 16

            val = read_psmt4_pixel(vram, page_base, block_idx, bpx, bpy)
            pixels[py * width + px] = val

    return pixels


def extract_clut_ct16(vram, cbp, num_colors=16):
    """Extract CLUT in PSMCT16 format."""
    base = cbp * 256
    clut = []
    for i in range(num_colors):
        if base + i*2 + 1 < len(vram):
            val = struct.unpack_from('<H', vram, base + i*2)[0]
            r = (val & 0x1F) << 3
            g = ((val >> 5) & 0x1F) << 3
            b = ((val >> 10) & 0x1F) << 3
            a = 255 if (val >> 15) else (255 if val == 0 else 128)
            clut.append((r, g, b, a))
        else:
            clut.append((0, 0, 0, 0))
    return clut


def main():
    from PIL import Image

    with open('RAMdumps/GS.bin', 'rb') as f:
        data = f.read()

    vram = data[GS_HEADER:]
    print(f"VRAM size: {len(vram)} bytes (expected {VRAM_SIZE})")

    TBP0 = 0x2A68
    TBW = 4
    WIDTH = 256
    HEIGHT = 256
    CBP = 0x2AE9

    base = TBP0 * 256
    print(f"\nRaw data at TBP0 offset 0x{base:X}:")
    print(f"First 64 bytes: {vram[base:base+64].hex()}")

    # Check if there's meaningful data
    chunk = vram[base:base+4096]
    nonzero = sum(1 for b in chunk if b != 0)
    print(f"Non-zero bytes in first 4096: {nonzero}/{len(chunk)}")

    # Extract swizzled
    print("\n--- Extracting PSMT4 (swizzled) ---")
    pixels = extract_psmt4(vram, TBP0, TBW, WIDTH, HEIGHT)
    if pixels is None:
        return

    with open('RAMdumps/tbp0_2A68_pixels.bin', 'wb') as f:
        f.write(pixels)
    print(f"Saved raw pixels: {len(pixels)} bytes")

    # Extract CLUT
    clut = extract_clut_ct16(vram, CBP)
    print(f"\nCLUT at CBP=0x{CBP:X} (offset 0x{CBP*256:X}):")
    for i, c in enumerate(clut):
        print(f"  [{i:2d}] R={c[0]:3d} G={c[1]:3d} B={c[2]:3d} A={c[3]:3d}")

    # Render grayscale
    img_gray = Image.new('L', (WIDTH, HEIGHT))
    for y in range(HEIGHT):
        for x in range(WIDTH):
            img_gray.putpixel((x, y), pixels[y * WIDTH + x] * 17)
    img_gray.save('RAMdumps/tbp0_2A68_gray.png')
    print("Saved: RAMdumps/tbp0_2A68_gray.png")

    # Render with CLUT
    img_clut = Image.new('RGBA', (WIDTH, HEIGHT))
    for y in range(HEIGHT):
        for x in range(WIDTH):
            img_clut.putpixel((x, y), clut[pixels[y * WIDTH + x]])
    img_clut.save('RAMdumps/tbp0_2A68_clut.png')
    print("Saved: RAMdumps/tbp0_2A68_clut.png")

    # Also extract LINEAR (no swizzle) for comparison
    print("\n--- Extracting LINEAR (no swizzle) ---")
    linear_pixels = bytearray(WIDTH * HEIGHT)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            off = base + (y * WIDTH + x) // 2
            if off < len(vram):
                bv = vram[off]
                if (y * WIDTH + x) % 2 == 0:
                    linear_pixels[y * WIDTH + x] = bv & 0x0F
                else:
                    linear_pixels[y * WIDTH + x] = (bv >> 4) & 0x0F

    img_linear = Image.new('L', (WIDTH, HEIGHT))
    for y in range(HEIGHT):
        for x in range(WIDTH):
            img_linear.putpixel((x, y), linear_pixels[y * WIDTH + x] * 17)
    img_linear.save('RAMdumps/tbp0_2A68_linear.png')
    print("Saved: RAMdumps/tbp0_2A68_linear.png")

    with open('RAMdumps/tbp0_2A68_linear.bin', 'wb') as f:
        f.write(linear_pixels)

    # Stats on extracted data
    used_indices = set(pixels)
    print(f"\nSwizzled: used palette indices: {sorted(used_indices)}")
    used_linear = set(linear_pixels)
    print(f"Linear: used palette indices: {sorted(used_linear)}")


if __name__ == '__main__':
    main()
