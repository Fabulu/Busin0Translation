"""
Check what data exists AFTER Section 2 in the built resources.
The inject_and_patch function preserves raw[sec2_end:] as "after_sec2".
If the original had trailing data (Section 0 / display commands),
this would be at a WRONG offset in the built file since Section 2 grew.
"""
import struct, os

os.chdir('C:/Programmieren/wizardrytranslation')

orig_dir = 'extracted/packdata_raw'
built_dir = 'build/packdata_resources'

print("Checking after-Section-2 data alignment:")
print("="*80)

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

    # Get sec2 info for original
    o_sec2_size = struct.unpack_from('<I', o, 0x14)[0]
    o_sec2_off = struct.unpack_from('<I', o, 0x18)[0]
    o_sec2_end = o_sec2_off + o_sec2_size

    # Get sec2 info for built
    b_sec2_size = struct.unpack_from('<I', b, 0x14)[0]
    b_sec2_off = struct.unpack_from('<I', b, 0x18)[0]
    b_sec2_end = b_sec2_off + b_sec2_size

    # What's after Section 2?
    o_after = o[o_sec2_end:]
    b_after = b[b_sec2_end:]

    # Strip trailing zero padding
    o_after_stripped = o_after.rstrip(b'\x00')
    b_after_stripped = b_after.rstrip(b'\x00')

    if len(o_after_stripped) > 0:
        print(f"\n  R{idx:04d}: has {len(o_after_stripped)} non-zero bytes after sec2 in original")
        print(f"    Original sec2 ends at 0x{o_sec2_end:X}, after_sec2={len(o_after)} bytes")
        print(f"    Built sec2 ends at 0x{b_sec2_end:X}, after_sec2={len(b_after)} bytes")

        # Check if after_sec2 data is preserved correctly
        # The after_sec2 data was at orig[o_sec2_end:] and should now be at built[b_sec2_end:]
        # Since Section 2 grew, the after_sec2 data moved forward
        if o_after_stripped == b_after_stripped:
            print(f"    After-sec2 data: PRESERVED correctly (just shifted)")
        else:
            print(f"    After-sec2 data: DIFFERENT!")
            print(f"      Orig first 32: {o_after_stripped[:32].hex()}")
            print(f"      Built first 32: {b_after_stripped[:32].hex()}")

        # This after_sec2 data includes Section 0 display data
        # The original Section 0 offset was at +0x18 in the header... wait
        # Let me re-read the header structure for type-02:
        # +0x00: 00000000 (magic)
        # +0x04: total_payload (Section 1 size hint?)
        # +0x08: 00000020 (type marker)
        # +0x0C: 00000000
        # +0x10: section count or entry count
        # +0x14: section 2 size
        # +0x18: section 2 offset from file start
        #
        # Wait -- what about Section 0?
        # The header at +0x10 shows section count, and +0x14/+0x18 is sec2
        # But where is Section 0 defined?

        # Actually, looking at check_type2_sections.py output:
        # Section 0: count=1 offset=0x51242 (this is the offset for Section 0 data)
        # Section 1: count=1 offset=0x18D0
        # So the section table at +0x10 is:
        # +0x10: sec0_count
        # +0x14: sec0_offset  -- but we've been calling this sec2_size!
        # +0x18: sec0_pad (or something)

        # WAIT. Let me re-examine. The structure from check_type2_sections:
        # Section entries at +16, each 12 bytes:
        # Section 0: count, offset, pad at +16, +20, +24
        # Section 1: count, offset, pad at +28, +32, +36
        # Section 2: count, offset, pad at +40, +44, +48

        # But inject_and_patch reads sec2_size from +0x14 and sec2_offset from +0x18
        # That's +20 and +24... which would be Section 0's offset and pad!

        # THIS IS A BUG! The code reads Section 0's offset as "sec2_size"
        # and Section 0's pad/zero field as "sec2_offset"!

# Let me verify the actual structure
print(f"\n\n{'='*80}")
print("Verifying type-02 header structure:")
print("="*80)

for idx in [1196, 1198, 35]:
    raw_path = f'{orig_dir}/{idx:04d}_type02.raw'
    if not os.path.exists(raw_path):
        continue
    data = open(raw_path, 'rb').read()

    print(f"\n  R{idx:04d} ({len(data)} bytes):")
    print(f"    +0x00: {struct.unpack_from('<I', data, 0x00)[0]:08X} (magic)")
    print(f"    +0x04: {struct.unpack_from('<I', data, 0x04)[0]:08X} (total_payload)")
    print(f"    +0x08: {struct.unpack_from('<I', data, 0x08)[0]:08X} (sub_marker)")
    print(f"    +0x0C: {struct.unpack_from('<I', data, 0x0C)[0]:08X} (zero)")

    # Section table (3 entries x 12 bytes starting at +0x10)
    for s in range(3):
        base = 0x10 + s * 12
        count = struct.unpack_from('<I', data, base)[0]
        off_field = struct.unpack_from('<I', data, base+4)[0]
        pad_field = struct.unpack_from('<I', data, base+8)[0]
        print(f"    Section {s}: count={count}, offset=0x{off_field:X} ({off_field}), pad={pad_field}")

    # What inject_and_patch reads:
    claimed_sec2_size = struct.unpack_from('<I', data, 0x14)[0]
    claimed_sec2_off = struct.unpack_from('<I', data, 0x18)[0]
    print(f"    inject_and_patch reads: sec2_size={claimed_sec2_size}, sec2_off=0x{claimed_sec2_off:X}")

    # Check if what inject_and_patch calls "sec2" actually contains FFFF-delimited groups
    sec_data = data[claimed_sec2_off:claimed_sec2_off + min(claimed_sec2_size, 100)]
    words = [struct.unpack_from('>H', sec_data, i*2)[0] for i in range(min(len(sec_data)//2, 50))]
    ffff_count = words.count(0xFFFF)
    print(f"    At claimed sec2_off: first words = {[f'0x{w:04X}' for w in words[:10]]}")
    print(f"    FFFF count in first 100 bytes: {ffff_count}")
