"""Debug R37 keyboard groups 17-20: compare original vs patched."""
import struct
import os

def read_original_r37(dig_path):
    """Read R37 from the original PACKDATA.DIG using TOC entry 37."""
    with open(dig_path, 'rb') as f:
        # TOC entry 37: 12 bytes per entry
        f.seek(37 * 12)
        sector_offset, sector_count, flags = struct.unpack('<III', f.read(12))
        print(f"[ORIGINAL] TOC entry 37: sector_offset={sector_offset}, sector_count={sector_count}, flags=0x{flags:08X}")
        f.seek(sector_offset * 2048)
        data = f.read(sector_count * 2048)
    return data

def read_patched_r37(path):
    """Read patched R37 from file."""
    with open(path, 'rb') as f:
        return f.read()

def parse_r37(data, label):
    """Parse R37 structure and return group glyph streams."""
    # 16-byte sub-header
    sub_header = data[:16]
    print(f"\n[{label}] Sub-header (16 bytes): {sub_header.hex()}")

    # At offset 16: BE u16 msg_count
    msg_count = struct.unpack('>H', data[16:18])[0]
    print(f"[{label}] msg_count = {msg_count}")
    # Bytes 18-19 often padding
    print(f"[{label}] Bytes 18-19: {data[18:20].hex()}")

    # Offset table starts at offset 20, 4 bytes per entry (BE u16 offset + 2 pad)
    offset_table = []
    for i in range(msg_count):
        pos = 20 + i * 4
        off = struct.unpack('>H', data[pos:pos+2])[0]
        pad = data[pos+2:pos+4]
        offset_table.append(off)

    # Parse glyph streams for each group
    groups = {}
    base = 16  # offsets are relative to after sub-header (offset 16)
    for i in range(msg_count):
        abs_off = base + offset_table[i]
        # Find FFFF terminator
        pos = abs_off
        glyphs = []
        while pos + 1 < len(data):
            val = struct.unpack('>H', data[pos:pos+2])[0]
            if val == 0xFFFF:
                break
            glyphs.append(val)
            pos += 2
        groups[i] = {
            'offset': abs_off,
            'end': pos + 2,  # include FFFF
            'glyphs': glyphs,
            'raw': data[abs_off:pos+2]
        }

    return groups

def display_group(groups, group_id, label):
    """Display a keyboard group with row boundaries."""
    if group_id not in groups:
        print(f"  [{label}] Group {group_id}: NOT FOUND")
        return

    g = groups[group_id]
    print(f"\n  [{label}] Group {group_id}: offset=0x{g['offset']:04X} - 0x{g['end']-1:04X} ({g['end'] - g['offset']} bytes), {len(g['glyphs'])} glyph entries")

    # Split by FFFE into rows
    rows = []
    current_row = []
    for glyph in g['glyphs']:
        if glyph == 0xFFFE:
            rows.append(current_row)
            current_row = []
        else:
            current_row.append(glyph)
    if current_row:
        rows.append(current_row)

    print(f"  Rows: {len(rows)}")
    for ri, row in enumerate(rows):
        hex_str = ' '.join(f'{v:04X}' for v in row)
        markers = []
        if 0x0206 in row:
            markers.append('HAS 0x0206')
        if 0x015D in row:
            markers.append('HAS 0x015D')
        marker_str = f"  <-- {', '.join(markers)}" if markers else ""
        print(f"    Row {ri:2d} ({len(row):2d} glyphs): {hex_str}{marker_str}")

    # Also show raw hex
    print(f"  Raw hex: {g['raw'].hex()}")

