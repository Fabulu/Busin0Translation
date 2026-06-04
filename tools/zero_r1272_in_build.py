"""
Zero R1272 in the BUILD v9 ISO — test whether the game re-reads R1272
from disc or caches it in RAM.

R1272 is the main dialogue font atlas (256x512 PSMT4).
In the build ISO it should be at sector offset 211372 (vs 211292 in original).

This script:
1. Copies build/BUSIN0_EN_v9.iso -> build/TEST_v9_zero_R1272.iso
2. Reads the PACKDATA TOC from the COPY
3. Finds R1272's sector offset
4. Zeros R1272's entire content (all sectors)
5. Verifies the zeros

Expected results when booting FRESH:
- If dialogue text goes BLANK -> R1272 IS read from disc (font atlas matters)
- If dialogue text persists -> R1272 is cached from a previous load
- Stat labels may persist even if dialogue blanks (different source)
"""

import struct, shutil, os

os.chdir('C:/Programmieren/wizardrytranslation')

ISO_SRC = 'build/BUSIN0_EN_v9.iso'
ISO_DST = 'build/TEST_v9_zero_R1272.iso'
SECTOR = 2048
TARGET_RESOURCE = 1272


def find_packdata_extent(iso_path):
    """Find PACKDATA.DIG start sector in the ISO's root directory."""
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
    """Read the PACKDATA TOC (12 bytes per entry: sector_offset, sector_count, type_code)."""
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


# --- Step 1: Copy the build ISO ---
print(f'Source: {ISO_SRC}')
if not os.path.exists(ISO_SRC):
    raise FileNotFoundError(f'{ISO_SRC} not found — run build_v9.py first')

print(f'Copying {ISO_SRC} -> {ISO_DST} ...')
shutil.copy2(ISO_SRC, ISO_DST)
size_mb = os.path.getsize(ISO_DST) / (1024 * 1024)
print(f'  Copy complete: {size_mb:.1f} MB')

# --- Step 2: Read PACKDATA TOC from the COPY ---
packdata_sector = find_packdata_extent(ISO_DST)
print(f'\nPACKDATA.DIG at ISO sector {packdata_sector} (byte offset {packdata_sector * SECTOR:,})')

toc = read_toc(ISO_DST, packdata_sector)
print(f'TOC entries: {len(toc)}')

if TARGET_RESOURCE >= len(toc):
    raise IndexError(f'R{TARGET_RESOURCE} not in TOC (only {len(toc)} entries)')

# --- Step 3: Find R1272's location ---
so, sc, tc = toc[TARGET_RESOURCE]
abs_sector = packdata_sector + so
byte_offset = abs_sector * SECTOR
byte_size = sc * SECTOR

print(f'\nR{TARGET_RESOURCE} in BUILD ISO:')
print(f'  TOC sector offset: {so}')
print(f'  Sector count:      {sc}')
print(f'  Type code:         {tc}')
print(f'  Absolute sector:   {abs_sector}')
print(f'  Byte offset:       {byte_offset:,} (0x{byte_offset:X})')
print(f'  Byte size:         {byte_size:,} (0x{byte_size:X})')

# --- Step 4: Read original content, then zero it ---
with open(ISO_DST, 'r+b') as f:
    f.seek(byte_offset)
    original_data = f.read(byte_size)
    non_zero_before = sum(1 for b in original_data if b != 0)
    print(f'\n  Pre-zero: {non_zero_before:,} non-zero bytes out of {byte_size:,}')

    # Show first 32 bytes of header for reference
    print(f'  Header (first 32 bytes): {original_data[:32].hex()}')

    # Write zeros
    f.seek(byte_offset)
    f.write(b'\x00' * byte_size)
    print(f'\n  ZEROED {byte_size:,} bytes ({sc} sectors) at offset 0x{byte_offset:X}')

# --- Step 5: Verify the zeros ---
with open(ISO_DST, 'rb') as f:
    f.seek(byte_offset)
    check = f.read(byte_size)
    non_zero_after = sum(1 for b in check if b != 0)
    print(f'  Post-zero verification: {non_zero_after} non-zero bytes (should be 0)')

if non_zero_after == 0:
    print('\n  VERIFICATION PASSED — R1272 is fully zeroed')
else:
    print('\n  VERIFICATION FAILED — some bytes were not zeroed!')

# --- Summary ---
print(f'\n{"=" * 60}')
print(f'Test ISO: {ISO_DST}')
print(f'R1272 zeroed: {sc} sectors ({byte_size:,} bytes) at sector {abs_sector}')
print(f'{"=" * 60}')
print()
print('TESTING INSTRUCTIONS:')
print('  1. Boot TEST_v9_zero_R1272.iso FRESH from title screen in PCSX2')
print('  2. Do NOT load any save states')
print('  3. Enter gameplay and check:')
print('     - Dialogue text: should go BLANK if R1272 is used for dialogue font')
print('     - Stat labels: may persist if they come from a different source')
print('  4. Compare with the unmodified BUSIN0_EN_v9.iso for reference')
print()
print('INTERPRETATION:')
print('  - Blank dialogue   -> R1272 IS the dialogue font atlas (read from disc)')
print('  - Normal dialogue  -> R1272 is cached in RAM, not re-read')
print('  - Labels persist   -> Labels use a DIFFERENT font resource (not R1272)')
print('  - Labels blank too -> Labels also depend on R1272')
