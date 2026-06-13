"""
CRITICAL CHECK: Is the total_payload field in the type-02 header stale?

The header field at offset +4 (total_payload) should reflect the actual
data size. If Section 2 grew but total_payload wasn't updated, the game
would read the wrong amount of data, potentially reading garbage past
the actual resource end into the next resource's data.

On real PS2, the game uses this total_payload (or sector count from TOC)
to know how much data to DMA from disc. If the header says the resource
is smaller than it actually is, the game will load a truncated version.
But the game's VIF/GIF references in Section 1 would point to the NEW
(larger) Section 2 positions, which are now outside the loaded buffer.
THIS WOULD CAUSE A VIF FIFO CRASH!
"""
import struct, os, math

os.chdir('C:/Programmieren/wizardrytranslation')
SECTOR = 2048

orig_dir = 'extracted/packdata_raw'
built_dir = 'build/packdata_resources'

print("Checking total_payload header consistency for all modified type-02 resources:")
print("="*80)

critical_issues = 0

for f in sorted(os.listdir(built_dir)):
    if not f.endswith('.raw') or '_type02' not in f:
        continue
    idx = int(f.split('_')[0])
    bp = os.path.join(built_dir, f)
    op = os.path.join(orig_dir, f)
    if not os.path.exists(op):
        continue

    b = open(bp, 'rb').read()
    o = open(op, 'rb').read()
    if b == o:
        continue

    # Parse headers
    b_magic, b_total, b_sub, b_zero = struct.unpack_from('<IIII', b, 0)
    o_magic, o_total, o_sub, o_zero = struct.unpack_from('<IIII', o, 0)

    # Parse Section 2 info
    b_sec2_size = struct.unpack_from('<I', b, 0x14)[0]
    b_sec2_off = struct.unpack_from('<I', b, 0x18)[0]
    o_sec2_size = struct.unpack_from('<I', o, 0x14)[0]
    o_sec2_off = struct.unpack_from('<I', o, 0x18)[0]

    # The actual data end is sec2_offset + sec2_size + any trailing data
    b_actual_end = b_sec2_off + b_sec2_size
    o_actual_end = o_sec2_off + o_sec2_size

    # Does total_payload match?
    total_changed = b_total != o_total
    sec2_grew = b_sec2_size > o_sec2_size
    sec2_shrank = b_sec2_size < o_sec2_size

    # Calculate what total_payload SHOULD be
    # total_payload seems to be: sec2_offset + sec2_size - header_size(16)
    # OR it could be an independent field
    # Let's check the original to understand the relationship
    o_expected_total = o_sec2_off + o_sec2_size - 16  # hypothesis 1
    o_alt_total = o_sec2_off + o_sec2_size  # hypothesis 2

    # Check the Section 0 fields too
    b_sec0_count = struct.unpack_from('<I', b, 0x10)[0]
    b_sec0_off = struct.unpack_from('<I', b, 0x14)[0]  # Wait, this is sec2_size...

    # Actually let me re-read the structure:
    # +0x00: magic (0)
    # +0x04: total_payload
    # +0x08: sub type marker (0x20)
    # +0x0C: zero
    # +0x10: section 0/2 count
    # +0x14: section 2 size (byte count)
    # +0x18: section 2 offset (from file start)

    if b_total == o_total and sec2_grew:
        # total_payload is STALE!
        print(f"\n  R{idx:04d}: *** STALE total_payload! ***")
        print(f"    total_payload: {b_total} (unchanged from original)")
        print(f"    sec2_size: {o_sec2_size} -> {b_sec2_size} (+{b_sec2_size - o_sec2_size})")
        print(f"    sec2_offset: 0x{b_sec2_off:X}")
        print(f"    actual data ends at: 0x{b_actual_end:X} ({b_actual_end} bytes)")
        print(f"    file size: {len(b)} bytes")

        # What does the game THINK the size is?
        # If total_payload = old total, game reads old amount
        # But Section 1 offsets now point to NEW (larger) Section 2 positions
        # This means the game would try to read glyphs from memory that
        # wasn't loaded -> crash or garbled text
        # BUT: the game loads by SECTOR count from TOC, not by total_payload!
        # So the full file IS loaded. The total_payload field might just be metadata.

        critical_issues += 1

    elif sec2_grew or sec2_shrank:
        print(f"  R{idx:04d}: sec2 {o_sec2_size}->{b_sec2_size} ({b_sec2_size-o_sec2_size:+d}), total={b_total}(orig={o_total})")

# Also check: what is total_payload actually used for?
# Let's see the relationship in original resources
print(f"\n\n{'='*80}")
print("Analyzing total_payload relationship in original type-02 resources:")
print(f"{'='*80}")

import json
manifest = json.load(open('extracted/packdata_resources/manifest.json', encoding='utf-8'))
samples = 0
for entry in manifest:
    idx = entry['index']
    if entry.get('skipped') or entry.get('type_code') != 2:
        continue
    raw_path = os.path.join(orig_dir, f'{idx:04d}_type02.raw')
    if not os.path.exists(raw_path):
        continue

    data = open(raw_path, 'rb').read()
    if len(data) < 0x1C:
        continue

    total_payload = struct.unpack_from('<I', data, 4)[0]
    sub_marker = struct.unpack_from('<I', data, 8)[0]
    sec2_size = struct.unpack_from('<I', data, 0x14)[0]
    sec2_off = struct.unpack_from('<I', data, 0x18)[0]

    if sub_marker != 0x20:
        continue

    # What is total_payload vs actual data?
    actual_data_end = sec2_off + sec2_size
    remainder = len(data) - actual_data_end

    if samples < 10:
        print(f"  R{idx:04d}: total_payload={total_payload}, sec2_end={actual_data_end}, "
              f"file={len(data)}, sec1_size={sec2_off-28}, sec2_size={sec2_size}")
        samples += 1

print(f"\n{'='*80}")
print(f"CRITICAL ISSUES: {critical_issues}")
if critical_issues > 0:
    print("The total_payload field is NOT updated when Section 2 grows.")
    print("If the game uses this to determine how much data to process,")
    print("it will miss the tail end of the grown Section 2.")
    print("\nHowever, the game loads resources by sector count from the TOC,")
    print("so the full file data IS present in RAM. The stale total_payload")
    print("might cause the game's internal parser to use wrong bounds.")
