#!/usr/bin/env python3
"""
Bisection test ISO: ALL patches EXCEPT R2100 chargen font atlas.
Copies build/BUSIN0_EN_v9.iso, then overwrites the R2100 region
(PACKDATA sectors 17-84) with the ORIGINAL R2100 data from the
extracted PACKDATA.DIG.

Purpose: Test whether our R2100 stat/gender patches cause F/M
to disappear from the keyboard screen.
"""
import struct, shutil, os

os.chdir('C:/Programmieren/wizardrytranslation')

SECTOR = 2048
R2100_START_SECTOR = 17   # within PACKDATA
R2100_END_SECTOR = 84     # inclusive
R2100_SECTORS = R2100_END_SECTOR - R2100_START_SECTOR + 1  # 68
R2100_OFFSET = R2100_START_SECTOR * SECTOR  # 34816
R2100_SIZE = R2100_SECTORS * SECTOR         # 139264

SRC_ISO = 'build/BUSIN0_EN_v9.iso'
DST_ISO = 'build/BUSIN0_EN_bisect_no_r2100.iso'
ORIG_PACKDATA = 'extracted/PACKDATA.DIG'

# --- Step 1: Read original R2100 from extracted PACKDATA ---
print(f"Reading original R2100 from {ORIG_PACKDATA} ...")
with open(ORIG_PACKDATA, 'rb') as f:
    f.seek(R2100_OFFSET)
    orig_r2100 = f.read(R2100_SIZE)
assert len(orig_r2100) == R2100_SIZE, f"Short read: {len(orig_r2100)} != {R2100_SIZE}"
print(f"  Got {len(orig_r2100):,} bytes of original R2100")

# --- Step 2: Copy the v9 ISO ---
print(f"Copying {SRC_ISO} -> {DST_ISO} ...")
shutil.copy2(SRC_ISO, DST_ISO)
print(f"  Copy complete")

# --- Step 3: Find PACKDATA LBA in the ISO ---
print("Finding PACKDATA LBA in ISO ...")
with open(DST_ISO, 'r+b') as iso:
    iso.seek(16 * SECTOR)
    pvd = iso.read(SECTOR)
    root_lba = struct.unpack_from('<I', pvd, 158)[0]
    root_size = struct.unpack_from('<I', pvd, 166)[0]
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

    assert pack_lba is not None, "Could not find PACKDATA in ISO directory!"
    print(f"  PACKDATA at LBA {pack_lba} (byte offset {pack_lba * SECTOR:,})")

    # --- Step 4: Overwrite R2100 with original data ---
    r2100_iso_offset = pack_lba * SECTOR + R2100_OFFSET
    print(f"Overwriting R2100 at ISO offset {r2100_iso_offset:,} ...")
    iso.seek(r2100_iso_offset)
    iso.write(orig_r2100)
    print(f"  Wrote {len(orig_r2100):,} bytes of original R2100")

print(f"\nDone! Bisection ISO: {DST_ISO}")
print("This ISO has ALL patches EXCEPT R2100 chargen font atlas.")
print("Boot fresh from title screen to test F/M visibility on keyboard.")
