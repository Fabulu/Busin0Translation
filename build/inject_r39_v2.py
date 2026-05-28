"""
R39 equipment/menu text injector (v2) — in-place fixed-length replacement.

Binary layout of 0039_type15.raw (26,624 bytes):
  bytes   0- 15: sub-header (payload_size=2462, stride=240)
  bytes  16-239: 14-entry sequential ID table (16 bytes each)
  bytes 240-627: 97-entry offset table (4 bytes each) — NOT TOUCHED
  bytes 628-631: 4 bytes padding/alignment       — NOT TOUCHED
  bytes 632-2701: glyph stream, 97 FFFF-delimited messages (BE uint16)
  bytes 2702+: sequential data sections           — NOT TOUCHED

Only the glyph content within each FFFF-delimited slot is replaced.
Shorter English text is padded with 0x0000 (null glyphs).
Longer English text is truncated with a warning.
The offset table, sub-header, sequential sections are preserved verbatim.
"""

import struct, json, os, sys

BASE = 'C:/Programmieren/wizardrytranslation'
os.chdir(BASE)

GLYPH_STREAM_START = 632
GLYPH_STREAM_END   = 2702  # exclusive; byte 2701 is the last byte of the last FFFF

# ---------------------------------------------------------------------------
# 1. Load original binary
# ---------------------------------------------------------------------------
raw = bytearray(open('extracted/packdata_raw/0039_type15.raw', 'rb').read())
assert len(raw) == 26624, f"Unexpected R39 size: {len(raw)}"
print(f"R39 original: {len(raw)} bytes")

# ---------------------------------------------------------------------------
# 2. Parse the 97 FFFF-delimited messages in the glyph stream
# ---------------------------------------------------------------------------
messages = []  # list of (start_byte, end_byte) — content only, FFFF excluded
pos = GLYPH_STREAM_START
while pos < GLYPH_STREAM_END:
    msg_start = pos
    while pos < GLYPH_STREAM_END:
        val = struct.unpack_from('>H', raw, pos)[0]
        pos += 2
        if val == 0xFFFF:
            # msg content is [msg_start, pos-2), FFFF is at pos-2
            messages.append((msg_start, pos - 2))
            break
    else:
        # Reached end without finding FFFF — shouldn't happen
        break

print(f"Parsed {len(messages)} FFFF-delimited messages in glyph stream")
assert len(messages) == 97, f"Expected 97 messages, got {len(messages)}"

# ---------------------------------------------------------------------------
# 3. Load translations (message indices are 1-based in the JSON files)
# ---------------------------------------------------------------------------
translations = {}
for ci in range(10):
    path = f'data/translate_chunks/chunk_{ci:02d}_translated.json'
    if not os.path.exists(path):
        continue
    data = json.load(open(path, encoding='utf-8'))
    for entry in data:
        if entry.get('resource') != 39:
            continue
        msg_idx = entry.get('message', entry.get('msg_index'))
        if msg_idx is None:
            continue
        en = (entry.get('english') or '').strip()
        jp = (entry.get('japanese') or '').strip()
        if en and en != jp:
            translations[msg_idx] = en

print(f"Loaded {len(translations)} R39 translations")

# ---------------------------------------------------------------------------
# 4. Load glyph table
# ---------------------------------------------------------------------------
glyph_table = json.load(open('data/english_glyph_table.json', encoding='utf-8'))

def encode_english(text):
    """Encode English text to a list of BE uint16 glyph IDs.
    ' / ' in text becomes 0xFFFE (line break).
    Each ASCII char maps via glyph_table (essentially ord(ch) - 0x20).
    """
    parts = text.split(' / ')
    glyphs = []
    for pi, part in enumerate(parts):
        if pi > 0:
            glyphs.append(0xFFFE)
        for ch in part.strip():
            if ch in glyph_table:
                glyphs.append(int(glyph_table[ch]))
            elif ch.lower() in glyph_table:
                glyphs.append(int(glyph_table[ch.lower()]))
            elif ch == ' ':
                glyphs.append(0)  # space
            else:
                glyphs.append(31)  # '?' fallback
    return glyphs

# ---------------------------------------------------------------------------
# 5. In-place replacement: write English glyphs into each message's slot
# ---------------------------------------------------------------------------
out = bytearray(raw)  # full copy — we only modify glyph content bytes
replaced = 0
truncated = 0

for slot_idx, (slot_start, slot_end) in enumerate(messages):
    msg_id = slot_idx + 1  # translations are 1-indexed
    if msg_id not in translations:
        continue

    en_text = translations[msg_id]
    en_glyphs = encode_english(en_text)

    slot_capacity = (slot_end - slot_start) // 2  # number of glyph slots available

    if len(en_glyphs) > slot_capacity:
        print(f"  WARNING: msg[{msg_id}] truncated: {len(en_glyphs)} glyphs -> {slot_capacity} slots "
              f"('{en_text[:40]}...')")
        en_glyphs = en_glyphs[:slot_capacity]
        truncated += 1

    # Write English glyphs into the slot
    write_pos = slot_start
    for g in en_glyphs:
        struct.pack_into('>H', out, write_pos, g)
        write_pos += 2

    # Pad remaining slot with 0x0000 (null glyphs)
    while write_pos < slot_end:
        struct.pack_into('>H', out, write_pos, 0x0000)
        write_pos += 2

    replaced += 1

print(f"Replaced {replaced} messages ({truncated} truncated)")

# ---------------------------------------------------------------------------
# 6. Sanity checks
# ---------------------------------------------------------------------------
# Verify FFFF delimiters are untouched
ffff_count = 0
for i in range(GLYPH_STREAM_START, GLYPH_STREAM_END, 2):
    if struct.unpack_from('>H', out, i)[0] == 0xFFFF:
        ffff_count += 1
assert ffff_count == 97, f"FFFF count changed! Expected 97, got {ffff_count}"

# Verify everything outside glyph content is unchanged
assert out[:GLYPH_STREAM_START] == raw[:GLYPH_STREAM_START], "Pre-stream bytes changed!"
assert out[GLYPH_STREAM_END:] == raw[GLYPH_STREAM_END:], "Post-stream bytes changed!"
print("Sanity checks passed: OT and sequential sections are untouched")

# ---------------------------------------------------------------------------
# 7. Pad to sector boundary and write
# ---------------------------------------------------------------------------
output = bytes(out)
pad = (2048 - len(output) % 2048) % 2048
output += b'\x00' * pad

os.makedirs('build/packdata_resources', exist_ok=True)
with open('build/packdata_resources/0039_type15.raw', 'wb') as f:
    f.write(output)
print(f"Written {len(output)} bytes to build/packdata_resources/0039_type15.raw")
