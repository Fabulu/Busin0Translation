#!/usr/bin/env python3
"""
Analyze R37 keyboard groups 17-20 in detail.
Parse rows (split on FFFE), find marker positions (0x0206, 0x015D),
and compare with English translations.
"""
import struct, json, os

SECTOR = 2048
DIG_PATH = r"C:\Programmieren\wizardrytranslation\extracted\PACKDATA.DIG"
CHUNK_PATH = r"C:\Programmieren\wizardrytranslation\data\translate_chunks\chunk_r37_extra.json"

# --- Extract R37 from PACKDATA.DIG TOC ---
with open(DIG_PATH, 'rb') as f:
    toc = f.read(2883 * 12)
    r37_so, r37_sc, r37_type = struct.unpack_from('<III', toc, 37 * 12)
    print(f"R37 TOC: sector_offset={r37_so}, sector_count={r37_sc}, type={r37_type}")
    f.seek(r37_so * SECTOR)
    data = f.read(r37_sc * SECTOR)

print(f"R37 raw size: {len(data)} bytes")

# --- Parse sub-header ---
sub_header = data[:16]
payload_size = struct.unpack_from('<I', sub_header, 4)[0]
print(f"Sub-header payload_size: {payload_size}")

# --- Parse offset table (BE uint32 entries until 0xFFFF as uint16) ---
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
print(f"Offset table entries: {len(offset_table)}")
print(f"Stream starts at byte: {stream_start}")

# --- Parse ALL groups from glyph stream ---
groups = []
gpos = stream_start
while gpos + 2 <= len(data):
    group_start_byte = gpos
    msg_glyphs = []
    while gpos + 2 <= len(data):
        g = struct.unpack_from('>H', data, gpos)[0]
        gpos += 2
        if g == 0xFFFF:
            break
        msg_glyphs.append(g)
    groups.append({
        'glyphs': msg_glyphs,
        'start_byte': group_start_byte,
        'end_byte': gpos,
    })
    if gpos >= stream_start + payload_size:
        break

print(f"Total groups parsed: {len(groups)}")

# --- Helper: glyph ID to readable label ---
def glyph_label(gid):
    if gid == 0xFFFE:
        return "FFFE(rowsep)"
    if gid == 0x0206:
        return "0206(MALE-BTN)"
    if gid == 0x015D:
        return "015D(FEM-BTN)"
    if gid == 0x0000:
        return "0000(space)"
    # ASCII range: glyph 1=! ... glyph 94=~
    # Actually glyph mapping: 0=space(?), 1='!', ... Let's use the standard
    # R1272 mapping: position 0-94 = ASCII 0x20-0x7E
    if 0 <= gid <= 94:
        ch = chr(gid + 0x20)
        return f"{gid:04X}('{ch}')"
    return f"{gid:04X}"

# --- Analyze groups 17-20 ---
GROUP_NAMES = {17: "Katakana KB", 18: "Hiragana KB", 19: "Alpha KB", 20: "Symbols KB"}

print("\n" + "=" * 80)
print("DETAILED ROW-BY-ROW ANALYSIS OF GROUPS 17-20")
print("=" * 80)

