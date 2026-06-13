#!/usr/bin/env python3
"""Test 1: Build ISO with PACKDATA growth but NO relocation.
PACKDATA overflows into BSN2_0.DSI - but we don't shift any files.
This tests whether the VIF crash comes from relocation vs resource growth."""
import sys, os, struct, shutil, math

os.chdir('C:/Programmieren/wizardrytranslation')
SECTOR = 2048

print("=" * 60)
print("  TEST 1: Growth + NO relocation (overflow allowed)")
print("=" * 60)

# Use the already-built PACKDATA_v3.DIG (full build with type-2)
pack_data = open('build/PACKDATA_v3.DIG', 'rb').read()
print(f"  PACKDATA size: {len(pack_data):,} bytes")

# Copy original ISO
src_iso = 'Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso'
dst_iso = 'build/BUSIN0_EN_noreloc.iso'
print(f"  Copying original ISO...")
shutil.copy2(src_iso, dst_iso)

# Write PACKDATA and update directory size (NO relocation)
with open(dst_iso, 'r+b') as iso:
    # Read PVD
    iso.seek(16 * SECTOR)
    pvd = iso.read(SECTOR)
    root_lba = struct.unpack_from('<I', pvd, 158)[0]
    root_size = struct.unpack_from('<I', pvd, 166)[0]

    # Read root directory
    iso.seek(root_lba * SECTOR)
    root_dir = bytearray(iso.read(root_size))

    # Find PACKDATA entry
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
            # Update size in directory (both LE and BE)
            iso.seek(root_lba * SECTOR + pos + 10)
            iso.write(struct.pack('<I', len(pack_data)))
            iso.write(struct.pack('>I', len(pack_data)))
            print(f"  PACKDATA at LBA {pack_lba}, new size: {len(pack_data):,}")
            break
        pos += rec_len

    # Write PACKDATA data (will overflow into BSN2_0.DSI area)
    iso.seek(pack_lba * SECTOR)
    iso.write(pack_data)

    pack_end_lba = pack_lba + math.ceil(len(pack_data) / SECTOR)

    # Show what we're overflowing into
    dir_entries = []
    pos = 0
    iso.seek(root_lba * SECTOR)
    root_dir = iso.read(root_size)
    while pos < len(root_dir):
        rec_len = root_dir[pos]
        if rec_len == 0:
            break
        name_len = root_dir[pos + 32]
        name = root_dir[pos + 33:pos + 33 + name_len].decode('ascii', errors='replace')
        lba = struct.unpack_from('<I', root_dir, pos + 2)[0]
        size = struct.unpack_from('<I', root_dir, pos + 10)[0]
        dir_entries.append((name, lba, size))
        pos += rec_len

    after_pack = sorted([e for e in dir_entries if e[1] > pack_lba and 'PACKDATA' not in e[0]], key=lambda e: e[1])
    if after_pack:
        first = after_pack[0]
        overflow = pack_end_lba - first[1]
        if overflow > 0:
            print(f"  OVERFLOW: {overflow} sectors into {first[0]} (LBA {first[1]})")
            print(f"  (NOT relocating - this is intentional for testing)")
        else:
            print(f"  No overflow detected")

# Now patch the EXE into the ISO
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
