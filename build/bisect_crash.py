"""
Bisect which modified resources cause the VIF crash.
Build PACKDATAs with different subsets of modifications enabled.
Group resources by category for efficient bisecting.
"""
import struct, json, os, math, shutil

os.chdir('C:/Programmieren/wizardrytranslation')

SECTOR = 2048
built_dir = 'build/packdata_resources'
orig_dir = 'extracted/packdata_raw'

# Identify ALL modified resources (excluding R1272 which works)
modified = {}
for f in sorted(os.listdir(built_dir)):
    if not f.endswith('.raw'):
        continue
    bp = os.path.join(built_dir, f)
    op = os.path.join(orig_dir, f)
    if not os.path.exists(op):
        continue
    b = open(bp, 'rb').read()
    o = open(op, 'rb').read()
    if b != o:
        idx = int(f.split('_')[0])
        modified[idx] = {
            'file': f,
            'built_data': b,
            'orig_data': o,
            'size_delta': len(b) - len(o),
        }

print(f"Total modified resources (excluding R1272): {len(modified) - (1272 in modified)}")

# Group by category
groups = {
    'type1_msg (R34-R49)': [i for i in modified if 34 <= i <= 49],
    'type2_dialogue (R989-R1034)': [i for i in modified if 989 <= i <= 1034],
    'type2_scenes (R1193-R1213)': [i for i in modified if 1193 <= i <= 1213],
    'type2_extra (R1347-R1355)': [i for i in modified if 1347 <= i <= 1355],
    'font_R1188': [i for i in modified if i == 1188],
    'font_R1272': [i for i in modified if i == 1272],
    'header_R2100': [i for i in modified if i == 2100],
    'msg_R2124': [i for i in modified if i == 2124],
    'font_R2138': [i for i in modified if i == 2138],
    'data_R2654': [i for i in modified if i == 2654],
}

# Check all resources are accounted for
accounted = set()
for name, indices in groups.items():
    accounted.update(indices)
    if indices:
        total_delta = sum(modified[i]['size_delta'] for i in indices)
        print(f"  {name}: {len(indices)} resources, total size delta: {total_delta:+d}")

unaccounted = set(modified.keys()) - accounted
if unaccounted:
    print(f"\n  UNACCOUNTED: {sorted(unaccounted)}")

# The key insight: the overflow is 86 sectors = 176,128 bytes
# Resources that GREW contribute to this overflow
# Resources that SHRANK offset it
# But the crash is VIF FIFO which is about GS data, not just overflow

# Let's identify which groups contribute to overflow
print(f"\n{'='*80}")
print("Size contribution per group:")
print(f"{'='*80}")
for name, indices in groups.items():
    if not indices:
        continue
    grew = sum(max(0, modified[i]['size_delta']) for i in indices)
    shrank = sum(min(0, modified[i]['size_delta']) for i in indices)
    print(f"  {name}: grew={grew:+d}, shrank={shrank:+d}, net={grew+shrank:+d}")

# Now let's check R989 specifically since it SHRANK a lot (-75776)
# and R1034 shrank -59392. These could cause issues if the game
# expects them at specific sizes
print(f"\n{'='*80}")
print("Investigating shrunken resources:")
print(f"{'='*80}")
for idx in sorted(modified.keys()):
    if modified[idx]['size_delta'] < 0:
        m = modified[idx]
        print(f"  R{idx:04d}: {len(m['orig_data'])} -> {len(m['built_data'])} ({m['size_delta']:+d})")
        # Check headers
        orig_hdr = struct.unpack('<IIII', m['orig_data'][:16])
        built_hdr = struct.unpack('<IIII', m['built_data'][:16])
        print(f"    Original header: magic={orig_hdr[0]} size={orig_hdr[1]} sub={orig_hdr[2]} zero={orig_hdr[3]}")
        print(f"    Built header:    magic={built_hdr[0]} size={built_hdr[1]} sub={built_hdr[2]} zero={built_hdr[3]}")
        # The size field in the header should match the actual data
        if built_hdr[1] > len(m['built_data']):
            print(f"    *** HEADER SIZE {built_hdr[1]} > FILE SIZE {len(m['built_data'])}! ***")

# Also check ALL modified resources for header consistency
print(f"\n{'='*80}")
print("Checking ALL modified resources for header size consistency:")
print(f"{'='*80}")
problems = 0
for idx in sorted(modified.keys()):
    m = modified[idx]
    data = m['built_data']
    if len(data) < 16:
        continue
    hdr = struct.unpack('<IIII', data[:16])
    magic, size_field, sub_count, zero = hdr
    # size_field typically is the total payload size (data after header)
    # For type-01: 16-byte header + offset table + data
    # For type-02: 16-byte header + sections
    # size_field should not exceed file size
    if size_field > len(data):
        print(f"  R{idx:04d}: HEADER SIZE MISMATCH! header says {size_field}, file is {len(data)}")
        problems += 1
    # Check if the declared size + 16 exceeds file size
    if size_field + 16 > len(data) and size_field < 0x10000000:  # reasonable limit
        pass  # Many formats don't include the 16-byte header in size

if problems == 0:
    print("  No header size mismatches found")

# Check for the specific pattern that could cause VIF FIFO:
# If a type-02 resource has corrupted section 1 opcodes that
# contain VIF/GIF upload commands with wrong sizes
print(f"\n{'='*80}")
print("Checking type-02 resources for Section 1 opcode integrity:")
print(f"{'='*80}")

for idx in sorted(modified.keys()):
    m = modified[idx]
    data = m['built_data']
    if len(data) < 16:
        continue
    hdr = struct.unpack('<IIII', data[:16])
    magic, total_size, sub_count_raw, zero = hdr

    # sub_count for type-02 is 0x20 (32)
    sub_count = sub_count_raw & 0xFFFF
    if sub_count != 0x20:
        continue  # Not type-02 format

    # Type-02 has sections. Section 1 contains GS upload opcodes
    # Check if section 1 data looks reasonable
    if len(data) < 32:
        continue

    # Read section table (after 16-byte header)
    n_sections = sub_count_raw >> 16 if sub_count_raw >> 16 else struct.unpack('<I', data[16:20])[0]

    # Actually let's look at the type-02 format more carefully
    # The header at +8 gives the sub-count (0x20 = type-02 marker)
    # Then there's a section offset table

    # For now, just flag if there are suspicious patterns
    # VIF UNPACK commands start with bytes 0x60-0x7F at offset +3 of a VIF word
    vif_count = 0
    for off in range(0, min(len(data), 1024), 4):
        word = struct.unpack('<I', data[off:off+4])[0]
        cmd = (word >> 24) & 0xFF
        if cmd >= 0x60 and cmd <= 0x7F:
            vif_count += 1
    if vif_count > 5:
        print(f"  R{idx:04d}: {vif_count} VIF UNPACK-like commands in first 1KB")
