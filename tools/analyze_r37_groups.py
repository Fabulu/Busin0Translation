#!/usr/bin/env python3
"""
Analyze ALL R37 groups (0-125) to understand font metrics pollution.

Extracts R37 from PACKDATA.DIG, parses all groups, and reports:
- Group 125's raw content and available byte space
- Which glyph IDs appear in keyboard groups (17-20) vs name groups (21-125)
- Which name groups contain uppercase A-Z (glyph IDs 33-58)
"""
import struct, os

SECTOR = 2048
DIG_PATH = r"C:\Programmieren\wizardrytranslation\extracted\PACKDATA.DIG"

# --- Extract R37 from PACKDATA.DIG TOC ---
with open(DIG_PATH, 'rb') as f:
    toc = f.read(2883 * 12)
    r37_so, r37_sc, r37_type = struct.unpack_from('<III', toc, 37 * 12)
    print(f"R37 TOC: sector_offset={r37_so}, sector_count={r37_sc}, type={r37_type}")
    f.seek(r37_so * SECTOR)
    data = f.read(r37_sc * SECTOR)

print(f"R37 raw size: {len(data)} bytes ({r37_sc} sectors)")

# --- Parse sub-header ---
sub_header = data[:16]
print(f"Sub-header hex: {sub_header.hex()}")
payload_size = struct.unpack_from('<I', sub_header, 4)[0]
print(f"Sub-header payload_size: {payload_size}")

# --- Parse offset table (BE uint32 entries until 0xFFFF as uint16) ---
offset_table = []
pos = 16
while pos + 4 <= len(data):
    check = struct.unpack_from('>H', data, pos)[0]
    if check == 0xFFFF:
        pos += 2  # skip FFFF marker
        break
    val = struct.unpack_from('>I', data, pos)[0]
    offset_table.append(val)
    pos += 4

stream_start = pos
print(f"Offset table entries: {len(offset_table)}")
print(f"Stream starts at byte: {stream_start}")

# --- Parse ALL groups from glyph stream ---
# Each group = sequence of BE uint16 glyph IDs, terminated by 0xFFFF
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
        'end_byte': gpos,  # includes the FFFF terminator
        'data_bytes': gpos - group_start_byte,  # total bytes including FFFF
    })
    # Stop if we've consumed the payload
    if gpos >= stream_start + payload_size:
        break

print(f"Total groups parsed: {len(groups)}")
print()

# --- Group 125 detail ---
if len(groups) > 125:
    g125 = groups[125]
    print("=" * 70)
    print(f"GROUP 125 (last name group):")
    print(f"  Start byte: {g125['start_byte']}")
    print(f"  End byte (after FFFF): {g125['end_byte']}")
    print(f"  Total bytes (including FFFF): {g125['data_bytes']}")
    print(f"  Data bytes (excluding FFFF): {g125['data_bytes'] - 2}")
    print(f"  Glyph count: {len(g125['glyphs'])}")
    print(f"  Glyphs: {[f'0x{g:04X}' for g in g125['glyphs']]}")

    # Raw hex dump
    raw = data[g125['start_byte']:g125['end_byte']]
    print(f"  Raw hex: {raw.hex()}")

    # Space needed for A-Z (26 glyphs) + FFFE + FFFF
    needed = 26 * 2 + 2 + 2  # 26 glyph IDs + FFFE terminator + FFFF group end
    print(f"\n  Space needed for A-Z (26 glyphs + FFFE + FFFF): {needed} bytes")
    print(f"  Available space (current group total): {g125['data_bytes']} bytes")
    print(f"  Fits? {'YES' if g125['data_bytes'] >= needed else 'NO - need more space'}")

    # Also check: space until next group or end of data
    if len(groups) > 126:
        space_to_next = groups[126]['start_byte'] - g125['start_byte']
        print(f"  Space to next group: {space_to_next} bytes")
    else:
        space_to_end = len(data) - g125['start_byte']
        print(f"  Space to end of data: {space_to_end} bytes (last group)")
    print()

# --- Analyze glyph IDs 33-58 (A-Z uppercase) across all groups ---
print("=" * 70)
print("UPPERCASE A-Z (glyph IDs 33-58) ANALYSIS")
print("=" * 70)

# Keyboard groups
print("\n--- KEYBOARD GROUPS (17-20) ---")
keyboard_glyph_ids = set()
for gi in range(17, min(21, len(groups))):
    glyphs = groups[gi]['glyphs']
    # Filter out FFFE (line breaks)
    content_glyphs = [g for g in glyphs if g != 0xFFFE]
    uppercase = [g for g in content_glyphs if 33 <= g <= 58]
    keyboard_glyph_ids.update(content_glyphs)

    label = {17: "Katakana", 18: "Hiragana", 19: "ABC/Alpha", 20: "Symbols"}.get(gi, "?")
    print(f"  Group {gi:3d} ({label}): {len(content_glyphs)} content glyphs, "
          f"{len(uppercase)} uppercase A-Z")
    if uppercase:
        letters = ''.join(chr(g + 32) for g in uppercase)  # glyph 33='A' -> chr(65)
        print(f"           Uppercase: {[f'0x{g:04X}' for g in sorted(uppercase)]}")
        print(f"           Letters:   {letters}")

