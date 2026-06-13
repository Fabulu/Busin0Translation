#!/usr/bin/env python3
"""Test 2: Build ISO with ONLY type-2 translations (revert type-01 MSG resources).
Type-01 resources R34-R49, R2124, R2654 are reverted to originals.
PACKDATA is rebuilt and overflow relocation IS applied.
This tests whether a specific type-01 resource is the crash cause."""
import sys, os, struct, shutil, math, glob

os.chdir('C:/Programmieren/wizardrytranslation')
SECTOR = 2048

print("=" * 60)
print("  TEST 2: Type-2 only (revert type-01 MSG to originals)")
print("=" * 60)

# Revert type-01 resources R34-R49 and R2654 to originals
type01_resources = list(range(34, 50)) + [2124, 2654]
reverted = 0

for r_id in type01_resources:
    # Find the built file
    built = glob.glob(f'build/packdata_resources/{r_id:04d}_type*.raw')
    orig = glob.glob(f'extracted/packdata_raw/{r_id:04d}_type*.raw')
    if built and orig:
        shutil.copy2(orig[0], built[0])
        print(f"  Reverted R{r_id}: {os.path.basename(orig[0])}")
        reverted += 1
    elif built:
        # No original found, remove the built file
        os.remove(built[0])
        print(f"  Removed R{r_id} (no original)")
        reverted += 1

print(f"  Reverted {reverted} type-01 resources")

# Rebuild PACKDATA with reverted type-01 resources
print("\n  Rebuilding PACKDATA...")
os.system('python build/rebuild_packdata.py')

pack_data = open('build/PACKDATA_v3.DIG', 'rb').read()
print(f"  PACKDATA size: {len(pack_data):,} bytes")

# Copy original ISO
src_iso = 'Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso'
dst_iso = 'build/BUSIN0_EN_type2only.iso'
print(f"\n  Copying original ISO...")
shutil.copy2(src_iso, dst_iso)

# Write PACKDATA and update directory size
with open(dst_iso, 'r+b') as iso:
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
            iso.write(struct.pack('<I', len(pack_data)))
            iso.write(struct.pack('>I', len(pack_data)))
            iso.seek(pack_lba * SECTOR)
            iso.write(pack_data)
            print(f"  PACKDATA at LBA {pack_lba}, size: {len(pack_data):,}")
            break
        pos += rec_len

# Apply overflow relocation (copied from build_v9.py Step 8.2)
print("\n  Checking PACKDATA overflow...")
with open(dst_iso, 'r+b') as iso:
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
    if pack_entry:
        _, _, pack_lba, pack_size = pack_entry[0]
        pack_end_lba = pack_lba + math.ceil(pack_size / SECTOR)

        after_pack = sorted(
            [e for e in dir_entries if e[2] > pack_lba and 'PACKDATA' not in e[1]],
            key=lambda e: e[2]
        )

        if after_pack:
            first_after_lba = after_pack[0][2]
            if pack_end_lba > first_after_lba:
                shift = pack_end_lba - first_after_lba
                print(f"  PACKDATA overflow: {shift} sectors into subsequent files")
                print(f"  Shifting {len(after_pack)} files forward by {shift} sectors...")

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

                print(f"  Done. ISO extended by {shift * SECTOR:,} bytes")
            else:
                print(f"  No overflow (PACKDATA ends at {pack_end_lba}, next file at {first_after_lba})")

# Patch EXE
exe_path = 'build/SLPM_653.78_patched'
if os.path.exists(exe_path):
    exe_data = open(exe_path, 'rb').read()
    with open(dst_iso, 'r+b') as iso:
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

final_size = os.path.getsize(dst_iso)
print(f"\n  Output: {dst_iso}")
print(f"  Size: {final_size:,} bytes")
print("=" * 60)
