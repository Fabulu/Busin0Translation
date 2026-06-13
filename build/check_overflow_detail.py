"""
Check exactly which resources overflow into BSN2_0.DSI territory,
and check if any resource has corrupted VIF/GIF data by examining
type-04 (texture) resources for valid headers.
"""
import struct, os, math

os.chdir('C:/Programmieren/wizardrytranslation')

SECTOR = 2048

# Get original PACKDATA size
orig_size = os.path.getsize('extracted/PACKDATA.DIG')
broken_size = os.path.getsize('build/PACKDATA_broken.DIG')
orig_sectors = orig_size // SECTOR
broken_sectors = broken_size // SECTOR

print(f"Original PACKDATA: {orig_size:,} bytes = {orig_sectors} sectors")
print(f"Broken PACKDATA:   {broken_size:,} bytes = {broken_sectors} sectors")
print(f"Overflow: {broken_size - orig_size:,} bytes = {(broken_size - orig_size) // SECTOR} sectors")

# Read broken TOC
with open('build/PACKDATA_broken.DIG', 'rb') as f:
    # Count entries from manifest
    import json
    manifest = json.load(open('extracted/packdata_resources/manifest.json', encoding='utf-8'))
    n = len(manifest)
    f.seek(0)
    btoc = [struct.unpack('<III', f.read(12)) for _ in range(n)]

# Find last resource
last_idx = 0
last_end = 0
for i, (s, c, t) in enumerate(btoc):
    end = s + c
    if end > last_end:
        last_end = end
        last_idx = i

print(f"\nLast resource: R{last_idx} ends at sector {last_end} ({last_end * SECTOR:,} bytes)")

# Read original TOC for comparison
with open('extracted/PACKDATA.DIG', 'rb') as f:
    otoc = [struct.unpack('<III', f.read(12)) for _ in range(n)]

orig_last_end = max(s + c for s, c, t in otoc)
print(f"Original last sector: {orig_last_end} ({orig_last_end * SECTOR:,} bytes)")

# Find which resources are in the overflow zone
print(f"\n{'='*80}")
print(f"Resources in overflow zone (sector >= {orig_sectors}):")
print(f"{'='*80}")
overflow_resources = []
for i, (s, c, t) in enumerate(btoc):
    end = s + c
    if end > orig_sectors:
        os_s, os_c, os_t = otoc[i]
        overflow_resources.append((i, s, c, t))
        print(f"  R{i:04d} type{t:02d}: sectors {s}-{s+c-1} (end={end}), "
              f"orig sectors {os_s}-{os_s+os_c-1} (end={os_s+os_c})")

print(f"\n{len(overflow_resources)} resources touch the overflow zone")

# Now check: which resources shifted the MOST from their original position?
print(f"\n{'='*80}")
print(f"Top 20 resources with largest sector offset shift:")
print(f"{'='*80}")
shifts = []
for i in range(n):
    os_s, os_c, os_t = otoc[i]
    bs_s, bs_c, bs_t = btoc[i]
    shifts.append((bs_s - os_s, i, os_s, os_c, bs_s, bs_c, os_t))

shifts.sort(key=lambda x: abs(x[0]), reverse=True)
for shift, i, os_s, os_c, bs_s, bs_c, t in shifts[:20]:
    print(f"  R{i:04d} type{t:02d}: shift={shift:+d} sectors, "
          f"size {os_c}->{bs_c} ({bs_c-os_c:+d})")

# Check for VIF-relevant resources: type-04 textures
print(f"\n{'='*80}")
print(f"Checking type-04 (texture) resources for valid headers:")
print(f"{'='*80}")

with open('build/PACKDATA_broken.DIG', 'rb') as f:
    for i, (s, c, t) in enumerate(btoc):
        if t != 4:
            continue
        f.seek(s * SECTOR)
        hdr = f.read(16)
        if len(hdr) < 16:
            print(f"  R{i:04d}: TRUNCATED (only {len(hdr)} bytes)")
            continue
        magic, size, sub, zero = struct.unpack('<IIII', hdr)
        if magic != 0:
            print(f"  R{i:04d}: UNUSUAL magic=0x{magic:08X} (expected 0)")
        # Check if size field is reasonable
        expected_size = c * SECTOR
        if size > expected_size:
            print(f"  R{i:04d}: SIZE FIELD {size} > allocated {expected_size} BYTES!")

# Check for type-29 (R2138 font data)
print(f"\n{'='*80}")
print(f"Checking R2138 (type-29) header:")
print(f"{'='*80}")
with open('build/PACKDATA_broken.DIG', 'rb') as f:
    s, c, t = btoc[2138]
    f.seek(s * SECTOR)
    hdr = f.read(64)
    print(f"  R2138: sector {s}, {c} sectors, type {t}")
    print(f"  Header: {hdr[:32].hex()}")
    print(f"  +32:    {hdr[32:64].hex()}")

# Check: do any resources OVERLAP in the broken PACKDATA?
print(f"\n{'='*80}")
print(f"Checking for resource overlaps:")
print(f"{'='*80}")

# Sort by start sector
entries = [(s, s+c, i, t) for i, (s, c, t) in enumerate(btoc) if c > 0]
entries.sort()
overlap_count = 0
for j in range(len(entries) - 1):
    s1, e1, i1, t1 = entries[j]
    s2, e2, i2, t2 = entries[j+1]
    if e1 > s2:
        overlap_count += 1
        if overlap_count <= 20:
            print(f"  OVERLAP: R{i1:04d} (sectors {s1}-{e1-1}) overlaps R{i2:04d} (sectors {s2}-{e2-1})")

if overlap_count == 0:
    print("  No overlaps detected")
else:
    print(f"  {overlap_count} total overlaps!")

# Final check: are resources that the town loads potentially corrupted?
# The town loads scene scripts, UI resources, etc.
# A VIF FIFO error specifically means bad GS packet data
print(f"\n{'='*80}")
print(f"Checking if any texture/GS resource has grown beyond its original size:")
print(f"{'='*80}")
for i, (s, c, t) in enumerate(btoc):
    os_s, os_c, os_t = otoc[i]
    if t in (4, 29) and c != os_c:  # textures and font data
        print(f"  R{i:04d} type{t:02d}: {os_c} -> {c} sectors ({c-os_c:+d})")
