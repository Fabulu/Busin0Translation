#!/usr/bin/env python3
"""Extract and decode type-2 Section 2 messages for dungeon batch A resources."""
import struct, json, os, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
os.chdir('C:/Programmieren/wizardrytranslation')

gmap = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))

RESOURCES = [2659, 1937, 1954, 1926, 1955]

def parse_sec2(data):
    """Extract Section 2 from type-2 resource."""
    sec2_size = struct.unpack_from('<I', data, 0x14)[0]
    sec2_off = struct.unpack_from('<I', data, 0x18)[0]
    return data[sec2_off:sec2_off + sec2_size]

def decode_groups(sec2_data):
    """Parse into FFFF-delimited groups and decode each."""
    nwords = len(sec2_data) // 2
    words = [struct.unpack_from('>H', sec2_data, i*2)[0] for i in range(nwords)]

    groups = []
    current = []
    for w in words:
        if w == 0xFFFF:
            if current:
                groups.append(current)
            current = []
        else:
            current.append(w)
    if current:
        groups.append(current)
    return groups

def decode_message(group):
    """Decode a glyph group to text. Returns (decoded_text, stats)."""
    chars = []
    mapped = 0
    unmapped = 0
    controls = 0
    for g in group:
        if g == 0xFFFE:
            chars.append(' / ')
        elif g >= 0xFB00:
            controls += 1
            chars.append(f'[{g:04X}]')
        elif str(g) in gmap:
            chars.append(gmap[str(g)])
            mapped += 1
        else:
            chars.append(f'[{g:04X}]')
            unmapped += 1
    text = ''.join(chars)
    return text, mapped, unmapped, controls

def classify_group(group, text, mapped, unmapped, controls):
    """Classify if a group is dialogue, data, or binary."""
    total = len(group)
    if total == 0:
        return 'EMPTY'

    # All controls
    if controls == total:
        return 'CONTROL'

    # Very short (1-2 glyphs) with no text
    if mapped == 0 and unmapped == 0:
        return 'CONTROL'

    # High unmapped ratio = likely binary data
    text_glyphs = mapped + unmapped
    if text_glyphs > 0 and unmapped / text_glyphs > 0.5:
        return 'BINARY'

    # Looks like it has readable text
    if mapped >= 1:
        return 'TEXT'

    return 'DATA'

all_results = {}

for rid in RESOURCES:
    path = f'extracted/packdata_raw/{rid:04d}_type02.raw'
    data = open(path, 'rb').read()
    sec2 = parse_sec2(data)
    groups = decode_groups(sec2)

    text_msgs = []
    skip_count = {'EMPTY': 0, 'CONTROL': 0, 'BINARY': 0, 'DATA': 0}

    for i, grp in enumerate(groups):
        text, mapped, unmapped, controls = decode_message(grp)
        cat = classify_group(grp, text, mapped, unmapped, controls)

        if cat == 'TEXT':
            text_msgs.append((i, text, grp))
        else:
            skip_count[cat] = skip_count.get(cat, 0) + 1

    all_results[rid] = text_msgs
    print(f"\nR{rid}: {len(groups)} total groups, {len(text_msgs)} text messages")
    print(f"  Skipped: {skip_count}")
    print(f"  First 5 text messages:")
    for idx, (gi, txt, _) in enumerate(text_msgs[:5]):
        print(f"    [{gi}] {txt[:80]}")

# Save full extraction
output = {}
for rid, msgs in all_results.items():
    output[rid] = []
    for gi, txt, grp in msgs:
        output[rid].append({
            'group_index': gi,
            'text': txt,
            'glyph_count': len(grp)
        })

json.dump(output, open('data/extracted_dungeon_a.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(f"\nSaved extraction to data/extracted_dungeon_a.json")
print(f"Total text messages: {sum(len(v) for v in output.values())}")
