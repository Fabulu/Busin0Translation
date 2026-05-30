#!/usr/bin/env python3
"""
Extract R38 directly from v17 ISO and do a complete message-by-message decode.
Shows exactly what the game will render for every message.
"""
import struct, json, sys, os, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SECTOR = 2048
ISO_PATH = "C:/Programmieren/wizardrytranslation/build/BUSIN0_EN_v17.iso"
GLYPH_MAP_PATH = "C:/Programmieren/wizardrytranslation/data/msg_glyph_map.json"
OUTPUT_PATH = "C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/v17_r38_full_dump.md"
TOC_ENTRIES = 2883
R38_INDEX = 38

# Load glyph map
with open(GLYPH_MAP_PATH, "r", encoding="utf-8") as f:
    gmap = json.load(f)

# ===== STEP 1: Open ISO, find PACKDATA via PVD/root directory =====
print(f"Opening ISO: {ISO_PATH}")
print(f"ISO size: {os.path.getsize(ISO_PATH):,} bytes")

with open(ISO_PATH, "rb") as iso:
    # Read PVD at sector 16
    iso.seek(16 * SECTOR)
    pvd = iso.read(SECTOR)

    # Root directory entry from PVD
    root_lba = struct.unpack_from('<I', pvd, 158)[0]
    root_size = struct.unpack_from('<I', pvd, 166)[0]
    print(f"Root directory: LBA={root_lba}, size={root_size}")

    # Read root directory
    iso.seek(root_lba * SECTOR)
    root_dir = iso.read(root_size)

    # Find PACKDATA.DIG
    pack_lba = None
    pack_size = None
    pos = 0
    while pos < len(root_dir):
        rec_len = root_dir[pos]
        if rec_len == 0:
            break
        name_len = root_dir[pos + 32]
        name = root_dir[pos + 33:pos + 33 + name_len].decode('ascii', errors='replace')
        file_lba = struct.unpack_from('<I', root_dir, pos + 2)[0]
        file_size = struct.unpack_from('<I', root_dir, pos + 10)[0]
        print(f"  Dir entry: '{name}' LBA={file_lba} size={file_size:,}")
        if 'PACKDATA' in name:
            pack_lba = file_lba
            pack_size = file_size
        pos += rec_len

    if pack_lba is None:
        print("ERROR: PACKDATA.DIG not found in root directory!")
        sys.exit(1)

    print(f"\nPACKDATA.DIG: LBA={pack_lba}, size={pack_size:,}")
    pack_offset = pack_lba * SECTOR

    # ===== STEP 2: Read R38 TOC entry =====
    # TOC is at the start of PACKDATA.DIG: 2883 entries x 12 bytes each
    iso.seek(pack_offset + R38_INDEX * 12)
    toc_entry = iso.read(12)
    r38_sector_off, r38_sector_count, r38_type_code = struct.unpack('<III', toc_entry)
    print(f"\nR38 TOC entry:")
    print(f"  sector_offset = 0x{r38_sector_off:X} ({r38_sector_off})")
    print(f"  sector_count  = {r38_sector_count}")
    print(f"  type_code     = {r38_type_code}")

    # ===== STEP 3: Read R38 raw data =====
    r38_abs_offset = pack_offset + r38_sector_off * SECTOR
    r38_raw_size = r38_sector_count * SECTOR
    iso.seek(r38_abs_offset)
    r38_raw = iso.read(r38_raw_size)
    print(f"\nR38 raw data:")
    print(f"  absolute offset in ISO = 0x{r38_abs_offset:X}")
    print(f"  raw size = {r38_raw_size:,} bytes")

    # ===== STEP 4: Parse sub-header (16 bytes) =====
    h_zero1, h_payload_size, h_stride, h_zero2 = struct.unpack_from('<IIII', r38_raw, 0)
    print(f"\nSub-header:")
    print(f"  zero1        = {h_zero1}")
    print(f"  payload_size = {h_payload_size}")
    print(f"  stride       = {h_stride}")
    print(f"  zero2        = {h_zero2}")

    payload = r38_raw[16:16 + h_payload_size]
    print(f"  payload bytes= {len(payload)}")

