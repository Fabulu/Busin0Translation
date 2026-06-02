#!/usr/bin/env python3
"""
R1370 pixel-data-only zeroing test + texture deswizzle/preview.

R1370 is at PACKDATA sectors 85-124 (40 sectors = 81920 bytes).
It contains 4 sub-blocks:
  Sub 0 (38560 bytes): PSMT4 256x256 texture atlas
    - 3744 bytes header (GIF tag + 32 A+D register blocks + vertex/sprite
      data + DMA transfer table)
    - 32768 bytes pixel data (PSMT4 256x256, swizzled)
    - 2048 bytes CLUT (PSMCT16 palettes, 32 per sub)
  Sub 1 (38240 bytes): PSMT4 256x256 texture atlas
    - 3680 bytes header
    - 32768 bytes pixel data
    - 1792 bytes CLUT (28 palettes)
  Sub 2 (2168 bytes): UV coordinate table (no pixels)
  Sub 3 (1588 bytes): UV coordinate table (no pixels)

TEX0 for both subs: TBP0=0 TBW=4 PSM=0x14 (PSMT4) 256x256, CPSM=PSMCT16

This script:
  1. Reads R1370 from PACKDATA.DIG
  2. Deswizzles the PSMT4 pixel data and saves as PNG for inspection
  3. Creates a test ISO with ONLY pixel data zeroed (headers, CLUT, UV tables preserved)
"""
import struct
import shutil
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))

from psmt4_deswizzle import deswizzle_psmt4

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

# ── Paths ──
DIG_PATH  = os.path.join(BASE, "extracted", "PACKDATA.DIG")
ORIG_ISO  = os.path.join(BASE, "Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso")
OUT_ISO   = os.path.join(BASE, "build", "TEST_r1370_pixels_only.iso")
PREVIEW_DIR = os.path.join(BASE, "build")

# ── Constants ──
SECTOR = 2048
PACKDATA_LBA = 16029

# R1370 location within PACKDATA
R1370_SECTOR_OFFSET = 85
R1370_SECTOR_COUNT  = 40
R1370_PACKDATA_BYTE_OFFSET = R1370_SECTOR_OFFSET * SECTOR  # 174080

# R1370 location within ISO
R1370_ISO_OFFSET = (PACKDATA_LBA + R1370_SECTOR_OFFSET) * SECTOR  # 33001472

# Sub-block descriptor table (64 bytes = 4 entries x 16 bytes)
# Each entry: [sub_index:u32, sub_size:u32, data_offset:u32, padding:u32]
SUB_DESCRIPTORS = [
    # (offset_in_resource, size, pixel_offset_in_sub, pixel_size)
    (0x40,   38560, 0xEA0, 32768),  # Sub 0
    (0x96E0, 38240, 0xE60, 32768),  # Sub 1
    # Sub 2 (2168 bytes) and Sub 3 (1588 bytes) are UV tables, no pixels
]

TEX_W, TEX_H = 256, 256
DBW_CT32 = 128  # TBW=4 -> buffer width in PSMCT32 pixels = 4*64 = 256, dbw_ct32=256/2=128


def unswizzle_psmct16_clut(clut_data):
    """Decode PSMCT16 palette (16 colors for PSMT4)."""
    colors = []
    for i in range(16):
        if i * 2 + 2 <= len(clut_data):
            val = struct.unpack_from('<H', clut_data, i * 2)[0]
            r = (val & 0x1F) << 3
            g = ((val >> 5) & 0x1F) << 3
            b = ((val >> 10) & 0x1F) << 3
            a = 255 if (val >> 15) & 1 else 128  # alpha bit
            colors.append((r, g, b, a))
        else:
            colors.append((0, 0, 0, 0))
    return colors


def deswizzle_and_save(sub_data, pixel_offset, clut_data, sub_idx, out_dir):
    """Deswizzle PSMT4 pixel data and save as PNG."""
    pixel_data = sub_data[pixel_offset:pixel_offset + 32768]

    # deswizzle_psmt4 returns flat bytearray: one byte per pixel, values 0-15
    pixels = deswizzle_psmt4(pixel_data, TEX_W, TEX_H, dbw_ct32=DBW_CT32)

    # Try first palette from CLUT
    palette = unswizzle_psmct16_clut(clut_data[:32])

    # Create RGBA image using first palette
    img = Image.new('RGBA', (TEX_W, TEX_H))
    for y in range(TEX_H):
        for x in range(TEX_W):
            idx = pixels[y * TEX_W + x] & 0xF
            img.putpixel((x, y), palette[idx])

    out_path = os.path.join(out_dir, f"r1370_sub{sub_idx}_deswizzled.png")
    img.save(out_path)
    print(f"    Saved deswizzled preview: {out_path}")

    # Also save grayscale (index values scaled to 0-255) for shape visibility
    img_bw = Image.new('L', (TEX_W, TEX_H))
    for y in range(TEX_H):
        for x in range(TEX_W):
            idx = pixels[y * TEX_W + x] & 0xF
            img_bw.putpixel((x, y), idx * 17)  # 0->0, 15->255

    out_path_bw = os.path.join(out_dir, f"r1370_sub{sub_idx}_grayscale.png")
    img_bw.save(out_path_bw)
    print(f"    Saved grayscale preview: {out_path_bw}")

    return pixels


