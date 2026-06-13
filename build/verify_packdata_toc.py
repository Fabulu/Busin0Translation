#!/usr/bin/env python3
"""Deep verification of PACKDATA_v3.DIG TOC vs actual resource data."""
import struct, os, glob, random, sys

os.chdir('C:/Programmieren/wizardrytranslation')

SECTOR = 2048
PACKDATA = 'build/PACKDATA_v3.DIG'
N_ENTRIES = 2883

errors = []
warnings = []

print(f"Opening {PACKDATA}...")
packdata_size = os.path.getsize(PACKDATA)
print(f"File size: {packdata_size:,} bytes = {packdata_size // SECTOR:,} sectors")

with open(PACKDATA, 'rb') as f:
    # Read TOC (2883 entries x 12 bytes each)
    toc = []
    for i in range(N_ENTRIES):
        raw = f.read(12)
        so, sc, tc = struct.unpack('<III', raw)
        toc.append((so, sc, tc))

print(f"TOC entries read: {len(toc)}")
print()

# ──────────────────────────────────────────────────
# 1. Verify header gap: R2100 (sectors 17-84) and R1370 (sectors 85-124)
# ──────────────────────────────────────────────────
print("=" * 60)
print("HEADER GAP VERIFICATION (sectors 17-124)")
print("=" * 60)

header_checks = [
    (2100, 17, 68, 'build/packdata_resources/2100_type04.raw'),
    (1370, 85, 40, 'build/packdata_resources/1370_type04.raw'),
]

with open(PACKDATA, 'rb') as f:
    for rid, start_sector, n_sectors, fpath in header_checks:
        f.seek(start_sector * SECTOR)
        pack_bytes = f.read(16)
        if os.path.exists(fpath):
            file_bytes = open(fpath, 'rb').read(16)
            match = pack_bytes == file_bytes
            status = "OK" if match else "MISMATCH"
            print(f"  R{rid} @ sector {start_sector}: {status}")
            if not match:
                print(f"    PACKDATA: {pack_bytes.hex()}")
                print(f"    File:     {file_bytes.hex()}")
                errors.append(f"R{rid} header gap MISMATCH")
            # Also check for all-zeros
            f.seek(start_sector * SECTOR)
            region = f.read(n_sectors * SECTOR)
            if all(b == 0 for b in region):
                print(f"  R{rid}: WARNING - entire region is zeroes!")
                warnings.append(f"R{rid} header gap is all-zeroes")
        else:
            print(f"  R{rid}: file not found at {fpath} - SKIP")

print()

# ──────────────────────────────────────────────────
# 2. Build resource file lookup table
# ──────────────────────────────────────────────────
res_files = {}
for path in glob.glob('build/packdata_resources/*.raw'):
    bn = os.path.basename(path)
    idx = int(bn.split('_')[0])
    res_files[idx] = ('build', path)
for path in glob.glob('extracted/packdata_raw/*.raw'):
    bn = os.path.basename(path)
    idx = int(bn.split('_')[0])
    if idx not in res_files:
        res_files[idx] = ('extracted', path)

print(f"Resource files available: {len(res_files)} (build: {sum(1 for v in res_files.values() if v[0]=='build')}, extracted: {sum(1 for v in res_files.values() if v[0]=='extracted')})")
print()

# ──────────────────────────────────────────────────
# 3. Full TOC verification: every resource with sc > 0
# ──────────────────────────────────────────────────
print("=" * 60)
print("FULL TOC VERIFICATION (all resources with sector_count > 0)")
print("=" * 60)

zero_data = 0
missing_file = 0
mismatches = []
size_warnings = []
ok_count = 0
skipped_count = 0

