import struct, json, os, sys
os.chdir('C:/programmieren/wizardrytranslation')
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

raw = open('extracted/packdata_raw/0039_type15.raw','rb').read()
gm = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))
gm2 = json.load(open('data/glyph_map_partial.json', encoding='utf-8'))
def gchar(g):
    if g == 0xFFFE: return '│'
    if g == 0xFFFF: return '#'
    s = gm.get(str(g)) or gm2.get(str(g))
    if s is None:
        s = chr(0x20+g) if 0<=g<95 else f'<{g:04X}>'
    return s
pos = 632; groups=[]; gstarts=[]; cur=[]; cs=pos
while pos+1 < len(raw):
    w = struct.unpack_from('>H', raw, pos)[0]
    if w==0xFFFF: groups.append(cur); gstarts.append(cs); cur=[]; cs=pos+2
    else: cur.append(w)
    pos+=2
def dg(gi): return ''.join(gchar(g) for g in groups[gi])

print("=== TITLE GROUPS G443-G477 ===")
for gi in range(443, 478):
    print(f"  G{gi} (start={gstarts[gi]}, len={len(groups[gi])}): '{dg(gi)}'")

print("\n=== DESCRIPTION GROUPS G347-G380 ===")
for gi in range(347, 381):
    print(f"  G{gi} (len={len(groups[gi])}): '{dg(gi)[:50]}'")

print("\n=== CLIENT/EVENT GROUPS G382-G410 ===")
for gi in range(382, 411):
    print(f"  G{gi} (len={len(groups[gi])}): '{dg(gi)[:50]}'")

print("\n=== UI LABEL GROUPS G412-G441 ===")
for gi in range(412, 442):
    print(f"  G{gi} (len={len(groups[gi])}): '{dg(gi)}'")
