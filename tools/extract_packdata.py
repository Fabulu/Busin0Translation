"""Extract payload data from PACKDATA.DIG into individual resource files."""
import struct
import sys
import os
import json

# Force UTF-8 stdout
sys.stdout.reconfigure(encoding='utf-8')

DIG_PATH = r'C:\Programmieren\wizardrytranslation\extracted\PACKDATA.DIG'
OUT_DIR  = r'C:\Programmieren\wizardrytranslation\extracted\packdata_resources'
SECTOR   = 2048
TOC_ENTRIES = 2883
OUTLIER_INDICES = {1370, 2100}

os.makedirs(OUT_DIR, exist_ok=True)

dig_size = os.path.getsize(DIG_PATH)
print(f'PACKDATA.DIG size: {dig_size:,} bytes')

manifest = []
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
    assert toc[first_valid][0] == 0x7D, f'First entry sector_offset mismatch: 0x{toc[first_valid][0]:X}'

    # Check outliers
    for oi in sorted(OUTLIER_INDICES):
        so, sc, tc = toc[oi]
        print(f'Outlier index {oi}: sector_offset=0x{so:X}, sector_count={sc}, type_code={tc} -- SKIPPING')

    # Find last valid entry by sector_offset + sector_count
    max_end = 0
    max_idx = -1
    for i in range(TOC_ENTRIES):
        if i in OUTLIER_INDICES:
            continue
        so, sc, tc = toc[i]
        end = (so + sc) * SECTOR
        if end > max_end:
            max_end = end
            max_idx = i
    print(f'Last entry ends at byte {max_end:,} (file size {dig_size:,}, match={max_end == dig_size})')

    # Extract
    for i in range(TOC_ENTRIES):
        if i in OUTLIER_INDICES:
            manifest.append({'index': i, 'skipped': True, 'reason': 'outlier'})
            continue

        so, sc, tc = toc[i]
        abs_off = so * SECTOR
        fname = f'{i:04d}_type{tc:02d}.bin'
        out_path = os.path.join(OUT_DIR, fname)

        try:
            f.seek(abs_off)
            header = f.read(16)
            if len(header) < 16:
                raise ValueError(f'Short header read: {len(header)} bytes')
            z1, payload_size, stride, z2 = struct.unpack('<IIII', header)

            # Read payload
            payload = f.read(payload_size)
            if len(payload) < payload_size:
                raise ValueError(f'Short payload: got {len(payload)}, expected {payload_size}')

            with open(out_path, 'wb') as out:
                out.write(payload)

            total_files += 1
            total_bytes += payload_size
            type_dist[tc] = type_dist.get(tc, 0) + 1

            manifest.append({
                'index': i,
                'filename': fname,
                'sector_offset': so,
                'sector_count': sc,
                'type_code': tc,
                'payload_size': payload_size,
                'stride': stride,
                'header_zero1': z1,
                'header_zero2': z2,
            })
        except Exception as e:
            errors.append((i, str(e)))
            manifest.append({'index': i, 'skipped': True, 'reason': str(e)})

        if (i + 1) % 100 == 0:
            print(f'  progress: {i+1}/{TOC_ENTRIES} entries processed')

# Write manifest
manifest_path = os.path.join(OUT_DIR, 'manifest.json')
with open(manifest_path, 'w', encoding='utf-8') as mf:
    json.dump(manifest, mf, indent=1)

print(f'\n=== Summary ===')
print(f'Total files extracted: {total_files}')
print(f'Total bytes extracted: {total_bytes:,}')
print(f'Type distribution:')
for tc in sorted(type_dist):
    print(f'  type {tc:2d}: {type_dist[tc]:5d} files')
if errors:
    print(f'Errors ({len(errors)}):')
    for idx, msg in errors:
        print(f'  entry {idx}: {msg}')
else:
    print('No errors.')
print(f'Manifest written to: {manifest_path}')
