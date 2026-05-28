import json
from collections import defaultdict

with open('C:/Programmieren/wizardrytranslation/data/full_decoded_text.json', 'r', encoding='utf-8') as f:
    decoded = json.load(f)

resources = {}
for entry in decoded:
    r = entry['resource']
    if r not in resources:
        resources[r] = []
    resources[r].append(entry)

translated_keys = set()

with open('C:/Programmieren/wizardrytranslation/data/translations_items_monsters.json', 'r', encoding='utf-8') as f:
    items = json.load(f)
for entry in items:
    translated_keys.add((entry['resource'], entry['message']))

with open('C:/Programmieren/wizardrytranslation/data/translations_menus.json', 'r', encoding='utf-8') as f:
    menus = json.load(f)
for sk, sec in menus.items():
    if sk == '_meta': continue
    if not isinstance(sec, dict): continue
    if sk.startswith('resource_'):
        parts = sk.split('_')
        rn = int(parts[1])
        for mid, val in sec.items():
            if isinstance(val, dict) and 'en' in val:
                translated_keys.add((rn, int(mid)))

with open('C:/Programmieren/wizardrytranslation/data/translations_dungeon_story.json', 'r', encoding='utf-8') as f:
    dungeon = json.load(f)
for sk, sec in dungeon.items():
    if sk in ('_metadata', 'cross_reference_notes'): continue
    if not isinstance(sec, dict): continue
    if not sk.startswith('resource_'): continue
    parts = sk.split('_')
    rn = int(parts[1])
    if 'messages' in sec:
        for mid, val in sec['messages'].items():
            if isinstance(val, dict) and 'english' in val:
                translated_keys.add((rn, int(mid)))

with open('C:/Programmieren/wizardrytranslation/data/translations_shop_church.json', 'r', encoding='utf-8') as f:
    shop = json.load(f)
for sk, sec in shop.items():
    if sk == '_metadata': continue
    if not isinstance(sec, dict): continue
    if not sk.startswith('resource_'): continue
    parts = sk.split('_')
    rn = int(parts[1])
    if 'entries' in sec:
        for ei in sec['entries']:
            if isinstance(ei, dict) and 'english' in ei:
                translated_keys.add((rn, int(ei['id'])))

menu_non_resource_count = 0
for sk, sec in menus.items():
    if sk == '_meta' or sk.startswith('resource_'): continue
    if isinstance(sec, dict):
        menu_non_resource_count += len([v for v in sec.values() if isinstance(v, dict) and 'en' in v])

fully_decoded_untranslated = []
partial_decoded_untranslated = []
very_short_untranslated = []
translated_count = 0

for entry in decoded:
    key = (entry['resource'], entry['message'])
    if key in translated_keys:
        translated_count += 1
        continue
    jp = entry.get('japanese', '')
    coverage = entry.get('coverage', 0)
    jp_clean = jp.rstrip(' /').strip()
    if len(jp_clean) <= 2:
        very_short_untranslated.append(entry)
    elif coverage < 100:
        partial_decoded_untranslated.append(entry)
    else:
        fully_decoded_untranslated.append(entry)

res_descriptions = {}
for section_key in list(menus.keys()) + list(dungeon.keys()) + list(shop.keys()):
    if section_key.startswith('resource_'):
        parts = section_key.split('_', 2)
        if len(parts) >= 3:
            res_descriptions[int(parts[1])] = parts[2].replace('_', ' ')

out = []
out.append('TOTAL_DECODED=' + str(len(decoded)))
out.append('TOTAL_RESOURCES=' + str(len(resources)))
out.append('RESOURCE_IDS=' + str(sorted(resources.keys())))
out.append('TRANSLATED=' + str(translated_count))
out.append('UNTRANS_FULL=' + str(len(fully_decoded_untranslated)))
out.append('UNTRANS_PARTIAL=' + str(len(partial_decoded_untranslated)))
out.append('UNTRANS_SHORT=' + str(len(very_short_untranslated)))
out.append('MENU_EXTRAS=' + str(menu_non_resource_count))
c100 = sum(1 for e in decoded if e['coverage'] == 100)
c80 = sum(1 for e in decoded if 80 <= e['coverage'] < 100)
clow = sum(1 for e in decoded if e['coverage'] < 80)
out.append('DECODE_100=' + str(c100))
out.append('DECODE_80_99=' + str(c80))
out.append('DECODE_LOW=' + str(clow))

out.append('---PERRESOURCE---')
for r in sorted(resources.keys()):
    entries = resources[r]
    total = len(entries)
    trans = sum(1 for e in entries if (e['resource'], e['message']) in translated_keys)
    desc = res_descriptions.get(r, '')
    out.append(str(r) + '|' + str(total) + '|' + str(trans) + '|' + desc)

out.append('---UNTRANS_SAMPLES---')
by_res = defaultdict(list)
for entry in fully_decoded_untranslated:
    by_res[entry['resource']].append(entry)
for r in sorted(by_res.keys()):
    entries = by_res[r]
    desc = res_descriptions.get(r, 'unknown')
    out.append('RES=' + str(r) + '|COUNT=' + str(len(entries)) + '|DESC=' + desc)
    for e in entries[:3]:
        jp = e['japanese'][:70].replace('\n',' ')
        m = e['message']
        out.append('  MSG=' + str(m) + '|JP=' + jp)

out.append('---VERYSHORT---')
for e in very_short_untranslated[:30]:
    r2 = e['resource']
    m2 = e['message']
    j2 = e['japanese'].replace('\n', ' ')
    out.append('  R' + str(r2) + ':M' + str(m2) + '=' + j2)

out.append('---ZERO_TRANS---')
for r in sorted(resources.keys()):
    entries = resources[r]
    trans = sum(1 for e in entries if (e['resource'], e['message']) in translated_keys)
    if trans == 0:
        total = len(entries)
        desc = res_descriptions.get(r, 'unknown')
        out.append('RES=' + str(r) + '|TOTAL=' + str(total) + '|DESC=' + desc)
        for e in entries[:3]:
            jp = e['japanese'][:60].replace('\n',' ')
            out.append('  SAMPLE=' + jp)

print('\n'.join(out))