for gi in [17, 18, 19, 20]:
    if gi >= len(groups):
        print(f"\nGroup {gi} not found!")
        continue

    g = groups[gi]
    glyphs = g['glyphs']
    group_start = g['start_byte']
    group_end = g['end_byte']

    print(f"\n{'='*80}")
    print(f"GROUP {gi} ({GROUP_NAMES.get(gi, '?')})")
    print(f"  Byte range: {group_start} - {group_end} (size: {group_end - group_start} bytes)")
    print(f"  Total glyph IDs (incl FFFE): {len(glyphs)}")

    # Split into rows on FFFE
    rows = []
    current_row = []
    for gid in glyphs:
        if gid == 0xFFFE:
            rows.append(current_row)
            current_row = []
        else:
            current_row.append(gid)
    if current_row:
        rows.append(current_row)

    print(f"  Number of rows: {len(rows)}")

    # Track byte offset within group for each glyph
    # Group data starts at group_start, each glyph is 2 bytes (BE uint16)
    byte_offset = 0  # relative to group start
    row_idx = 0
    glyph_idx_in_stream = 0

    # Re-walk glyphs to compute offsets
    marker_offsets = []
    byte_offset = 0
    for idx, gid in enumerate(glyphs):
        if gid == 0x0206 or gid == 0x015D:
            abs_offset = group_start + idx * 2
            rel_offset = idx * 2
            marker_offsets.append((gid, rel_offset, abs_offset))

    # Wait - glyphs list doesn't include the FFFE separators... Actually it does!
    # Let me re-check: the parsing code above appends ALL non-FFFF values
    # So FFFE IS in the glyphs list. Good.

    for row_num, row in enumerate(rows):
        has_markers = any(g in (0x0206, 0x015D) for g in row)
        marker_flag = " *** MARKERS ***" if has_markers else ""
        labels = [glyph_label(g) for g in row]
        print(f"  Row {row_num:2d} ({len(row):2d} glyphs){marker_flag}: {' '.join(labels)}")

    # Report marker positions
    if marker_offsets:
        print(f"\n  MARKER POSITIONS IN GROUP {gi}:")
        for gid, rel_off, abs_off in marker_offsets:
            print(f"    {glyph_label(gid)}: relative offset {rel_off} (0x{rel_off:04X}), "
                  f"absolute offset in R37 data: {abs_off} (0x{abs_off:04X})")
    else:
        print(f"\n  No markers (0x0206 or 0x015D) found in group {gi}")

    # Raw hex dump of last 40 bytes
    tail_start = max(group_start, group_end - 60)
    raw_tail = data[tail_start:group_end]
    print(f"\n  Last {len(raw_tail)} bytes (hex): {raw_tail.hex()}")

# --- Now analyze which rows have markers and what else is in those rows ---
print("\n" + "=" * 80)
print("SUMMARY: MARKER ROWS AND SURROUNDING GLYPHS")
print("=" * 80)

for gi in [17, 18, 19, 20]:
    g = groups[gi]
    glyphs = g['glyphs']

    rows = []
    current_row = []
    for gid in glyphs:
        if gid == 0xFFFE:
            rows.append(current_row)
            current_row = []
        else:
            current_row.append(gid)
    if current_row:
        rows.append(current_row)

    print(f"\nGroup {gi} ({GROUP_NAMES.get(gi, '?')}):")
    for row_num, row in enumerate(rows):
        has_male = 0x0206 in row
        has_female = 0x015D in row
        if has_male or has_female:
            non_marker = [g for g in row if g not in (0x0206, 0x015D)]
            print(f"  Row {row_num}: MALE={has_male}, FEMALE={has_female}")
            print(f"    Markers at positions: ", end="")
            for i, g in enumerate(row):
                if g in (0x0206, 0x015D):
                    print(f"[{i}]={glyph_label(g)} ", end="")
            print()
            print(f"    Other glyphs ({len(non_marker)}): {' '.join(glyph_label(g) for g in non_marker)}")
            print(f"    These 'other' glyphs are the Japanese chars that show as garble")

# --- Compute exact byte offsets for zero-padding strategy ---
print("\n" + "=" * 80)
print("ZERO-PAD STRATEGY: EXACT BYTE OFFSETS OF EACH 0x0206 AND 0x015D")
print("=" * 80)

for gi in [17, 18, 19, 20]:
    g = groups[gi]
    glyphs = g['glyphs']
    group_start = g['start_byte']

    print(f"\nGroup {gi} ({GROUP_NAMES.get(gi, '?')}):")
    print(f"  Group starts at byte {group_start} in R37 data")

    for idx, gid in enumerate(glyphs):
        if gid in (0x0206, 0x015D):
            byte_in_group = idx * 2
            byte_in_r37 = group_start + byte_in_group
            print(f"  {glyph_label(gid)}: glyph index {idx}, "
                  f"byte offset in group = {byte_in_group} (0x{byte_in_group:04X}), "
                  f"byte offset in R37 = {byte_in_r37} (0x{byte_in_r37:04X})")

    # How many total glyphs (including FFFE)?
    print(f"  Total glyph entries (incl FFFE): {len(glyphs)}")
    print(f"  Group total bytes (incl FFFF terminator): {g['end_byte'] - g['start_byte']}")

# --- Part 5: Compare English translations with original ---
print("\n" + "=" * 80)
print("ENGLISH vs ORIGINAL COMPARISON FOR GROUPS 18, 19, 20")
print("=" * 80)

with open(CHUNK_PATH, 'r', encoding='utf-8') as f:
    chunks = json.load(f)

# Build lookup by message number
en_by_msg = {}
for entry in chunks:
    if entry.get('resource') == 37:
        en_by_msg[entry['message']] = entry

