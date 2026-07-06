import json, struct, sys, os
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
os.chdir('C:/programmieren/wizardrytranslation')
r39 = open('build/packdata_resources/0039_type15.raw','rb').read()
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
g,s=scan(r39)
print('=== BUILT G442 (quest-title offset table) full slots ===')
print('start',s[442],'len',len(g[442]))
print('first 30 glyphs decoded:', ''.join(gch(x) for x in g[442][:30]))
print('raw slots:', g[442])
# G442 is the title offset table. Its slot values were rebuilt to point at title group starts.
# But G411 slots 54-66 now point at G442 g0. What does the renderer DRAW for a UI label
# when it reads from G442 g0? It reads glyphs until FFFE/FFFF.
print('\nG442 stream until first FFFE/FFFF:')
out=[]
for x in g[442]:
    if x in (0xFFFE,0xFFFF): break
    out.append(x)
print('glyphs:', out[:20])
print('decoded:', ''.join(gch(x) for x in out[:20]))
# Where does 966 appear as a SLOT VALUE in G442? (these are byte offsets to title groups)
print('\nNumber of 966 slot values in G442:', sum(1 for x in g[442] if x==966))
