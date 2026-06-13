#!/usr/bin/env python3
"""
build_test_isos.py — Build T1/T2/T3 test ISOs to isolate VIF FIFO crash.

T1: R1272 + R2124 only
T2: R1272 + R2654 only
T3: R1272 + R2124 + R2654

For each ISO:
  1. Backup current packdata_resources/
  2. Fill packdata_resources/ with originals from extracted/packdata_raw/
  3. Copy R1272 from backup
  4. Copy test-specific resources from backup
  5. Run rebuild_packdata.py
  6. Build ISO (PACKDATA at LBA 16029, overflow handling, EXE patch)
  7. Restore full packdata_resources/ from backup
"""
import os, sys, struct, math, shutil, glob

os.chdir('C:/Programmieren/wizardrytranslation')

SECTOR = 2048
ORIG_ISO = 'Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso'
PACKDATA_LBA = 16029
BACKUP_DIR = 'build/packdata_resources_backup_testbuild'

# ── helpers ─────────────────────────────────────────────────────────────────

def backup_resources():
    if os.path.exists(BACKUP_DIR):
        shutil.rmtree(BACKUP_DIR)
    shutil.copytree('build/packdata_resources', BACKUP_DIR)
    print(f'  Backed up {len(os.listdir(BACKUP_DIR))} files to {BACKUP_DIR}')

def restore_resources():
    shutil.rmtree('build/packdata_resources')
    shutil.copytree(BACKUP_DIR, 'build/packdata_resources')
    print(f'  Restored {len(os.listdir("build/packdata_resources"))} files from backup')

def fill_with_originals():
    """Copy ALL originals from extracted/packdata_raw/ into packdata_resources/."""
    # Clear current
    for f in os.listdir('build/packdata_resources'):
        os.remove(f'build/packdata_resources/{f}')
    # Copy originals
    copied = 0
    for f in os.listdir('extracted/packdata_raw'):
        shutil.copy(f'extracted/packdata_raw/{f}', f'build/packdata_resources/{f}')
        copied += 1
    print(f'  Copied {copied} original files into packdata_resources/')

def copy_from_backup(r_id):
    """Copy a resource from backup into packdata_resources/ (overwrite original)."""
    matches = glob.glob(f'{BACKUP_DIR}/{r_id:04d}_type*.raw')
    if not matches:
        print(f'  WARNING: R{r_id} not found in backup!')
        return False
    src = matches[0]
    fname = os.path.basename(src)
    # Determine correct destination filename based on what's in packdata_resources/
    # (the original file might have a different type suffix than the patched one).
    dst = f'build/packdata_resources/{fname}'
    shutil.copy(src, dst)
    size = os.path.getsize(dst)
    print(f'  Copied R{r_id} from backup: {fname} ({size:,} bytes)')
    return True

def build_iso(iso_name, packdata_path):
    """
    Build ISO from original, write PACKDATA at PACKDATA_LBA,
    handle overflow (shift subsequent files), patch EXE.
    Returns (pack_size, overflow_sectors).
    """
    pack_data = open(packdata_path, 'rb').read()
    pack_size = len(pack_data)

    # Copy original ISO
    shutil.copy2(ORIG_ISO, iso_name)

    overflow_sectors = 0

    with open(iso_name, 'r+b') as iso:
        # ── Write PACKDATA ────────────────────────────────────────────────
        iso.seek(PACKDATA_LBA * SECTOR)
        iso.write(pack_data)

        # ── Update PACKDATA directory entry size ──────────────────────────
        iso.seek(16 * SECTOR)
        pvd = iso.read(SECTOR)
        root_lba  = struct.unpack_from('<I', pvd, 158)[0]
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
            lba  = struct.unpack_from('<I', root_dir, pos + 2)[0]
            size = struct.unpack_from('<I', root_dir, pos + 10)[0]
            dir_entries.append((pos, name, lba, size))
            pos += rec_len

        # Update PACKDATA size in directory
        for dir_off, name, lba, size in dir_entries:
            if 'PACKDATA' in name:
                iso.seek(root_lba * SECTOR + dir_off + 10)
                iso.write(struct.pack('<I', pack_size))
                iso.write(struct.pack('>I', pack_size))
                break

        # ── Overflow handling ─────────────────────────────────────────────
        pack_end_lba = PACKDATA_LBA + math.ceil(pack_size / SECTOR)
        after_pack = sorted(
            [e for e in dir_entries if e[2] > PACKDATA_LBA and 'PACKDATA' not in e[1]],
            key=lambda e: e[2]
        )
        if after_pack:
            first_after_lba = after_pack[0][2]
            if pack_end_lba > first_after_lba:
                shift = pack_end_lba - first_after_lba
                overflow_sectors = shift
                print(f'  PACKDATA overflow: {shift} sectors — shifting {len(after_pack)} files forward')

                orig_iso_fh = open(ORIG_ISO, 'rb')
                for dir_off, name, old_lba, fsize in reversed(after_pack):
                    new_lba = old_lba + shift
                    sec_count = math.ceil(fsize / SECTOR)
                    orig_iso_fh.seek(old_lba * SECTOR)
                    fdata = orig_iso_fh.read(sec_count * SECTOR)
                    iso.seek(new_lba * SECTOR)
                    iso.write(fdata)
                    struct.pack_into('<I', root_dir, dir_off + 2, new_lba)
                    struct.pack_into('>I', root_dir, dir_off + 6, new_lba)
                orig_iso_fh.close()

                # Write updated directory
                iso.seek(root_lba * SECTOR)
                iso.write(root_dir)

                # Extend ISO if needed
                iso.seek(0, 2)
                current_size = iso.tell()
                last = after_pack[-1]
                needed = (last[2] + shift + math.ceil(last[3] / SECTOR)) * SECTOR
                if needed > current_size:
                    iso.seek(needed - 1)
                    iso.write(b'\x00')

                # Update PVD volume space
                new_vol_sectors = math.ceil(needed / SECTOR)
                iso.seek(16 * SECTOR + 80)
                iso.write(struct.pack('<I', new_vol_sectors))
                iso.write(struct.pack('>I', new_vol_sectors))

                print(f'  ISO extended. New vol size: {new_vol_sectors} sectors')
            else:
                print(f'  No overflow (PACKDATA ends at sector {pack_end_lba}, next file at {first_after_lba})')

    # ── Patch EXE ─────────────────────────────────────────────────────────
    exe_path = 'build/SLPM_653.78_patched'
    if os.path.exists(exe_path):
        exe_data = open(exe_path, 'rb').read()
        with open(iso_name, 'r+b') as iso:
            iso.seek(16 * SECTOR)
            pvd = iso.read(SECTOR)
            root_lba  = struct.unpack_from('<I', pvd, 158)[0]
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
                    print(f'  EXE patched: {len(exe_data):,} bytes at LBA {exe_lba}')
                    break
                pos += rec_len
    else:
        print('  No patched EXE found, skipping')

    iso_size = os.path.getsize(iso_name)
    print(f'  ISO size: {iso_size:,} bytes')
    return pack_size, overflow_sectors


