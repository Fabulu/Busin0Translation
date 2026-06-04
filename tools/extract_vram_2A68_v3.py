#!/usr/bin/env python3
"""
Extract TBP0=0x2A68 from VRAM trying multiple PSM formats and buffer widths.
Also extract the actual stat label textures from the kanji font page region.
"""
import os
import sys
import struct

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))
from psmt4_deswizzle import _psmt4_nibble_addr, _psmct32_word_addr, deswizzle_psmt4

from PIL import Image

GS_HEADER = 509

# PSMT8 tables from PCSX2
BLOCK_TABLE_8 = [
    [ 0,  1,  4,  5, 16, 17, 20, 21],
    [ 2,  3,  6,  7, 18, 19, 22, 23],
    [ 8,  9, 12, 13, 24, 25, 28, 29],
    [10, 11, 14, 15, 26, 27, 30, 31],
]

# PSMT8 column table: 16 rows x 16 columns
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


def _psmt8_byte_addr(x, y, bw):
    """PSMT8 pixel address -> byte index in VRAM.
    PSMT8: 128x64 per page, 16x16 per block
    """
    PAGE_W, PAGE_H = 128, 64
    BLOCK_W, BLOCK_H = 16, 16
    ppr = max(1, bw // PAGE_W)
    pid = (y // PAGE_H) * ppr + (x // PAGE_W)
    bid = BLOCK_TABLE_8[(y % PAGE_H) // BLOCK_H][(x % PAGE_W) // BLOCK_W]
    byte_idx = COLUMN_TABLE_8[y % BLOCK_H][x % BLOCK_W]
    # Page = 32 blocks * 256 bytes = 8192 bytes
    return pid * 8192 + bid * 256 + byte_idx


def read_psmt4_from_vram(vram, tbp0, w, h, bw):
    base_nibble = tbp0 * 512
    out = bytearray(w * h)
    for y in range(h):
        for x in range(w):
            nib_off = _psmt4_nibble_addr(x, y, bw)
            nib = base_nibble + nib_off
            ba = nib // 2
            if ba < len(vram):
                bv = vram[ba]
                out[y * w + x] = ((bv >> 4) & 0xF) if (nib & 1) else (bv & 0xF)
    return out


def read_psmt8_from_vram(vram, tbp0, w, h, bw):
    base_byte = tbp0 * 256
    out = bytearray(w * h)
    for y in range(h):
        for x in range(w):
            byte_off = _psmt8_byte_addr(x, y, bw)
            addr = base_byte + byte_off
            if addr < len(vram):
                out[y * w + x] = vram[addr]
    return out


def save_img(pixels, w, h, path, invert=False, bpp=4):
    img = Image.new('L', (w, h))
    data = []
    for p in pixels[:w*h]:
        if bpp == 4:
            v = p * 17
        else:
            v = p
        if invert:
            v = 255 - v
        data.append(min(255, v))
    img.putdata(data)
    img.save(path)


def main():
    out_dir = os.path.join(BASE, "debug_vram")
    os.makedirs(out_dir, exist_ok=True)

    with open(os.path.join(BASE, "RAMdumps", "GS.bin"), 'rb') as f:
        data = f.read()
    vram = data[GS_HEADER:]
    print(f"VRAM: {len(vram)} bytes")

    # =========================================
    # Extract TBP0=0x2A68 as BOTH PSMT4 and PSMT8
    # =========================================
    TBP0 = 0x2A68

    print(f"\n=== TBP0=0x{TBP0:X} as PSMT4 256x256 bw=256 ===")
    p4 = read_psmt4_from_vram(vram, TBP0, 256, 256, 256)
    nz4 = sum(1 for p in p4 if p != 0)
    save_img(p4, 256, 256, os.path.join(out_dir, f"vram_{TBP0:04X}_psmt4_256.png"), invert=True)
    print(f"  Non-zero: {nz4}")

    print(f"\n=== TBP0=0x{TBP0:X} as PSMT8 256x256 bw=256 ===")
    p8_256 = read_psmt8_from_vram(vram, TBP0, 256, 256, 256)
    nz8 = sum(1 for p in p8_256 if p != 0)
    save_img(p8_256, 256, 256, os.path.join(out_dir, f"vram_{TBP0:04X}_psmt8_256.png"), invert=True, bpp=8)
    print(f"  Non-zero: {nz8}")

    print(f"\n=== TBP0=0x{TBP0:X} as PSMT8 128x128 bw=128 ===")
    p8_128 = read_psmt8_from_vram(vram, TBP0, 128, 128, 128)
    nz8b = sum(1 for p in p8_128 if p != 0)
    save_img(p8_128, 128, 128, os.path.join(out_dir, f"vram_{TBP0:04X}_psmt8_128.png"), invert=True, bpp=8)
    print(f"  Non-zero: {nz8b}")

    # Also try as PSMCT32 (maybe it's a rendered sprite strip)
    print(f"\n=== TBP0=0x{TBP0:X} as PSMCT32 64x64 bw=64 ===")
    base_word = TBP0 * 64
    out32 = bytearray(64 * 64 * 4)
    for y in range(64):
        for x in range(64):
            word_off = _psmct32_word_addr(x, y, 64)
            wa = base_word + word_off
            ba = wa * 4
            if ba + 4 <= len(vram):
                off = (y * 64 + x) * 4
                out32[off:off+4] = vram[ba:ba+4]
    img32 = Image.new('RGBA', (64, 64))
    for y in range(64):
        for x in range(64):
            off = (y * 64 + x) * 4
            r, g, b, a = out32[off], out32[off+1], out32[off+2], min(out32[off+3]*2, 255)
            img32.putpixel((x, y), (r, g, b, a))
    img32.save(os.path.join(out_dir, f"vram_{TBP0:04X}_ct32_64x64.png"))

    # =========================================
    # Now extract the KANJI FONT PAGES from VRAM
    # These are the actual stat label sources
    # =========================================
    # From stat_vram_source.md:
    # Kanji pages are at TBP0=0x3000+ as PSMT8 256x256 tiles
    # R1272 is also at TBP0=0x3000 as PSMT4 256x512

    print("\n" + "=" * 60)
    print("KANJI FONT PAGES (stat label sources)")
    print("=" * 60)

    # From stat_vram_source.md: kanji pages at TBP0=0x3000-0x3C38
    # These overlap with R1272 region
    # Let's try various TBP0s as PSMT8

    # From gs_vram_analysis.md tile list for R1188:
    r1188_tiles = [0x2840, 0x28CA, 0x2954, 0x29DE, 0x2A68,
                   0x2B08, 0x2BA4, 0x2C34, 0x2CC4, 0x2D56]

    # Let's try reading each as PSMT8 too
    print("\n--- R1188 region tiles as PSMT8 ---")
    for tbp0 in r1188_tiles:
        pix = read_psmt8_from_vram(vram, tbp0, 256, 256, 256)
        nz = sum(1 for p in pix if p != 0)
        path = os.path.join(out_dir, f"vram_{tbp0:04X}_psmt8.png")
        save_img(pix, 256, 256, path, invert=True, bpp=8)
        print(f"  TBP0=0x{tbp0:04X} PSMT8: {nz} nz -> {os.path.basename(path)}")

    # =========================================
    # Compare R1188 disc data with VRAM tiles
    # The issue might be we're comparing wrong sub-regions
    # R1188 uploads 1024x1024 as tiles, but which order?
    # =========================================
    print("\n=== R1188 disc tile comparison (trying all possible mappings) ===")

    r1188_path = os.path.join(BASE, "extracted", "packdata_resources", "1188_type01.bin")
    r1188_data = open(r1188_path, 'rb').read()
    r1188_full = deswizzle_psmt4(r1188_data[0xC00:0xC00 + 524288], 1024, 1024,
                                  bw_psmt4=1024, dbw_ct32=512)

    # Extract 16 sub-tiles from R1188 (4x4 grid of 256x256)
    disc_tiles = {}
    for row in range(4):
        for col in range(4):
            tile = bytearray(256*256)
            for y in range(256):
                src_y = row * 256 + y
                for x in range(256):
                    src_x = col * 256 + x
                    tile[y*256+x] = r1188_full[src_y*1024+src_x]
            disc_tiles[row*4+col] = tile

    # For each VRAM tile, find best match against all 16 disc tiles
    for tbp0 in r1188_tiles:
        vpix = read_psmt4_from_vram(vram, tbp0, 256, 256, 256)
        vnz = sum(1 for p in vpix if p != 0)
        best_pct = 0
        best_tile = -1
        for ti, dpix in disc_tiles.items():
            total = 256*256
            matches = sum(1 for i in range(total) if vpix[i] == dpix[i])
            pct = matches / total * 100
            if pct > best_pct:
                best_pct = pct
                best_tile = ti
        print(f"  VRAM 0x{tbp0:04X} (nz={vnz}): best disc tile {best_tile} "
              f"(row={best_tile//4},col={best_tile%4}) at {best_pct:.1f}%")

    # =========================================
    # The R1188 comparison is only ~30% - this is noise.
    # The texture at 0x2A68 may NOT be from R1188.
    # Let's look at what ELSE could produce this data.
    # =========================================

    # Search ALL type01 and type04 resources for pixel data matching
    print("\n=== Brute-force search: try deswizzling each resource and comparing ===")
    res_dir = os.path.join(BASE, "extracted", "packdata_resources")
    target = read_psmt4_from_vram(vram, 0x2A68, 256, 256, 256)
    target_nz = sum(1 for p in target if p != 0)

    # For faster search, use a fingerprint: histogram of palette indices
    target_hist = [0] * 16
    for p in target:
        target_hist[p] += 1
    print(f"  Target histogram: {target_hist}")

    # Check top candidates by trying various deswizzle params
    files = sorted(os.listdir(res_dir))
    type01_files = [f for f in files if 'type01' in f]

    print(f"\n  Checking {len(type01_files)} type01 resources...")
    best_results = []

    for fname in type01_files:
        fpath = os.path.join(res_dir, fname)
        fdata = open(fpath, 'rb').read()

        # Skip tiny files
        if len(fdata) < 32768:
            continue

        # Try as 256x256 PSMT4 with various headers and dbw values
        for hdr in [0, 0x400, 0xC00, 0x200, 0x800, 0x1000]:
            pdata = fdata[hdr:hdr+32768]
            if len(pdata) < 32768:
                continue

            for dbw in [128, 256]:
                try:
                    dpix = deswizzle_psmt4(pdata, 256, 256, bw_psmt4=256, dbw_ct32=dbw)
                    matches = sum(1 for i in range(65536) if target[i] == dpix[i])
                    pct = matches / 65536 * 100
                    if pct > 60:
                        print(f"  ** {fname} hdr=0x{hdr:X} dbw={dbw}: {pct:.1f}%")
                        best_results.append((pct, fname, hdr, dbw))
                except:
                    pass

    if best_results:
        best_results.sort(reverse=True)
        print("\nBest matches:")
        for pct, fname, hdr, dbw in best_results[:10]:
            print(f"  {pct:.1f}% - {fname} (hdr=0x{hdr:X}, dbw={dbw})")
    else:
        print("  No strong matches found in type01 resources.")

    # Also check: is TBP0=0x2A68 actually R1188?
    # The R1188 tile spacing from gs_vram_analysis.md:
    # 0x2840, 0x28CA, 0x2954, 0x29DE ... spacing = 0x8A, 0x8A, 0x8A
    # Then 0x2A68 is at 0x29DE + 0x8A = 0x2A68. Yes! It fits the pattern!
    print("\n=== R1188 tile spacing analysis ===")
    for i in range(1, len(r1188_tiles)):
        diff = r1188_tiles[i] - r1188_tiles[i-1]
        print(f"  0x{r1188_tiles[i]:04X} - 0x{r1188_tiles[i-1]:04X} = 0x{diff:02X} ({diff} blocks = {diff*256} bytes)")

    # 0x8A blocks = 138 blocks = 35328 bytes
    # For 256x256 PSMT4: pixel data = 32768 bytes
    # Remaining 2560 bytes = CLUT (256 bytes per 16-entry PSMCT16 = 32 bytes, so this is bigger)
    # Actually CLUT at TBP0+0x80 = 0x2840+0x80 = 0x28C0, and 0x80 = 128 blocks = 32768 bytes
    # So: tile data = 0x80 blocks = 32768 bytes, then CLUT, then gap to next tile

    print("\nDone!")


if __name__ == '__main__':
    main()
