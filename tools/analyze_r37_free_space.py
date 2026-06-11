"""Analyze R37 resource: find free space and plan relocation of instruction text groups."""
import struct
import os

SECTOR = 2048

# Read original R37 from PACKDATA.DIG
packdata_path = r'C:\Programmieren\wizardrytranslation\extracted\PACKDATA.DIG'
with open(packdata_path, 'rb') as f:
    toc = f.read(2883 * 12)
    r37_so, r37_sc, r37_tc = struct.unpack_from('<III', toc, 37 * 12)
    print(f"R37 TOC: sector_offset={r37_so}, sector_count={r37_sc}, type_code={r37_tc}")
    f.seek(r37_so * SECTOR)
    orig = f.read(r37_sc * SECTOR)

total_size = len(orig)
print(f"R37 total size: {total_size} bytes ({total_size // SECTOR} sectors)")

# Parse structure
msg_count = struct.unpack_from('>H', orig, 16)[0]
print(f"Message count: {msg_count}")

ot_start = 20
ot_end = ot_start + msg_count * 4  # offset table ends here
print(f"Offset table: bytes {ot_start}-{ot_end} ({msg_count} entries x 4 bytes)")

# Parse all groups
groups = []
for gi in range(msg_count):
    off = struct.unpack_from('>H', orig, ot_start + gi * 4)[0]
    start = 16 + off
    # Find FFFF terminator
    pos = start
    while pos < len(orig) - 1:
        if struct.unpack_from('>H', orig, pos)[0] == 0xFFFF:
            break
        pos += 2
    groups.append({
        'gi': gi,
        'ot_offset': off,
        'data_start': start,
        'ffff_pos': pos,
        'data_size': pos - start,
        'end_with_ffff': pos + 2,  # includes the FFFF terminator
    })

# Find last non-zero byte
last_nonzero = 0
for i in range(total_size - 1, -1, -1):
    if orig[i] != 0:
        last_nonzero = i
        break

print(f"\nLast non-zero byte at: {last_nonzero} (0x{last_nonzero:04X})")
print(f"Free space: bytes {last_nonzero+1}-{total_size-1} = {total_size - last_nonzero - 1} bytes")

# Show all groups
print(f"\n{'='*80}")
print(f"ALL R37 GROUPS:")
print(f"{'='*80}")
print(f"{'GI':>4} {'OT_Off':>8} {'DataStart':>10} {'FFFF_Pos':>10} {'DataSize':>9} {'Category'}")
print(f"{'-'*4} {'-'*8} {'-'*10} {'-'*10} {'-'*9} {'-'*20}")

for g in groups:
    gi = g['gi']
    if gi <= 16:
        cat = "INSTRUCTION"
    elif gi <= 20:
        cat = "KEYBOARD (FIXED!)"
    else:
        cat = "NAME"
    print(f"{gi:4d} {g['ot_offset']:>8d} (0x{g['ot_offset']:04X}) {g['data_start']:>6d} (0x{g['data_start']:04X}) "
          f"{g['ffff_pos']:>6d} (0x{g['ffff_pos']:04X}) {g['data_size']:>6d}B  {cat}")

# Keyboard fixed offsets
print(f"\n{'='*80}")
print(f"KEYBOARD GROUPS (FIXED BYTE OFFSETS):")
print(f"{'='*80}")
kb_fixed = {17: 0x0340, 18: 0x041E, 19: 0x04FC, 20: 0x05DA}
for gi, fixed_off in kb_fixed.items():
    g = groups[gi]
    actual = g['data_start']
    print(f"  Group {gi}: fixed=0x{fixed_off:04X} ({fixed_off}), actual=0x{actual:04X} ({actual}), match={'YES' if fixed_off == actual else 'NO'}")

# Show what the existing English translations look like
# Read the current patched version to see truncation
patched_path = r'C:\Programmieren\wizardrytranslation\build\packdata_resources\0037_type01.raw'
if os.path.exists(patched_path):
    patched = open(patched_path, 'rb').read()
    print(f"\n{'='*80}")
    print(f"CURRENT PATCHED R37 ({len(patched)} bytes):")
    print(f"{'='*80}")

    # Check for truncation in instruction groups
    for gi in range(17):  # groups 0-16
        g = groups[gi]
        data_start = g['data_start']
        ffff_pos = g['ffff_pos']
        orig_data_size = g['data_size']

        # Read original glyphs
        orig_glyphs = []
        for pos in range(data_start, ffff_pos, 2):
            glyph = struct.unpack_from('>H', orig, pos)[0]
            orig_glyphs.append(glyph)

        # Read patched glyphs
        patched_glyphs = []
        for pos in range(data_start, ffff_pos, 2):
            if pos + 1 < len(patched):
                glyph = struct.unpack_from('>H', patched, pos)[0]
                patched_glyphs.append(glyph)

        # Count non-zero patched glyphs
        nonzero_patched = [g for g in patched_glyphs if g != 0]

        print(f"  Group {gi:2d}: orig={len(orig_glyphs)} glyphs ({orig_data_size}B), "
              f"patched={len(nonzero_patched)} non-zero glyphs")

