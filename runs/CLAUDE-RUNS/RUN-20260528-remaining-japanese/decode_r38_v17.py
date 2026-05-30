import struct
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

ISO_PATH = r'C:\Programmieren\wizardrytranslation\build\BUSIN0_EN_v17.iso'
GLYPH_MAP_PATH = r'C:\Programmieren\wizardrytranslation\data\msg_glyph_map.json'
SECTOR = 2048
TOC_ENTRIES = 2883
RESOURCE_INDEX = 38

# Load glyph map
with open(GLYPH_MAP_PATH, 'r', encoding='utf-8') as f:
    raw_map = json.load(f)
glyph_map = {int(k): v for k, v in raw_map.items()}

def glyph_to_ascii(gid):
    if 0 <= gid <= 94:
        return chr(gid + 0x20)
    return None

def decode_glyph(gid):
    asc = glyph_to_ascii(gid)
    if asc is not None:
        return asc, 'ascii'
    if gid in glyph_map:
        return glyph_map[gid], 'map'
    return f'[{gid}]', 'unmapped'

def is_japanese_char(ch):
    cp = ord(ch)
    return (0x3040 <= cp <= 0x309F or
            0x30A0 <= cp <= 0x30FF or
            0x4E00 <= cp <= 0x9FFF or
            0xFF00 <= cp <= 0xFFEF)

# Find PACKDATA.DIG in ISO
with open(ISO_PATH, 'rb') as f:
    f.seek(16 * SECTOR)
    pvd = f.read(SECTOR)
    root_rec = pvd[156:156+34]
    root_extent = struct.unpack_from('<I', root_rec, 2)[0]
    root_size = struct.unpack_from('<I', root_rec, 10)[0]

    f.seek(root_extent * SECTOR)
    root_data = f.read(root_size)

    packdata_extent = None
    pos = 0
    while pos < len(root_data):
        rec_len = root_data[pos]
        if rec_len == 0:
            break
        name_len = root_data[pos + 32]
        name = root_data[pos + 33: pos + 33 + name_len]
        if b'PACKDATA' in name:
            packdata_extent = struct.unpack_from('<I', root_data, pos + 2)[0]
            break
        pos += rec_len

    if packdata_extent is None:
        print("ERROR: PACKDATA.DIG not found in ISO")
        sys.exit(1)

    packdata_base = packdata_extent * SECTOR
    print(f"PACKDATA.DIG at LBA {packdata_extent} (byte offset {packdata_base:,})")

    # Read TOC entry for R38
    f.seek(packdata_base + RESOURCE_INDEX * 12)
    toc_data = f.read(12)
    sector_offset, sector_count, type_code = struct.unpack('<III', toc_data)

    abs_offset = packdata_base + sector_offset * SECTOR
    print(f"R38: sector_offset={sector_offset}, sector_count={sector_count}, type_code={type_code}")
    print(f"R38 absolute offset: {abs_offset:,} (0x{abs_offset:X})")

    # Read sub-header (16 bytes)
    f.seek(abs_offset)
    sub_header = f.read(16)
    z1, payload_size, stride, z2 = struct.unpack('<IIII', sub_header)
    print(f"Sub-header: zero1={z1}, payload_size={payload_size}, stride=0x{stride:X} ({stride}), zero2={z2}")

    # Read payload
    payload = f.read(payload_size)
    print(f"Payload read: {len(payload)} bytes")

# Parse as BE uint16 stream
glyphs = []
for i in range(0, len(payload) - 1, 2):
    glyphs.append(struct.unpack_from('>H', payload, i)[0])

print(f"\nFirst 64 bytes of payload (hex):")
print(' '.join(f'{b:02X}' for b in payload[:64]))
print(f"\nTotal uint16 values in payload: {len(glyphs)}")

ffff_count = glyphs.count(0xFFFF)
print(f"FFFF delimiter count: {ffff_count}")

# Split into messages at FFFF boundaries
messages = []
current_msg = []
for g in glyphs:
    if g == 0xFFFF:
        messages.append(current_msg)
        current_msg = []
    else:
        current_msg.append(g)
