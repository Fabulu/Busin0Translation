#!/usr/bin/env python3
"""
PS2 GS PSMT8 deswizzle tool.

Uses the exact block and column tables from PCSX2 (GSTables.cpp) to correctly
decode 8-bit palettized textures stored in PS2 GS VRAM format.

The game uploads PSMT8 texture data to VRAM using PSMCT32 IMAGE transfers.
The data in the .raw files is organized for PSMCT32 upload format. To
reconstruct the PSMT8 texture we simulate the GS VRAM:
  1. Write the host data to a VRAM buffer using PSMCT32 swizzle
  2. Read PSMT8 pixels back from VRAM using PSMT8 swizzle

File layout: 1024-byte header | pixel data (W*H bytes) | 1024-byte palette

PSMCT32 layout: 64x32 pixels per page, 8x8 per block
PSMT8 layout:   128x64 pixels per page, 16x16 per block
"""
import struct
import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(BASE, "build", "textures_to_edit")


# ---- PCSX2-sourced tables (from GSTables.cpp) ----

BLOCK_TABLE_32 = [
    [ 0,  1,  4,  5, 16, 17, 20, 21],
    [ 2,  3,  6,  7, 18, 19, 22, 23],
    [ 8,  9, 12, 13, 24, 25, 28, 29],
    [10, 11, 14, 15, 26, 27, 30, 31],
]

COLUMN_TABLE_32 = [
    [ 0,  1,  4,  5,  8,  9, 12, 13],
    [ 2,  3,  6,  7, 10, 11, 14, 15],
    [16, 17, 20, 21, 24, 25, 28, 29],
    [18, 19, 22, 23, 26, 27, 30, 31],
    [32, 33, 36, 37, 40, 41, 44, 45],
    [34, 35, 38, 39, 42, 43, 46, 47],
    [48, 49, 52, 53, 56, 57, 60, 61],
    [50, 51, 54, 55, 58, 59, 62, 63],
]

BLOCK_TABLE_8 = [
    [ 0,  1,  4,  5, 16, 17, 20, 21],
    [ 2,  3,  6,  7, 18, 19, 22, 23],
    [ 8,  9, 12, 13, 24, 25, 28, 29],
    [10, 11, 14, 15, 26, 27, 30, 31],
]

