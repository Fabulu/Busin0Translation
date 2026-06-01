"""
Build a test ISO with R1188 kanji rows (6-41, y=144-1007) WIPED (zeroed),
but kana/ASCII rows (0-5, y=0-143) PRESERVED.

Purpose: If chargen stat labels DISAPPEAR -> they come from R1188 kanji rows.
         If they REMAIN -> they come from somewhere else entirely.

R1188 is a 1024x1024 PSMT4 texture (4bpp), so each row = 512 bytes.
Header = 3072 bytes, pixel data = 524,288 bytes, trailing = 1024 bytes.
"""

import struct, json, os, math, shutil, glob

os.chdir('C:/Programmieren/wizardrytranslation')

SECTOR = 2048

# --- Step 1: Create R1188 with kanji rows zeroed ---
print('Step 1: Creating R1188 with kanji rows (y=144-1007) zeroed ...')
src_1188 = 'extracted/packdata_raw/1188_type01.raw'
data = bytearray(open(src_1188, 'rb').read())

HEADER_SIZE = 3072
PIXEL_SIZE = 524288  # 1024x1024 PSMT4
TRAILING_SIZE = len(data) - HEADER_SIZE - PIXEL_SIZE
ROW_BYTES = 512  # 1024 pixels / 2 (4bpp)

# Kanji rows: grid rows 6-41, y = 144 to 1007 (inclusive)
# Each grid row is 24 pixels tall: row 6 starts at y=144, row 41 ends at y=1007
Y_START = 144
Y_END = 1008  # exclusive (y=144 to y=1007 inclusive = 864 rows)

pixel_start = HEADER_SIZE
kanji_byte_start = pixel_start + Y_START * ROW_BYTES
kanji_byte_end = pixel_start + Y_END * ROW_BYTES

print(f'  File size: {len(data)} bytes')
print(f'  Header: 0-{HEADER_SIZE-1} (preserved)')
print(f'  Kana/ASCII rows (y=0-143): preserved ({Y_START * ROW_BYTES} bytes)')
print(f'  Kanji rows (y=144-1007): ZEROED (bytes {kanji_byte_start}-{kanji_byte_end-1}, {kanji_byte_end - kanji_byte_start} bytes)')
print(f'  Trailing data: preserved ({TRAILING_SIZE} bytes)')

# Zero only the kanji region
modified_1188 = bytearray(data)
modified_1188[kanji_byte_start:kanji_byte_end] = b'\x00' * (kanji_byte_end - kanji_byte_start)

# Verify sizes match
assert len(modified_1188) == len(data), "Size mismatch!"

# Pad to sector boundary
sc_1188 = math.ceil(len(modified_1188) / SECTOR)
if len(modified_1188) < sc_1188 * SECTOR:
    modified_1188 += b'\x00' * (sc_1188 * SECTOR - len(modified_1188))
print(f'  R1188: {len(modified_1188)} bytes ({sc_1188} sectors)')

# Verify kana rows preserved
kana_orig = data[HEADER_SIZE:kanji_byte_start]
kana_mod = modified_1188[HEADER_SIZE:kanji_byte_start]
assert kana_orig == kana_mod, "Kana rows were accidentally modified!"
print(f'  Kana rows (y=0-143) verified: PRESERVED ({len(kana_orig)} bytes, all match original)')

# Verify kanji rows zeroed
kanji_mod = modified_1188[kanji_byte_start:kanji_byte_end]
assert all(b == 0 for b in kanji_mod), "Kanji rows not fully zeroed!"
print(f'  Kanji rows (y=144-1007) verified: ALL ZEROED')

# --- Step 2: Rebuild PACKDATA.DIG with ONLY R1188 modified ---
print('\nStep 2: Rebuilding PACKDATA.DIG ...')
manifest = json.load(open('extracted/packdata_resources/manifest.json', encoding='utf-8'))
orig_packdata = 'extracted/PACKDATA.DIG'

with open(orig_packdata, 'rb') as f:
    otoc = [struct.unpack('<III', f.read(12)) for _ in range(2883)]
    f.seek(0)
    hdr = f.read(125 * SECTOR)

orig_size = os.path.getsize(orig_packdata)
out_packdata = 'build/PACKDATA_r1188_kanji_wipe.DIG'

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
            d = bytes(modified_1188)
        else:
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
print('\nStep 3: Building ISO ...')
ISO_PATH = 'Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso'
OUTPUT_ISO = 'build/BUSIN0_EN_r1188_kanji_wipe.iso'

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
        print('  ERROR: Could not find PACKDATA.DIG in ISO directory')
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
        print('=== R1188 KANJI WIPE TEST ISO READY ===')
        print(f'  File: {OUTPUT_ISO}')
        print()
        print('TEST INSTRUCTIONS:')
        print('  1. Load this ISO in PCSX2')
        print('  2. Go to character creation (chargen)')
        print('  3. Look at stat labels and kanji text')
        print('  4. Kana (hiragana/katakana) should STILL be visible (rows 0-5 preserved)')
        print('  5. If stat labels (kanji) DISAPPEAR -> they come from R1188 kanji rows 6-41')
        print('  6. If stat labels REMAIN -> they come from somewhere else entirely')