# ===== STEP 5: Parse payload: sequential table -> offset table -> glyph stream =====
# Check for sequential table (16-byte entries starting with id=1,2,3...)
def count_sequential_table(data):
    if len(data) < 16:
        return 0
    first4 = struct.unpack_from("<I", data, 0)[0]
    if first4 != 1:
        return 0
    max_entries = min(256, len(data) // 16)
    count = 0
    for e in range(max_entries):
        off = e * 16
        if off + 16 > len(data):
            break
        entry_id = struct.unpack_from("<I", data, off)[0]
        if entry_id == e + 1:
            count = e + 1
        else:
            break
    return count

seq_count = count_sequential_table(payload)
seq_table_size = seq_count * 16
print(f"\nSequential table: {seq_count} entries ({seq_table_size} bytes)")

# Show sequential table entries
if seq_count > 0:
    for i in range(seq_count):
        off = i * 16
        entry = struct.unpack_from("<IIII", payload, off)
        print(f"  Entry {i}: id={entry[0]}, f1=0x{entry[1]:X}, f2=0x{entry[2]:X}, f3=0x{entry[3]:X}")

# After sequential table, find the glyph stream
# Look for first FFFF delimiter in the remaining payload
glyph_region = payload[seq_table_size:]
print(f"\nGlyph region: {len(glyph_region)} bytes (starting at payload offset {seq_table_size})")

# Check for offset table before glyph data
# Many MSG resources have an offset table (array of LE32 offsets) before the glyph stream
# Let's look at the first few 32-bit values
print("\nFirst 32 bytes of glyph region (hex):")
print("  " + " ".join(f"{b:02X}" for b in glyph_region[:32]))
print("First 16 uint16 BE values:")
for i in range(0, min(32, len(glyph_region)), 2):
    val = struct.unpack_from(">H", glyph_region, i)[0]
    print(f"  offset {i}: 0x{val:04X} ({val})")

# Find first FFFF in glyph region
first_ffff = None
for off in range(0, len(glyph_region) - 1, 2):
    val = struct.unpack_from(">H", glyph_region, off)[0]
    if val == 0xFFFF:
        first_ffff = off
        break

print(f"\nFirst FFFF at glyph region offset: {first_ffff}")

# The glyph stream starts at first FFFF
stream = glyph_region[first_ffff:]
n = len(stream) // 2
vals = struct.unpack(f">{n}H", stream[:n*2])

# ===== STEP 6: Parse messages (FFFF-delimited) =====
# FFFF = message delimiter
# FFFE = line break within message
# FFD2 = page break
# Other 0xFFxx = control codes (skip)
# 0-94: ASCII-range glyphs (chr(glyph+0x20))
# 95+: Japanese/special glyphs

messages = []
cur_glyphs = []
cur_controls = []  # track control codes for analysis

for v in vals:
    if v == 0xFFFF:
        if cur_glyphs:
            messages.append((cur_glyphs, cur_controls))
        cur_glyphs = []
        cur_controls = []
    elif v == 0xFFFE:
        cur_glyphs.append(('LF', v))
    elif v == 0xFFD2:
        cur_glyphs.append(('PAGE', v))
    elif v >= 0xFFC0:
        cur_controls.append(v)
    else:
        cur_glyphs.append(('GLYPH', v))

if cur_glyphs:
    messages.append((cur_glyphs, cur_controls))

print(f"\nTotal messages parsed: {len(messages)}")

# ===== STEP 7: Decode each message =====
def decode_glyph(glyph_id):
    """Decode a single glyph ID to display text."""
    # Check glyph map first
    ch = gmap.get(str(glyph_id))
    if ch:
        return ch, True  # mapped
    # ASCII range: 0-94 maps to chr(0x20 + glyph_id) = space through tilde
    if 0 <= glyph_id <= 94:
        return chr(glyph_id + 0x20), True
    # Unmapped
    return f"[JP:{glyph_id}]", False

def decode_message(glyphs):
    """Decode a full message (list of (type, value) tuples)."""
    parts = []
    total = 0
    english = 0
    japanese = 0
    for typ, val in glyphs:
        if typ == 'LF':
            parts.append("[LF]")
        elif typ == 'PAGE':
            parts.append("[PAGE]")
        elif typ == 'GLYPH':
            total += 1
            ch, mapped = decode_glyph(val)
            parts.append(ch)
            # Classify: ASCII printable range = English
            if 0 <= val <= 94:
                english += 1
            else:
                japanese += 1
        else:
            parts.append(f"[CTRL:0x{val:04X}]")
    return "".join(parts), total, english, japanese

# Decode all messages
decoded_msgs = []
grand_total = 0
grand_english = 0
grand_japanese = 0

for i, (glyphs, controls) in enumerate(messages):
    text, total, eng, jpn = decode_message(glyphs)
    decoded_msgs.append({
        'index': i,
        'text': text,
        'total_glyphs': total,
        'english': eng,
        'japanese': jpn,
        'controls': controls,
        'raw_glyphs': [(t, v) for t, v in glyphs if t == 'GLYPH']
    })
    grand_total += total
    grand_english += eng
    grand_japanese += jpn

# ===== Print summary =====
print(f"\n{'='*70}")
print(f"R38 COMPLETE DECODE SUMMARY")
print(f"{'='*70}")
print(f"Total messages:  {len(decoded_msgs)}")
print(f"Total glyphs:    {grand_total}")
print(f"English glyphs:  {grand_english} ({grand_english/grand_total*100:.1f}%)" if grand_total else "")
print(f"Japanese glyphs: {grand_japanese} ({grand_japanese/grand_total*100:.1f}%)" if grand_total else "")

# Print each message
for msg in decoded_msgs:
    status = "EN" if msg['japanese'] == 0 else "JP" if msg['english'] == 0 else "MIX"
    ctrl_str = ""
    if msg['controls']:
        ctrl_str = f"  ctrls=[{','.join(f'0x{c:04X}' for c in msg['controls'])}]"
    print(f"MSG {msg['index']:3d} [{status:3s}] ({msg['english']:2d}E/{msg['japanese']:2d}J): {msg['text']}{ctrl_str}")

# ===== STEP 8: Write complete dump to markdown file =====
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

with open(OUTPUT_PATH, "w", encoding="utf-8") as out:
    out.write("# R38 Complete Decode from v17 ISO\n\n")
    out.write(f"**Source:** `{ISO_PATH}`\n\n")
    out.write(f"**Extraction method:** Direct ISO read via PVD -> root dir -> PACKDATA.DIG -> TOC entry 38\n\n")
    out.write(f"## Summary\n\n")
    out.write(f"| Metric | Value |\n")
    out.write(f"|--------|-------|\n")
    out.write(f"| Total messages | {len(decoded_msgs)} |\n")
    out.write(f"| Total glyphs | {grand_total} |\n")
    out.write(f"| English glyphs | {grand_english} ({grand_english/grand_total*100:.1f}%) |\n" if grand_total else "")
    out.write(f"| Japanese glyphs | {grand_japanese} ({grand_japanese/grand_total*100:.1f}%) |\n" if grand_total else "")

    en_msgs = sum(1 for m in decoded_msgs if m['japanese'] == 0)
    jp_msgs = sum(1 for m in decoded_msgs if m['english'] == 0 and m['japanese'] > 0)
    mix_msgs = sum(1 for m in decoded_msgs if m['english'] > 0 and m['japanese'] > 0)
    out.write(f"| All-English messages | {en_msgs} |\n")
    out.write(f"| All-Japanese messages | {jp_msgs} |\n")
    out.write(f"| Mixed messages | {mix_msgs} |\n")

    # === Critical sections ===
    sections = [
        ("Stat Labels (MSG 1-7)", 1, 7),
        ("Field Labels (MSG 8-16)", 8, 16),
        ("Male/Female (MSG 27-28)", 27, 28),
        ("Race Names (MSG 29-34)", 29, 34),
        ("Class Names (MSG 35-52)", 35, 52),
        ("Personality Traits (MSG 53-86)", 53, 86),
        ("Descriptions (MSG 87-148)", 87, 148),
        ("Alignment Labels (MSG 150-158)", 150, 158),
    ]

    out.write(f"\n## Critical Sections\n\n")
    for section_name, start, end in sections:
        out.write(f"\n### {section_name}\n\n")
        out.write(f"| MSG | Status | Text | Raw Glyph IDs |\n")
        out.write(f"|-----|--------|------|----------------|\n")
        for msg in decoded_msgs:
            if start <= msg['index'] <= end:
                status = "EN" if msg['japanese'] == 0 else "JP" if msg['english'] == 0 else "MIX"
                emoji = "OK" if status == "EN" else "JAPANESE" if status == "JP" else "MIXED"
                raw_ids = [v for t, v in msg['raw_glyphs']]
                raw_str = str(raw_ids) if len(raw_ids) <= 20 else str(raw_ids[:20]) + "..."
                text_escaped = msg['text'].replace("|", "\\|")
                out.write(f"| {msg['index']} | {emoji} | `{text_escaped}` | `{raw_str}` |\n")

    # === Full dump ===
    out.write(f"\n## Complete Message Dump\n\n")
    out.write(f"| MSG | Status | E | J | Rendered Text |\n")
    out.write(f"|-----|--------|---|---|---------------|\n")
    for msg in decoded_msgs:
        status = "EN" if msg['japanese'] == 0 else "JP" if msg['english'] == 0 else "MIX"
        text_escaped = msg['text'].replace("|", "\\|")
        out.write(f"| {msg['index']} | {status} | {msg['english']} | {msg['japanese']} | `{text_escaped}` |\n")

    # === Messages still containing Japanese ===
    out.write(f"\n## Messages Still Containing Japanese\n\n")
    out.write(f"These messages have at least one glyph with ID >= 95 (outside ASCII range):\n\n")
    out.write(f"| MSG | Text | Japanese Glyph IDs |\n")
    out.write(f"|-----|------|--------------------|\n")
    jp_detail_count = 0
    for msg in decoded_msgs:
        if msg['japanese'] > 0:
            jp_detail_count += 1
            jp_ids = [v for t, v in msg['raw_glyphs'] if v >= 95]
            text_escaped = msg['text'].replace("|", "\\|")
            out.write(f"| {msg['index']} | `{text_escaped}` | `{jp_ids}` |\n")

    if jp_detail_count == 0:
        out.write(f"| - | None! All messages are English | - |\n")

    out.write(f"\n## Raw Glyph IDs for All Messages\n\n")
    out.write("```\n")
    for msg in decoded_msgs:
        raw_ids = [v for t, v in msg['raw_glyphs']]
        lf_positions = [j for j, (t, v) in enumerate(messages[msg['index']][0]) if t == 'LF']
        page_positions = [j for j, (t, v) in enumerate(messages[msg['index']][0]) if t == 'PAGE']
        extra = ""
        if lf_positions:
            extra += f"  LF@{lf_positions}"
        if page_positions:
            extra += f"  PAGE@{page_positions}"
        out.write(f"MSG {msg['index']:3d}: {raw_ids}{extra}\n")
    out.write("```\n")

print(f"\nOutput written to: {OUTPUT_PATH}")
