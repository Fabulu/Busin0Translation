#!/usr/bin/env python3
"""Build 3 binary-search test ISOs to narrow down VIF FIFO crash cause.

Each ISO has R1272 (font atlas) + one group of changes:
  - groupA: Type-01 MSG text (R34-R49, R2124, R2654)
  - groupB: Type-02 dialogue (R989, R990, R1034, R1193-R1213, R1347-R1355)
  - groupC: Special/texture resources (R2138, R2100, R1188, R39, R46, R47)
"""

import os, sys, struct, math, shutil, glob

os.chdir('C:/Programmieren/wizardrytranslation')
SECTOR = 2048

BACKUP_DIR = 'build/packdata_resources_backup'
RES_DIR = 'build/packdata_resources'
ORIG_DIR = 'extracted/packdata_raw'
ORIG_ISO = 'Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso'
PATCHED_EXE = 'build/SLPM_653.78_patched'

# Define groups by resource ID
GROUP_A_IDS = set(range(34, 50)) | {2124, 2654}  # R34-R49, R2124, R2654
GROUP_B_IDS = {989, 990, 1034} | set(range(1193, 1214)) | set(range(1347, 1356))  # R989,990,1034, R1193-R1213, R1347-R1355
GROUP_C_IDS = {2138, 2100, 1188, 39, 46, 47}  # Special resources
# R1272 is always included (font atlas)
R1272_ID = 1272

# Map resource IDs to their filenames in backup
def get_res_files(res_dir):
    """Return dict mapping resource ID -> filename"""
    result = {}
    for f in os.listdir(res_dir):
        if f.endswith('.raw') and '_type' in f:
            try:
                rid = int(f.split('_')[0])
                result[rid] = f
            except ValueError:
                pass
    return result

def clear_resources():
    """Remove all .raw files from packdata_resources"""
    for f in os.listdir(RES_DIR):
        if f.endswith('.raw'):
            os.remove(os.path.join(RES_DIR, f))

def copy_resources(res_ids, source_dir):
    """Copy resources for given IDs from source to packdata_resources"""
    files = get_res_files(source_dir)
    copied = []
    for rid in res_ids:
        if rid in files:
            fn = files[rid]
            shutil.copy2(os.path.join(source_dir, fn), os.path.join(RES_DIR, fn))
            copied.append(rid)
    return copied

def rebuild_packdata():
    """Run rebuild_packdata.py and return PACKDATA size"""
    os.system('python build/rebuild_packdata.py')
    return os.path.getsize('build/PACKDATA_v3.DIG')

