import json, struct, sys, os
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
BASE='C:/programmieren/wizardrytranslation'
os.chdir(BASE)

r39 = open('build/packdata_resources/0039_type15.raw','rb').read()
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

g,s = scan(r39)
go,so = scan(r39o)

print('=== BUILT G411 (UI label offset table) raw slots ===')
print('start', s[411], 'len', len(g[411]))
print(g[411])
print('=== ORIG G411 raw slots ===')
print('start', so[411], 'len', len(go[411]))
print(go[411])

# The table base for G411 in built
base = s[411] + len(g[411])*2 + 2
print('\nBUILT G411 base (after-FFFF):', base)
# resolve each non-zero slot
print('\n=== BUILT G411 slot resolution ===')
for i,v in enumerate(g[411]):
    if v==0: continue
    tgt = base+v
    # which group
    gi=None
    for k in range(len(s)):
        gs=s[k]; ge=gs+len(g[k])*2+2
        if gs<=tgt<ge: gi=k; break
    if gi is not None:
        glidx=(tgt-s[gi])//2
        dec=decode_first = ''.join(gch(x) for x in g[gi][glidx:glidx+30])
        print(f'  slot[{i}]={v} -> byte {tgt} G{gi} g{glidx}: "{dec[:40]}"')
    else:
        print(f'  slot[{i}]={v} -> byte {tgt} OUT OF RANGE (>{s[-1]+len(g[-1])*2+2})')
