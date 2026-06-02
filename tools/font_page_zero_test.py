"""
Font Page Zero Test — create 3 test ISOs to identify which font page resources
provide chargen stat labels.

Test A: Zero R1215-R1268 (54 resources, "main" font pages)
Test B: Zero R1269-R1311 (43 resources, "extended" font pages)
Test C: Zero R1215-R1311 (97 resources, ALL font pages)

Each test copies the original Japanese ISO, finds PACKDATA.DIG inside it,
reads the TOC, and overwrites the target resources with zeroes.
"""

import struct, shutil, os

os.chdir('C:/Programmieren/wizardrytranslation')

ISO_SRC = 'Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso'
SECTOR = 2048

# --- Locate PACKDATA.DIG extent in ISO ---
def find_packdata_extent(iso_path):
    with open(iso_path, 'rb') as f:
        f.seek(16 * SECTOR)
        pvd = f.read(SECTOR)
        root_rec = pvd[156:156 + 34]
        root_extent = struct.unpack_from('<I', root_rec, 2)[0]
        root_size = struct.unpack_from('<I', root_rec, 10)[0]
        f.seek(root_extent * SECTOR)
        root_data = f.read(root_size)

    pos = 0
    while pos < len(root_data):
        rec_len = root_data[pos]
        if rec_len == 0:
            break
        name_len = root_data[pos + 32]
        name = root_data[pos + 33: pos + 33 + name_len]
        if b'PACKDATA' in name:
            return struct.unpack_from('<I', root_data, pos + 2)[0]
        pos += rec_len
    raise RuntimeError('PACKDATA.DIG not found in ISO directory')

# --- Read TOC from ISO ---
def read_toc(iso_path, packdata_sector):
    with open(iso_path, 'rb') as f:
        f.seek(packdata_sector * SECTOR)
        hdr = f.read(125 * SECTOR)

    entries = []
    for i in range(len(hdr) // 12):
        so, sc, tc = struct.unpack_from('<III', hdr, i * 12)
        if so == 0 and sc == 0 and tc == 0:
            break
        entries.append((so, sc, tc))
    return entries

# --- Zero resources in an ISO copy ---
def zero_resources(iso_path, packdata_sector, toc, r_start, r_end, label):
    print(f'\n=== Test {label}: Zeroing R{r_start}-R{r_end} ({r_end - r_start + 1} resources) ===')
    total_bytes = 0
    with open(iso_path, 'r+b') as f:
        for idx in range(r_start, r_end + 1):
            so, sc, tc = toc[idx]
            byte_offset = (packdata_sector + so) * SECTOR
            byte_size = sc * SECTOR
            f.seek(byte_offset)
            f.write(b'\x00' * byte_size)
            total_bytes += byte_size
    print(f'  Zeroed {total_bytes:,} bytes across {r_end - r_start + 1} resources')

# --- Main ---
packdata_sector = find_packdata_extent(ISO_SRC)
print(f'PACKDATA.DIG at ISO sector {packdata_sector} (byte offset {packdata_sector * SECTOR:,})')

toc = read_toc(ISO_SRC, packdata_sector)
print(f'TOC entries: {len(toc)}')

tests = [
    ('A', 1215, 1268, 'build/BUSIN0_EN_fontpage_A_1215-1268.iso'),
    ('B', 1269, 1311, 'build/BUSIN0_EN_fontpage_B_1269-1311.iso'),
    ('C', 1215, 1311, 'build/BUSIN0_EN_fontpage_C_all.iso'),
]

for label, r_start, r_end, out_path in tests:
    print(f'\nCopying original ISO -> {out_path} ...')
    shutil.copy2(ISO_SRC, out_path)
    zero_resources(out_path, packdata_sector, toc, r_start, r_end, label)
    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f'  Output: {out_path} ({size_mb:.1f} MB)')

print('\n=== Done! ===')
print('Test each ISO by booting FRESH from title screen in PCSX2.')
print('Check chargen stat labels to see which disappear.')
print('  A (R1215-1268): main font pages')
print('  B (R1269-1311): extended font pages')
print('  C (R1215-1311): all font pages')