def build_iso(output_name):
    """Build ISO from PACKDATA_v3.DIG, handle overflow, patch EXE"""
    packdata = open('build/PACKDATA_v3.DIG', 'rb').read()
    pack_size = len(packdata)

    print(f"  PACKDATA size: {pack_size:,} bytes")

    # Copy original ISO
    shutil.copy2(ORIG_ISO, f'build/{output_name}')

    iso_path = f'build/{output_name}'

    # Write PACKDATA and update directory size
    with open(iso_path, 'r+b') as iso:
        iso.seek(16 * SECTOR)
        pvd = iso.read(SECTOR)
        root_lba = struct.unpack_from('<I', pvd, 158)[0]
        root_size = struct.unpack_from('<I', pvd, 166)[0]
        iso.seek(root_lba * SECTOR)
        root_dir = iso.read(root_size)
        pos = 0
        while pos < len(root_dir):
            rec_len = root_dir[pos]
            if rec_len == 0:
                break
            name_len = root_dir[pos + 32]
            name = root_dir[pos + 33:pos + 33 + name_len].decode('ascii', errors='replace')
            if 'PACKDATA' in name:
                pack_lba = struct.unpack_from('<I', root_dir, pos + 2)[0]
                iso.seek(root_lba * SECTOR + pos + 10)
                iso.write(struct.pack('<I', pack_size))
                iso.write(struct.pack('>I', pack_size))
                iso.seek(pack_lba * SECTOR)
                iso.write(packdata)
                break
            pos += rec_len

    # Handle overflow (Step 8.2 logic)
    with open(iso_path, 'r+b') as iso:
        iso.seek(16 * SECTOR)
        pvd = iso.read(SECTOR)
        root_lba = struct.unpack_from('<I', pvd, 158)[0]
        root_size = struct.unpack_from('<I', pvd, 166)[0]
        iso.seek(root_lba * SECTOR)
        root_dir = bytearray(iso.read(root_size))

        dir_entries = []
        pos = 0
        while pos < len(root_dir):
            rec_len = root_dir[pos]
            if rec_len == 0:
                break
            name_len = root_dir[pos + 32]
            name = root_dir[pos + 33:pos + 33 + name_len].decode('ascii', errors='replace')
            lba = struct.unpack_from('<I', root_dir, pos + 2)[0]
            size = struct.unpack_from('<I', root_dir, pos + 10)[0]
            dir_entries.append((pos, name, lba, size))
            pos += rec_len

        pack_entry = [e for e in dir_entries if 'PACKDATA' in e[1]]
        overflow_sectors = 0
        if pack_entry:
            _, _, pack_lba, p_size = pack_entry[0]
            pack_end_lba = pack_lba + math.ceil(p_size / SECTOR)

            after_pack = sorted(
                [e for e in dir_entries if e[2] > pack_lba and 'PACKDATA' not in e[1]],
                key=lambda e: e[2]
            )

            if after_pack:
                first_after_lba = after_pack[0][2]
                if pack_end_lba > first_after_lba:
                    shift = pack_end_lba - first_after_lba
                    overflow_sectors = shift
                    print(f"  Overflow: {shift} sectors, shifting {len(after_pack)} files")

                    for dir_off, name, old_lba, fsize in reversed(after_pack):
                        new_lba = old_lba + shift
                        sec_count = math.ceil(fsize / SECTOR)
                        iso.seek(old_lba * SECTOR)
                        fdata = iso.read(sec_count * SECTOR)
                        iso.seek(new_lba * SECTOR)
                        iso.write(fdata)
                        struct.pack_into('<I', root_dir, dir_off + 2, new_lba)
                        struct.pack_into('>I', root_dir, dir_off + 6, new_lba)

                    iso.seek(root_lba * SECTOR)
                    iso.write(root_dir)

                    iso.seek(0, 2)
                    current_size = iso.tell()
                    needed = (after_pack[-1][2] + shift + math.ceil(after_pack[-1][3] / SECTOR)) * SECTOR
                    if needed > current_size:
                        iso.seek(needed - 1)
                        iso.write(b'\x00')

                    new_vol_sectors = math.ceil(needed / SECTOR)
                    iso.seek(16 * SECTOR + 80)
                    iso.write(struct.pack('<I', new_vol_sectors))
                    iso.write(struct.pack('>I', new_vol_sectors))
                else:
                    print(f"  No overflow (PACKDATA ends at {pack_end_lba}, next at {first_after_lba})")

    # Patch EXE
    if os.path.exists(PATCHED_EXE):
        exe_data = open(PATCHED_EXE, 'rb').read()
        with open(iso_path, 'r+b') as iso:
            iso.seek(16 * SECTOR)
            pvd = iso.read(SECTOR)
            root_lba = struct.unpack_from('<I', pvd, 158)[0]
            root_size = struct.unpack_from('<I', pvd, 166)[0]
            iso.seek(root_lba * SECTOR)
            root_dir = iso.read(root_size)
            pos = 0
            while pos < len(root_dir):
                rec_len = root_dir[pos]
                if rec_len == 0:
                    break
                name_len = root_dir[pos + 32]
                name = root_dir[pos + 33:pos + 33 + name_len].decode('ascii', errors='replace')
                if 'SLPM' in name:
                    exe_lba = struct.unpack_from('<I', root_dir, pos + 2)[0]
                    iso.seek(root_lba * SECTOR + pos + 10)
                    iso.write(struct.pack('<I', len(exe_data)))
                    iso.write(struct.pack('>I', len(exe_data)))
                    iso.seek(exe_lba * SECTOR)
                    iso.write(exe_data)
                    print(f"  EXE patched: {len(exe_data):,} bytes at LBA {exe_lba}")
                    break
                pos += rec_len
    else:
        print("  WARNING: No patched EXE found!")

    final_size = os.path.getsize(iso_path)
    print(f"  ISO built: {iso_path} ({final_size:,} bytes)")
    return pack_size, overflow_sectors


