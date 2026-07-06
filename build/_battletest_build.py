#!/usr/bin/env python3
"""ONE-OFF battle-isolation test build (NOT part of the build pipeline).

Produces an ISO with OUR PATCHED EXE but PRISTINE/UNMODIFIED PACKDATA, to
isolate the EXE patches from the resource-resize cascade.

Method: copy the pristine Japanese ISO verbatim, then overwrite ONLY the
SLPM_653.78 EXE file (Step 8.4/8.5 logic). PACKDATA.DIG and every other file
are left byte-identical to the pristine source ISO.

Run patch_exe.py FIRST to produce build/SLPM_653.78_patched.
ASCII-only stdout (Windows cp1252 safe).
"""
import os
import struct
import shutil
import math
import sys

os.chdir('C:/Programmieren/wizardrytranslation')
SECTOR = 2048

PRISTINE_ISO = 'Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso'
EXE_PATCHED  = 'build/SLPM_653.78_patched'
OUT_ISO      = 'build/BUSIN0_EN_battletest_pristinepack.iso'

print('=' * 60)
print('  BATTLE-ISOLATION TEST BUILD (patched EXE + pristine PACKDATA)')
print('=' * 60)

if not os.path.isfile(EXE_PATCHED):
    print('ERROR: patched EXE missing: %s' % EXE_PATCHED)
    print('       run "python build/patch_exe.py" first')
    sys.exit(1)

exe_data = open(EXE_PATCHED, 'rb').read()
print('Patched EXE: %d bytes' % len(exe_data))

# --- copy pristine ISO verbatim (PACKDATA stays untouched) ---
print('Copying pristine ISO -> %s ...' % OUT_ISO)
shutil.copy2(PRISTINE_ISO, OUT_ISO)

# --- overwrite ONLY the SLPM_653.78 file (Step 8.5 logic) ---
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
            exe_size = struct.unpack_from('<I', root_dir, pos + 10)[0]
            # size is identical (in-place patches), but write LE+BE size for safety
            iso.seek(root_lba * SECTOR + pos + 10)
            iso.write(struct.pack('<I', len(exe_data)))
            iso.write(struct.pack('>I', len(exe_data)))
            iso.seek(exe_lba * SECTOR)
            iso.write(exe_data)
            print('  EXE written: %d bytes at LBA %d (was size %d)'
                  % (len(exe_data), exe_lba, exe_size))
            break
        pos += rec_len

print('Done. Output: %s (%d bytes)' % (OUT_ISO, os.path.getsize(OUT_ISO)))
