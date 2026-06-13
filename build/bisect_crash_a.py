#!/usr/bin/env python3
"""Build 4 binary-search test ISOs to narrow down VIF FIFO crash within Group A.

ISO A1: R1272 + R34, R35, R36, R37, R38 (first half)
ISO A2: R1272 + R39-R49 (second half)
ISO A3: R1272 + R37 only (M/F fix suspect)
ISO A4: R1272 + everything EXCEPT R37
"""

import os, sys, struct, math, shutil

os.chdir('C:/Programmieren/wizardrytranslation')
SECTOR = 2048

BACKUP_DIR = 'build/packdata_resources_backup'
RES_DIR = 'build/packdata_resources'
ORIG_DIR = 'extracted/packdata_raw'
ORIG_ISO = 'Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso'
PATCHED_EXE = 'build/SLPM_653.78_patched'

# Group A resources split into sub-groups
GROUP_A1_IDS = {34, 35, 36, 37, 38}
GROUP_A2_IDS = set(range(39, 50))  # R39-R49
GROUP_A3_IDS = {37}                 # R37 only
# A4 = Group A minus R37
GROUP_A_ALL = set(range(34, 50)) | {2124, 2654}
GROUP_A4_IDS = GROUP_A_ALL - {37}

R1272_ID = 1272

def get_res_files(res_dir):
    result = {}
    for f in os.listdir(res_dir):
        if f.endswith('.raw') and '_type' in f and not f.endswith('_kanji_wipe.raw'):
            try:
                rid = int(f.split('_')[0])
                result[rid] = f
            except ValueError:
                pass
    return result

def clear_resources():
    for f in os.listdir(RES_DIR):
        if f.endswith('.raw'):
            os.remove(os.path.join(RES_DIR, f))

def copy_resources(res_ids, source_dir):
    files = get_res_files(source_dir)
    copied = []
    for rid in res_ids:
        if rid in files:
            fn = files[rid]
            shutil.copy2(os.path.join(source_dir, fn), os.path.join(RES_DIR, fn))
            copied.append(rid)
    return copied

def rebuild_packdata():
    os.system('python build/rebuild_packdata.py')
    return os.path.getsize('build/PACKDATA_v3.DIG')