with open(PACKDATA, 'rb') as f:
    for idx, (so, sc, tc) in enumerate(toc):
        if sc == 0:
            skipped_count += 1
            continue

        # Check bounds
        if so + sc > packdata_size // SECTOR + 1:
            errors.append(f"R{idx}: sector_offset={so} + sector_count={sc} exceeds file size")
            continue

        # Read first 16 bytes from PACKDATA
        f.seek(so * SECTOR)
        pack_first16 = f.read(16)

        # Check for all-zeros
        if all(b == 0 for b in pack_first16):
            zero_data += 1
            errors.append(f"R{idx} (type={tc}): first 16 bytes are ALL ZEROS at sector {so}")
            continue

        # Find corresponding file
        if idx in res_files:
            src, fpath = res_files[idx]
            file_data = open(fpath, 'rb').read()
            file_first16 = file_data[:16]

            if pack_first16 != file_first16:
                mismatches.append((idx, tc, so, sc, pack_first16, file_first16, src, fpath))
            else:
                # Verify size alignment: resource should fill sc*SECTOR bytes
                expected_size = sc * SECTOR
                actual_file_size = len(file_data)
                # File data gets padded to sector boundary, so:
                import math
                required_sectors = math.ceil(actual_file_size / SECTOR)
                if required_sectors != sc:
                    size_warnings.append(
                        f"R{idx}: TOC claims {sc} sectors but file needs {required_sectors} "
                        f"sectors ({actual_file_size} bytes)"
                    )
                ok_count += 1
        else:
            missing_file += 1
            # Can't verify content but not necessarily an error

print(f"Results:")
print(f"  OK:              {ok_count}")
print(f"  Skipped (sc=0):  {skipped_count}")
print(f"  All-zeros:       {zero_data}")
print(f"  Mismatches:      {len(mismatches)}")
print(f"  Missing files:   {missing_file}")
print(f"  Size warnings:   {len(size_warnings)}")
print()

if mismatches:
    print("=" * 60)
    print(f"MISMATCHES ({len(mismatches)} total):")
    print("=" * 60)
    for idx, tc, so, sc, pack16, file16, src, fpath in mismatches:
        print(f"  R{idx} (type={tc:02d}) @ sector {so} ({sc} sectors):")
        print(f"    PACKDATA first 16: {pack16.hex()}")
        print(f"    File     first 16: {file16.hex()}")
        print(f"    Source: [{src}] {fpath}")
    print()

if size_warnings:
    print("=" * 60)
    print(f"SIZE WARNINGS ({len(size_warnings)} total):")
    print("=" * 60)
    for w in size_warnings[:20]:
        print(f"  {w}")
    if len(size_warnings) > 20:
        print(f"  ... and {len(size_warnings)-20} more")
    print()

# ──────────────────────────────────────────────────
# 4. Spot-check 10 random resources
# ──────────────────────────────────────────────────
print("=" * 60)
print("SPOT CHECK: 10 random resources")
print("=" * 60)

random.seed(42)
active = [(idx, so, sc, tc) for idx, (so, sc, tc) in enumerate(toc) if sc > 0]
samples = random.sample(active, min(10, len(active)))

with open(PACKDATA, 'rb') as f:
    for idx, so, sc, tc in sorted(samples, key=lambda x: x[0]):
        f.seek(so * SECTOR)
        pack_bytes = f.read(min(32, sc * SECTOR))
        is_zero = all(b == 0 for b in pack_bytes[:16])
        status = "ZEROED" if is_zero else "DATA"

        fpath = None
        if idx in res_files:
            _, fpath = res_files[idx]
            file_bytes = open(fpath, 'rb').read(16)
            match = pack_bytes[:16] == file_bytes
            match_str = "match" if match else "MISMATCH"
        else:
            match_str = "no file to compare"

        print(f"  R{idx:4d} type={tc:02d} @ sector {so:5d} ({sc:4d} sec): [{status}] {match_str}")
        if fpath and pack_bytes[:16] != file_bytes[:16]:
            print(f"    PACKDATA: {pack_bytes[:16].hex()}")
            print(f"    File:     {file_bytes[:16].hex()}")
print()

