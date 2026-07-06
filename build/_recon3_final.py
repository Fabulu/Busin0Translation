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
def find_group(target):
    for gi,gs in enumerate(gstarts):
        ge=gs+len(groups[gi])*2+2
        if gs<=target<ge: return gi,(target-gs)//2
    return -1,0
def dec(gi): return ''.join(gchar(x) for x in groups[gi])

# Theory: base = gstarts[tablegroup] + 8 . Verify.
for t in [346,442,411,381]:
    B = gstarts[t]+8
    vals=groups[t]
    offs=[vals[i*2] for i in range(len(vals)//2)]
    print(f"\n=== G{t}: base = gstarts[{t}]+8 = {gstarts[t]}+8 = {B} ===")
    hits=0
    for i,o in enumerate(offs):
        gi,gidx=find_group(B+o)
        st = "START" if gidx==0 else f"idx{gidx}"
        if gidx==0 and gi>=0: hits+=1
        txt = dec(gi)[:30] if gi>=0 else '?'
        print(f"   slot[{i:2d}] o={o:5d} -> G{gi} {st:6s} '{txt}'")
    print(f"   => {hits}/{len(offs)} land on a group START")
