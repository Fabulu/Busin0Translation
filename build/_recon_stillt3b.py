import json, struct, sys, os
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
BASE='C:/programmieren/wizardrytranslation'
os.chdir(BASE)

ee = open('ramdumps/_stillt3_ex/eeMemory.bin','rb').read()
r39 = open('build/packdata_resources/0039_type15.raw','rb').read()
R39_EE = 0xe33900

gmap = json.load(open('data/msg_glyph_map.json',encoding='utf-8'))  # id->char
def gch(g):
    if g==0xFFFF: return '[END]'
    if g==0xFFFE: return '[LB]'
    if g==0: return ' '
    if 1<=g<95: return chr(0x20+g)
    return gmap.get(str(g), f'<{g}>')

def decode(glyphs):
    return ''.join(gch(x) for x in glyphs)

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

# 1) Where in BUILT R39 does glyph 966 (0x03C6) appear?
pat = struct.pack('>H',966)
print('=== 966 occurrences in BUILT R39 ===')
i=0
occ=[]
while True:
    i=r39.find(pat,i)
    if i<0: break
    occ.append(i); i+=2
print('count:', len(occ))
# group these by run
for o in occ[:40]:
    # which group?
    gi=None
    for k in range(len(s)):
        gs=s[k]; ge=gs+len(g[k])*2+2
        if gs<=o<ge: gi=k; break
    print(f'  byte {o} (off-from-632 {o-632}) in G{gi} glyphidx {(o-s[gi])//2 if gi is not None else "?"}')

# Show runs of >=3 consecutive 966 in the built stream
print('=== consecutive 966 runs in BUILT R39 ===')
gi=0
flat=[]
for k in range(len(g)):
    for j,gl in enumerate(g[k]):
        flat.append((k,j,gl))
run=0; startk=None
for idx,(k,j,gl) in enumerate(flat):
    if gl==966:
        if run==0: startk=(k,j)
        run+=1
    else:
        if run>=3:
            print(f'  run of {run} x 966 starting G{startk[0]} glyph {startk[1]}')
        run=0
if run>=3: print(f'  run of {run} x 966 starting G{startk[0]} glyph {startk[1]}')