# Name groups
print("\n--- NAME GROUPS (21-125) ---")
name_polluters = {}  # glyph_id -> list of groups that contain it
all_name_glyph_ids = set()

for gi in range(21, min(126, len(groups))):
    glyphs = groups[gi]['glyphs']
    content_glyphs = [g for g in glyphs if g != 0xFFFE]
    uppercase = [g for g in content_glyphs if 33 <= g <= 58]
    all_name_glyph_ids.update(content_glyphs)

    for g in uppercase:
        if g not in name_polluters:
            name_polluters[g] = []
        name_polluters[g].append(gi)

print(f"\n  Total unique glyph IDs in name groups: {len(all_name_glyph_ids)}")
print(f"  Uppercase A-Z glyphs found in name groups: {len(name_polluters)}")

if name_polluters:
    print("\n  Polluting uppercase glyphs (glyph ID -> letter -> groups containing it):")
    for gid in sorted(name_polluters.keys()):
        letter = chr(gid + 32)  # glyph 33 = 'A' (33+32=65=ord('A'))
        grps = name_polluters[gid]
        last_group = max(grps)
        print(f"    0x{gid:04X} ({letter}): in {len(grps)} groups, "
              f"last occurrence = group {last_group}")

# Which uppercase letters are in keyboard groups but get overwritten by name groups?
keyboard_uppercase = {g for g in keyboard_glyph_ids if 33 <= g <= 58}
name_uppercase = set(name_polluters.keys())
polluted = keyboard_uppercase & name_uppercase
only_keyboard = keyboard_uppercase - name_uppercase
only_names = name_uppercase - keyboard_uppercase

print(f"\n  Uppercase in keyboard groups: {len(keyboard_uppercase)}")
print(f"  Uppercase in name groups:    {len(name_uppercase)}")
print(f"  POLLUTED (in both):          {len(polluted)}")
if polluted:
    letters = ''.join(chr(g+32) for g in sorted(polluted))
    print(f"    Polluted letters: {letters}")
print(f"  Only in keyboards:           {len(only_keyboard)}")
if only_keyboard:
    letters = ''.join(chr(g+32) for g in sorted(only_keyboard))
    print(f"    Letters: {letters}")
print(f"  Only in names:               {len(only_names)}")
if only_names:
    letters = ''.join(chr(g+32) for g in sorted(only_names))
    print(f"    Letters: {letters}")

# --- Dump first few and last few groups for context ---
print("\n" + "=" * 70)
print("GROUP SIZE SUMMARY (all 126 groups)")
print("=" * 70)
for gi in range(min(126, len(groups))):
    g = groups[gi]
    content = [x for x in g['glyphs'] if x != 0xFFFE]
    label = ""
    if gi <= 16:
        label = " (label)"
    elif 17 <= gi <= 20:
        label = " (keyboard)"
    elif 21 <= gi <= 125:
        label = " (name)"
    print(f"  Group {gi:3d}{label}: {g['data_bytes']:4d} bytes, "
          f"{len(content):3d} content glyphs, "
          f"{len(g['glyphs']) - len(content):2d} FFFE breaks")

# --- Check what the offset table says about group positions ---
print("\n" + "=" * 70)
print("OFFSET TABLE vs ACTUAL POSITIONS")
print("=" * 70)
for gi in range(min(10, len(offset_table))):
    ot_offset = offset_table[gi]
    actual_start = groups[gi]['start_byte'] - 16  # relative to after sub-header
    print(f"  Group {gi}: OT offset=0x{ot_offset:04X} ({ot_offset}), "
          f"actual offset from byte 16=0x{actual_start:04X} ({actual_start})")

# Check group 125 offset table entry
if len(offset_table) > 125:
    ot_offset = offset_table[125]
    actual_start = groups[125]['start_byte'] - 16
    print(f"  ...")
    print(f"  Group 125: OT offset=0x{ot_offset:04X} ({ot_offset}), "
          f"actual offset from byte 16=0x{actual_start:04X} ({actual_start})")

# --- Critical question: what happens AFTER group 125? ---
print("\n" + "=" * 70)
print("DATA AFTER GROUP 125")
print("=" * 70)
if len(groups) > 125:
    end_of_125 = groups[125]['end_byte']
    remaining = data[end_of_125:end_of_125 + 64]
    print(f"  End of group 125: byte {end_of_125}")
    print(f"  Next 64 bytes: {remaining.hex()}")
    # Check if there are more groups
    if len(groups) > 126:
        print(f"  Additional groups found: {len(groups) - 126}")
    # Check total payload vs end of last group
    payload_end = stream_start + payload_size
    print(f"  Payload end (stream_start + payload_size): byte {payload_end}")
    print(f"  Padding after group 125 to payload end: {payload_end - end_of_125} bytes")
