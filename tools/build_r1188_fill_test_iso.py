"""
Build a test ISO with R1188 atlas filled with 0x88 (solid blocks).
This is a MINIMAL test: only R1188 is modified, everything else is original.

Steps:
1. Fill R1188 pixel data with 0x88
2. Rebuild PACKDATA.DIG (only R1188 differs from original)
3. Inject into ISO copy
"""

import struct, json, os, math, shutil, glob

os.chdir('C:/Programmieren/wizardrytranslation')

SECTOR = 2048

# --- Step 1: Create filled R1188 ---
print('Step 1: Creating filled R1188 ...')
src_1188 = 'extracted/packdata_raw/1188_type01.raw'
data = bytearray(open(src_1188, 'rb').read())
HEADER_SIZE = 3072
PIXEL_SIZE = len(data) - HEADER_SIZE  # everything after header is pixels
header = data[:HEADER_SIZE]
pixels = b'\x88' * PIXEL_SIZE
filled_1188 = bytearray(header + pixels)
sc_1188 = math.ceil(len(filled_1188) / SECTOR)
if len(filled_1188) < sc_1188 * SECTOR:
    filled_1188 += b'\x00' * (sc_1188 * SECTOR - len(filled_1188))
print(f'  R1188: {len(filled_1188)} bytes ({sc_1188} sectors), pixels filled with 0x88')

# --- Step 2: Rebuild PACKDATA.DIG with ONLY R1188 modified ---
print('Step 2: Rebuilding PACKDATA.DIG ...')
manifest = json.load(open('extracted/packdata_resources/manifest.json', encoding='utf-8'))
orig_packdata = 'extracted/PACKDATA.DIG'

with open(orig_packdata, 'rb') as f:
    otoc = [struct.unpack('<III', f.read(12)) for _ in range(2883)]
    f.seek(0)
    hdr = f.read(125 * SECTOR)

orig_size = os.path.getsize(orig_packdata)
out_packdata = 'build/PACKDATA_r1188_fill.DIG'

with open(out_packdata, 'wb') as out:
    out.write(hdr)
    cs = 125
    ntoc = []

    for entry in manifest:
        idx = entry['index']
        if entry.get('skipped'):
            ntoc.append(otoc[idx])
            continue

        tc = entry['type_code']
        fn = f'{idx:04d}_type{tc:02d}.raw'

        if idx == 1188:
            # Use our filled version
            d = bytes(filled_1188)
        else:
            # Use original
            rp = f'extracted/packdata_raw/{fn}'
            if os.path.exists(rp):
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

print(f'  Size: {fs:,} bytes (orig: {orig_size:,}, diff: {fs - orig_size:+,})')

if fs < orig_size:
    with open(out_packdata, 'ab') as f:
        f.write(b'\x00' * (orig_size - fs))
    print(f'  Padded to {orig_size:,} bytes')

# --- Step 3: Build ISO ---
print('Step 3: Building ISO ...')
ISO_PATH = 'Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso'
OUTPUT_ISO = 'build/BUSIN0_EN_r1188_fill_test.iso'

if not os.path.exists(ISO_PATH):
    print(f'  ERROR: Source ISO not found: {ISO_PATH}')
    print(f'  PACKDATA ready at {out_packdata}')
else:
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
        print(f'  ERROR: Could not find PACKDATA.DIG in ISO directory')
    else:
        print(f'  PACKDATA.DIG at ISO sector {packdata_extent}')
        print(f'  Copying ISO ...')
        shutil.copy2(ISO_PATH, OUTPUT_ISO)

        with open(OUTPUT_ISO, 'r+b') as iso_f:
            iso_f.seek(packdata_extent * 2048)
            with open(out_packdata, 'rb') as pd:
                while True:
                    chunk = pd.read(4 * 1024 * 1024)
                    if not chunk:
                        break
                    iso_f.write(chunk)

        print(f'  ISO written: {OUTPUT_ISO}')
        print(f'  Size: {os.path.getsize(OUTPUT_ISO):,} bytes')
        print()
        print('=== R1188 FILL TEST ISO READY ===')
        print(f'  File: {OUTPUT_ISO}')
        print()
        print('TEST INSTRUCTIONS:')
        print('  1. Load this ISO in PCSX2')
        print('  2. Go to character creation (chargen)')
        print('  3. Look at stat labels and tab labels')
        print('  4. If ALL kanji/labels are solid blocks -> R1188 IS the source')
        print('  5. If labels still show normally -> R1188 is NOT the source')