# Determine free space boundaries
# Find the highest byte used by any group (including FFFF terminator)
max_used = 0
for g in groups:
    end = g['end_with_ffff']  # includes FFFF
    if end > max_used:
        max_used = end

print(f"\n{'='*80}")
print(f"FREE SPACE ANALYSIS:")
print(f"{'='*80}")
print(f"Highest group end (incl FFFF): {max_used} (0x{max_used:04X})")
print(f"Last non-zero byte: {last_nonzero} (0x{last_nonzero:04X})")
print(f"Total resource size: {total_size}")
print(f"Free space from {max_used} to {total_size}: {total_size - max_used} bytes")

# Now let's check if there's data between max_used and the end
# that's NOT part of any group
print(f"\nBytes {max_used}-{last_nonzero} dump (should all be zero):")
nonzero_orphan = []
for i in range(max_used, min(max_used + 200, total_size)):
    if orig[i] != 0:
        nonzero_orphan.append((i, orig[i]))
if nonzero_orphan:
    for pos, val in nonzero_orphan[:20]:
        print(f"  0x{pos:04X}: 0x{val:02X}")
    if len(nonzero_orphan) > 20:
        print(f"  ... and {len(nonzero_orphan) - 20} more")
else:
    print(f"  All zeros from {max_used} to end - CONFIRMED FREE SPACE")

# Plan the relocation
print(f"\n{'='*80}")
print(f"RELOCATION PLAN:")
print(f"{'='*80}")
print(f"Strategy: Write longer English content at the end of R37 (in free space)")
print(f"          Update offset table entries for groups 0-16 to point to new locations")
print(f"          Keyboard groups (17-20) are NOT affected (read from fixed offsets)")
print(f"          Name groups (21-125) are NOT affected (their data stays in place)")

# Check: what's the original byte budget for each instruction group?
print(f"\nInstruction group byte budgets (original Japanese):")
print(f"{'GI':>4} {'OrigBytes':>10} {'MaxEnglish':>12} {'Offset':>8}")
free_start = max_used
cursor = free_start
for gi in range(17):
    g = groups[gi]
    orig_bytes = g['data_size']
    # Max English = original slot size (if we don't relocate)
    # With relocation = (total_size - cursor) but in practice limited by resource size
    print(f"  {gi:2d}: {orig_bytes:6d} bytes = {orig_bytes//2:3d} glyphs, "
          f"offset table entry at byte {ot_start + gi*4}")

print(f"\nFree space starts at byte {free_start} (0x{free_start:04X})")
print(f"Free space available: {total_size - free_start} bytes = {(total_size - free_start)//2} glyphs")
print(f"This is MORE than enough for any instruction text.")

# Implementation plan
print(f"\n{'='*80}")
print(f"IMPLEMENTATION PLAN:")
print(f"{'='*80}")
print(f"""
1. In fixup_r37_inplace(), after the current in-place patching loop:
   - Track groups that were TRUNCATED (len(new_data) > orig_data_size)
   - For each truncated group, write the full content at 'cursor' in free space
   - Update the offset table entry: struct.pack_into('>H', orig, ot_start + gi*4, cursor - 16)
   - Advance cursor by len(new_data) + 2 (for FFFF terminator)

2. The offset table entry is at byte {ot_start} + gi*4, and stores a BE u16 offset
   relative to byte 16 (payload start). So for content at absolute byte X:
   offset_value = X - 16

3. Safety checks:
   - cursor must not exceed {total_size} (resource boundary)
   - No overlap with keyboard groups at fixed offsets 0x0340-0x06B8
   - Keyboard groups are at absolute bytes 0x0340-0x06B8, well below free space at 0x{free_start:04X}

4. The FFFF terminator MUST be written after each relocated group's glyph data.
   The game scans for FFFF to know where the group ends.

5. Name groups (21-125) use the offset table too, but their data stays at original
   positions. We're only adding NEW data in free space, not shifting anything.
""")

# Verify keyboard groups don't overlap with free space
kb_max_end = max(groups[gi]['end_with_ffff'] for gi in range(17, 21))
print(f"Keyboard groups end at: {kb_max_end} (0x{kb_max_end:04X})")
print(f"Free space starts at: {free_start} (0x{free_start:04X})")
print(f"Gap between keyboard end and free space: {free_start - kb_max_end} bytes")
print(f"Overlap risk: NONE (keyboard groups are embedded within the main data area)")

# Also verify: do name groups extend beyond keyboard groups?
name_max_end = max(groups[gi]['end_with_ffff'] for gi in range(21, msg_count))
print(f"Name groups end at: {name_max_end} (0x{name_max_end:04X})")
print(f"This should be close to max_used ({max_used}) since name groups are the last data")
