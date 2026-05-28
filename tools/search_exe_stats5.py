import json, sys, glob
sys.stdout.reconfigure(encoding='utf-8')

# Check ALL R37 translations
print("=== All R37 translations found ===")
for f in sorted(glob.glob('data/translate_chunks/*.json')):
    data = json.load(open(f, encoding='utf-8'))
    r37_entries = [e for e in data if e.get('resource') == 37]
    if r37_entries:
        print(f"\n  {f}: {len(r37_entries)} R37 entries")
        for e in r37_entries:
            en = e.get('english', '')
            jp = e.get('japanese', '')
            if en:
                print(f"    msg[{e['message']}]: JP={jp[:40]} -> EN={en[:40]}")
            else:
                print(f"    msg[{e['message']}]: JP={jp[:40]} -> (EMPTY)")

# Summary: which R37 msgs have translations, which don't
print("\n=== R37 translation coverage ===")
translated = {}
untranslated = {}
for f in sorted(glob.glob('data/translate_chunks/*.json')):
    data = json.load(open(f, encoding='utf-8'))
    for e in data:
        if e.get('resource') != 37: continue
        m = e['message']
        en = e.get('english', '').strip()
        if en:
            translated[m] = en[:40]
        else:
            untranslated[m] = e.get('japanese', '')[:40]

print(f"  Translated: {len(translated)} messages")
print(f"  Untranslated: {len(untranslated)} messages")
print(f"  Untranslated msg IDs: {sorted(untranslated.keys())}")

# Check: is msg 123 among them?
if 123 in translated:
    print(f"\n  msg[123] IS translated: {translated[123]}")
elif 123 in untranslated:
    print(f"\n  msg[123] is UNTRANSLATED: {untranslated[123]}")
else:
    print(f"\n  msg[123] is NOT in any chunk file!")

# Also check R38 msg 2 (力) - it's missing!
print("\n=== R38 msg 2 (力/STR) - MISSING ===")
for f in sorted(glob.glob('data/translate_chunks/*.json')):
    data = json.load(open(f, encoding='utf-8'))
    for e in data:
        if e.get('resource') == 38 and e['message'] == 2:
            print(f"  Found in {f}: {e}")

# Check R38 message 25, 26 (also possibly missing)
print("\n=== R38 missing messages ===")
all_r38 = set()
for f in sorted(glob.glob('data/translate_chunks/*.json')):
    data = json.load(open(f, encoding='utf-8'))
    for e in data:
        if e.get('resource') == 38:
            all_r38.add(e['message'])
print(f"  Translated msg IDs: {sorted(all_r38)}")
print(f"  Missing in range 0-30: {[i for i in range(30) if i not in all_r38]}")
