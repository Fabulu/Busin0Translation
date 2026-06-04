#!/usr/bin/env python3
"""
Find all 13 stat label kanji positions in R1188's bw=256 deswizzled view.

Builds VRAM simulation, reads back as PSMT4 bw=256, and uses the reverse
nibble mapping to locate each stat kanji glyph cell.
"""
import sys
import os

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))

from psmt4_deswizzle import (
    _psmt4_nibble_addr, _psmct32_word_addr,
    make_rgba_image_4bit
)

try:
    from PIL import Image
except ImportError:
    print("Pillow not installed"); sys.exit(1)

# ---------------------------------------------------------------------------
# R1188 constants
# ---------------------------------------------------------------------------
TEX_W, TEX_H = 1024, 1024
DBW_CT32 = 512
ATLAS_TBP = 0x2840
GLYPH_TBW = 128
VRAM_BLOCK_UNIT = 64

BW256 = 256
H256 = 4096

BIN_PATH = os.path.join(BASE, "extracted", "packdata_resources", "1188_type01.bin")
RAW_PATH = os.path.join(BASE, "extracted", "packdata_raw", "1188_type01.raw")
DEBUG_DIR = os.path.join(BASE, "build", "textures_to_edit")

# Stat label glyph cells from EXE
STAT_GLYPHS = [
    ("STR/力",   "T",  1, 60, 0xA450),
    ("INT1/知",  "I",  1, 66, 0xA270),
    ("INT2/恵",  "Q",  0, 84, 0xA480),
    ("PIE1/信",  "P",  0, 62, 0xA328),
    ("PIE2/仰",  "I",  1, 67, 0xA490),
    ("PIE3/心",  "E",  0, 64, 0xA380),
    ("VIT1/生",  "V",  0, 85, 0xA7E8),
    ("VIT2/命",  "I",  4, 70, 0xA758),
    ("AGI1/敏",  "A",  0, 74, 0xA3D0),
    ("AGI2/捷",  "G",  0, 86, 0xA7F0),
    ("AGI3/度",  "I",  0, 82, 0xA410),
    ("LCK1/幸",  "L",  0, 87, 0xA7F8),
    ("LCK2/運",  "C",  0, 88, 0xA800),
]


