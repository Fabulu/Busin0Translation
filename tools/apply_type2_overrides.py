import struct, json, re, sys
from collections import Counter

PACKDATA = 'C:/Programmieren/wizardrytranslation/extracted/PACKDATA.DIG'
GLYPH_MAP_PATH = 'C:/Programmieren/wizardrytranslation/data/msg_glyph_map.json'
OVERRIDES_PATH = 'C:/Programmieren/wizardrytranslation/data/type2_glyph_overrides.json'
OUT_JSON = 'C:/Programmieren/wizardrytranslation/data/type2_dialogue_corrected.json'
OUT_TXT = 'C:/Programmieren/wizardrytranslation/data/type2_dialogue_corrected.txt'

SECTOR = 2048
TOC_ENTRIES = 2883
OUTLIER_INDICES = {1370, 2100}

sys.stdout.reconfigure(encoding='utf-8')

with open(GLYPH_MAP_PATH, 'r', encoding='utf-8') as f:
    glyph_map = {int(k): v for k, v in json.load(f).items()}
print(f'Loaded {len(glyph_map)} base glyph mappings', flush=True)

with open(OVERRIDES_PATH, 'r', encoding='utf-8') as f:
    overrides = json.load(f)
print(f'Loaded {len(overrides)} glyph overrides', flush=True)

corrected_map = dict(glyph_map)
applied = 0
for gid_str, info in overrides.items():
    gid = int(gid_str)
    old_char = info['t1']
    new_char = info['t2']
    if gid in corrected_map:
        if corrected_map[gid] == old_char:
            corrected_map[gid] = new_char
            applied += 1
        else:
            print(f'  WARNING: glyph {gid} expected {old_char} but found {corrected_map[gid]}, overriding to {new_char}')
            corrected_map[gid] = new_char
            applied += 1
    else:
        print(f'  WARNING: glyph {gid} not in base map, adding as {new_char}')
        corrected_map[gid] = new_char
        applied += 1
print(f'Applied {applied} overrides to glyph map', flush=True)

with open(PACKDATA, 'rb') as f:
    toc_data = f.read(TOC_ENTRIES * 12)

toc = []
for i in range(TOC_ENTRIES):
    so, sc, tc = struct.unpack_from('<III', toc_data, i * 12)
    toc.append((i, so, sc, tc))

type2 = [(idx, so, sc, tc) for idx, so, sc, tc in toc if tc == 2 and sc > 10 and idx not in OUTLIER_INDICES]
print(f'Found {len(type2)} type-2 resources with >10 sectors', flush=True)

def find_dialogue_in_section2(data, resource_idx, sec2_offset):
    results = []
    sec2 = data[sec2_offset:]
    if len(sec2) < 4:
        return results
    n_words = len(sec2) // 2
    words = []
    for wi in range(n_words):
        words.append(struct.unpack_from('>H', sec2, wi * 2)[0])
    msg_start = 0
    msg_index = 0
    for wi in range(n_words):
        if words[wi] == 0xFFFF:
            msg_glyphs = words[msg_start:wi]
            text_glyphs = [g for g in msg_glyphs if g < 0xFB00]
            if len(text_glyphs) >= 10:
                mapped = sum(1 for g in text_glyphs if g in corrected_map)
                coverage = 100 * mapped / len(text_glyphs) if text_glyphs else 0
                if coverage >= 50:
                    decoded = []
                    for g in msg_glyphs:
                        if g >= 0xFB00:
                            continue
                        elif g in corrected_map:
                            decoded.append(corrected_map[g])
                        else:
                            decoded.append(f'[{g:04X}]')
                    text = ''.join(decoded)
                    clean = re.sub(r'\[[0-9A-F]{4}\]', '', text).replace(' ', '')
                    if len(clean) >= 5:
                        results.append({
                            'resource': resource_idx,
                            'offset': sec2_offset + msg_start * 2,
                            'msg_index': msg_index,
                            'japanese': text,
                            'coverage': round(coverage),
                            'glyph_count': len(text_glyphs)
                        })
            msg_start = wi + 1
            msg_index += 1
    return results

all_dialogue = []
processed = 0
no_sec2 = 0

