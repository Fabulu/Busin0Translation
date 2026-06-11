#!/usr/bin/env python3
"""Bisection test: copy v9 ISO and revert R1188 to original (unpatched) data.
This tests whether the R1188 patches cause F/M to disappear on the keyboard."""

import struct, shutil, os

os.chdir('C:/Programmieren/wizardrytranslation')

SECTOR = 2048
SRC_ISO = 'build/BUSIN0_EN_v9.iso'
DST_ISO = 'build/BUSIN0_EN_bisect_no_r1188.iso'
ORIG_PACKDATA = 'extracted/PACKDATA.DIG'
TARGET_IDX = 1188

# Step 1: Read original R1188 from extracted PACKDATA
print("=== Reading original R1188 from extracted PACKDATA ===")
with open(ORIG_PACKDATA, 'rb') as f:
    # Read TOC entry for index 1188
    f.seek(TARGET_IDX * 12)
    orig_sector, orig_count, orig_type = struct.unpack('<III', f.read(12))
    print(f"  Original TOC[{TARGET_IDX}]: sector={orig_sector}, count={orig_count}, type={orig_type}")

    # Read the original R1188 data
    f.seek(orig_sector * SECTOR)
    orig_r1188 = f.read(orig_count * SECTOR)
    print(f"  Original R1188 size: {len(orig_r1188):,} bytes")

# Step 2: Copy the v9 ISO
print(f"\n=== Copying {SRC_ISO} -> {DST_ISO} ===")
shutil.copy2(SRC_ISO, DST_ISO)
print(f"  Copied ({os.path.getsize(DST_ISO):,} bytes)")

# Step 3: Find PACKDATA LBA in the ISO
print("\n=== Finding PACKDATA location in ISO ===")
with open(DST_ISO, 'r+b') as iso:
    # Read PVD
    iso.seek(16 * SECTOR)
    pvd = iso.read(SECTOR)
    root_lba = struct.unpack_from('<I', pvd, 158)[0]
    root_size = struct.unpack_from('<I', pvd, 166)[0]

    # Find PACKDATA in root directory
    iso.seek(root_lba * SECTOR)
    root_dir = iso.read(root_size)
    pos = 0
    pack_lba = None
    while pos < len(root_dir):
        rec_len = root_dir[pos]
        if rec_len == 0:
            break
        name_len = root_dir[pos + 32]
        name = root_dir[pos + 33:pos + 33 + name_len].decode('ascii', errors='replace')
        if 'PACKDATA' in name:
            pack_lba = struct.unpack_from('<I', root_dir, pos + 2)[0]
            pack_size = struct.unpack_from('<I', root_dir, pos + 10)[0]
            print(f"  PACKDATA: LBA={pack_lba}, size={pack_size:,} bytes")
            break
        pos += rec_len

    if pack_lba is None:
        print("ERROR: PACKDATA not found in ISO!")
        exit(1)

    # Step 4: Read the rebuilt PACKDATA TOC entry for R1188
    print("\n=== Reading rebuilt PACKDATA TOC for R1188 ===")
    iso.seek(pack_lba * SECTOR + TARGET_IDX * 12)
    new_sector, new_count, new_type = struct.unpack('<III', iso.read(12))
    print(f"  Rebuilt TOC[{TARGET_IDX}]: sector={new_sector}, count={new_count}, type={new_type}")

    # The TOC sector offsets are relative to PACKDATA start
    abs_offset = pack_lba * SECTOR + new_sector * SECTOR
    print(f"  Absolute ISO offset: {abs_offset:,} (0x{abs_offset:X})")

    # Step 5: Overwrite with original R1188 data
    print(f"\n=== Overwriting R1188 with original data ===")
    # Pad/trim original to match the sector count in rebuilt PACKDATA
    write_size = new_count * SECTOR
    if len(orig_r1188) >= write_size:
        write_data = orig_r1188[:write_size]
    else:
        write_data = orig_r1188 + b'\x00' * (write_size - len(orig_r1188))

    iso.seek(abs_offset)
    iso.write(write_data)
    print(f"  Wrote {len(write_data):,} bytes at offset 0x{abs_offset:X}")

    # Verify by reading back
    iso.seek(abs_offset)
    verify = iso.read(16)
    print(f"  First 16 bytes after write: {verify.hex()}")

print(f"\n{'='*60}")
print(f"  Bisection ISO built: {DST_ISO}")
print(f"  R1188 reverted to ORIGINAL (no kana/stat/label patches)")
print(f"  All other patches (dialogue, EXE, R2138, etc.) remain")
print(f"{'='*60}")
