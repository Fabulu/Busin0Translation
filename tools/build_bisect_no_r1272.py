#!/usr/bin/env python3
"""Bisection test: build ISO with ALL patches EXCEPT R1272 font atlas.

Takes the fully-built v9 ISO and replaces R1272 (dialogue font atlas)
with the ORIGINAL Japanese R1272, preserving all other translations.
This tests whether the R1272 rebuild causes F/M to disappear on the keyboard.
"""
import struct, os, shutil

os.chdir('C:/Programmieren/wizardrytranslation')

SECTOR = 2048
SRC_ISO = 'build/BUSIN0_EN_v9.iso'
DST_ISO = 'build/BUSIN0_EN_bisect_no_r1272.iso'
ORIG_R1272 = 'extracted/packdata_raw/1272_type01.raw'
R1272_INDEX = 1272

print("=" * 60)
print("  BISECTION: Revert R1272 to original Japanese")
print("=" * 60)

# Verify source files exist
assert os.path.exists(SRC_ISO), f"Source ISO not found: {SRC_ISO}"
assert os.path.exists(ORIG_R1272), f"Original R1272 not found: {ORIG_R1272}"

# Read original R1272
orig_data = open(ORIG_R1272, 'rb').read()
orig_sectors = (len(orig_data) + SECTOR - 1) // SECTOR
print(f"  Original R1272: {len(orig_data):,} bytes ({orig_sectors} sectors)")

# Copy ISO
print(f"  Copying {SRC_ISO} -> {DST_ISO}")
shutil.copy2(SRC_ISO, DST_ISO)

# Find PACKDATA LBA in ISO
with open(DST_ISO, 'r+b') as iso:
    # Read PVD
    iso.seek(16 * SECTOR)
    pvd = iso.read(SECTOR)
    root_lba = struct.unpack_from('<I', pvd, 158)[0]
    root_size = struct.unpack_from('<I', pvd, 166)[0]

    # Find PACKDATA.DIG in root directory
    iso.seek(root_lba * SECTOR)
    root_dir = iso.read(root_size)
    pack_lba = None
    pos = 0
    while pos < len(root_dir):
        rec_len = root_dir[pos]
        if rec_len == 0:
            break
        name_len = root_dir[pos + 32]
        name = root_dir[pos + 33:pos + 33 + name_len].decode('ascii', errors='replace')
        if 'PACKDATA' in name:
            pack_lba = struct.unpack_from('<I', root_dir, pos + 2)[0]
            break
        pos += rec_len

    assert pack_lba is not None, "PACKDATA.DIG not found in ISO"
    print(f"  PACKDATA at ISO LBA {pack_lba}")

    # Read TOC entry for R1272
    toc_offset = pack_lba * SECTOR + R1272_INDEX * 12
    iso.seek(toc_offset)
    r_sector, r_count, r_type = struct.unpack('<III', iso.read(12))
    print(f"  R1272 TOC: sector={r_sector}, count={r_count}, type={r_type}")

    # Verify sizes match
    assert orig_sectors <= r_count, \
        f"Original R1272 ({orig_sectors} sectors) > allocated ({r_count} sectors)"

    # Write original R1272 data at the correct position
    data_offset = (pack_lba + r_sector) * SECTOR
    iso.seek(data_offset)

    # Pad to full sector count
    padded = orig_data + b'\x00' * (r_count * SECTOR - len(orig_data))
    iso.write(padded)
    print(f"  Wrote {len(padded):,} bytes at ISO offset 0x{data_offset:X}")

final_size = os.path.getsize(DST_ISO)
print(f"\n{'=' * 60}")
print(f"  {DST_ISO}")
print(f"  Size: {final_size:,} bytes")
print(f"  R1272 reverted to original Japanese")
print(f"  All other patches preserved")
print(f"{'=' * 60}")