with open(PACKDATA, 'rb') as f:
    for idx, so, sc, tc in type2:
        abs_off = so * SECTOR
        size = sc * SECTOR
        f.seek(abs_off)
        data = f.read(size)
        if len(data) < 0x1C:
            no_sec2 += 1
            continue
        z1, payload_size, stride, z2 = struct.unpack_from('<IIII', data, 0)
        sec_count = struct.unpack_from('<I', data, 0x10)[0]
        if sec_count >= 1 and len(data) >= 0x1C:
            sec2_size = struct.unpack_from('<I', data, 0x14)[0]
            sec2_offset = struct.unpack_from('<I', data, 0x18)[0]
            if sec2_offset > 0 and sec2_offset < len(data) and sec2_size > 20:
                runs = find_dialogue_in_section2(data, idx, sec2_offset)
                if runs:
                    all_dialogue.extend(runs)
            else:
                no_sec2 += 1
        else:
            no_sec2 += 1
        processed += 1
        if processed % 100 == 0:
            print(f'  Processed {processed}/{len(type2)}, {len(all_dialogue)} runs...', flush=True)

print(f'\nTotal: {len(all_dialogue)} dialogue runs', flush=True)
print(f'Resources without usable section 2: {no_sec2}', flush=True)

all_dialogue.sort(key=lambda x: (x['resource'], x['offset']))
unique_resources = len(set(d['resource'] for d in all_dialogue))
print(f'Dialogue in {unique_resources} unique resources', flush=True)

with open(OUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(all_dialogue, f, ensure_ascii=False, indent=2)
print(f'Saved {OUT_JSON}', flush=True)

EQ = '=' * 60
with open(OUT_TXT, 'w', encoding='utf-8') as f:
    current_resource = None
    for entry in all_dialogue:
        if entry['resource'] != current_resource:
            current_resource = entry['resource']
            f.write(f'\n{EQ}\n')
            f.write(f'Resource {current_resource}\n')
            f.write(f'{EQ}\n')
        mi = entry["msg_index"]
        off = entry["offset"]
        gc = entry["glyph_count"]
        cov = entry["coverage"]
        jp = entry["japanese"]
        f.write(f'  [msg {mi:3d}] [offset {off:06X}] ({gc} glyphs, {cov}% mapped)\n')
        f.write(f'  {jp}\n\n')
print(f'Saved {OUT_TXT}', flush=True)

if all_dialogue:
    avg_cov = sum(d['coverage'] for d in all_dialogue) / len(all_dialogue)
    avg_gl = sum(d['glyph_count'] for d in all_dialogue) / len(all_dialogue)
    total_glyphs = sum(d['glyph_count'] for d in all_dialogue)
    print(f'\nStats: avg coverage={avg_cov:.1f}%, avg glyphs={avg_gl:.1f}, total glyphs={total_glyphs}')
    res_counts = Counter(d['resource'] for d in all_dialogue)
    print(f'\nTop 20 resources by dialogue count:')
    for res, count in res_counts.most_common(20):
        print(f'  R{res}: {count} runs')

print(f'\n--- Override Impact ---')
try:
    with open('C:/Programmieren/wizardrytranslation/data/type2_dialogue_full.json', 'r', encoding='utf-8') as f:
        old_dialogue = json.load(f)
    old_by_key = {}
    for d in old_dialogue:
        old_by_key[(d['resource'], d['offset'])] = d['japanese']
    new_by_key = {}
    for d in all_dialogue:
        new_by_key[(d['resource'], d['offset'])] = d['japanese']
    changed = 0
    total_char_changes = 0
    for d in all_dialogue:
        key = (d['resource'], d['offset'])
        if key in old_by_key:
            old_text = old_by_key[key]
            new_text = d['japanese']
            if old_text != new_text:
                changed += 1
                for oc, nc in zip(old_text, new_text):
                    if oc != nc:
                        total_char_changes += 1
    new_entries = sum(1 for d in all_dialogue if (d['resource'], d['offset']) not in old_by_key)
    missing = sum(1 for k in old_by_key if k not in new_by_key)
    print(f'Entries with text changes: {changed} / {len(all_dialogue)}')
    print(f'Total character substitutions: {total_char_changes}')
    print(f'New entries (not in old): {new_entries}')
    print(f'Old entries missing from new: {missing}')
except Exception as e:
    print(f'Could not compare with old data: {e}')
