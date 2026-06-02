"""
Chargen Cluster Nuclear Test — Zero EVERY resource R1175-R1195 EXCEPT:
  - R2100 (sectors 17-84, already tested separately)
  - R1370 (sectors 85-124, already tested separately)
  - R1188 (already tested separately)

This leaves 20 resources to zero:
  R1175 (type-104), R1176 (type-08), R1177 (type-04), R1178 (type-57),
  R1179 (type-18), R1180 (type-59), R1181 (type-12), R1182 (type-36),
  R1183 (type-07), R1184 (type-41), R1185 (type-08), R1186 (type-20),
  R1187 (type-02), R1189 (type-02), R1190 (type-01), R1191 (type-03),
  R1192 (type-02), R1193 (type-02), R1194 (type-02), R1195 (type-02)

Output: build/TEST_chargen_cluster_zero.iso
"""

import struct, shutil, os

os.chdir('C:/Programmieren/wizardrytranslation')

ISO_SRC = 'Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso'
ISO_OUT = 'build/TEST_chargen_cluster_zero.iso'
SECTOR = 2048

# Resources to EXCLUDE from zeroing
EXCLUDE = {1188}  # R2100 and R1370 are outside R1175-R1195 range anyway

# Resources to zero: R1175-R1195 minus exclusions
ZERO_INDICES = [i for i in range(1175, 1196) if i not in EXCLUDE]


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


def zero_resources(iso_path, packdata_sector, toc, resource_indices):
    """Zero the specified resources in the ISO."""
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
                  f'ISO_offset=0x{byte_offset:X}, size={byte_size:,} bytes  -> ZEROED')

    print(f'\n  Total zeroed: {total_bytes:,} bytes ({total_bytes / 1024:.1f} KB)')
    return details


def verify_zeros(iso_path, details):
    """Read back the zeroed regions and confirm they are all zeros."""
    print(f'\n--- Verification ---')
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
        print(f'  ALL VERIFIED: every resource fully zeroed.')
    else:
        print(f'  WARNING: some resources NOT fully zeroed!')
    return all_ok


# --- Main ---
print('=' * 70)
print('CHARGEN CLUSTER NUCLEAR TEST')
print('Zeroing R1175-R1195 EXCEPT R1188 (already tested)')
print('=' * 70)

packdata_sector = find_packdata_extent(ISO_SRC)
print(f'\nPACKDATA.DIG at ISO sector {packdata_sector} (byte offset 0x{packdata_sector * SECTOR:X})')

toc = read_toc(ISO_SRC, packdata_sector)
print(f'TOC entries: {len(toc)}')

# Show all resources in the range
print(f'\n--- R1175-R1195 resource info ---')
for idx in range(1175, 1196):
    so, sc, tc = toc[idx]
    status = 'SKIP (excluded)' if idx in EXCLUDE else 'ZERO'
    print(f'  R{idx}: sector_offset={so}, sectors={sc} ({sc * SECTOR:,} bytes), type={tc}  [{status}]')

print(f'\nResources to zero: {len(ZERO_INDICES)}')
print(f'Resources excluded: R1188')

# Copy and zero
print(f'\nCopying original ISO -> {ISO_OUT} ...')
shutil.copy2(ISO_SRC, ISO_OUT)
print(f'Copy complete.')

print(f'\n--- Zeroing resources ---')
details = zero_resources(ISO_OUT, packdata_sector, toc, ZERO_INDICES)

verify_zeros(ISO_OUT, details)

size_mb = os.path.getsize(ISO_OUT) / (1024 * 1024)
print(f'\n{"=" * 70}')
print(f'Output: {ISO_OUT} ({size_mb:.1f} MB)')
print(f'')
print(f'TEST INSTRUCTIONS:')
print(f'  1. Boot FRESH from title screen (NEVER use save states)')
print(f'  2. Navigate to character creation / stat allocation')
print(f'  3. If stat labels disappear or game crashes, one of these')
print(f'     20 resources provides the font/label data.')
print(f'  4. If stat labels are STILL visible, the data comes from')
print(f'     elsewhere (EXE, R2100, R1370, or R1188).')
print(f'{"=" * 70}')