for msg_id in [18, 19, 20]:
    print(f"\n--- Message/Group {msg_id} ---")

    # Original
    if msg_id < len(groups):
        g = groups[msg_id]
        orig_glyphs = g['glyphs']
        orig_content = [x for x in orig_glyphs if x != 0xFFFE]
        orig_fffe = sum(1 for x in orig_glyphs if x == 0xFFFE)
        orig_rows_list = []
        cur = []
        for gid in orig_glyphs:
            if gid == 0xFFFE:
                orig_rows_list.append(cur)
                cur = []
            else:
                cur.append(gid)
        if cur:
            orig_rows_list.append(cur)

        print(f"  Original: {len(orig_content)} content glyphs, {orig_fffe} FFFE separators, "
              f"{len(orig_rows_list)} rows")
        print(f"  Original total glyph entries (incl FFFE): {len(orig_glyphs)}")
        print(f"  Original bytes (incl FFFF term): {g['end_byte'] - g['start_byte']}")

        for ri, row in enumerate(orig_rows_list):
            print(f"    Row {ri}: {len(row)} glyphs")

    # English
    if msg_id in en_by_msg:
        en = en_by_msg[msg_id]
        en_text = en['english']
        # Split on " / "
        en_rows = en_text.split(' / ')
        # Remove trailing empty
        while en_rows and en_rows[-1].strip() == '':
            en_rows.pop()

        print(f"  English text: {repr(en_text)}")
        print(f"  English rows (after splitting on ' / '): {len(en_rows)}")

        total_en_glyphs = 0
        for ri, row_text in enumerate(en_rows):
            # Each character becomes a glyph
            n_glyphs = len(row_text)
            total_en_glyphs += n_glyphs
            print(f"    Row {ri}: '{row_text}' -> {n_glyphs} glyphs")

        # Total with FFFE separators
        total_with_fffe = total_en_glyphs + (len(en_rows) - 1) if len(en_rows) > 0 else 0
        print(f"  English total: {total_en_glyphs} content glyphs + {len(en_rows)-1} FFFE = {total_with_fffe} entries")
        print(f"  English bytes (entries * 2 + 2 for FFFF): {total_with_fffe * 2 + 2}")

        # Compare
        if msg_id < len(groups):
            orig_total = len(orig_glyphs)
            diff = orig_total - total_with_fffe
            print(f"\n  COMPARISON: Original has {orig_total} entries, English produces {total_with_fffe}")
            print(f"  Difference: {diff} entries ({diff * 2} bytes)")
            if diff > 0:
                print(f"  -> English is SHORTER by {diff} entries. Trailing rows get stripped.")
                # Check if original has trailing empty-ish rows
                print(f"  Original rows that would be 'extra':")
                for ri in range(len(en_rows), len(orig_rows_list)):
                    row = orig_rows_list[ri]
                    labels = [glyph_label(g) for g in row]
                    print(f"    Original row {ri}: {' '.join(labels)}")
    else:
        print(f"  No English translation found for message {msg_id}")

# --- Group 17 analysis too (Katakana = message 17, but its English is message 17) ---
print("\n--- Message/Group 17 ---")
if 17 < len(groups):
    g = groups[17]
    orig_glyphs = g['glyphs']
    orig_rows_list = []
    cur = []
    for gid in orig_glyphs:
        if gid == 0xFFFE:
            orig_rows_list.append(cur)
            cur = []
        else:
            cur.append(gid)
    if cur:
        orig_rows_list.append(cur)
    print(f"  Original: {len([x for x in orig_glyphs if x != 0xFFFE])} content glyphs, "
          f"{len(orig_rows_list)} rows, {len(orig_glyphs)} total entries")
    for ri, row in enumerate(orig_rows_list):
        has_markers = any(g in (0x0206, 0x015D) for g in row)
        labels = [glyph_label(g) for g in row]
        flag = " ***MARKER***" if has_markers else ""
        print(f"    Row {ri}: {' '.join(labels)}{flag}")

# Check if group 17 has an English translation
if 17 in en_by_msg:
    print(f"  English for msg 17: {repr(en_by_msg[17]['english'])}")
else:
    print(f"  No English translation for message 17 in chunk_r37_extra.json")
    # Check original chunks
    print(f"  (May be in chunk_00-09 or chunk_r37_r48_r49)")

print("\nDone.")
