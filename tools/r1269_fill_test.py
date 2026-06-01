#!/usr/bin/env python3
"""
r1269_fill_test.py -- Fill R1269 pixel data with 0x88 to identify which kanji glyphs it provides.

R1269 is a PSMT8 512x512 font page texture. Its header (GS regs + palette) occupies
bytes 0x000-0x4BF (1216 bytes). Pixel data starts at 0x4C0 (262144 bytes).

This script:
  1. Copies the original ISO
  2. Locates PACKDATA.DIG inside the ISO
  3. Reads R1269's TOC entry to find its sector offset
  4. Fills R1269's pixel data (offset 0x4C0 onwards) with 0x88
  5. Writes the result as build/BUSIN0_EN_r1269_fill_test.iso

If some kanji in-game become solid blocks, those glyphs live on R1269.
"""

import struct
import shutil
import os
import sys

SECTOR = 2048
TOC_ENTRIES = 2883
R1269_INDEX = 1269

# R1269 format: PSMT8 512x512
# In the ISO raw resource, there's a 16-byte sub-header before the TIM2 data.
# TIM2 header + GS regs + palette: 0x4C0 bytes (1216)
# So pixel data starts at 16 + 0x4C0 = 0x4D0 from the raw resource start.
# Pixel data: 512*512 = 262144 bytes
PIX_START = 0x4D0
PIX_SIZE = 262144
FILL_BYTE = 0x88

BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
ISO_PATH = os.path.join(BASE, "Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso")
OUTPUT_ISO = os.path.join(BASE, "build", "BUSIN0_EN_r1269_fill_test.iso")


def find_packdata_in_iso(f):
    """Parse ISO9660 PVD -> root directory -> find PACKDATA.DIG extent."""
    f.seek(16 * SECTOR)
    pvd = f.read(SECTOR)
    root_lba = struct.unpack_from('<I', pvd, 158)[0]
    root_size = struct.unpack_from('<I', pvd, 166)[0]

    f.seek(root_lba * SECTOR)
    root_dir = f.read(root_size)

    pos = 0
    while pos < len(root_dir):
        rec_len = root_dir[pos]
        if rec_len == 0:
            break
        name_len = root_dir[pos + 32]
        name = root_dir[pos + 33:pos + 33 + name_len].decode('ascii', errors='replace')
        file_lba = struct.unpack_from('<I', root_dir, pos + 2)[0]
        file_size = struct.unpack_from('<I', root_dir, pos + 10)[0]
        if 'PACKDATA' in name:
            print(f"  PACKDATA.DIG: LBA={file_lba}, size={file_size:,}")
            return file_lba, file_size
        pos += rec_len

    raise RuntimeError("PACKDATA.DIG not found in ISO root directory!")


def main():
    print("=" * 60)
    print("  R1269 FILL TEST - Solid block font page identification")
    print("=" * 60)
    print()

    if not os.path.exists(ISO_PATH):
        print(f"ERROR: Source ISO not found: {ISO_PATH}")
        sys.exit(1)

    # Step 1: Copy ISO
    print(f"Step 1: Copying ISO to {OUTPUT_ISO} ...")
    os.makedirs(os.path.dirname(OUTPUT_ISO), exist_ok=True)
    shutil.copy2(ISO_PATH, OUTPUT_ISO)
    print(f"  Done. Size: {os.path.getsize(OUTPUT_ISO):,} bytes")

    # Step 2: Patch R1269 in-place
    print(f"\nStep 2: Opening ISO for in-place editing ...")
    with open(OUTPUT_ISO, "r+b") as f:
        # Find PACKDATA.DIG
        print("\nStep 3: Finding PACKDATA.DIG ...")
        pack_lba, pack_size = find_packdata_in_iso(f)
        pack_offset = pack_lba * SECTOR

        # Read R1269 TOC entry
        print(f"\nStep 4: Reading R1269 TOC entry ...")
        toc_offset = pack_offset + R1269_INDEX * 12
        f.seek(toc_offset)
        toc_entry = f.read(12)
        r_so, r_sc, r_tc = struct.unpack('<III', toc_entry)
        print(f"  R1269: sector_offset=0x{r_so:X}, sector_count={r_sc}, type_code={r_tc}")

        # Calculate absolute offset of R1269 in ISO
        r_abs_offset = pack_offset + r_so * SECTOR
        r_raw_size = r_sc * SECTOR
        print(f"  Absolute offset: 0x{r_abs_offset:X} ({r_abs_offset:,})")
        print(f"  Raw size: {r_raw_size:,} bytes")

        # Verify the resource by reading its sub-header and TIM2 header
        f.seek(r_abs_offset)
        sub_header = f.read(16)
        print(f"  Sub-header: {sub_header.hex()}")
        h_zero1, h_payload, h_stride, h_zero2 = struct.unpack('<IIII', sub_header)
        print(f"  Payload size: {h_payload:,}, stride: {h_stride}")

        # TIM2 data starts at +16, TEX0 register at +16+0x50 = +0x60
        f.seek(r_abs_offset + 0x60)
        tex0_bytes = f.read(8)
        tex0 = struct.unpack('<Q', tex0_bytes)[0]
        psm = (tex0 >> 20) & 0x3F
        tw = (tex0 >> 26) & 0xF
        th = (tex0 >> 30) & 0xF
        W = 1 << tw
        H = 1 << th
        print(f"  TEX0: PSM={psm} (PSMT8=19), {W}x{H}")

        if psm != 19 or W != 512 or H != 512:
            print(f"  WARNING: Unexpected format! Expected PSMT8 512x512")

        # Fill pixel data with 0x88
        pix_abs_offset = r_abs_offset + PIX_START
        print(f"\nStep 5: Filling pixel data at 0x{pix_abs_offset:X} with 0x{FILL_BYTE:02X} ...")
        print(f"  {PIX_SIZE:,} bytes of pixel data")

        fill_data = bytes([FILL_BYTE]) * PIX_SIZE
        f.seek(pix_abs_offset)
        f.write(fill_data)

        # Verify write
        f.seek(pix_abs_offset)
        verify = f.read(16)
        expected = bytes([FILL_BYTE]) * 16
        if verify == expected:
            print("  Verified: pixel data written correctly")
        else:
            print(f"  ERROR: verification failed! Got {verify.hex()}")
            sys.exit(1)

    print(f"\nDone! Output: {OUTPUT_ISO}")
    print(f"  Size: {os.path.getsize(OUTPUT_ISO):,} bytes")
    print()
    print("TEST INSTRUCTIONS:")
    print("  1. Boot the ISO in PCSX2")
    print("  2. Navigate to any screen with kanji text")
    print("  3. If some kanji appear as solid blocks, those glyphs are on R1269")
    print("  4. Compare with other font pages (R1270, R1271, etc.) to map coverage")


if __name__ == "__main__":
    main()