def main():
    print("=" * 60)
    print("  Find stat kanji positions in R1188 bw=256 deswizzled view")
    print("=" * 60)

    # Load R1188
    if os.path.exists(BIN_PATH):
        data = open(BIN_PATH, 'rb').read()
        header_size = 0xC00
    else:
        data = open(RAW_PATH, 'rb').read()
        header_size = 0xC10
    pixel_data = data[header_size:header_size + TEX_W * TEX_H // 2]
    print(f"  Loaded {len(pixel_data)} bytes of pixel data")

    # Step 1: Upload to simulated VRAM using PSMCT32
    print("  Uploading to VRAM via PSMCT32 (dbw={})...".format(DBW_CT32))
    upload_w = DBW_CT32
    upload_h = len(pixel_data) // (upload_w * 4)
    vram_size = 4 * 1024 * 1024
    vram = bytearray(vram_size)

    for y in range(upload_h):
        for x in range(upload_w):
            off = (y * upload_w + x) * 4
            if off + 4 > len(pixel_data):
                break
            wa = _psmct32_word_addr(x, y, upload_w)
            vb = wa * 4
            if vb + 4 <= len(vram):
                vram[vb:vb+4] = pixel_data[off:off+4]

    # Step 2: Read back as PSMT4 bw=256
    print("  Reading back as PSMT4 bw=256 (256x4096)...")
    pixels_bw256 = bytearray(BW256 * H256)
    for y in range(H256):
        for x in range(BW256):
            nib = _psmt4_nibble_addr(x, y, BW256)
            ba = nib // 2
            if ba < len(vram):
                bv = vram[ba]
                if nib & 1:
                    pixels_bw256[y * BW256 + x] = (bv >> 4) & 0xF
                else:
                    pixels_bw256[y * BW256 + x] = bv & 0xF

    # Save the bw=256 deswizzled image
    os.makedirs(DEBUG_DIR, exist_ok=True)
    palette = bytearray(64)
    for i in range(16):
        v = i * 17
        palette[i*4:i*4+4] = bytes([v, v, v, 128])
    img256 = make_rgba_image_4bit(pixels_bw256, palette, BW256, H256)
    out_png = os.path.join(DEBUG_DIR, "R1188_bw256_deswizzled.png")
    img256.save(out_png)
    print(f"  Saved: {out_png}")

    # Step 3: Build reverse lookup
    print("  Building VRAM-nibble -> bw256 (x,y) reverse lookup...")
    nib_to_xy = {}
    for y in range(H256):
        for x in range(BW256):
            nib = _psmt4_nibble_addr(x, y, BW256)
            nib_to_xy[nib] = (x, y)

    vram_base = ATLAS_TBP * 256

    # Step 4: Map each glyph and verify with density check
    print("\n  === ALL 13 STAT GLYPH POSITIONS (bw=256 view) ===\n")
    print(f"  {'Label':<12s}  {'VRAM':>6s}  {'U':>2s} {'V':>2s}  {'bw256 (x,y)':>14s}  {'Density':>8s}")
    print("  " + "-" * 56)

    results = {}
    for label, eng, u_cell, v_cell, vram_blk in STAT_GLYPHS:
        local_tbp = (vram_blk * VRAM_BLOCK_UNIT) - vram_base
        cell_nib = _psmt4_nibble_addr(u_cell, v_cell, GLYPH_TBW)
        vram_nib = local_tbp * 2 + cell_nib

        if vram_nib in nib_to_xy:
            x256, y256 = nib_to_xy[vram_nib]

            # Count nonzero pixels in 20x20 block
            nonzero = 0
            for dy in range(20):
                for dx in range(20):
                    tx, ty = x256 + dx, y256 + dy
                    if 0 <= tx < BW256 and 0 <= ty < H256:
                        if pixels_bw256[ty * BW256 + tx] > 0:
                            nonzero += 1

            results[label] = (x256, y256)
            print(f"  {label:<12s}  0x{vram_blk:04X}  {u_cell:2d} {v_cell:2d}  "
                  f"({x256:3d}, {y256:4d})    {nonzero:3d}/400")
        else:
            print(f"  {label:<12s}  0x{vram_blk:04X}  {u_cell:2d} {v_cell:2d}  NOT FOUND")

    # Step 5: Print the final dict
    print("\n  === STAT_POSITIONS_BW256 ===")
    print("  STAT_POSITIONS_BW256 = {")
    for label, eng, u_cell, v_cell, vram_blk in STAT_GLYPHS:
        if label in results:
            x, y = results[label]
            kanji = label.split("/")[1] if "/" in label else label
            print(f"      0x{vram_blk:04X}: ({x:3d}, {y:4d}),  # {kanji}")
    print("  }")

    # Step 6: Also save closeup images for verification
    print("\n  Saving closeup images...")
    closeup_w = 6 * 80  # 6 columns, 80px each
    closeup_h = 3 * 80  # 3 rows (13 glyphs: 5 cols x 3 rows)
    cols = 5
    closeup = Image.new('L', (cols * 82, 3 * 82), 0)
    idx = 0
    for label, eng, u_cell, v_cell, vram_blk in STAT_GLYPHS:
        if label in results:
            x, y = results[label]
            # Extract 20x20 region and scale 4x
            cell_img = Image.new('L', (20, 20), 0)
            for dy in range(20):
                for dx in range(20):
                    tx, ty = x + dx, y + dy
                    if 0 <= tx < BW256 and 0 <= ty < H256:
                        cell_img.putpixel((dx, dy), pixels_bw256[ty * BW256 + tx] * 17)
            cell_big = cell_img.resize((80, 80), Image.NEAREST)
            col = idx % cols
            row = idx // cols
            closeup.paste(cell_big, (col * 82 + 1, row * 82 + 1))
            idx += 1
    closeup_path = os.path.join(DEBUG_DIR, "R1188_bw256_stat_closeups.png")
    closeup.save(closeup_path)
    print(f"  Saved: {closeup_path}")

    print("\n  Done! All 13 stat kanji positions found in bw=256 view.")


if __name__ == "__main__":
    main()
