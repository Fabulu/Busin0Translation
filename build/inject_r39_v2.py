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
# 3. Load translations (message indices match slot positions directly)
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

# Additive fix file: system prompts G90-G96 (v86). NEVER overrides chunk_00-09.
fix_path = 'data/translate_chunks/chunk_r39_sysmsgs_fix.json'
if os.path.exists(fix_path):
    added = 0
    for entry in json.load(open(fix_path, encoding='utf-8')):
        if entry.get('resource') != 39:
            continue
        msg_idx = entry.get('message', entry.get('msg_index'))
        if msg_idx is None or msg_idx in translations:
            continue  # originals are authoritative — additive only
        en = (entry.get('english') or '').strip()
        if en:
            translations[msg_idx] = en
            added += 1
    print(f"Loaded {added} additional R39 sysmsg translations from {fix_path}")

# ---------------------------------------------------------------------------
# 4. Load glyph table
# ---------------------------------------------------------------------------
glyph_table = json.load(open('data/english_glyph_table.json', encoding='utf-8'))

def encode_english(text):
    """Encode English text to a list of BE uint16 glyph IDs.
    ' / ' in text becomes 0xFFFE (line break).
    Each ASCII char maps via glyph_table (essentially ord(ch) - 0x20).

    TRAILING line-break (R39-scoped fix): the pristine R39 prompt/option groups
    (e.g. G88/G89 "Chest"/"Remain", G8/G10 "Is this OK?"/"No") END in a single
    0xFFFE line-break, and the chest magic-detection box height is sized from that
    trailing-0xFFFE count (EXE 0x38DA80 -> jal 0x3A3A10). The authored English
    encodes this break as a TRAILING ' / ' marker. BUT the caller .strip()s the
    string at load time (translations[...] = en.strip()), collapsing a trailing
    ' / ' down to a bare trailing '/' that split(' / ') no longer sees -> it was
    wrongly encoded as a LITERAL slash glyph 0x000F (the stray-slash bug) AND no
    trailing 0xFFFE was emitted (so the box could not grow). We therefore peel a
    trailing '/'-marker here and emit a REAL trailing 0xFFFE instead of a literal
    slash. Mid-string ' / ' breaks are unchanged. This logic lives ONLY in this
    R39 encoder; build_full_english_v2.clean_and_encode (R38 chargen 3-line boxes,
    which rely on their existing trailing-empty strip) is deliberately untouched.
    """
    # An authored trailing ' / ' survives the caller's .strip() as a bare trailing
    # '/' (or, defensively, ' / ' if some path skipped the strip). Peel it off and
    # remember to append one trailing 0xFFFE line-break after encoding the body.
    trailing_break = False
    stripped = text.rstrip()
    if stripped.endswith(' /'):            # ' word /' (un-stripped trailing ' / ')
        text = stripped[:-2]
        trailing_break = True
    elif stripped.endswith('/') and not stripped.endswith('//'):
        # ' word/' — the collapsed form the caller's .strip() produces from ' / '.
        text = stripped[:-1]
        trailing_break = True

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
    if trailing_break:
        glyphs.append(0xFFFE)
    return glyphs

# ---------------------------------------------------------------------------
# 5. In-place replacement: write English glyphs into each message's slot
# ---------------------------------------------------------------------------
out = bytearray(raw)  # full copy — we only modify glyph content bytes
replaced = 0
truncated = 0

for slot_idx, (slot_start, slot_end) in enumerate(messages):
    msg_id = slot_idx  # JSON 'message' field matches slot index directly
    if msg_id not in translations:
        continue

    en_text = translations[msg_id]
    en_glyphs = encode_english(en_text)
    if msg_id == 15:  # issue #28: render "[Name] IDing" with a leading space
        en_glyphs = [0] + en_glyphs  # (JSON strip() eats a leading space, so inject it here)

    slot_capacity = (slot_end - slot_start) // 2  # number of glyph slots available

    if len(en_glyphs) > slot_capacity:
        # PRESERVE A TRAILING 0xFFFE THROUGH TRUNCATION. The fixed-size slot
        # (e.g. msg88 "Chest" cap=5, "Chest"+FFFE=6) may be one cell too small to
        # hold both the full text AND the trailing line-break. The line-break is
        # what the chest box-height sizer counts (EXE 0x38DA80), so it MUST survive
        # — we drop a body glyph instead of the terminator (truncates "Chest"->
        # "Ches" but the box still grows). Naive en_glyphs[:cap] would drop the FFFE.
        keep_trailing_break = en_glyphs and en_glyphs[-1] == 0xFFFE
        if keep_trailing_break:
            body = en_glyphs[:-1][:slot_capacity - 1]
            en_glyphs = body + [0xFFFE]
        else:
            en_glyphs = en_glyphs[:slot_capacity]
        print(f"  WARNING: msg[{msg_id}] truncated -> {len(en_glyphs)} slots "
              f"(cap {slot_capacity}, trailing-LB kept={keep_trailing_break}) "
              f"('{en_text[:40]}')")
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
# 6b. STRAY-SLASH ASSERT (mirrors tests/test_r39_client_cap.py style):
# No translated R39 group may END in a literal slash glyph 0x000F. A trailing
# 0x000F is the fingerprint of the stray-slash bug — an authored trailing ' / '
# line-break marker that the caller's .strip() collapsed to a bare '/' and that
# was then encoded as a literal slash glyph instead of a 0xFFFE line-break. With
# the encoder fix above, every authored trailing-'/' is converted to 0xFFFE, so a
# trailing 0x000F here means the fix regressed. (A literal slash is fine MID-group
# — only a TRAILING one is the bug, since legitimate text never ends in '/'.)
SLASH_GLYPH = int(glyph_table.get('/', 0x0F))
for slot_idx, (slot_start, slot_end) in enumerate(messages):
    if slot_idx not in translations:
        continue
    cells = [struct.unpack_from('>H', out, p)[0] for p in range(slot_start, slot_end, 2)]
    content = [g for g in cells if g != 0x0000]  # ignore trailing null padding
    if content and content[-1] == SLASH_GLYPH:
        raise AssertionError(
            f"R39 msg[{slot_idx}] ('{translations[slot_idx][:40]}') ends in a literal "
            f"slash glyph 0x{SLASH_GLYPH:04X} — the stray-slash bug from a trailing "
            f"' / ' marker that should have become a 0xFFFE line-break. The encoder's "
            f"trailing-'/' -> 0xFFFE conversion regressed.")
print("Stray-slash assert passed: no translated R39 group ends in a literal slash glyph.")

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
