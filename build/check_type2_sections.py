"""
Deep inspection of type-02 resources that shrank.
The header total_size field is unchanged but the file is smaller.
This means Section 1 (VIF/GIF data) was modified.
Check if the section offsets/sizes are consistent with the actual data.
"""
import struct, os

os.chdir('C:/Programmieren/wizardrytranslation')

SECTOR = 2048

def analyze_type2(name, data):
    """Analyze a type-02 resource structure"""
    if len(data) < 16:
        return

    magic, total_payload, sub_marker, zero = struct.unpack('<IIII', data[:16])
    print(f"\n  {name}: {len(data)} bytes")
    print(f"    Header: magic={magic} total_payload={total_payload} sub=0x{sub_marker:X} zero={zero}")

    # Type-02 format: 16-byte header, then section count, then section offsets
    # sub_marker = 0x20 means type-02
    # After header: the first field is typically the number of sections or entries

    # Read section 0 offset at +16
    if len(data) < 20:
        return

    first_val = struct.unpack('<I', data[16:20])[0]
    print(f"    Value at +16: {first_val} (0x{first_val:X})")

    # For type-02 with sub=0x20:
    # +0: magic (0)
    # +4: total payload size
    # +8: sub type (0x20)
    # +12: zero
    # +16: section 0 entry count
    # +20: section 0 offset (from start)
    # +24: section 0 ???
    # etc.

    # Let's read the section table
    # The structure has 3 sections typically:
    # Each section entry: count(4), offset(4), zero(4)
    n_sections = 3  # typical for type-02

    sections = []
    off = 16
    for s in range(n_sections):
        if off + 12 > len(data):
            break
        count, offset, pad = struct.unpack('<III', data[off:off+12])
        sections.append((count, offset))
        print(f"    Section {s}: count={count} offset=0x{offset:X} ({offset})")
        off += 12

    # Section 0: text/dialogue data
    # Section 1: GS/VIF upload opcodes
    # Section 2: might not exist or be empty

    # Check if section offsets are within bounds
    for s, (count, offset) in enumerate(sections):
        if offset > len(data):
            print(f"    *** Section {s} offset 0x{offset:X} BEYOND FILE END ({len(data)})! ***")
        elif offset > 0:
            # Check what's at that offset
            if offset + 4 <= len(data):
                peek = struct.unpack('<I', data[offset:offset+4])[0]
                print(f"    Section {s} data peek: 0x{peek:08X}")

    # Check total_payload vs actual file size
    expected_end = total_payload + 16  # header + payload
    if expected_end > len(data):
        print(f"    *** CRITICAL: header claims {expected_end} bytes but file is {len(data)} "
              f"(short by {expected_end - len(data)})! ***")
    elif expected_end < len(data):
        print(f"    File has {len(data) - expected_end} bytes of padding after declared end")

# Check the shrunken resources
shrunken = [989, 990, 1034, 1206, 1207, 1212, 1353]

orig_dir = 'extracted/packdata_raw'
built_dir = 'build/packdata_resources'

for idx in shrunken:
    print(f"\n{'='*60}")
    print(f"R{idx:04d}")
    print(f"{'='*60}")

    # Find file
    import glob
    orig_files = glob.glob(f'{orig_dir}/{idx:04d}_type*.raw')
    built_files = glob.glob(f'{built_dir}/{idx:04d}_type*.raw')

    if orig_files:
        orig_data = open(orig_files[0], 'rb').read()
        analyze_type2(f"ORIGINAL ({os.path.basename(orig_files[0])})", orig_data)

    if built_files:
        built_data = open(built_files[0], 'rb').read()
        analyze_type2(f"BUILT ({os.path.basename(built_files[0])})", built_data)

# Also check the resources that the Step 4 (type-2 injection) modifies
# These are the ones with Section 1 opcode patching
print(f"\n\n{'='*60}")
print("Checking ALL type-02 modified resources for section integrity")
print(f"{'='*60}")

for f in sorted(os.listdir(built_dir)):
    if not f.endswith('.raw') or '_type02' not in f:
        continue
    idx = int(f.split('_')[0])
    built_data = open(os.path.join(built_dir, f), 'rb').read()
    orig_path = os.path.join(orig_dir, f)
    if not os.path.exists(orig_path):
        continue
    orig_data = open(orig_path, 'rb').read()

    if built_data == orig_data:
        continue

    # Check header
    b_magic, b_total, b_sub, b_zero = struct.unpack('<IIII', built_data[:16])
    o_magic, o_total, o_sub, o_zero = struct.unpack('<IIII', orig_data[:16])

    # For type-02, check section 1 specifically
    # Section 1 offset is at +28 (section table: 3 entries * 12 bytes starting at +16)
    if len(built_data) >= 40:
        # Section 0
        s0_count, s0_off, s0_pad = struct.unpack('<III', built_data[16:28])
        # Section 1
        s1_count, s1_off, s1_pad = struct.unpack('<III', built_data[28:40])

        # Original section 1
        o_s1_count, o_s1_off, o_s1_pad = struct.unpack('<III', orig_data[28:40])

        issue = ""
        if s1_off > len(built_data):
            issue = f"SEC1 OFF BEYOND EOF (0x{s1_off:X} > {len(built_data)})"
        elif b_total + 16 > len(built_data):
            issue = f"TOTAL_PAYLOAD+16 > FILE ({b_total+16} > {len(built_data)})"

        if issue or s1_off != o_s1_off or b_total != o_total:
            print(f"  R{idx:04d}: total={b_total}(orig={o_total}) "
                  f"sec1_off=0x{s1_off:X}(orig=0x{o_s1_off:X}) "
                  f"file={len(built_data)}(orig={len(orig_data)}) "
                  f"{issue}")