if current_msg:
    messages.append(current_msg)

print(f"Message count (FFFF groups): {len(messages)}")

# Decode all messages
output_lines = []

def out(s=""):
    print(s)
    output_lines.append(s)

out(f"{'='*80}")
out(f"R38 FULL MESSAGE DECODE FROM v17 ISO")
out(f"{'='*80}")
out(f"Total messages: {len(messages)}")
out(f"Expected (original R38): 189")
out(f"Count match: {len(messages) == 189}")
out()

issues = []

for idx, msg in enumerate(messages):
    decoded_chars = []
    has_japanese = False
    is_empty = (len(msg) == 0)
    unmapped_glyphs = []
    japanese_glyphs = []
    control_codes = []

    for g in msg:
        if g == 0xFFFE:
            decoded_chars.append('\\n')
            continue
        if 0xFFC0 <= g <= 0xFFFD:
            decoded_chars.append(f'[{g:04X}]')
            control_codes.append(g)
            continue

        ch, source = decode_glyph(g)
        decoded_chars.append(ch)

        if source == 'map' and g >= 95:
            for c in ch:
                if is_japanese_char(c):
                    has_japanese = True
                    japanese_glyphs.append((g, ch))
                    break
        elif source == 'unmapped':
            unmapped_glyphs.append(g)

    decoded_text = ''.join(decoded_chars)

    flag = ""
    if is_empty:
        flag = " [EMPTY]"
        issues.append(f"MSG {idx}: Empty message")
    if has_japanese:
        flag += " [JAPANESE]"
        jp_detail = ', '.join(f'glyph {g}={ch}' for g, ch in japanese_glyphs)
        issues.append(f"MSG {idx}: Japanese glyphs: {jp_detail} | full text: {decoded_text}")
    if unmapped_glyphs:
        flag += " [UNMAPPED]"
        issues.append(f"MSG {idx}: Unmapped glyphs: {unmapped_glyphs} | full text: {decoded_text}")
    if control_codes:
        flag += f" [CTRL]"

    out(f"MSG {idx:3d}{flag}: {decoded_text}")
    out(f"      raw: {' '.join(f'{g:04X}' for g in msg)}")

# Summary
out()
out(f"{'='*80}")
out(f"ISSUES SUMMARY")
out(f"{'='*80}")
out(f"Total issues: {len(issues)}")
for issue in issues:
    out(f"  - {issue}")

# Specific checks
out()
out(f"{'='*80}")
out(f"SPECIFIC CHECKS")
out(f"{'='*80}")

def decode_msg_text(idx):
    if idx >= len(messages):
        return "OUT OF RANGE"
    msg = messages[idx]
    decoded = []
    for g in msg:
        if g == 0xFFFE:
            decoded.append('\\n')
        elif 0xFFC0 <= g <= 0xFFFD:
            decoded.append(f'[{g:04X}]')
        else:
            ch, _ = decode_glyph(g)
            decoded.append(ch)
    return ''.join(decoded)

out("\n--- Stat Labels (MSG 1-7) ---")
for i in range(1, 8):
    out(f"  MSG {i}: {decode_msg_text(i)}")

out("\n--- Gender (MSG 27-28) ---")
for i in range(27, 29):
    out(f"  MSG {i}: {decode_msg_text(i)}")

out("\n--- Alignment (MSG 150-158) ---")
for i in range(150, 159):
    out(f"  MSG {i}: {decode_msg_text(i)}")

out("\n--- Personality Traits (MSG 53-86) ---")
for i in range(53, 87):
    out(f"  MSG {i}: {decode_msg_text(i)}")

# Write output file
out_path = r'C:\Programmieren\wizardrytranslation\runs\CLAUDE-RUNS\RUN-20260528-remaining-japanese\v17_r38_decode.md'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write("# R38 Full Decode from v17 ISO\n\n")
    f.write("```\n")
    for line in output_lines:
        f.write(line + "\n")
    f.write("```\n")

print(f"\nOutput written to: {out_path}")