def compare_groups(orig_groups, patch_groups, group_id):
    """Compare original vs patched for a group."""
    if group_id not in orig_groups or group_id not in patch_groups:
        print(f"  Group {group_id}: missing in one version")
        return

    og = orig_groups[group_id]
    pg = patch_groups[group_id]

    orig_raw = og['raw']
    patch_raw = pg['raw']

    print(f"\n  === COMPARISON Group {group_id} ===")
    print(f"  Original size: {len(orig_raw)} bytes, Patched size: {len(patch_raw)} bytes")

    if orig_raw == patch_raw:
        print(f"  IDENTICAL - no changes!")
        return

    # Find differences
    min_len = min(len(orig_raw), len(patch_raw))
    diff_ranges = []
    in_diff = False
    diff_start = 0
    for i in range(min_len):
        if orig_raw[i] != patch_raw[i]:
            if not in_diff:
                diff_start = i
                in_diff = True
        else:
            if in_diff:
                diff_ranges.append((diff_start, i))
                in_diff = False
    if in_diff:
        diff_ranges.append((diff_start, min_len))

    print(f"  Changed regions: {len(diff_ranges)}")
    for start, end in diff_ranges:
        print(f"    Bytes {start}-{end-1}: ORIG={orig_raw[start:end].hex()} -> PATCH={patch_raw[start:end].hex()}")

    if len(patch_raw) < len(orig_raw):
        leftover_start = len(patch_raw)
        # Actually the patched file is the same total file, so let's look at it differently
        print(f"  Patched is {len(orig_raw) - len(patch_raw)} bytes shorter")
    elif len(patch_raw) > len(orig_raw):
        print(f"  Patched is {len(patch_raw) - len(orig_raw)} bytes longer")

    # Identify leftover Japanese: bytes in patched that match original and come after the English content
    # Find where FFFE separators stop being useful
    patch_glyphs = pg['glyphs']
    orig_glyphs = og['glyphs']

    # Count rows in patched
    patch_rows = []
    cur = []
    for g in patch_glyphs:
        if g == 0xFFFE:
            patch_rows.append(cur)
            cur = []
        else:
            cur.append(g)
    if cur:
        patch_rows.append(cur)

    # Check which rows in patched match original exactly
    orig_rows = []
    cur = []
    for g in orig_glyphs:
        if g == 0xFFFE:
            orig_rows.append(cur)
            cur = []
        else:
            cur.append(g)
    if cur:
        orig_rows.append(cur)

    print(f"\n  Row-by-row comparison (orig has {len(orig_rows)} rows, patched has {len(patch_rows)} rows):")
    max_rows = max(len(orig_rows), len(patch_rows))
    for ri in range(max_rows):
        o_row = orig_rows[ri] if ri < len(orig_rows) else None
        p_row = patch_rows[ri] if ri < len(patch_rows) else None
        if o_row == p_row:
            status = "SAME"
        elif o_row is None:
            status = "NEW in patched"
        elif p_row is None:
            status = "MISSING in patched"
        else:
            status = "CHANGED"

        o_str = ' '.join(f'{v:04X}' for v in o_row) if o_row else '(none)'
        p_str = ' '.join(f'{v:04X}' for v in p_row) if p_row else '(none)'

        leftover = ""
        if status == "SAME" and ri >= 6:
            leftover = " <-- LEFTOVER JAPANESE?"

        print(f"    Row {ri:2d}: {status}{leftover}")
        if status != "SAME":
            print(f"           ORIG:    {o_str}")
            print(f"           PATCHED: {p_str}")

def main():
    dig_path = r"C:\Programmieren\wizardrytranslation\extracted\PACKDATA.DIG"
    patched_path = r"C:\Programmieren\wizardrytranslation\build\packdata_resources\0037_type01.raw"

    if not os.path.exists(dig_path):
        print(f"ERROR: {dig_path} not found")
        return
    if not os.path.exists(patched_path):
        print(f"ERROR: {patched_path} not found")
        return

    print("="*80)
    print("R37 KEYBOARD GROUP ANALYSIS (Groups 17-20)")
    print("="*80)

    orig_data = read_original_r37(dig_path)
    patch_data = read_patched_r37(patched_path)

    print(f"\nOriginal R37 size: {len(orig_data)} bytes")
    print(f"Patched R37 size: {len(patch_data)} bytes")

    orig_groups = parse_r37(orig_data, "ORIGINAL")
    patch_groups = parse_r37(patch_data, "PATCHED")

    print(f"\nOriginal has {len(orig_groups)} groups, Patched has {len(patch_groups)} groups")

    for gid in [17, 18, 19, 20]:
        print(f"\n{'='*80}")
        print(f"GROUP {gid}")
        print(f"{'='*80}")
        display_group(orig_groups, gid, "ORIGINAL")
        display_group(patch_groups, gid, "PATCHED")
        compare_groups(orig_groups, patch_groups, gid)

if __name__ == '__main__':
    main()