def build_test_iso(group_name, group_ids, iso_name):
    """Build a test ISO with R1272 + specified group"""
    print(f"\n{'='*60}")
    print(f"  Building {iso_name}: R1272 + GROUP {group_name}")
    print(f"  Resources: {sorted(group_ids)}")
    print(f"{'='*60}")

    # Clear all modified resources
    clear_resources()
    print(f"  Cleared packdata_resources")

    # Copy R1272 (font atlas) - always included
    backup_files = get_res_files(BACKUP_DIR)
    if R1272_ID in backup_files:
        fn = backup_files[R1272_ID]
        shutil.copy2(os.path.join(BACKUP_DIR, fn), os.path.join(RES_DIR, fn))
        print(f"  Copied R1272 (font atlas)")

    # Copy group resources
    copied = copy_resources(group_ids, BACKUP_DIR)
    print(f"  Copied {len(copied)} resources: {sorted(copied)}")

    # For GROUP C, handle R2100 specially (it goes in header via rebuild_packdata)
    # R2100 is already in packdata_resources if it was copied above
    # R1370 is NOT in backup (never was in packdata_resources), so it won't be included

    # Rebuild PACKDATA
    print(f"\n  Rebuilding PACKDATA...")
    pack_size = rebuild_packdata()

    # Build ISO
    print(f"\n  Building ISO...")
    pack_size, overflow = build_iso(iso_name)

    return pack_size, overflow


# Verify backup exists
if not os.path.isdir(BACKUP_DIR):
    print("ERROR: Backup directory not found! Run the full build first.")
    sys.exit(1)

backup_files = get_res_files(BACKUP_DIR)
print(f"Backup has {len(backup_files)} resource files")
print(f"Resources: {sorted(backup_files.keys())}")

# Verify which group IDs actually have built resources
print(f"\nGROUP A (type-01 MSG) IDs in backup: {sorted(GROUP_A_IDS & set(backup_files.keys()))}")
print(f"GROUP B (type-02 dialogue) IDs in backup: {sorted(GROUP_B_IDS & set(backup_files.keys()))}")
print(f"GROUP C (special) IDs in backup: {sorted(GROUP_C_IDS & set(backup_files.keys()))}")

results = {}

# Build ISO 1: R1272 + GROUP A
pack_a, over_a = build_test_iso('A', GROUP_A_IDS, 'BUSIN0_EN_groupA.iso')
results['A'] = (pack_a, over_a)

# Build ISO 2: R1272 + GROUP C
pack_c, over_c = build_test_iso('C', GROUP_C_IDS, 'BUSIN0_EN_groupC.iso')
results['C'] = (pack_c, over_c)

# Build ISO 3: R1272 + GROUP B
pack_b, over_b = build_test_iso('B', GROUP_B_IDS, 'BUSIN0_EN_groupB.iso')
results['B'] = (pack_b, over_b)

# Restore full build state
print(f"\n{'='*60}")
print(f"  Restoring full build state")
print(f"{'='*60}")
clear_resources()
for rid, fn in backup_files.items():
    shutil.copy2(os.path.join(BACKUP_DIR, fn), os.path.join(RES_DIR, fn))
print(f"  Restored {len(backup_files)} resources")

# Summary
print(f"\n{'='*60}")
print(f"  BINARY SEARCH ISO SUMMARY")
print(f"{'='*60}")
orig_packdata_size = os.path.getsize('extracted/PACKDATA.DIG')
for group, (psize, overflow) in sorted(results.items()):
    diff = psize - orig_packdata_size
    print(f"  GROUP {group}: PACKDATA {psize:,} bytes (diff: {diff:+,}), overflow: {overflow} sectors")
print(f"  Original PACKDATA: {orig_packdata_size:,} bytes")
print(f"\nISOs saved to:")
print(f"  build/BUSIN0_EN_groupA.iso  (R1272 + type-01 MSG text)")
print(f"  build/BUSIN0_EN_groupB.iso  (R1272 + type-02 dialogue)")
print(f"  build/BUSIN0_EN_groupC.iso  (R1272 + special/texture)")
