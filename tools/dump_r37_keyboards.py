#!/usr/bin/env python3
"""
Dump keyboard grid messages (17-20) from original R37 (type-01 resource).

Type-01 format:
  - 16-byte sub-header
  - Offset table: BE uint32 entries, terminated by 0xFFFF (as uint16)
  - Glyph stream: BE uint16 values
    - 0xFFFF = group separator (end of message)
    - 0xFFFE = line separator (newline within message)
"""
import struct, sys, os

R37_PATH = r"C:\Programmieren\wizardrytranslation\extracted\packdata_resources\0037_type01.bin"

data = open(R37_PATH, 'rb').read()
print(f"R37 file size: {len(data)} bytes")

# Sub-header: first 16 bytes
sub_header = data[:16]
payload_size = struct.unpack_from('<I', sub_header, 4)[0]
print(f"Sub-header payload_size field: {payload_size}")

# Parse offset table starting at byte 16
# Each entry is BE uint32, table ends when we hit 0xFFFF pattern
offset_table = []
pos = 16
while pos + 4 <= len(data):
    # Check if next 2 bytes are 0xFFFF (end of offset table marker)
    check = struct.unpack_from('>H', data, pos)[0]
    if check == 0xFFFF:
        pos += 2  # skip the FFFF marker
        break
    val = struct.unpack_from('>I', data, pos)[0]
    offset_table.append(val)
    pos += 4

stream_start = pos
print(f"Offset table entries: {len(offset_table)}")
print(f"Stream starts at byte: {stream_start}")
print()

# Parse ALL message groups from the glyph stream
# Each group ends with 0xFFFF
messages = []
gpos = stream_start
while gpos + 2 <= len(data):
    msg_glyphs = []
    while gpos + 2 <= len(data):
        g = struct.unpack_from('>H', data, gpos)[0]
        gpos += 2
        if g == 0xFFFF:
            break
        msg_glyphs.append(g)
    messages.append(msg_glyphs)
    # Check if we've hit the end
    if gpos + 2 > len(data):
        break
    # Peek ahead - if nothing but zeros or we're past payload, stop
    if gpos >= stream_start + payload_size:
        break

print(f"Total messages parsed: {len(messages)}")
print()

# Now dump messages 17-20 (0-indexed)
keyboard_names = {17: "Katakana", 18: "Hiragana", 19: "ABC/Alphanumeric", 20: "Symbols"}

for msg_idx in [17, 18, 19, 20]:
    if msg_idx >= len(messages):
        print(f"Message {msg_idx}: NOT FOUND (only {len(messages)} messages)")
        continue

    glyphs = messages[msg_idx]
    name = keyboard_names.get(msg_idx, "???")
    print(f"=== Message {msg_idx}: {name} keyboard ===")
    print(f"Total glyphs (excl. FFFF): {len(glyphs)}")

    # Split by FFFE (line breaks) to show grid rows
    rows = []
    current_row = []
    for g in glyphs:
        if g == 0xFFFE:
            rows.append(current_row)
            current_row = []
        else:
            current_row.append(g)
    if current_row:
        rows.append(current_row)

    print(f"Rows: {len(rows)}")
    for ri, row in enumerate(rows):
        hex_str = ' '.join(f'{g:04X}' for g in row)
        print(f"  Row {ri}: [{len(row)} glyphs] {hex_str}")
    print()

# Specifically identify F and M in message 19
print("=" * 60)
print("Looking for F and M in message 19 (ABC keyboard)...")
if 19 < len(messages):
    glyphs = messages[19]
    rows = []
    current_row = []
    for g in glyphs:
        if g == 0xFFFE:
            rows.append(current_row)
            current_row = []
        else:
            current_row.append(g)
    if current_row:
        rows.append(current_row)

    # The ABC keyboard in the Japanese original has lowercase Latin letters
    # arranged in rows. The japanese field in the translation says:
    # "abcde[65-69] / fghij[70-74] / klmno[75-79] / pqrst[80-84] / uvwxy[85-89] / z[90] ..."
    # So row 0 = a-e (+ something), row 1 = f-j (+ something)
    # 'f' would be first glyph in row 1, 'm' would be 3rd glyph in row 2

    print("\nFull grid with row/col indices:")
    for ri, row in enumerate(rows):
        for ci, g in enumerate(row):
            print(f"  [{ri},{ci}] = 0x{g:04X} ({g})")

    # Try to find what might be 'f' and 'm' - look for sequential patterns
    print("\nLooking for sequential glyph patterns that could be alphabet...")
    all_glyphs = [g for g in glyphs if g != 0xFFFE]
    for i in range(len(all_glyphs) - 1):
        if all_glyphs[i+1] == all_glyphs[i] + 1:
            pass  # sequential

    # Just report what's in the expected positions
    # If the grid is 10 columns wide:
    # Row 0: a b c d e + 5 more
    # Row 1: f g h i j + 5 more  => f = row1[0]
    # Row 2: k l m n o + 5 more  => m = row2[2]
    if len(rows) > 1 and len(rows[1]) > 0:
        print(f"\n'f' should be at row 1, col 0: glyph 0x{rows[1][0]:04X} ({rows[1][0]})")
    if len(rows) > 2 and len(rows[2]) > 2:
        print(f"'m' should be at row 2, col 2: glyph 0x{rows[2][2]:04X} ({rows[2][2]})")
