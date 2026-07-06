import json, struct, sys, os
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
BASE='C:/programmieren/wizardrytranslation'
os.chdir(BASE)
r39o = open('extracted/packdata_raw/0039_type15.raw','rb').read()
gmap = json.load(open('data/msg_glyph_map.json',encoding='utf-8'))
def gch(g):
    if g==0xFFFF: return '[END]'
    if g==0xFFFE: return '[LB]'
    if g==0: return '_'
    if 1<=g<95: return chr(0x20+g)
    return gmap.get(str(g), f'<{g}>')
def scan(raw):
    pos=632; groups=[]; starts=[]; cur=[]; cs=pos
    while pos+1<len(raw):
        w=struct.unpack_from('>H',raw,pos)[0]
        if w==0xFFFF:
            groups.append(cur); starts.append(cs); cur=[]; cs=pos+2
        else: cur.append(w)
        pos+=2
    return groups,starts
go,so = scan(r39o)
base = so[411] + len(go[411])*2 + 2
print('ORIG G411 base (after-FFFF):', base)
print('=== ORIG G411 slot resolution (54..66) ===')
for i in range(54,67):
    v=go[411][i]
    if v==0:
        print(f'  slot[{i}]=0 (pad)'); continue
    tgt=base+v
    gi=None
    for k in range(len(so)):
        gs=so[k]; ge=gs+len(go[k])*2+2
        if gs<=tgt<ge: gi=k; break
    if gi is not None:
        glidx=(tgt-so[gi])//2
        dec=''.join(gch(x) for x in go[gi][glidx:glidx+20])
        print(f'  slot[{i}]={v} -> G{gi} g{glidx}: "{dec}"')
    else:
        print(f'  slot[{i}]={v} -> OOR')
# also show what UI groups G442-G449 are in orig (the JP)
print('\n=== ORIG G442..G450 first glyphs ===')
for k in range(442,451):
    dec=''.join(gch(x) for x in go[k][:18])
    print(f'  G{k}: "{dec}"')