COLUMN_TABLE_8 = [
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


def _psmct32_word_addr(x, y, bw_ct32):
    """PSMCT32 pixel address -> word index in VRAM."""
    PAGE_W, PAGE_H = 64, 32
    ppr = max(1, bw_ct32 // PAGE_W)
    pid = (y // PAGE_H) * ppr + (x // PAGE_W)
    bid = BLOCK_TABLE_32[(y % PAGE_H) // 8][(x % PAGE_W) // 8]
    wib = COLUMN_TABLE_32[y % 8][x % 8]
    return pid * 2048 + bid * 64 + wib


def _psmt8_byte_addr(x, y, bw_psmt8):
    """PSMT8 pixel address -> byte offset in VRAM."""
    PAGE_W, PAGE_H = 128, 64
    ppr = max(1, bw_psmt8 // PAGE_W)
    pid = (y // PAGE_H) * ppr + (x // PAGE_W)
    bid = BLOCK_TABLE_8[(y % PAGE_H) // 16][(x % PAGE_W) // 16]
    bib = COLUMN_TABLE_8[y % 16][x % 16]
    return pid * 8192 + bid * 256 + bib


def deswizzle_psmt8(host_data, tex_w, tex_h, bw_psmt8=None, dbw_ct32=None):
    """Deswizzle PSMT8 texture uploaded via PSMCT32 transfers.

    Args:
        host_data: Raw bytes from the file (PSMCT32-organized upload data)
        tex_w: Texture width in PSMT8 pixels
        tex_h: Texture height in pixels
        bw_psmt8: PSMT8 buffer width (default: tex_w)
        dbw_ct32: PSMCT32 upload buffer width in pixels (default: tex_w)

    Returns:
        bytearray of deswizzled PSMT8 pixel indices
    """
    if bw_psmt8 is None:
        bw_psmt8 = tex_w
    if dbw_ct32 is None:
        dbw_ct32 = tex_w  # Upload width in PSMCT32 pixels

    # Calculate upload dimensions
    upload_w = dbw_ct32
    upload_h = (len(host_data) // 4) // upload_w
    if upload_h * upload_w * 4 > len(host_data):
        upload_h = len(host_data) // (upload_w * 4)

    # Build VRAM by writing host data with PSMCT32 swizzle
    vram_size = max(tex_w * tex_h, len(host_data)) + 8192  # extra page for safety
    vram = bytearray(vram_size)

    for y in range(upload_h):
        for x in range(upload_w):
            host_off = (y * upload_w + x) * 4
            if host_off + 4 > len(host_data):
                break
            vram_word = _psmct32_word_addr(x, y, upload_w)
            vram_byte = vram_word * 4
            if vram_byte + 4 <= len(vram):
                vram[vram_byte:vram_byte + 4] = host_data[host_off:host_off + 4]

    # Read PSMT8 pixels from VRAM
    out = bytearray(tex_w * tex_h)
    for y in range(tex_h):
        for x in range(tex_w):
            addr = _psmt8_byte_addr(x, y, bw_psmt8)
            if addr < len(vram):
                out[y * tex_w + x] = vram[addr]

    return out


def swizzle_psmt8(linear_pixels, tex_w, tex_h, bw_psmt8=None, dbw_ct32=None):
    """Re-swizzle linear PSMT8 data back into PSMCT32 upload format.

    This is the inverse of deswizzle_psmt8 -- useful for patching textures.
    """
    if bw_psmt8 is None:
        bw_psmt8 = tex_w
    if dbw_ct32 is None:
        dbw_ct32 = tex_w

    upload_w = dbw_ct32
    upload_h = (tex_w * tex_h) // (upload_w * 4)

    vram_size = max(tex_w * tex_h, upload_w * upload_h * 4) + 8192
    vram = bytearray(vram_size)

    # Write PSMT8 pixels to VRAM
    for y in range(tex_h):
        for x in range(tex_w):
            addr = _psmt8_byte_addr(x, y, bw_psmt8)
            if addr < len(vram):
                vram[addr] = linear_pixels[y * tex_w + x]

    # Read back from VRAM using PSMCT32 swizzle
    out = bytearray(upload_w * upload_h * 4)
    for y in range(upload_h):
        for x in range(upload_w):
            vram_word = _psmct32_word_addr(x, y, upload_w)
            vram_byte = vram_word * 4
            host_off = (y * upload_w + x) * 4
            if vram_byte + 4 <= len(vram) and host_off + 4 <= len(out):
                out[host_off:host_off + 4] = vram[vram_byte:vram_byte + 4]

    return out


def deswizzle_palette(palette_data):
    """Deswizzle PS2 CLUT for 8-bit textures."""
    result = bytearray(len(palette_data))
    for i in range(256):
        block = i // 32
        idx_in_block = i % 32
        if 8 <= idx_in_block < 16:
            new_idx = block * 32 + idx_in_block + 8
        elif 16 <= idx_in_block < 24:
            new_idx = block * 32 + idx_in_block - 8
        else:
            new_idx = i
        result[i * 4:i * 4 + 4] = palette_data[new_idx * 4:new_idx * 4 + 4]
    return result


def make_rgba_image(pixels, palette, width, height):
    """Create RGBA PIL Image from palette indices and RGBA palette bytes."""
    img = Image.new('RGBA', (width, height))
    pal_colors = []
    for i in range(256):
        r = palette[i * 4]
        g = palette[i * 4 + 1]
        b = palette[i * 4 + 2]
        a = min(palette[i * 4 + 3] * 2, 255)  # PS2 alpha is 0-128
        pal_colors.append((r, g, b, a))
    img_data = [pal_colors[p] for p in pixels[:width * height]]
    img.putdata(img_data)
    return img


def process_raw_texture(raw_path, width, height, out_prefix, dbw_ct32=None):
    """Load a raw texture file, deswizzle, and save as PNG."""
    data = open(raw_path, 'rb').read()
    npix = width * height

    # File layout: 1024-byte header, pixel data, 1024-byte palette
    header_size = 1024
    pixels_raw = data[header_size:header_size + npix]
    palette_raw = data[-1024:]

    if dbw_ct32 is None:
        dbw_ct32 = width  # Default: upload width = texture width

    print(f"  File: {len(data)} bytes, texture: {width}x{height}")
    print(f"  PSMCT32 upload width: {dbw_ct32} pixels")

    # Deswizzle palette
    palette = deswizzle_palette(palette_raw)

    # Deswizzle pixels (PSMCT32 upload -> VRAM -> PSMT8 read)
    print("  Deswizzling pixels (VRAM simulation)...")
    pixels_lin = deswizzle_psmt8(pixels_raw, width, height,
                                  bw_psmt8=width, dbw_ct32=dbw_ct32)

    # Save
    img = make_rgba_image(pixels_lin, palette, width, height)
    out_path = os.path.join(TEX_DIR, f"{out_prefix}_psmt8_deswizzled.png")
    img.save(out_path)
    print(f"  Saved: {out_path}")

    return pixels_lin, palette


def main():
    print("=== PS2 PSMT8 Deswizzle (VRAM simulation) ===\n")

    # R2118 - tavern background (512x512)
    r2118_raw = os.path.join(TEX_DIR, "R2118_tavern_background.raw")
    if os.path.exists(r2118_raw):
        print("Processing R2118 (512x512)...")
        process_raw_texture(r2118_raw, 512, 512, "R2118", dbw_ct32=256)
    else:
        print(f"Not found: {r2118_raw}")

    print()

    # R2119 - tavern buttons (512x64)
    r2119_raw = os.path.join(TEX_DIR, "R2119_tavern_buttons_1.raw")
    if os.path.exists(r2119_raw):
        print("Processing R2119 (512x64)...")
        process_raw_texture(r2119_raw, 512, 64, "R2119", dbw_ct32=256)
    else:
        print(f"Not found: {r2119_raw}")

    print("\nDone!")


if __name__ == "__main__":
    main()
