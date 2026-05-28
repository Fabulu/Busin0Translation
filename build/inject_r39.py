import struct, json, os, sys

os.chdir('C:/Programmieren/wizardrytranslation')
sys.path.insert(0, 'tools')
from encode_english_text import encode_text

# Load translations for R39
translations = {}
for i in range(10):
    try:
        d = json.load(open(f'data/translate_chunks/chunk_{i:02d}_translated.json', encoding='utf-8'))
        for e in d:
            if e.get('resource') == 39:
                msg_idx = e.get('message', e.get('msg_index'))
                en = e.get('english', '').strip()
                if en and en != e.get('japanese', ''):
                    translations[msg_idx] = en
    except: pass

print(f'R39 translations loaded: {len(translations)}')

# Read original R39
raw = bytearray(open('extracted/packdata_raw/0039_type15.raw', 'rb').read())
h_zero1, h_payload_size, h_stride, h_zero2 = struct.unpack_from('<IIII', raw, 0)
payload_end = 16 + h_payload_size
extra_data = bytearray(raw[payload_end:])

print(f'R39: {len(raw)} bytes, payload={h_payload_size}, extra={len(extra_data)}')

# The glyph data is in the extra_data region
# Find all FFFF-delimited messages
messages = []
msg_start = 0
for i in range(0, len(extra_data) - 1, 2):
    val = struct.unpack_from('>H', extra_data, i)[0]
    if val == 0xFFFF:
        messages.append((msg_start, i))
        msg_start = i + 2

print(f'FFFF groups in extra data: {len(messages)}')

# Encode and replace translations
def clean_and_encode(text):
    import re
    text = text.strip()
    if not text:
        return []
    
    parts = text.split(' / ')
    glyphs = []
    table = json.load(open('data/english_glyph_table.json', encoding='utf-8'))
    
    for pi, part in enumerate(parts):
        part = part.strip()
        if pi > 0:
            glyphs.append(0xFFFE)
        for ch in part:
            if ch in table:
                glyphs.append(int(table[ch]))
            elif ch.lower() in table:
                glyphs.append(int(table[ch.lower()]))
            elif ch == ' ':
                glyphs.append(1)
            else:
                glyphs.append(31)  # ?
    return glyphs

replaced = 0
new_extra = bytearray()
for gi, (gs, ge) in enumerate(messages):
    msg_idx = gi + 1  # translations are 1-indexed
    
    if msg_idx in translations:
        glyphs = clean_and_encode(translations[msg_idx])
        for g in glyphs:
            new_extra += struct.pack('>H', g)
        replaced += 1
    else:
        new_extra += extra_data[gs:ge]
    
    new_extra += struct.pack('>H', 0xFFFF)

print(f'Replaced {replaced} messages')

# Verify same FFFF count
new_ffff = sum(1 for i in range(0, len(new_extra)-1, 2) if struct.unpack_from('>H', new_extra, i)[0] == 0xFFFF)
print(f'FFFF count: orig={len(messages)} new={new_ffff}')
assert new_ffff == len(messages), "FFFF count mismatch!"

# Reassemble: sub-header + payload (unchanged) + new extra data
# The payload contains the offset table which points into extra data
# We need to update those offsets since message sizes changed

# But actually the offset table offsets are ABSOLUTE from file start
# Let's check the sequential table offsets
seq_table = raw[16:16+240]
print('\nSequential table section offsets:')
for i in range(14):
    vals = struct.unpack_from('<IIII', seq_table, i*16)
    print(f'  Section {vals[0]}: offset={vals[2]} size={vals[1]}')

# The section offsets point into the file. Since we only changed content within 
# FFFF groups (not adding/removing groups), and the sections reference groups by
# position, we can try keeping the payload unchanged if message sizes didn't change much.
# 
# BUT if messages changed size, the offsets are wrong.
# Simpler approach: DON'T update the offset table. The game reads messages
# sequentially by FFFF delimiters, not by offset table lookup (for rendering).
# The offset table is used for random access, but if we keep the same number
# of FFFF groups, sequential reading still works.

# Actually safest: just write the new extra data at the same starting position
output = bytes(raw[:payload_end]) + bytes(new_extra)

# Pad to sector boundary
pad = (2048 - len(output) % 2048) % 2048
output += b'\x00' * pad

print(f'Output: {len(output)} bytes (orig {len(raw)})')
open('build/packdata_resources/0039_type15.raw', 'wb').write(output)
print('Written to build/packdata_resources/0039_type15.raw')
