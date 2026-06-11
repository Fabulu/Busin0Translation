#!/usr/bin/env python3
"""
Bisection test: Original PACKDATA + Patched EXE only.

If F/M appear on the keyboard -> cause is in PACKDATA changes.
If F/M are still missing -> cause is in EXE patches.
"""
import os, sys, struct, shutil

os.chdir('C:/Programmieren/wizardrytranslation')

SECTOR = 2048
SRC_ISO = 'Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso'
OUT_ISO = 'build/BUSIN0_EN_bisect_exe.iso'

print("=" * 60)
print("  BISECTION BUILD: EXE patches only (no PACKDATA changes)")
print("=" * 60)

if not os.path.isfile(SRC_ISO):
    print(f"ERROR: source ISO not found: {SRC_ISO}")
    sys.exit(1)

# Step 1: Copy original ISO (untouched PACKDATA)
print(f"\n=== Step 1: Copy original ISO ===")
shutil.copy2(SRC_ISO, OUT_ISO)
print(f"  Copied to {OUT_ISO}")

# Step 2: Run EXE patcher (produces build/SLPM_653.78_patched)
print(f"\n=== Step 2: Patch EXE ===")
os.system('python build/patch_exe.py')

# Step 3: Write patched EXE into ISO
print(f"\n=== Step 3: Write patched EXE into ISO ===")
exe_path = 'build/SLPM_653.78_patched'
if not os.path.exists(exe_path):
    print(f"ERROR: patched EXE not found: {exe_path}")
    sys.exit(1)

exe_data = open(exe_path, 'rb').read()
with open(OUT_ISO, 'r+b') as iso:
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

iso_size = os.path.getsize(OUT_ISO)
print(f"\n{'=' * 60}")
print(f"  {OUT_ISO} built ({iso_size:,} bytes)")
print(f"  PACKDATA: ORIGINAL (Japanese)")
print(f"  EXE: PATCHED (Patches 1-7)")
print(f"{'=' * 60}")