def build_iso(output_name):
    """Build ISO with CRITICAL FIX: read relocated files from ORIGINAL ISO."""
    packdata = open('build/PACKDATA_v3.DIG', 'rb').read()
    pack_size = len(packdata)
    print(f"  PACKDATA size: {pack_size:,} bytes")

    # Copy original ISO
    shutil.copy2(ORIG_ISO, f'build/{output_name}')
    iso_path = f'build/{output_name}'

    # Read directory from ORIGINAL ISO to find PACKDATA entry
    with open(ORIG_ISO, 'rb') as orig:
        orig.seek(16 * SECTOR)
        pvd = orig.read(SECTOR)
        root_lba = struct.unpack_from('<I', pvd, 158)[0]
        root_size = struct.unpack_from('<I', pvd, 166)[0]
        orig.seek(root_lba * SECTOR)
        root_dir_data = bytearray(orig.read(root_size))

    # Parse directory entries
    dir_entries = []
    pos = 0
    while pos < len(root_dir_data):
        rec_len = root_dir_data[pos]
        if rec_len == 0:
            break
        name_len = root_dir_data[pos + 32]
        name = root_dir_data[pos + 33:pos + 33 + name_len].decode('ascii', errors='replace')
        lba = struct.unpack_from('<I', root_dir_data, pos + 2)[0]
        size = struct.unpack_from('<I', root_dir_data, pos + 10)[0]
        dir_entries.append((pos, name, lba, size))
        pos += rec_len

    pack_entry = [e for e in dir_entries if 'PACKDATA' in e[1]][0]
    pack_dir_off, _, pack_lba, _ = pack_entry

    # Update PACKDATA size in directory (both LE and BE)
    struct.pack_into('<I', root_dir_data, pack_dir_off + 10, pack_size)
    struct.pack_into('>I', root_dir_data, pack_dir_off + 14, pack_size)

    # Write PACKDATA into ISO
    with open(iso_path, 'r+b') as iso:
        iso.seek(pack_lba * SECTOR)
        iso.write(packdata)

    # Handle overflow: shift files that PACKDATA now overlaps
    pack_end_lba = pack_lba + math.ceil(pack_size / SECTOR)

    after_pack = sorted(
        [e for e in dir_entries if e[2] > pack_lba and 'PACKDATA' not in e[1]],
        key=lambda e: e[2]
    )

    overflow_sectors = 0
    if after_pack:
        first_after_lba = after_pack[0][2]
        if pack_end_lba > first_after_lba:
            shift = pack_end_lba - first_after_lba
            overflow_sectors = shift
            print(f"  Overflow: {shift} sectors ({shift * SECTOR:,} bytes), shifting {len(after_pack)} files")

            # CRITICAL: Read file data from ORIGINAL ISO, not the working copy!
            with open(ORIG_ISO, 'rb') as orig:
                with open(iso_path, 'r+b') as iso:
                    # Shift files in reverse order (furthest first) to avoid overwriting
                    for dir_off, name, old_lba, fsize in reversed(after_pack):
                        new_lba = old_lba + shift
                        sec_count = math.ceil(fsize / SECTOR)
                        # Read from ORIGINAL
                        orig.seek(old_lba * SECTOR)
                        fdata = orig.read(sec_count * SECTOR)
                        # Write to new location in working ISO
                        iso.seek(new_lba * SECTOR)
                        iso.write(fdata)
                        # Update directory entry
                        struct.pack_into('<I', root_dir_data, dir_off + 2, new_lba)
                        struct.pack_into('>I', root_dir_data, dir_off + 6, new_lba)
                        print(f"    Shifted {name}: LBA {old_lba} -> {new_lba}")
        else:
            print(f"  No overflow (PACKDATA ends at LBA {pack_end_lba}, next file at LBA {first_after_lba})")

    # Write updated directory
    with open(iso_path, 'r+b') as iso:
        iso.seek(root_lba * SECTOR)
        iso.write(root_dir_data)

        # Ensure ISO is large enough
        if after_pack and overflow_sectors > 0:
            last = after_pack[-1]
            last_end = (last[2] + shift + math.ceil(last[3] / SECTOR)) * SECTOR
            iso.seek(0, 2)
            current_size = iso.tell()
            if last_end > current_size:
                iso.seek(last_end - 1)
                iso.write(b'\x00')

            # Update volume size in PVD
            new_vol_sectors = math.ceil(last_end / SECTOR)
            iso.seek(16 * SECTOR + 80)
            iso.write(struct.pack('<I', new_vol_sectors))
            iso.write(struct.pack('>I', new_vol_sectors))

    # Patch EXE
    if os.path.exists(PATCHED_EXE):
        exe_data = open(PATCHED_EXE, 'rb').read()
        # Find SLPM entry in (possibly updated) directory
        with open(iso_path, 'r+b') as iso:
            iso.seek(root_lba * SECTOR)
            rd = iso.read(root_size)
            pos = 0
            while pos < len(rd):
                rec_len = rd[pos]
                if rec_len == 0:
                    break
                name_len = rd[pos + 32]
                name = rd[pos + 33:pos + 33 + name_len].decode('ascii', errors='replace')
                if 'SLPM' in name:
                    exe_lba = struct.unpack_from('<I', rd, pos + 2)[0]
                    # Update size
                    iso.seek(root_lba * SECTOR + pos + 10)
                    iso.write(struct.pack('<I', len(exe_data)))
                    iso.write(struct.pack('>I', len(exe_data)))
                    # Write EXE
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
    print(f"\n{'='*60}")
    print(f"  Building {iso_name}: R1272 + {group_name}")
    print(f"  Resources: {sorted(group_ids)}")
    print(f"{'='*60}")

    clear_resources()

    # Copy R1272 (font atlas)
    backup_files = get_res_files(BACKUP_DIR)
    if R1272_ID in backup_files:
        fn = backup_files[R1272_ID]
        shutil.copy2(os.path.join(BACKUP_DIR, fn), os.path.join(RES_DIR, fn))
        print(f"  Copied R1272 (font atlas)")

    # Copy group resources
    copied = copy_resources(group_ids, BACKUP_DIR)
    print(f"  Copied {len(copied)} resources: {sorted(copied)}")

    # Rebuild PACKDATA
    print(f"\n  Rebuilding PACKDATA...")
    pack_size = rebuild_packdata()

    # Build ISO
    print(f"\n  Building ISO...")
    return build_iso(iso_name)


# Verify backup
if not os.path.isdir(BACKUP_DIR):
    print("ERROR: Backup directory not found!")
    sys.exit(1)

backup_files = get_res_files(BACKUP_DIR)
print(f"Backup has {len(backup_files)} resource files")

# Show which resources are available for each group
for name, ids in [('A1', GROUP_A1_IDS), ('A2', GROUP_A2_IDS), ('A3', GROUP_A3_IDS), ('A4', GROUP_A4_IDS)]:
    available = sorted(ids & set(backup_files.keys()))
    print(f"  {name}: want {sorted(ids)}, have {available}")

results = {}

# Build all 4 ISOs
for name, ids, iso_name in [
    ('A1 (R34-R38)', GROUP_A1_IDS, 'BUSIN0_EN_A1.iso'),
    ('A2 (R39-R49)', GROUP_A2_IDS, 'BUSIN0_EN_A2.iso'),
    ('A3 (R37 only)', GROUP_A3_IDS, 'BUSIN0_EN_A3.iso'),
    ('A4 (all except R37)', GROUP_A4_IDS, 'BUSIN0_EN_A4.iso'),
]:
    pack_size, overflow = build_test_iso(name, ids, iso_name)
    results[name] = (pack_size, overflow)

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
print(f"  BISECT ISO SUMMARY")
print(f"{'='*60}")
orig_packdata_size = os.path.getsize('extracted/PACKDATA.DIG')
print(f"  Original PACKDATA: {orig_packdata_size:,} bytes")
for name, (psize, overflow) in results.items():
    diff = psize - orig_packdata_size
    print(f"  {name}: PACKDATA {psize:,} (diff: {diff:+,}), overflow: {overflow} sectors ({overflow * SECTOR:,} bytes)")

print(f"\nISOs saved to:")
print(f"  build/BUSIN0_EN_A1.iso  (R1272 + R34,R35,R36,R37,R38)")
print(f"  build/BUSIN0_EN_A2.iso  (R1272 + R39-R49)")
print(f"  build/BUSIN0_EN_A3.iso  (R1272 + R37 only)")
print(f"  build/BUSIN0_EN_A4.iso  (R1272 + all Group A except R37)")
