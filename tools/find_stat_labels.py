import struct, json, os

gmap = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))
rev = {v: int(k) for k, v in gmap.items()}

labels = {
    '種族': [rev[c] for c in '種族'],
    '属性': [rev[c] for c in '属性'],
    '職業': [rev[c] for c in '職業'],
    '知恵': [rev[c] for c in '知恵'],
    '信仰心': [rev[c] for c in '信仰心'],
    '生命力': [rev[c] for c in '生命力'],
    '敏捷度': [rev[c] for c in '敏捷度'],
    '幸運度': [rev[c] for c in '幸運度'],
}

print("Glyph IDs:", {k: v for k, v in labels.items()})

resdir = 'extracted/packdata_resources'
allfiles = sorted(os.listdir(resdir))
print(f"Searching {len(allfiles)} resource files...")

for fname in allfiles:
    data = open(os.path.join(resdir, fname), 'rb').read()
    found = []
    for jp, ids in labels.items():
        target = b''.join(struct.pack('>H', g) for g in ids)
        if target in data:
            found.append(jp)
    if found:
        print(f"  {fname}: {found}")

print("\nDone searching resources.")

# Also search EXE for Shift-JIS encoded versions
print("\n--- Searching EXE for Shift-JIS encoded labels ---")
exe = open('extracted/SLPM_653.78', 'rb').read()
all_labels = ['性別', '種族', '属性', '職業', '知恵', '信仰心', '生命力', '敏捷度', '幸運度', '力']
for label in all_labels:
    sjis = label.encode('shift_jis')
    pos = 0
    hits = []
    while True:
        pos = exe.find(sjis, pos)
        if pos < 0:
            break
        hits.append(pos)
        pos += 1
    if hits:
        print(f"  {label}: SJIS at {[hex(h) for h in hits[:10]]}")
    else:
        print(f"  {label}: NOT in EXE as SJIS")
