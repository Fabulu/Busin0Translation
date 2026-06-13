"""
Check the shrunken resources (R989, R990, R1034) more carefully.
Their total_payload didn't change, but the file shrank.
The file contains padding after the actual data.
If total_payload points to Section 1 data, and Section 1 didn't change,
then the shrunken Section 0 (text data) just has less padding.
Check if there's any issue with this.
"""
import struct, os

os.chdir('C:/Programmieren/wizardrytranslation')

orig_dir = 'extracted/packdata_raw'
built_dir = 'build/packdata_resources'

for idx in [989, 990, 1034]:
    op = os.path.join(orig_dir, f'{idx:04d}_type02.raw')
    bp = os.path.join(built_dir, f'{idx:04d}_type02.raw')

    o = open(op, 'rb').read()
    b = open(bp, 'rb').read()

    print(f"\nR{idx:04d}: orig={len(o)}, built={len(b)} ({len(b)-len(o):+d})")

    # Header
    o_total = struct.unpack_from('<I', o, 4)[0]
    b_total = struct.unpack_from('<I', b, 4)[0]

    # Section 0 (text data)
    o_sec0_size = struct.unpack_from('<I', o, 0x14)[0]
    o_sec0_off = struct.unpack_from('<I', o, 0x18)[0]
    b_sec0_size = struct.unpack_from('<I', b, 0x14)[0]
    b_sec0_off = struct.unpack_from('<I', b, 0x18)[0]

    print(f"  total_payload: orig={o_total}, built={b_total}")
    print(f"  sec0: orig size={o_sec0_size} off=0x{o_sec0_off:X}")
    print(f"        built size={b_sec0_size} off=0x{b_sec0_off:X}")

    # Section 1 (event script) is at +0x1C
    o_sec1_count = struct.unpack_from('<I', o, 0x1C)[0]
    o_sec1_off = struct.unpack_from('<I', o, 0x20)[0]
    b_sec1_count = struct.unpack_from('<I', b, 0x1C)[0]
    b_sec1_off = struct.unpack_from('<I', b, 0x20)[0]

    print(f"  sec1: orig count={o_sec1_count} off=0x{o_sec1_off:X}")
    print(f"        built count={b_sec1_count} off=0x{b_sec1_off:X}")

    # Check: where does data actually end?
    o_actual_end = o_sec0_off + o_sec0_size
    b_actual_end = b_sec0_off + b_sec0_size

    # The file after this should be zero padding
    o_trail = o[o_actual_end:]
    b_trail = b[b_actual_end:]
    o_nonzero = sum(1 for x in o_trail if x != 0)
    b_nonzero = sum(1 for x in b_trail if x != 0)

    print(f"  actual data end: orig=0x{o_actual_end:X}, built=0x{b_actual_end:X}")
    print(f"  trailing: orig={len(o_trail)} bytes ({o_nonzero} non-zero)")
    print(f"           built={len(b_trail)} bytes ({b_nonzero} non-zero)")

    # CRITICAL: did Section 1 data change?
    # Section 1 is between header (0x28) and sec0_off
    o_sec1 = o[0x28:o_sec0_off]
    b_sec1 = b[0x28:b_sec0_off]
    if o_sec1 == b_sec1:
        print(f"  Section 1: IDENTICAL (no opcode changes)")
    else:
        diff = sum(1 for a, c in zip(o_sec1, b_sec1) if a != c)
        print(f"  Section 1: {diff} bytes differ")

    # CRITICAL: did sec0_off change? If sec0 (text) shrank, the offset should be the same
    # since sec1 is before sec0
    if o_sec0_off != b_sec0_off:
        print(f"  *** sec0 OFFSET CHANGED! This means Section 1 also changed size! ***")
