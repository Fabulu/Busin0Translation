import json, os

# Files in my scope that plausibly hold ITEM/EQUIPMENT DESCRIPTION records (sentence-style)
targets = [
    'data/type2_translated/batch_r39_equip_a.json',
    'data/type2_translated/batch_r39_equip_b.json',
    'data/translate_chunks/chunk_09_translated.json',  # R2654 skill descs
]

BUDGET = 40

def longest_line(s):
    # split on ' / ' line-break marker; if no marker, whole string is one line
    if ' / ' in s or s.rstrip().endswith('/'):
        parts = [p.strip() for p in s.split('/')]
    else:
        parts = [s]
    parts = [p for p in parts if p != '']
    if not parts:
        return 0, ''
    longest = max(parts, key=len)
    return len(longest), longest

scanned = 0
overflow = 0
examples = []
for f in targets:
    if not os.path.exists(f):
        continue
    d = json.load(open(f, encoding='utf-8'))
    if not isinstance(d, list):
        continue
    for e in d:
        if not isinstance(e, dict):
            continue
        en = e.get('english', '') or ''
        if not en.strip():
            continue
        # Heuristic: description = sentence-style (>=3 words OR has a line-break marker)
        words = en.replace('/', ' ').split()
        is_desc = (len(words) >= 3) or (' / ' in en)
        if not is_desc:
            continue
        scanned += 1
        ll, line = longest_line(en)
        has_break = (' / ' in en) or en.rstrip().endswith('/')
        is_over = ll > BUDGET or (not has_break and len(en.strip()) > BUDGET)
        if is_over:
            overflow += 1
            rid = '%s R%s m%s' % (os.path.basename(f), e.get('resource'), e.get('message'))
            examples.append((ll, rid, en, line))

examples.sort(reverse=True)
print('DESCRIPTIONS_SCANNED', scanned)
print('OVERFLOW_COUNT', overflow)
print('---WORST---')
for ll, rid, en, line in examples[:12]:
    s = en.encode('ascii', 'replace').decode('ascii')
    print(ll, rid, repr(s)[:140])
