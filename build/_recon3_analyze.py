import struct, json, os, sys
os.chdir('C:/programmieren/wizardrytranslation')
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
raw = open('extracted/packdata_raw/0039_type15.raw','rb').read()
gm = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))
gm2 = json.load(open('data/glyph_map_partial.json', encoding='utf-8'))
def gchar(g):
    if g==0xFFFE: return '|'
    s = gm.get(str(g)) or gm2.get(str(g))
    return s if s is not None else (chr(0x20+g) if 0<=g<95 else f'<{g:04X}>')
pos=632; groups=[]; gstarts=[]; cur=[]; cs=pos
while pos+1<len(raw):
    w=struct.unpack_from('>H',raw,pos)[0]
    if w==0xFFFF: groups.append(cur); gstarts.append(cs); cur=[]; cs=pos+2
    else: cur.append(w)
    pos+=2
TABLES={346:'DESC',381:'CLIENT',411:'UILABEL',442:'TITLE'}
bases={t:gstarts[t]+len(groups[t])*2+2 for t in TABLES}
def find_group(target):
    for gi,gs in enumerate(gstarts):
        ge=gs+len(groups[gi])*2+2
        if gs<=target<ge: return gi,(target-gs)//2
    return -1,0
for t,name in TABLES.items():
    print(f"\n{'='*60}\nTABLE G{t} ({name}) base={bases[t]}")
    vals=groups[t]
    # Build (value,0) pairs but track ALL u16 (slot index = pair index)
    nslots = len(vals)//2
    prev_gi = None
    for si in range(nslots):
        v = vals[si*2]; z = vals[si*2+1]
        if v==0:
            continue
        tgt = bases[t]+v
        gi,gidx = find_group(tgt)
        glen = len(groups[gi]) if gi>=0 else 0
        marker = ""
        if gi==prev_gi: marker=" <-- SAME group as prev (multi-slot)"
        elif gidx==0: marker=" [glyph0=START]"
        else: marker=f" [mid-string idx={gidx}]"
        # offset from END of group (how far before terminator)
        from_end = glen - gidx if gi>=0 else -1
        print(f"  slot[{si:2d}] v={v:5d} -> G{gi} idx={gidx}/{glen} (from_end={from_end}){marker}")
        prev_gi=gi
