import json, os

BUDGET = 40

def get_id(e):
    return e.get('message', e.get('msg_index'))

def lines_of(s):
    tmp = s.replace('\n', ' / ')
    parts = [p.strip() for p in tmp.split('/')]
    return [p for p in parts if p != '']

def longest(s):
    parts = lines_of(s)
    if not parts:
        return 0, ''
    L = max(parts, key=len)
    return len(L), L

# In-scope DESCRIPTION sources. Split R39 into:
#   - single-line spell/skill desc (no \n) -> item-desc analog, renders in a strip
#   - multi-paragraph (\n) quest text -> separate known request-desc bug (report but tagged)
sources = [
    ('R2654-skilldesc', 'data/translate_chunks/chunk_09_translated.json', 2654),
    ('R39-batch_a', 'data/type2_translated/batch_r39_equip_a.json', None),
    ('R39-batch_b', 'data/type2_translated/batch_r39_equip_b.json', None),
]

scanned_total = 0
overflow_total = 0
examples = []
quest_para = 0

for label, path, resfilter in sources:
    if not os.path.exists(path): continue
    d = json.load(open(path, encoding='utf-8'))
    cnt = 0; ov = 0
    for e in d:
        if not isinstance(e, dict): continue
        if resfilter is not None and e.get('resource') != resfilter: continue
        en = (e.get('english') or '').strip()
        if not en: continue
        words = en.replace('/', ' ').replace('\n', ' ').split()
        # description = sentence-style: >=4 words (filters bare names like 'Kreta','Analyze')
        if len(words) < 4 and ' / ' not in en:
            continue
        if '\n' in en:
            quest_para += 1
            continue  # multi-paragraph quest text = separate known bug, exclude from item-desc count
        cnt += 1; scanned_total += 1
        ll, line = longest(en)
        has_break = (' / ' in en) or en.rstrip().endswith('/')
        over = ll > BUDGET or (not has_break and len(en) > BUDGET)
        if over:
            ov += 1; overflow_total += 1
            examples.append((ll, '%s R%s m%s' % (os.path.basename(path), e.get('resource'), get_id(e)), en))
    print(label, 'scanned=%d overflow=%d' % (cnt, ov))

print()
print('excluded multi-paragraph quest(\\n) entries:', quest_para)
print('TOTAL item-style descriptions scanned', scanned_total, 'overflow', overflow_total)
print('---worst (longest single line in glyphs)---')
examples.sort(reverse=True)
for ll, rid, en in examples[:10]:
    s = en.encode('ascii','replace').decode('ascii')
    print(ll, rid, repr(s)[:120])
