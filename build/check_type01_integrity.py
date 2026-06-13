"""
Check type-01 resources (R34-R49) for structural integrity.
Type-01 has: 16-byte header + offset table + glyph data.
The offset table must be self-consistent and not exceed the file size.
"""
import struct, os

os.chdir('C:/Programmieren/wizardrytranslation')
SECTOR = 2048

orig_dir = 'extracted/packdata_raw'
built_dir = 'build/packdata_resources'

for idx in list(range(34, 50)) + [1188, 1272, 2124]:
    for suffix in ['type01', 'type20', 'type15', 'type03']:
        op = os.path.join(orig_dir, f'{idx:04d}_{suffix}.raw')
        bp = os.path.join(built_dir, f'{idx:04d}_{suffix}.raw')
        if os.path.exists(bp):
            break
    else:
        continue

    if not os.path.exists(op):
        continue

    o = open(op, 'rb').read()
    b = open(bp, 'rb').read()

    if o == b:
        continue

    # Parse type-01 header
    b_magic, b_total, b_sub, b_zero = struct.unpack_from('<IIII', b, 0)
    o_magic, o_total, o_sub, o_zero = struct.unpack_from('<IIII', o, 0)

    print(f"\nR{idx:04d} ({suffix}): orig={len(o)} built={len(b)} (+{len(b)-len(o)})")
    print(f"  Header: magic={b_magic}, total=0x{b_total:X}({b_total}), sub=0x{b_sub:X}, zero={b_zero}")
    print(f"  Orig:   magic={o_magic}, total=0x{o_total:X}({o_total}), sub=0x{o_sub:X}, zero={o_zero}")

    if b_total != o_total:
        print(f"  *** total_payload CHANGED: {o_total} -> {b_total}")
    else:
        print(f"  total_payload UNCHANGED (might be stale if data grew)")

    # For type-01 (sub=0x10): offset table follows header
    # Number of entries = first field in header area
    if b_sub == 0x10:
        # Parse offset table
        n_groups = struct.unpack_from('<I', b, 0x10)[0]
        o_n_groups = struct.unpack_from('<I', o, 0x10)[0]
        print(f"  Groups: orig={o_n_groups}, built={n_groups}")

        if n_groups > 0 and 0x14 + n_groups * 4 <= len(b):
            offsets = [struct.unpack_from('<I', b, 0x14 + i*4)[0] for i in range(n_groups)]
            # Check offsets are in bounds
            header_end = 0x14 + n_groups * 4
            for i, off in enumerate(offsets):
                if off > len(b):
                    print(f"  *** Group {i}: offset 0x{off:X} BEYOND FILE END ({len(b)})!")
            # Check total field matches actual data
            last_off = max(offsets) if offsets else 0
            print(f"  Offset range: 0x{min(offsets):X} - 0x{max(offsets):X}")
            print(f"  total_payload ({b_total}) vs file_size ({len(b)})")

    # Check for the R34 type-20 format (item database)
    if suffix == 'type20':
        # Type-20 is a flat data table
        record_size = struct.unpack_from('<I', b, 0x08)[0]
        n_records_hint = b_total // record_size if record_size else 0
        print(f"  Type-20: record_size=0x{record_size:X}, payload indicates ~{n_records_hint} records")

    # Check for R39 type-15 format (equipment)
    if suffix == 'type15':
        # Check sub-structure
        print(f"  Type-15 equipment data")

    # For ALL types: check total_payload vs actual data size
    if b_total + 16 > len(b):
        print(f"  *** CRITICAL: total_payload + 16 = {b_total + 16} > file size {len(b)}!")
    elif b_total + 16 < len(b):
        padding = len(b) - (b_total + 16)
        # Check if padding is all zeros
        pad_data = b[b_total + 16:]
        if pad_data == b'\x00' * len(pad_data):
            print(f"  Padding after payload: {padding} zero bytes")
        else:
            non_zero = sum(1 for x in pad_data if x != 0)
            print(f"  Data after payload end: {padding} bytes ({non_zero} non-zero)")
