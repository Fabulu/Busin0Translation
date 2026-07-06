import struct, json, os, sys
os.chdir('C:/programmieren/wizardrytranslation')
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

raw = open('extracted/packdata_raw/0039_type15.raw','rb').read()
gm = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))
gm2 = json.load(open('data/glyph_map_partial.json', encoding='utf-8'))

def gchar(g):
    if g == 0xFFFE: return '│'  # line break visual
    if g == 0xFFFF: return '#'
    s = gm.get(str(g))
    if s is None: s = gm2.get(str(g))
    if s is None:
        if 0 <= g < 95: s = chr(0x20+g)
        else: s = f'<{g:04X}>'
    return s

# Scan FFFF groups from 632
pos = 632
groups = []
gstarts = []
cur = []
cs = pos
while pos+1 < len(raw):
    w = struct.unpack_from('>H', raw, pos)[0]
    if w == 0xFFFF:
        groups.append(cur); gstarts.append(cs); cur=[]; cs=pos+2
    else:
        cur.append(w)
    pos += 2

print(f"total groups {len(groups)}")
TABLES = {346:73, 381:66, 411:67, 442:71}
bases = {t: gstarts[t] + len(groups[t])*2 + 2 for t in TABLES}
for t in TABLES:
    print(f"\nG{t}: start={gstarts[t]} len={len(groups[t])} base(after FFFF)={bases[t]}")

def find_group(target):
    for gi,gs in enumerate(gstarts):
        ge = gs + len(groups[gi])*2 + 2
        if gs <= target < ge:
            return gi, (target-gs)//2
    return -1, 0

def decode_grp(gi):
    return ''.join(gchar(g) for g in groups[gi])

def decode_from(target):
    # decode glyphs from target byte until FFFF
    s=''
    p=target
    while p+1 < len(raw):
        w = struct.unpack_from('>H', raw, p)[0]
        if w == 0xFFFF: break
        s += gchar(w)
        p += 2
    return s

for t in TABLES:
    print(f"\n{'='*70}\nTABLE G{t}  base={bases[t]}")
    vals = groups[t]
    # interpret as (value,0) pairs
    pairs = []
    for i in range(0, len(vals)-1, 2):
        pairs.append((vals[i], vals[i+1]))
    # also handle odd
    print(f"  {len(vals)} u16 values, {len(pairs)} (value,0) pairs")
    print(f"  raw values: {vals}")
    for pi,(v,z) in enumerate(pairs):
        if v == 0:
            print(f"  slot[{pi}] v=0 (empty)")
            continue
        target = bases[t] + v
        gi, gidx = find_group(target)
        # decode starting AT target (renderer read pattern) and the whole group
        at = decode_from(target)
        whole = decode_grp(gi) if gi>=0 else '?'
        print(f"  slot[{pi}] v={v} -> byte{target} = G{gi} glyph_idx={gidx}")
        print(f"        from-target: '{at[:60]}'")
        if gidx != 0:
            print(f"        whole-grp  : '{whole[:60]}'")