# ──────────────────────────────────────────────────
# 5. Check for sector-overlap between consecutive entries
# ──────────────────────────────────────────────────
print("=" * 60)
print("OVERLAP CHECK: consecutive TOC entries")
print("=" * 60)

active_sorted = sorted([(so, sc, tc, idx) for idx, (so, sc, tc) in enumerate(toc) if sc > 0])
overlaps = []
for i in range(len(active_sorted) - 1):
    so1, sc1, tc1, idx1 = active_sorted[i]
    so2, sc2, tc2, idx2 = active_sorted[i+1]
    end1 = so1 + sc1
    if end1 > so2:
        overlaps.append((idx1, so1, sc1, idx2, so2, end1 - so2))

if overlaps:
    print(f"OVERLAPS FOUND: {len(overlaps)}")
    for idx1, so1, sc1, idx2, so2, overlap_secs in overlaps:
        print(f"  R{idx1} (sec {so1}+{sc1}) overlaps R{idx2} (sec {so2}) by {overlap_secs} sectors")
else:
    print("  No overlaps found.")
print()

# ──────────────────────────────────────────────────
# 6. Check for gaps between consecutive entries
# ──────────────────────────────────────────────────
print("=" * 60)
print("GAP CHECK: unaccounted sectors between entries")
print("=" * 60)

# Start after header (sector 125)
gap_count = 0
prev_end = 125
for so, sc, tc, idx in active_sorted:
    if so < 125:
        continue  # skip header area
    if so > prev_end:
        gap_secs = so - prev_end
        if gap_secs > 0:
            gap_count += 1
            if gap_count <= 5:
                print(f"  Gap of {gap_secs} sectors between sector {prev_end} and {so} (before R{idx})")
    prev_end = max(prev_end, so + sc)

if gap_count == 0:
    print("  No gaps found — resources are contiguous.")
elif gap_count > 5:
    print(f"  ... and {gap_count - 5} more gaps")
print()

# ──────────────────────────────────────────────────
# 7. Specific resource checks (patched resources)
# ──────────────────────────────────────────────────
print("=" * 60)
print("PATCHED RESOURCE SPOT-CHECKS")
print("=" * 60)

critical_resources = [34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49,
                      989, 990, 1034, 1188, 1193, 1194, 1272, 2100, 2124, 2138, 2654]

with open(PACKDATA, 'rb') as f:
    for idx in critical_resources:
        if idx >= len(toc):
            continue
        so, sc, tc = toc[idx]
        if sc == 0:
            print(f"  R{idx:4d}: sector_count=0 (SKIPPED in TOC)")
            continue
        f.seek(so * SECTOR)
        pack16 = f.read(16)
        is_zero = all(b == 0 for b in pack16)
        if idx in res_files:
            _, fpath = res_files[idx]
            file16 = open(fpath, 'rb').read(16)
            match = pack16 == file16
            print(f"  R{idx:4d} type={tc:02d} @ sec {so:5d} ({sc:3d} sec): {'OK' if match else 'MISMATCH'} {'[ZERO!]' if is_zero else ''}")
            if not match:
                print(f"    PACKDATA: {pack16.hex()}")
                print(f"    File:     {file16.hex()}")
        else:
            print(f"  R{idx:4d} type={tc:02d} @ sec {so:5d} ({sc:3d} sec): {'ZERO!' if is_zero else pack16[:8].hex()+'...'} (no patch file)")
print()

# ──────────────────────────────────────────────────
# Summary
# ──────────────────────────────────────────────────
print("=" * 60)
print("SUMMARY")
print("=" * 60)
total_errors = len(errors) + len(mismatches) + len(overlaps)
print(f"Total errors: {total_errors}")
print(f"  Zero-data resources: {zero_data}")
print(f"  Content mismatches:  {len(mismatches)}")
print(f"  Sector overlaps:     {len(overlaps)}")
if errors:
    print(f"\nOther errors:")
    for e in errors:
        print(f"  {e}")
if total_errors == 0:
    print("ALL CHECKS PASSED")
