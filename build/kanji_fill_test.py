#!/usr/bin/env python3
"""
kanji_fill_test.py -- Fill ALL kanji font page resources with solid blocks.

Resources R1269-R1276, R1303 are filled with 0xFF pixel data (preserving headers).
Then PACKDATA.DIG is rebuilt and an ISO is created.

If every kanji on the chargen screen becomes a solid block, these ARE the font pages.
If some kanji remain normal, there are other font sources.
"""

import struct, os, math, shutil, glob

BASE = 'C:/Programmieren/wizardrytranslation'
os.chdir(BASE)

SECTOR = 2048
KANJI_RESOURCES = [1269, 1270, 1271, 1273, 1274, 1275, 1276, 1303]

# ---------------------------------------------------------------------------
# STEP 1: Fill kanji page resources with 0xFF
# ---------------------------------------------------------------------------
print("=" * 60)
print("  KANJI FILL TEST -- All pages filled with solid blocks")
print("=" * 60)

os.makedirs('build/packdata_resources', exist_ok=True)

# Back up any existing kanji resources in build dir
backup_dir = 'build/packdata_resources/_kanji_backup'
os.makedirs(backup_dir, exist_ok=True)

for rid in KANJI_RESOURCES:
    raw_path = glob.glob(f'extracted/packdata_raw/{rid:04d}_type*.raw')[0]
    out_name = os.path.basename(raw_path)
    out_path = f'build/packdata_resources/{out_name}'

    # Back up if exists
    if os.path.exists(out_path):
        shutil.copy2(out_path, f'{backup_dir}/{out_name}')

    orig = open(raw_path, 'rb').read()
    size = len(orig)

    # These are type01 (raw image data) resources.
    # They have a 16-byte sub-header: [u32 unknown, u32 payload_size, u32 unknown, u32 unknown]
    # Fill the entire content with 0xFF to make every glyph a solid block
    filled = b'\xFF' * size

    open(out_path, 'wb').write(filled)
    print(f"  R{rid}: {out_name} -- {size:,} bytes filled with 0xFF")

# ---------------------------------------------------------------------------
# STEP 2: Rebuild PACKDATA.DIG using the standard rebuild script logic
# ---------------------------------------------------------------------------
print()
print("STEP 2: Rebuilding PACKDATA.DIG ...")

import json

manifest = json.load(open('extracted/packdata_resources/manifest.json', encoding='utf-8'))
n_entries = len(manifest)

with open('extracted/PACKDATA.DIG', 'rb') as f:
    otoc = [struct.unpack('<III', f.read(12)) for _ in range(n_entries)]
    f.seek(0)
    hdr = f.read(125 * SECTOR)

orig_size = os.path.getsize('extracted/PACKDATA.DIG')

dig_path = 'build/PACKDATA_kanji_fill.DIG'

with open(dig_path, 'wb') as out:
    out.write(hdr)
    cs = 125
    ntoc = []
    patched = 0

    for entry in manifest:
        idx = entry['index']
        if entry.get('skipped'):
            ntoc.append(otoc[idx])
            continue

        tc = entry['type_code']
        fn = f'{idx:04d}_type{tc:02d}.raw'
        mp = f'build/packdata_resources/{fn}'
        rp = f'extracted/packdata_raw/{fn}'

        if os.path.exists(mp):
            d = open(mp, 'rb').read()
            patched += 1
        elif os.path.exists(rp):
            d = open(rp, 'rb').read()
        else:
            cc = glob.glob(f'extracted/packdata_raw/{idx:04d}_type*.raw')
            d = open(cc[0], 'rb').read() if cc else b'\x00' * SECTOR

        sc = math.ceil(len(d) / SECTOR)
        if len(d) < sc * SECTOR:
            d += b'\x00' * (sc * SECTOR - len(d))

        out.seek(cs * SECTOR)
        out.write(d)
        ntoc.append((cs, sc, tc))
        cs += sc

    out.seek(0)
    for so, sc, tc in ntoc:
        out.write(struct.pack('<III', so, sc, tc))

    out.seek(0, 2)
    fs = out.tell()

print(f'  Patched: {patched} resources')
print(f'  Size: {fs:,} bytes (orig: {orig_size:,}, diff: {fs - orig_size:+,})')

if fs < orig_size:
    with open(dig_path, 'ab') as f:
        f.write(b'\x00' * (orig_size - fs))
    print(f'  Padded to {orig_size:,} bytes')

# ---------------------------------------------------------------------------
# STEP 3: Build ISO
# ---------------------------------------------------------------------------
print()
print("STEP 3: Building ISO ...")

ISO_PATH = 'Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso'
OUTPUT_ISO = 'build/BUSIN0_EN_all_kanji_fill.iso'

with open(ISO_PATH, 'rb') as f:
    f.seek(16 * 2048)
    pvd = f.read(2048)
    root_rec = pvd[156:156 + 34]
    root_extent = struct.unpack_from('<I', root_rec, 2)[0]
    root_size = struct.unpack_from('<I', root_rec, 10)[0]
    f.seek(root_extent * 2048)
    root_data = f.read(root_size)

packdata_extent = None
pos = 0
while pos < len(root_data):
    rec_len = root_data[pos]
    if rec_len == 0:
        break
    name_len = root_data[pos + 32]
    name = root_data[pos + 33: pos + 33 + name_len]
    if b'PACKDATA' in name:
        packdata_extent = struct.unpack_from('<I', root_data, pos + 2)[0]
        break
    pos += rec_len

if packdata_extent is None:
    print('  ERROR: Could not find PACKDATA.DIG in ISO directory')
else:
    print(f'  PACKDATA.DIG at ISO sector {packdata_extent}')

    shutil.copy2(ISO_PATH, OUTPUT_ISO)

    with open(OUTPUT_ISO, 'r+b') as iso_f:
        iso_f.seek(packdata_extent * 2048)
        with open(dig_path, 'rb') as pd:
            while True:
                chunk = pd.read(4 * 1024 * 1024)
                if not chunk:
                    break
                iso_f.write(chunk)

    print(f'  ISO written: {OUTPUT_ISO}')
    print(f'  Size: {os.path.getsize(OUTPUT_ISO):,} bytes')

# ---------------------------------------------------------------------------
# STEP 4: Clean up -- remove the kanji fills from build/packdata_resources
#         so they don't pollute normal builds
# ---------------------------------------------------------------------------
print()
print("STEP 4: Cleaning up kanji fills from build/packdata_resources ...")
for rid in KANJI_RESOURCES:
    raw_path = glob.glob(f'extracted/packdata_raw/{rid:04d}_type*.raw')[0]
    out_name = os.path.basename(raw_path)
    out_path = f'build/packdata_resources/{out_name}'
    backup_path = f'{backup_dir}/{out_name}'

    if os.path.exists(backup_path):
        # Restore original
        shutil.copy2(backup_path, out_path)
        print(f"  R{rid}: restored from backup")
    else:
        # Remove the fill -- wasn't there before
        if os.path.exists(out_path):
            os.remove(out_path)
            print(f"  R{rid}: removed (no prior version)")

# Remove backup dir if empty
try:
    os.rmdir(backup_dir)
except:
    pass

print()
print("=" * 60)
print("  DONE -- ISO: build/BUSIN0_EN_all_kanji_fill.iso")
print("  Load in emulator and check chargen stat labels.")
print("  If ALL kanji are solid blocks -> these are the font pages.")
print("  If some remain normal -> other font sources exist.")
print("=" * 60)
