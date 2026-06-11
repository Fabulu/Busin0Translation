#!/usr/bin/env python3
"""
Investigate why the female name button (0x015D) is inaccessible in the patched R37.
Compare ORIGINAL vs PATCHED keyboard groups 17-20.
Focus on FFFE row separators and marker positions.
"""
import struct

SECTOR = 2048

def parse_r37(data, label):
    """Parse R37 type-01 resource, return list of group dicts."""
    # Sub-header
    msg_count = struct.unpack_from('>H', data, 16)[0]

    # Offset table starts at byte 16; first 4 bytes = msg_count(2) + ?(2), then 4-byte entries
    # Actually let's parse it properly
    # Byte 16-17: first uint16 of offset table area
    # The offset table format: each entry is a BE uint32 (2-byte high + 2-byte low?)
    # Let me use the same approach as the existing scripts

    # Parse offset table (BE uint32 entries until 0xFFFF)
    offset_table = []
    pos = 16
    while pos + 4 <= len(data):
        check = struct.unpack_from('>H', data, pos)[0]
        if check == 0xFFFF:
            pos += 2
            break
        val = struct.unpack_from('>I', data, pos)[0]
        offset_table.append(val)
        pos += 4

    stream_start = pos

    # Parse groups from glyph stream
    groups = []
    gpos = stream_start
    while gpos + 2 <= len(data):
        group_start = gpos
        glyphs = []
        while gpos + 2 <= len(data):
            g = struct.unpack_from('>H', data, gpos)[0]
            gpos += 2
            if g == 0xFFFF:
                break
            glyphs.append(g)
        groups.append({
            'start': group_start,
            'end': gpos,  # byte AFTER the FFFF
            'glyphs': glyphs,
        })
        # Stop if we've gone past reasonable data
        if gpos >= len(data) or len(groups) > 200:
            break

    return groups, stream_start

def dump_group_grid(glyphs, label_prefix=""):
    """Split glyphs on FFFE, show rows."""
    rows = []
    cur = []
    for g in glyphs:
        if g == 0xFFFE:
            rows.append(cur)
            cur = []
        else:
            cur.append(g)
    if cur:
        rows.append(cur)

    for ri, row in enumerate(rows):
        parts = []
        for g in row:
            if g == 0x0206:
                parts.append("MALE")
            elif g == 0x015D:
                parts.append("FEM ")
            elif g == 0x0000:
                parts.append("----")
            elif 0 <= g <= 94:
                ch = chr(g + 0x20)
                parts.append(f" {ch}  ")
            else:
                parts.append(f"{g:04X}")
        print(f"  {label_prefix}Row {ri:2d} [{len(row):2d}]: {' '.join(parts)}")
    return rows

def hex_dump_region(data, start, end, label=""):
    """Hex dump a region as uint16 BE values."""
    print(f"  {label} bytes {start}-{end} ({end-start} bytes):")
    vals = []
    for p in range(start, end, 2):
        if p + 2 <= len(data):
            v = struct.unpack_from('>H', data, p)[0]
            vals.append(f"{v:04X}")
    # Print in groups of 10
    for i in range(0, len(vals), 10):
        chunk = vals[i:i+10]
        offset = start + i * 2
        print(f"    @{offset:5d}: {' '.join(chunk)}")


# =====================================================================
# Load ORIGINAL R37
# =====================================================================
print("=" * 80)
print("LOADING ORIGINAL R37 FROM PACKDATA.DIG")
print("=" * 80)

with open('extracted/PACKDATA.DIG', 'rb') as f:
    toc = f.read(2883 * 12)
    r37_so, r37_sc, r37_type = struct.unpack_from('<III', toc, 37 * 12)
    f.seek(r37_so * SECTOR)
    orig_data = f.read(r37_sc * SECTOR)

orig_groups, orig_stream = parse_r37(orig_data, "ORIGINAL")
print(f"Original R37: {len(orig_data)} bytes, {len(orig_groups)} groups, stream@{orig_stream}")

# =====================================================================
# Load PATCHED R37
# =====================================================================
print("\n" + "=" * 80)
print("LOADING PATCHED R37")
print("=" * 80)

with open('build/packdata_resources/0037_type01.raw', 'rb') as f:
    patch_data = f.read()

patch_groups, patch_stream = parse_r37(patch_data, "PATCHED")
print(f"Patched R37: {len(patch_data)} bytes, {len(patch_groups)} groups, stream@{patch_stream}")

# =====================================================================
# Compare groups 17-20
# =====================================================================
GROUP_NAMES = {17: "Katakana", 18: "Hiragana", 19: "Alpha/ABC", 20: "Symbols"}

