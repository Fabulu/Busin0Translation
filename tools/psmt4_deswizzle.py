#!/usr/bin/env python3
"""
PS2 GS PSMT4 deswizzle tool.

Uses the exact block and column tables from PCSX2 (GSTables.cpp) to correctly
decode 4-bit palettized textures stored in PS2 GS VRAM format.

The game uploads PSMT4 texture data to VRAM using PSMCT32 IMAGE transfers.
The data in the .raw files is organized for PSMCT32 upload format. To
reconstruct the PSMT4 texture we simulate the GS VRAM:
  1. Write the host data to a VRAM buffer using PSMCT32 swizzle
  2. Read PSMT4 pixels back from VRAM using PSMT4 swizzle

File layout: 1024-byte header | pixel data (W*H/2 bytes) | 1024-byte palette

PSMCT32 layout: 64x32 pixels per page, 8x8 per block
PSMT4 layout:   128x128 pixels per page, 32x16 per block
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

# PSMCT32: 64x32 page, 8x8 blocks, 32 blocks per page
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

# PSMT4: 128x128 page, 32x16 blocks, 32 blocks per page
# Block table: 8 rows x 4 columns (page is 128/32=4 blocks wide, 128/16=8 blocks tall)
BLOCK_TABLE_4 = [
    [ 0,  2,  8, 10],
    [ 1,  3,  9, 11],
    [ 4,  6, 12, 14],
    [ 5,  7, 13, 15],
    [16, 18, 24, 26],
    [17, 19, 25, 27],
    [20, 22, 28, 30],
    [21, 23, 29, 31],
]

# Column table: 16 rows x 32 columns (block is 32x16 pixels)
# Each entry is a nibble index (0-511) within a 256-byte block (512 nibbles)
COLUMN_TABLE_4 = [
    [  0,   8,  32,  40,  64,  72,  96, 104,   2,  10,  34,  42,  66,  74,  98, 106,   4,  12,  36,  44,  68,  76, 100, 108,   6,  14,  38,  46,  70,  78, 102, 110],
    [ 16,  24,  48,  56,  80,  88, 112, 120,  18,  26,  50,  58,  82,  90, 114, 122,  20,  28,  52,  60,  84,  92, 116, 124,  22,  30,  54,  62,  86,  94, 118, 126],
    [ 65,  73,  97, 105,   1,   9,  33,  41,  67,  75,  99, 107,   3,  11,  35,  43,  69,  77, 101, 109,   5,  13,  37,  45,  71,  79, 103, 111,   7,  15,  39,  47],
    [ 81,  89, 113, 121,  17,  25,  49,  57,  83,  91, 115, 123,  19,  27,  51,  59,  85,  93, 117, 125,  21,  29,  53,  61,  87,  95, 119, 127,  23,  31,  55,  63],
    [192, 200, 224, 232, 128, 136, 160, 168, 194, 202, 226, 234, 130, 138, 162, 170, 196, 204, 228, 236, 132, 140, 164, 172, 198, 206, 230, 238, 134, 142, 166, 174],
    [208, 216, 240, 248, 144, 152, 176, 184, 210, 218, 242, 250, 146, 154, 178, 186, 212, 220, 244, 252, 148, 156, 180, 188, 214, 222, 246, 254, 150, 158, 182, 190],
    [129, 137, 161, 169, 193, 201, 225, 233, 131, 139, 163, 171, 195, 203, 227, 235, 133, 141, 165, 173, 197, 205, 229, 237, 135, 143, 167, 175, 199, 207, 231, 239],
    [145, 153, 177, 185, 209, 217, 241, 249, 147, 155, 179, 187, 211, 219, 243, 251, 149, 157, 181, 189, 213, 221, 245, 253, 151, 159, 183, 191, 215, 223, 247, 255],
    [256, 264, 288, 296, 320, 328, 352, 360, 258, 266, 290, 298, 322, 330, 354, 362, 260, 268, 292, 300, 324, 332, 356, 364, 262, 270, 294, 302, 326, 334, 358, 366],
    [272, 280, 304, 312, 336, 344, 368, 376, 274, 282, 306, 314, 338, 346, 370, 378, 276, 284, 308, 316, 340, 348, 372, 380, 278, 286, 310, 318, 342, 350, 374, 382],
    [321, 329, 353, 361, 257, 265, 289, 297, 323, 331, 355, 363, 259, 267, 291, 299, 325, 333, 357, 365, 261, 269, 293, 301, 327, 335, 359, 367, 263, 271, 295, 303],
    [337, 345, 369, 377, 273, 281, 305, 313, 339, 347, 371, 379, 275, 283, 307, 315, 341, 349, 373, 381, 277, 285, 309, 317, 343, 351, 375, 383, 279, 287, 311, 319],
    [448, 456, 480, 488, 384, 392, 416, 424, 450, 458, 482, 490, 386, 394, 418, 426, 452, 460, 484, 492, 388, 396, 420, 428, 454, 462, 486, 494, 390, 398, 422, 430],
    [464, 472, 496, 504, 400, 408, 432, 440, 466, 474, 498, 506, 402, 410, 434, 442, 468, 476, 500, 508, 404, 412, 436, 444, 470, 478, 502, 510, 406, 414, 438, 446],
    [385, 393, 417, 425, 449, 457, 481, 489, 387, 395, 419, 427, 451, 459, 483, 491, 389, 397, 421, 429, 453, 461, 485, 493, 391, 399, 423, 431, 455, 463, 487, 495],
    [401, 409, 433, 441, 465, 473, 497, 505, 403, 411, 435, 443, 467, 475, 499, 507, 405, 413, 437, 445, 469, 477, 501, 509, 407, 415, 439, 447, 471, 479, 503, 511],
]


def _psmct32_word_addr(x, y, bw_ct32):
    """PSMCT32 pixel address -> word index in VRAM."""
    PAGE_W, PAGE_H = 64, 32
    ppr = max(1, bw_ct32 // PAGE_W)
    pid = (y // PAGE_H) * ppr + (x // PAGE_W)
    bid = BLOCK_TABLE_32[(y % PAGE_H) // 8][(x % PAGE_W) // 8]
    wib = COLUMN_TABLE_32[y % 8][x % 8]
    return pid * 2048 + bid * 64 + wib


def _psmt4_nibble_addr(x, y, bw_psmt4):
    """PSMT4 pixel address -> nibble offset in VRAM.

    Each PSMT4 pixel is a 4-bit nibble. Returns the nibble index in VRAM.
    To get byte address: nibble_addr // 2
    Low/high nibble: nibble_addr & 1 (0=low, 1=high)
    """
    PAGE_W, PAGE_H = 128, 128
    BLOCK_W, BLOCK_H = 32, 16
    ppr = max(1, bw_psmt4 // PAGE_W)
    pid = (y // PAGE_H) * ppr + (x // PAGE_W)
    bid = BLOCK_TABLE_4[(y % PAGE_H) // BLOCK_H][(x % PAGE_W) // BLOCK_W]
    nib = COLUMN_TABLE_4[y % BLOCK_H][x % BLOCK_W]
    # Each page = 32 blocks * 256 bytes = 8192 bytes = 16384 nibbles
    # Each block = 256 bytes = 512 nibbles
    return pid * 16384 + bid * 512 + nib


def deswizzle_psmt4(host_data, tex_w, tex_h, bw_psmt4=None, dbw_ct32=None):
    """Deswizzle PSMT4 texture uploaded via PSMCT32 transfers.

    Args:
        host_data: Raw bytes from the file (PSMCT32-organized upload data)
        tex_w: Texture width in PSMT4 pixels
        tex_h: Texture height in pixels
        bw_psmt4: PSMT4 buffer width (default: tex_w)
        dbw_ct32: PSMCT32 upload buffer width in pixels (default: tex_w)

    Returns:
        bytearray of deswizzled PSMT4 pixel indices (one byte per pixel, values 0-15)
    """
    if bw_psmt4 is None:
        bw_psmt4 = tex_w
    if dbw_ct32 is None:
        dbw_ct32 = tex_w

    # Calculate upload dimensions in PSMCT32 pixels
    upload_w = dbw_ct32
    upload_h = (len(host_data) // 4) // upload_w
    if upload_h * upload_w * 4 > len(host_data):
        upload_h = len(host_data) // (upload_w * 4)

    # Build VRAM by writing host data with PSMCT32 swizzle
    vram_size = max(tex_w * tex_h // 2, len(host_data)) + 16384  # extra page
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

    # Read PSMT4 pixels from VRAM (each pixel is a nibble)
    out = bytearray(tex_w * tex_h)
    for y in range(tex_h):
        for x in range(tex_w):
            nib_addr = _psmt4_nibble_addr(x, y, bw_psmt4)
            byte_addr = nib_addr // 2
            if byte_addr < len(vram):
                byte_val = vram[byte_addr]
                if nib_addr & 1:
                    out[y * tex_w + x] = (byte_val >> 4) & 0xF
                else:
                    out[y * tex_w + x] = byte_val & 0xF

    return out


def swizzle_psmt4(linear_pixels, tex_w, tex_h, bw_psmt4=None, dbw_ct32=None):
    """Re-swizzle linear PSMT4 data back into PSMCT32 upload format.

    This is the inverse of deswizzle_psmt4 -- useful for patching textures.

    Args:
        linear_pixels: Linear pixel indices (one byte per pixel, values 0-15)
        tex_w: Texture width
        tex_h: Texture height
        bw_psmt4: PSMT4 buffer width (default: tex_w)
        dbw_ct32: PSMCT32 upload buffer width (default: tex_w)

    Returns:
        bytearray of PSMCT32 upload data
    """
    if bw_psmt4 is None:
        bw_psmt4 = tex_w
    if dbw_ct32 is None:
        dbw_ct32 = tex_w

    upload_w = dbw_ct32
    total_nibbles = tex_w * tex_h
    upload_h = (total_nibbles // 2) // (upload_w * 4)

    vram_size = max(tex_w * tex_h // 2, upload_w * upload_h * 4) + 16384
    vram = bytearray(vram_size)

    # Write PSMT4 pixels to VRAM
    for y in range(tex_h):
        for x in range(tex_w):
            nib_addr = _psmt4_nibble_addr(x, y, bw_psmt4)
            byte_addr = nib_addr // 2
            if byte_addr < len(vram):
                val = linear_pixels[y * tex_w + x] & 0xF
                if nib_addr & 1:
                    vram[byte_addr] = (vram[byte_addr] & 0x0F) | (val << 4)
                else:
                    vram[byte_addr] = (vram[byte_addr] & 0xF0) | val

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


def make_rgba_image_4bit(pixels, palette, width, height):
    """Create RGBA PIL Image from 4-bit palette indices and RGBA palette bytes.

    Args:
        pixels: Linear pixel indices (0-15), one byte per pixel
        palette: 64 bytes of RGBA palette (16 colors x 4 bytes)
        width: Image width
        height: Image height
    """
    img = Image.new('RGBA', (width, height))
    pal_colors = []
    for i in range(16):
        r = palette[i * 4]
        g = palette[i * 4 + 1]
        b = palette[i * 4 + 2]
        a = min(palette[i * 4 + 3] * 2, 255)  # PS2 alpha is 0-128
        pal_colors.append((r, g, b, a))
    img_data = [pal_colors[min(p, 15)] for p in pixels[:width * height]]
    img.putdata(img_data)
    return img


def process_raw_psmt4(raw_path, width, height, out_path, dbw_ct32=None,
                      header_size=1024, clut_size=1024):
    """Load a raw PSMT4 texture file, deswizzle, and save as PNG.

    Args:
        raw_path: Path to raw file
        width: Texture width in pixels
        height: Texture height in pixels
        out_path: Output PNG path
        dbw_ct32: PSMCT32 upload buffer width (default: width)
        header_size: Header size in bytes (default: 1024)
        clut_size: CLUT block size at end of file (default: 1024)
    """
    data = open(raw_path, 'rb').read()
    npix = width * height
    pixel_bytes = npix // 2  # 4 bits per pixel

    pixels_raw = data[header_size:header_size + pixel_bytes]
    palette_raw = data[-clut_size:] if clut_size > 0 else bytearray(64)

    # For PSMT4, only first 64 bytes of CLUT matter (16 colors x 4 bytes RGBA)
    palette = bytearray(palette_raw[:64])

    if dbw_ct32 is None:
        dbw_ct32 = width

    print(f"  File: {len(data)} bytes, texture: {width}x{height} PSMT4")
    print(f"  Pixel data: {len(pixels_raw)} bytes at offset 0x{header_size:x}")
    print(f"  PSMCT32 upload width: {dbw_ct32} pixels")

    # Deswizzle pixels
    print("  Deswizzling pixels (VRAM simulation)...")
    pixels_lin = deswizzle_psmt4(pixels_raw, width, height,
                                  bw_psmt4=width, dbw_ct32=dbw_ct32)

    # Check if palette is all zeros (common for font textures using raw intensity)
    pal_nonzero = any(b != 0 for b in palette)
    if not pal_nonzero:
        print("  NOTE: Palette is all zeros. Using grayscale ramp for visualization.")
        palette = bytearray(64)
        for i in range(16):
            v = i * 17  # 0, 17, 34, ... 255
            palette[i*4] = v
            palette[i*4+1] = v
            palette[i*4+2] = v
            palette[i*4+3] = 128  # full alpha in PS2 terms

    # Save
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img = make_rgba_image_4bit(pixels_lin, palette, width, height)
    img.save(out_path)
    print(f"  Saved: {out_path}")

    return pixels_lin, palette, pixels_raw


def roundtrip_test(pixels_lin, width, height, original_data, dbw_ct32=None):
    """Verify round-trip: deswizzle then re-swizzle produces original data."""
    if dbw_ct32 is None:
        dbw_ct32 = width
    print("  Round-trip test: re-swizzling...")
    reswizzled = swizzle_psmt4(pixels_lin, width, height,
                                bw_psmt4=width, dbw_ct32=dbw_ct32)
    if reswizzled == original_data[:len(reswizzled)]:
        print("  Round-trip: PASS (exact match)")
        return True
    else:
        mismatches = sum(1 for a, b in zip(reswizzled, original_data) if a != b)
        print(f"  Round-trip: FAIL ({mismatches} byte mismatches out of {len(reswizzled)})")
        shown = 0
        for i, (a, b) in enumerate(zip(reswizzled, original_data)):
            if a != b:
                print(f"    offset 0x{i:x}: got 0x{a:02x}, expected 0x{b:02x}")
                shown += 1
                if shown >= 5:
                    break
        return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="PS2 PSMT4 deswizzle/swizzle tool")
    parser.add_argument("input", nargs="?", help="Input raw file path")
    parser.add_argument("-W", "--width", type=int, default=256,
                        help="Texture width (default: 256)")
    parser.add_argument("-H", "--height", type=int, default=512,
                        help="Texture height (default: 512)")
    parser.add_argument("--dbw", type=int, default=None,
                        help="PSMCT32 upload buffer width (default: width)")
    parser.add_argument("--bw", type=int, default=None,
                        help="PSMT4 buffer width for readback (default: width)")
    parser.add_argument("--header", type=int, default=1024,
                        help="Header size in bytes (default: 1024)")
    parser.add_argument("--clut", type=int, default=1024,
                        help="CLUT block size in bytes (default: 1024)")
    parser.add_argument("-o", "--output", default=None, help="Output PNG path")
    parser.add_argument("--roundtrip", action="store_true",
                        help="Run round-trip verification")
    parser.add_argument("--test-r1272", action="store_true",
                        help="Process R1272 (main font atlas, 256x512)")
    parser.add_argument("--test-r1188", action="store_true",
                        help="Process R1188 (name entry font, 1024x1024)")
    args = parser.parse_args()

    print("=== PS2 PSMT4 Deswizzle (VRAM simulation) ===\n")

    if args.test_r1272:
        raw_path = os.path.join(BASE, "extracted", "packdata_raw", "1272_type01.raw")
        out_path = os.path.join(TEX_DIR, "R1272_psmt4_deswizzled.png")
        print("Processing R1272 (256x512 PSMT4, main font atlas)...")
        pixels_lin, palette, pixels_raw = process_raw_psmt4(
            raw_path, 256, 512, out_path, dbw_ct32=256)
        if args.roundtrip:
            roundtrip_test(pixels_lin, 256, 512, pixels_raw, dbw_ct32=256)
        print()

    if args.test_r1188:
        # Try .bin first (packdata_resources), fall back to .raw
        bin_path = os.path.join(BASE, "extracted", "packdata_resources", "1188_type01.bin")
        raw_path = os.path.join(BASE, "extracted", "packdata_raw", "1188_type01.raw")
        out_path = os.path.join(TEX_DIR, "R1188_psmt4_deswizzled.png")
        print("Processing R1188 (1024x1024 PSMT4, name entry font)...")
        # R1188 bin: 527360 bytes = 3072 (0xC00) GIF header + 524288 pixel bytes
        # TEX0: TBP0=0, TBW=16, PSM=PSMT4(20), 1024x1024
        # CRITICAL: dbw_ct32=512 (NOT 1024!) -- empirically verified against
        # 21/31 PCSX2 texture dumps with exact roundtrip PASS.
        # No CLUT block at end of file (CLUT stored in separate VRAM region).
        if os.path.exists(bin_path):
            pixels_lin, palette, pixels_raw = process_raw_psmt4(
                bin_path, 1024, 1024, out_path, dbw_ct32=512,
                header_size=0xC00, clut_size=0)
            if args.roundtrip:
                roundtrip_test(pixels_lin, 1024, 1024, pixels_raw, dbw_ct32=512)
        else:
            # .raw has 16-byte outer container before .bin data
            pixels_lin, palette, pixels_raw = process_raw_psmt4(
                raw_path, 1024, 1024, out_path, dbw_ct32=512,
                header_size=0xC10, clut_size=0)
            if args.roundtrip:
                roundtrip_test(pixels_lin, 1024, 1024, pixels_raw, dbw_ct32=512)
        print()

    if args.input:
        raw_path = args.input
        out_path = args.output or raw_path.replace('.raw', '_psmt4_deswizzled.png')
        dbw = args.dbw or args.width
        bw = args.bw or args.width
        data = open(raw_path, 'rb').read()
        pixel_bytes = args.width * args.height // 2
        pixels_raw = data[args.header:args.header + pixel_bytes]

        print(f"  File: {len(data)} bytes, texture: {args.width}x{args.height} PSMT4")
        print(f"  Pixel data: {len(pixels_raw)} bytes at offset 0x{args.header:x}")
        print(f"  PSMCT32 upload width: {dbw}, PSMT4 buffer width: {bw}")

        # Get palette
        palette_raw = data[-args.clut:] if args.clut > 0 else bytearray(64)
        palette = bytearray(palette_raw[:64])
        pal_nonzero = any(b != 0 for b in palette)
        if not pal_nonzero:
            print("  NOTE: Palette is all zeros. Using grayscale ramp.")
            palette = bytearray(64)
            for i in range(16):
                v = i * 17
                palette[i*4] = v; palette[i*4+1] = v
                palette[i*4+2] = v; palette[i*4+3] = 128

        print("  Deswizzling pixels (VRAM simulation)...")
        pixels_lin = deswizzle_psmt4(pixels_raw, args.width, args.height,
                                      bw_psmt4=bw, dbw_ct32=dbw)
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        img = make_rgba_image_4bit(pixels_lin, palette, args.width, args.height)
        img.save(out_path)
        print(f"  Saved: {out_path}")

        if args.roundtrip:
            roundtrip_test(pixels_lin, args.width, args.height, pixels_raw,
                          dbw_ct32=dbw)

    if not args.input and not args.test_r1272 and not args.test_r1188:
        parser.print_help()

    print("\nDone!")


if __name__ == "__main__":
    main()