def main():
    os.makedirs(PREVIEW_DIR, exist_ok=True)

    # ── Step 1: Read R1370 from PACKDATA.DIG ──
    print("Reading R1370 from PACKDATA.DIG...")
    with open(DIG_PATH, 'rb') as f:
        f.seek(R1370_PACKDATA_BYTE_OFFSET)
        r1370 = bytearray(f.read(R1370_SECTOR_COUNT * SECTOR))

    print(f"  Read {len(r1370)} bytes from offset {R1370_PACKDATA_BYTE_OFFSET}")

    # Verify descriptor table
    for i in range(4):
        sub_idx, sub_size, data_off, pad = struct.unpack_from('<IIII', r1370, i * 16)
        print(f"  Sub {i}: index={sub_idx}, size={sub_size}, offset=0x{data_off:X}")

    # ── Step 2: Deswizzle and save PNGs ──
    print("\nDeswizzling textures...")
    for sub_idx, (sub_off, sub_size, pix_off, pix_size) in enumerate(SUB_DESCRIPTORS):
        print(f"\n  Sub {sub_idx}: offset=0x{sub_off:X}, size={sub_size}")
        sub_data = r1370[sub_off:sub_off + sub_size]

        # CLUT is at: pixel_offset + pixel_size to end of sub
        clut_offset = pix_off + pix_size
        clut_data = sub_data[clut_offset:]
        print(f"    Pixel data: sub+0x{pix_off:X}, {pix_size} bytes")
        print(f"    CLUT data: sub+0x{clut_offset:X}, {len(clut_data)} bytes")

        deswizzle_and_save(sub_data, pix_off, clut_data, sub_idx, PREVIEW_DIR)

    # ── Step 3: Create test ISO with only pixel data zeroed ──
    print(f"\nCreating test ISO: {OUT_ISO}")
    print(f"  Copying original ISO: {ORIG_ISO}")
    shutil.copy2(ORIG_ISO, OUT_ISO)

    with open(OUT_ISO, 'r+b') as f:
        for sub_idx, (sub_off, sub_size, pix_off, pix_size) in enumerate(SUB_DESCRIPTORS):
            # Calculate absolute ISO offset for this sub's pixel data
            abs_offset = R1370_ISO_OFFSET + sub_off + pix_off
            print(f"  Sub {sub_idx}: zeroing {pix_size} bytes at ISO offset 0x{abs_offset:X}")
            f.seek(abs_offset)
            f.write(b'\x00' * pix_size)

    # ── Step 4: Verify ──
    print("\nVerifying...")
    with open(OUT_ISO, 'rb') as f:
        # Check pixel regions are zeroed
        for sub_idx, (sub_off, sub_size, pix_off, pix_size) in enumerate(SUB_DESCRIPTORS):
            abs_offset = R1370_ISO_OFFSET + sub_off + pix_off
            f.seek(abs_offset)
            data = f.read(pix_size)
            is_zero = all(b == 0 for b in data)
            print(f"  Sub {sub_idx} pixels: {'ZEROED' if is_zero else 'NOT ZEROED'}")

        # Check headers are NOT zeroed
        for sub_idx, (sub_off, sub_size, pix_off, pix_size) in enumerate(SUB_DESCRIPTORS):
            abs_offset = R1370_ISO_OFFSET + sub_off
            f.seek(abs_offset)
            header = f.read(pix_off)
            is_zero = all(b == 0 for b in header)
            print(f"  Sub {sub_idx} header ({pix_off} bytes): {'ZEROED (BAD!)' if is_zero else 'INTACT'}")

        # Check CLUT is NOT zeroed
        for sub_idx, (sub_off, sub_size, pix_off, pix_size) in enumerate(SUB_DESCRIPTORS):
            clut_off = pix_off + pix_size
            clut_size = sub_size - clut_off
            abs_offset = R1370_ISO_OFFSET + sub_off + clut_off
            f.seek(abs_offset)
            clut = f.read(clut_size)
            is_zero = all(b == 0 for b in clut)
            print(f"  Sub {sub_idx} CLUT ({clut_size} bytes): {'ZEROED (BAD!)' if is_zero else 'INTACT'}")

        # Check UV tables (subs 2, 3) are NOT zeroed
        for sub_idx in (2, 3):
            si, ss, so, _ = struct.unpack_from('<IIII', r1370, sub_idx * 16)
            abs_offset = R1370_ISO_OFFSET + so
            f.seek(abs_offset)
            uv_data = f.read(ss)
            is_zero = all(b == 0 for b in uv_data)
            print(f"  Sub {sub_idx} UV table ({ss} bytes): {'ZEROED (BAD!)' if is_zero else 'INTACT'}")

    iso_size = os.path.getsize(OUT_ISO)
    print(f"\nOutput ISO: {OUT_ISO} ({iso_size:,} bytes)")
    print("\n=== DONE ===")
    print("Test plan:")
    print("  1. Boot TEST_r1370_pixels_only.iso in PCSX2")
    print("  2. Navigate to name entry / character creation screen")
    print("  3. Check if backgrounds are gone but text/UI remains")
    print("  4. Compare with full R1370 zero test to see what the headers control")


if __name__ == "__main__":
    main()
