import json, glob, re, os

EXCL = {'chunk_md_import.json', 'chunk_r34_fix.json', 'batch_md_import.json'}
files = glob.glob('data/translate_chunks/*.json') + glob.glob('data/type2_translated/*.json')
clean = []
for f in files:
    base = os.path.basename(f)
    if base in EXCL: continue
    if f.endswith('.master') or f.endswith('.bak'): continue
    clean.append(f)

vocab = re.compile(r'\b(sword|blade|dagger|axe|mace|spear|staff|wand|bow|shield|armor|armour|helm|gauntlet|boots|robe|ring|amulet|potion|herb|elixir|scroll|charm|stone|hairpin|band|equip|wield|wear|wielded|forged|honed|balanced|attack|defen|damage|cursed|enchant)\b', re.I)

hits = []
for f in clean:
    try:
        d = json.load(open(f, encoding='utf-8'))
    except Exception:
        continue
    if not isinstance(d, list): continue
    for e in d:
        if not isinstance(e, dict): continue
        en = e.get('english', '') or ''
        if not en: continue
        words = en.replace('/', ' ').split()
        if vocab.search(en) and (len(words) >= 4 or '.' in en):
            hits.append((os.path.basename(f), e.get('resource'), e.get('message'), en))

print('candidate sentence-style item-vocab hits:', len(hits))
from collections import Counter
c = Counter((h[0], h[1]) for h in hits)
for k, v in sorted(c.items()):
    print(k, v)
print('---SAMPLES---')
for h in hits[:40]:
    s = h[3].encode('ascii', 'replace').decode('ascii')
    print(h[0], 'R%s' % h[1], 'm%s' % h[2], repr(s)[:120])