for gi in [17, 18, 19, 20]:
    print("\n" + "=" * 80)
    print(f"GROUP {gi} ({GROUP_NAMES.get(gi, '?')})")
    print("=" * 80)

    if gi >= len(orig_groups) or gi >= len(patch_groups):
        print("  NOT FOUND!")
        continue

    og = orig_groups[gi]
    pg = patch_groups[gi]

    print(f"\n  ORIGINAL: bytes {og['start']}-{og['end']} ({og['end']-og['start']} bytes)")
    print(f"  PATCHED:  bytes {pg['start']}-{pg['end']} ({pg['end']-pg['start']} bytes)")

    # Check if byte ranges match (in-place should be same)
    if og['start'] == pg['start'] and og['end'] == pg['end']:
        print(f"  Byte ranges MATCH (good, in-place patch)")
    else:
        print(f"  *** BYTE RANGES DIFFER! ***")

    # --- ORIGINAL grid ---
    print(f"\n  --- ORIGINAL grid ---")
    orig_rows = dump_group_grid(og['glyphs'], "ORIG ")

    # Count markers in original
    orig_male = sum(1 for g in og['glyphs'] if g == 0x0206)
    orig_fem  = sum(1 for g in og['glyphs'] if g == 0x015D)
    print(f"  Original markers: {orig_male}x MALE(0206), {orig_fem}x FEM(015D)")

    # --- PATCHED grid ---
    print(f"\n  --- PATCHED grid ---")
    patch_rows = dump_group_grid(pg['glyphs'], "PATC ")

    # Count markers in patched
    patch_male = sum(1 for g in pg['glyphs'] if g == 0x0206)
    patch_fem  = sum(1 for g in pg['glyphs'] if g == 0x015D)
    print(f"  Patched markers: {patch_male}x MALE(0206), {patch_fem}x FEM(015D)")

    # --- Find where markers are in ORIGINAL ---
    print(f"\n  --- MARKER BYTE OFFSETS ---")
    for idx, g in enumerate(og['glyphs']):
        if g in (0x0206, 0x015D):
            abs_off = og['start'] + idx * 2
            name = "MALE" if g == 0x0206 else "FEM "
            # Which row is this in?
            row_num = 0
            count = 0
            for g2 in og['glyphs'][:idx]:
                if g2 == 0xFFFE:
                    row_num += 1
            print(f"    ORIG {name} at glyph[{idx}] = byte {abs_off} (0x{abs_off:04X}), row {row_num}")

    for idx, g in enumerate(pg['glyphs']):
        if g in (0x0206, 0x015D):
            abs_off = pg['start'] + idx * 2
            name = "MALE" if g == 0x0206 else "FEM "
            row_num = 0
            for g2 in pg['glyphs'][:idx]:
                if g2 == 0xFFFE:
                    row_num += 1
            print(f"    PATC {name} at glyph[{idx}] = byte {abs_off} (0x{abs_off:04X}), row {row_num}")

    # --- Hex dump of the gap (after English content, before FFFF) ---
    # Find where English content ends (last non-zero, non-marker glyph before
    # the zero-padded region)
    print(f"\n  --- HEX DUMP: Full patched group as uint16 BE ---")
    hex_dump_region(patch_data, pg['start'], pg['end'], "PATCHED")

    # --- KEY CHECK: Are FFFE separators present between rows 6-9? ---
    print(f"\n  --- FFFE SEPARATOR CHECK ---")
    # In patched data, find all FFFE positions
    fffe_positions = []
    for idx, g in enumerate(pg['glyphs']):
        if g == 0xFFFE:
            fffe_positions.append(idx)
    print(f"    Patched FFFE at glyph indices: {fffe_positions}")
    print(f"    Total FFFE in patched: {len(fffe_positions)}")

    # Same for original
    orig_fffe = []
    for idx, g in enumerate(og['glyphs']):
        if g == 0xFFFE:
            orig_fffe.append(idx)
    print(f"    Original FFFE at glyph indices: {orig_fffe}")
    print(f"    Total FFFE in original: {len(orig_fffe)}")

    # Check: in the patched version, between the last English FFFE and the markers,
    # are there FFFE separators or just 0000?
    if fffe_positions:
        last_en_fffe = fffe_positions[-1]
        # Check what comes after the last FFFE
        after_last_fffe = pg['glyphs'][last_en_fffe+1:]
        zero_count = sum(1 for g in after_last_fffe if g == 0x0000)
        marker_count = sum(1 for g in after_last_fffe if g in (0x0206, 0x015D))
        fffe_after = sum(1 for g in after_last_fffe if g == 0xFFFE)
        print(f"    After last FFFE (glyph[{last_en_fffe}]): {len(after_last_fffe)} glyphs remain")
        print(f"      0000 (zeros): {zero_count}")
        print(f"      Markers: {marker_count}")
        print(f"      More FFFE: {fffe_after}")

    if orig_fffe:
        last_orig_fffe = orig_fffe[-1]
        # Find which original FFFE's got zero-padded in the patched version
        # The original had FFFE at certain byte offsets. Check those same offsets
        # in the patched data.
        print(f"\n  --- FFFE BYTE OFFSET COMPARISON ---")
        for fffe_idx in orig_fffe:
            byte_off = og['start'] + fffe_idx * 2
            orig_val = struct.unpack_from('>H', orig_data, byte_off)[0]
            patch_val = struct.unpack_from('>H', patch_data, byte_off)[0]
            status = "OK" if patch_val == 0xFFFE else f"DESTROYED -> {patch_val:04X}"
            print(f"    FFFE at glyph[{fffe_idx}] byte {byte_off}: orig={orig_val:04X} patched={patch_val:04X} [{status}]")

print("\n" + "=" * 80)
print("DIAGNOSIS")
print("=" * 80)
print("""
The in-place patcher:
1. Writes English content (rows 0-5) at the start of each group
2. Zero-pads everything from English end to FFFF terminator
3. Re-stamps 0x0206/0x015D markers at their ORIGINAL byte offsets

Problem: Step 2 also destroys the FFFE row separators between rows 6-9.
The markers are at the correct byte offsets, but without FFFE separators
between them, the game may interpret the grid as having fewer rows.

If the game counts rows by FFFE separators:
- Original: 10 rows (9 FFFE separators), male on rows 7-8, female on row 9
- Patched: 6 rows (5 FFFE separators from English), then a blob of 0000s
  with markers scattered in. Row 9 (female) doesn't exist as a row anymore.

The male button might still work because the game navigates to the marker
position by byte offset. But the female button on row 9 is unreachable
because the grid only has 6 rows of FFFE-delimited content.
""")
