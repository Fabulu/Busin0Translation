"""
Chargen Resource Zero Test — verify R1196-R1212 provide chargen stat screen text.

Test 1: Zero R1196-R1212 (17 resources) — entire content including headers
Test 2: Zero ONLY R1203 (largest at 83 sectors / ~170KB) — if it's the stat
         allocation screen resource, zeroing should crash or blank the stat screen.

Each test copies the original Japanese ISO, finds PACKDATA.DIG inside it,
reads the TOC, overwrites the target resources with zeroes, then verifies.
"""

import struct, shutil, os

os.chdir('C:/Programmieren/wizardrytranslation')

ISO_SRC = 'Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso'
SECTOR = 2048


def find_packdata_extent(iso_path):
    """Locate PACKDATA.DIG LBA in the ISO root directory."""
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


def read_toc(iso_path, packdata_sector):
    """Read PACKDATA TOC entries from the ISO."""
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


def zero_resources(iso_path, packdata_sector, toc, resource_indices, label):
    """Zero the specified resources in the ISO and return list of (idx, offset, size)."""
    r_min = min(resource_indices)
    r_max = max(resource_indices)
    count = len(resource_indices)
    print(f'\n=== {label}: Zeroing {count} resource(s) (R{r_min}-R{r_max}) ===')

    total_bytes = 0
    details = []
    with open(iso_path, 'r+b') as f:
        for idx in resource_indices:
            so, sc, tc = toc[idx]
            byte_offset = (packdata_sector + so) * SECTOR
            byte_size = sc * SECTOR
            f.seek(byte_offset)
            f.write(b'\x00' * byte_size)
            total_bytes += byte_size
            details.append((idx, byte_offset, byte_size, sc, tc))
            print(f'  R{idx}: sector_offset={so}, sectors={sc}, type={tc}, '
                  f'ISO_offset=0x{byte_offset:X}, size={byte_size:,} bytes')

    print(f'  Total zeroed: {total_bytes:,} bytes')
    return details


def verify_zeros(iso_path, details, label):
    """Read back the zeroed regions and confirm they are all zeros."""
    print(f'\n--- Verifying {label} ---')
    all_ok = True
    with open(iso_path, 'rb') as f:
        for idx, byte_offset, byte_size, sc, tc in details:
            f.seek(byte_offset)
            data = f.read(byte_size)
            if data == b'\x00' * byte_size:
                print(f'  R{idx}: OK (all zeros, {byte_size:,} bytes)')
            else:
                nonzero = sum(1 for b in data if b != 0)
                print(f'  R{idx}: FAIL ({nonzero} non-zero bytes!)')
                all_ok = False
    if all_ok:
        print(f'  VERIFIED: all resources zeroed correctly.')
    else:
        print(f'  WARNING: some resources NOT fully zeroed!')
    return all_ok


# --- Main ---
packdata_sector = find_packdata_extent(ISO_SRC)
print(f'PACKDATA.DIG at ISO sector {packdata_sector} (byte offset 0x{packdata_sector * SECTOR:X})')

toc = read_toc(ISO_SRC, packdata_sector)
print(f'TOC entries: {len(toc)}')

# Print info for R1196-R1212
print(f'\n--- R1196-R1212 resource info ---')
for idx in range(1196, 1213):
    so, sc, tc = toc[idx]
    print(f'  R{idx}: sector_offset={so}, sectors={sc} ({sc * SECTOR:,} bytes), type={tc}')

# ===== TEST 1: Zero R1196-R1212 (17 resources) =====
out1 = 'build/BUSIN0_EN_chargen_r1196_r1212_zero.iso'
print(f'\nCopying original ISO -> {out1} ...')
shutil.copy2(ISO_SRC, out1)
details1 = zero_resources(out1, packdata_sector, toc, list(range(1196, 1213)), 'Test 1')
verify_zeros(out1, details1, 'Test 1')
size_mb1 = os.path.getsize(out1) / (1024 * 1024)
print(f'  Output: {out1} ({size_mb1:.1f} MB)')

# ===== TEST 2: Zero ONLY R1203 =====
out2 = 'build/BUSIN0_EN_chargen_r1203_zero.iso'
print(f'\nCopying original ISO -> {out2} ...')
shutil.copy2(ISO_SRC, out2)
details2 = zero_resources(out2, packdata_sector, toc, [1203], 'Test 2')
verify_zeros(out2, details2, 'Test 2')
size_mb2 = os.path.getsize(out2) / (1024 * 1024)
print(f'  Output: {out2} ({size_mb2:.1f} MB)')

print(f'\n{"=" * 60}')
print(f'Done! Test each ISO by booting FRESH from title screen in PCSX2.')
print(f'Navigate to character creation -> stat allocation screen.')
print(f'')
print(f'  Test 1 ({out1}):')
print(f'    R1196-R1212 zeroed — if chargen text disappears/crashes, confirmed.')
print(f'  Test 2 ({out2}):')
print(f'    R1203 only zeroed (largest, 83 sectors) — isolates the key resource.')
print(f'{"=" * 60}')
