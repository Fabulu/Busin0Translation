import struct, json, sys
sys.stdout.reconfigure(encoding='utf-8')

# Parse R38 .bin (payload only, no raw wrapper)
with open('C:/Programmieren/wizardrytranslation/extracted/packdata_resources/0038_type01.bin', 'rb') as f:
    data = f.read()

with open('C:/Programmieren/wizardrytranslation/data/msg_glyph_map.json', 'r', encoding='utf-8') as f:
    gmap = json.load(f)

# Find first FFFF (start of glyph stream)
first_ffff = None
for off in range(0, len(data) - 1, 2):
    val = struct.unpack_from('>H', data, off)[0]
    if val == 0xFFFF:
        first_ffff = off
        break

# Parse glyph stream - split on FFFF only (FFFE = line break within msg)
stream = data[first_ffff:]
n = len(stream) // 2
vals = struct.unpack(f'>{n}H', stream[:n*2])

raw_messages = []
cur = []
for v in vals:
    if v == 0xFFFF:
        raw_messages.append(cur)
        cur = []
    else:
        cur.append(v)
if cur:
    raw_messages.append(cur)

# raw_messages[0] is empty (leading FFFF), real messages start at index 1
# Translation MSG N = raw_messages[N+1]

print(f"File: 0038_type01.bin ({len(data)} bytes)")
print(f"Glyph stream starts at: 0x{first_ffff:04X}")
print(f"Raw message slots: {len(raw_messages)} (188 real messages: indices 0-187)")

# Load all translations
with open('C:/Programmieren/wizardrytranslation/data/translations_menus.json', 'r', encoding='utf-8') as f:
    menus = json.load(f)

r38 = menus.get('resource_38_character_details', {})
translations = {}
for section_key, section_val in r38.items():
    if not isinstance(section_val, dict):
        continue
    for msg_id, entry in section_val.items():
        if isinstance(entry, dict) and 'en' in entry:
            try:
                mid = int(msg_id)
                translations[mid] = {
                    'en': entry['en'],
                    'ja': entry.get('ja', entry.get('ja_summary', entry.get('ja_partial', '?'))),
                    'section': section_key
                }
            except ValueError:
                pass

# Load chunk_r38_fix.json overrides
with open('C:/Programmieren/wizardrytranslation/data/translate_chunks/chunk_r38_fix.json', 'r', encoding='utf-8') as f:
    fixes = json.load(f)
for fix in fixes:
    if fix.get('resource') == 38:
        mid = fix['message']
        en = fix['english']
        en_clean = en.rstrip(' /').rstrip()
        translations[mid] = {
            'en': en_clean,
            'ja': fix.get('japanese', '?'),
            'source': 'chunk_r38_fix'
        }

print(f"Translations loaded: {len(translations)}")
print()

# Full audit
results = []
overflow_count = 0
ok_count = 0
no_trans_count = 0

print("=" * 120)
print(f"{'MSG':>4} {'JP_Gly':>7} {'EN_Chr':>7} {'Delta':>6} {'Status':>12}  {'English':<35} {'Japanese (decoded)'}")
print("=" * 120)

for trans_idx in range(188):
    arr_idx = trans_idx + 1
    if arr_idx >= len(raw_messages):
        break

    m = raw_messages[arr_idx]
    content = [g for g in m if g < 0xFB00 and g != 0xFFFE]
    jp_glyphs = len(content)
    line_breaks = m.count(0xFFFE)

    # Decode Japanese
    decoded_ja = ''.join(gmap.get(str(g), f'[{g}]') for g in content)

    if trans_idx in translations:
        en = translations[trans_idx]['en']
        ja_ref = translations[trans_idx].get('ja', decoded_ja)
        en_len = len(en)
        delta = en_len - jp_glyphs

        if en_len > jp_glyphs:
            status = "OVERFLOW"
            overflow_count += 1
        elif en_len == jp_glyphs:
            status = "EXACT"
            ok_count += 1
        else:
            status = "OK"
            ok_count += 1

        print(f"{trans_idx:4d} {jp_glyphs:7d} {en_len:7d} {delta:+6d} {status:>12}  {en:<35} {decoded_ja}")
        results.append({
            'msg': trans_idx, 'jp_glyphs': jp_glyphs, 'en_chars': en_len,
            'delta': delta, 'status': status, 'english': en,
            'japanese_decoded': decoded_ja, 'glyph_ids': content,
            'line_breaks': line_breaks
        })
    else:
        no_trans_count += 1
        glyph_str = ','.join(str(g) for g in content[:6])
        if len(content) > 6:
            glyph_str += f'...({len(content)} total)'
        print(f"{trans_idx:4d} {jp_glyphs:7d}     ---    ---     NO_TRANS  {decoded_ja[:35]:<35} glyph_ids=[{glyph_str}]")
        results.append({
            'msg': trans_idx, 'jp_glyphs': jp_glyphs,
            'status': 'NO_TRANS', 'japanese_decoded': decoded_ja,
            'glyph_ids': content, 'line_breaks': line_breaks
        })

print()
print("=" * 120)
print(f"SUMMARY: 188 messages total")
print(f"  Translated:     {ok_count + overflow_count}")
print(f"  OK/EXACT fit:   {ok_count}")
print(f"  OVERFLOW:        {overflow_count}")
print(f"  No translation: {no_trans_count}")

if overflow_count > 0:
    print()
    print("--- OVERFLOW DETAILS (English longer than Japanese glyph count) ---")
    for r in results:
        if r['status'] == 'OVERFLOW':
            print(f"  MSG {r['msg']:3d}: JP={r['jp_glyphs']} glyphs, EN={r['en_chars']} chars (delta=+{r['delta']})")
            print(f"           EN: \"{r['english']}\"")
            print(f"           JP: \"{r['japanese_decoded']}\"")

# Save results
out = {
    'messages': results,
    'summary': {
        'total': 188,
        'translated': ok_count + overflow_count,
        'ok': ok_count,
        'overflow': overflow_count,
        'no_translation': no_trans_count
    }
}
with open('C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/r38_audit_results.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("\nResults saved to r38_audit_results.json")