# ── TESTS ────────────────────────────────────────────────────────────────────

TESTS = [
    ('T1', [1272, 2124],        'build/BUSIN0_EN_T1.iso'),
    ('T2', [1272, 2654],        'build/BUSIN0_EN_T2.iso'),
    ('T3', [1272, 2124, 2654],  'build/BUSIN0_EN_T3.iso'),
]

print('=' * 60)
print('  BUILD TEST ISOS — VIF FIFO crash isolation')
print('=' * 60)

# Step 1: Backup current full build state
print('\n--- Backing up current packdata_resources ---')
backup_resources()

results = []

for label, resource_ids, iso_path in TESTS:
    print(f'\n{"=" * 60}')
    print(f'  Building {label}: R{"+R".join(str(r) for r in resource_ids)}')
    print(f'{"=" * 60}')

    # Step 2: Fill with all originals
    print(f'\n  Filling with originals...')
    fill_with_originals()

    # Step 3+4: Copy test resources from backup
    print(f'  Applying patched resources from backup...')
    for r_id in resource_ids:
        copy_from_backup(r_id)

    # Step 5: Rebuild PACKDATA
    print(f'\n  Rebuilding PACKDATA...')
    ret = os.system('python build/rebuild_packdata.py')
    if ret != 0:
        print(f'  ERROR: rebuild_packdata.py failed (code {ret})')
        continue

    pack_size = os.path.getsize('build/PACKDATA_v3.DIG')
    print(f'  PACKDATA_v3.DIG: {pack_size:,} bytes')

    # Step 6: Build ISO
    print(f'\n  Building ISO: {iso_path}')
    final_pack_size, overflow = build_iso(iso_path, 'build/PACKDATA_v3.DIG')
    iso_size = os.path.getsize(iso_path)

    results.append({
        'label': label,
        'resources': resource_ids,
        'iso': iso_path,
        'pack_size': final_pack_size,
        'overflow_sectors': overflow,
        'iso_size': iso_size,
    })
    print(f'\n  {label} complete: PACKDATA={final_pack_size:,}B, overflow={overflow} sectors, ISO={iso_size:,}B')

# Restore full build state
print(f'\n{"=" * 60}')
print('  Restoring full build state...')
restore_resources()

# Summary
print(f'\n{"=" * 60}')
print('  RESULTS SUMMARY')
print(f'{"=" * 60}')
print(f'  {"ISO":<8} {"Resources":<22} {"PACKDATA size":>16}  {"Overflow":>12}  {"ISO size":>16}')
print(f'  {"-"*8} {"-"*22} {"-"*16}  {"-"*12}  {"-"*16}')
for r in results:
    res_str = '+'.join(f'R{x}' for x in r['resources'])
    print(f'  {r["label"]:<8} {res_str:<22} {r["pack_size"]:>16,}  {r["overflow_sectors"]:>10} sec  {r["iso_size"]:>16,}')

print(f'\n  T1 = {TESTS[0][2]}')
print(f'  T2 = {TESTS[1][2]}')
print(f'  T3 = {TESTS[2][2]}')
print(f'{"=" * 60}')
