"""Extract raw resource blocks from PACKDATA.DIG (with 16-byte header, padded to sector boundary)."""
import struct
import sys
import os
import math

sys.stdout.reconfigure(encoding='utf-8')

DIG_PATH = r'C:\Programmieren\wizardrytranslation\extracted\PACKDATA.DIG'
OUT_DIR  = r'C:\Programmieren\wizardrytranslation\extracted\packdata_raw'
SECTOR   = 2048
TOC_ENTRIES = 2883
OUTLIER_INDICES = {1370, 2100}

os.makedirs(OUT_DIR, exist_ok=True)

dig_size = os.path.getsize(DIG_PATH)
print(f'PACKDATA.DIG size: {dig_size:,} bytes')

type_dist = {}
total_bytes = 0
total_files = 0
errors = []

with open(DIG_PATH, 'rb') as f:
    # Read TOC
    toc_data = f.read(TOC_ENTRIES * 12)
    toc = []
    for i in range(TOC_ENTRIES):
        so, sc, tc = struct.unpack_from('<III', toc_data, i * 12)
        toc.append((so, sc, tc))

    # Verify first valid entry
    first_valid = next(i for i in range(TOC_ENTRIES) if i not in OUTLIER_INDICES)
    print(f'First entry sector_offset: 0x{toc[first_valid][0]:X} (expect 0x7D)')
    assert toc[first_valid][0] == 0x7D

    # Check outliers
    for oi in sorted(OUTLIER_INDICES):
        so, sc, tc = toc[oi]
        print(f'Outlier index {oi}: sector_offset=0x{so:X} -- SKIPPING')

    # Last entry check
    max_end = 0
    for i in range(TOC_ENTRIES):
        if i in OUTLIER_INDICES:
            continue
        so, sc, tc = toc[i]
        end = (so + sc) * SECTOR
        if end > max_end:
            max_end = end
    print(f'Last entry ends at byte {max_end:,} (file size {dig_size:,}, match={max_end == dig_size})')

    # Extract raw blocks
    for i in range(TOC_ENTRIES):
        if i in OUTLIER_INDICES:
            continue

        so, sc, tc = toc[i]
        abs_off = so * SECTOR
        raw_size = sc * SECTOR
        fname = f'{i:04d}_type{tc:02d}.raw'
        out_path = os.path.join(OUT_DIR, fname)

        try:
            f.seek(abs_off)
            raw_data = f.read(raw_size)
            if len(raw_data) < raw_size:
                raise ValueError(f'Short read: got {len(raw_data)}, expected {raw_size}')

            with open(out_path, 'wb') as out:
                out.write(raw_data)

            total_files += 1
            total_bytes += raw_size
            type_dist[tc] = type_dist.get(tc, 0) + 1
        except Exception as e:
            errors.append((i, str(e)))

        if (i + 1) % 100 == 0:
            print(f'  progress: {i+1}/{TOC_ENTRIES} entries processed')

print(f'\n=== Summary ===')
print(f'Total files extracted: {total_files}')
print(f'Total raw bytes extracted: {total_bytes:,}')
print(f'Type distribution:')
for tc in sorted(type_dist):
    print(f'  type {tc:2d}: {type_dist[tc]:5d} files')
if errors:
    print(f'Errors ({len(errors)}):')
    for idx, msg in errors:
        print(f'  entry {idx}: {msg}')
else:
    print('No errors.')
