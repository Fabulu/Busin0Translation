import json, struct, sys, os
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
os.chdir('C:/programmieren/wizardrytranslation')
ee = open('ramdumps/_stillt3_ex/eeMemory.bin','rb').read()
r39 = open('build/packdata_resources/0039_type15.raw','rb').read()
R39_EE=0xe33900
gmap = json.load(open('data/msg_glyph_map.json',encoding='utf-8'))
def gch(g):
    if g==0:return '_'
    if 1<=g<95:return chr(0x20+g)
    if g==0xFFFF:return '[END]'
    if g==0xFFFE:return '[LB]'
    return gmap.get(str(g),f'<{g}>')
def scan(raw):
    pos=632;groups=[];starts=[];cur=[];cs=pos
    while pos+1<len(raw):
        w=struct.unpack_from('>H',raw,pos)[0]
        if w==0xFFFF:groups.append(cur);starts.append(cs);cur=[];cs=pos+2
        else:cur.append(w)
        pos+=2
    return groups,starts
g,s=scan(r39)
# G411 starts at file byte s[411]; in EE = R39_EE + s[411]
g411_ee = R39_EE + s[411]
print('G411 file start', s[411], '-> EE', hex(g411_ee))
# The composed buffer copies G411's stream. Does the renderer index G411 via the
# section table or via another mechanism? Check: which UI label index maps to this.
# The buffer at +132 IS G411 from glyph 0 (the leading 6 zeros = G411 slots 0-5 which are 0).
# So the renderer was told 'draw the group at G411' (a group index), and it walked
# G411 as glyphs. That means some pointer resolved to G411 g0.
# In pristine, which G411 slot or which OTHER table slot equals G411 g0?
# Actually the composed buffer shows G411 glyphs THEN 'Accept this request?'.
# 'Accept this request?' is G413 (slot6=30 -> G413 g12 earlier? no, G413 g0).
# Let's find 'Accept this request?' group.
for k in range(411,445):
    dec=''.join(gch(x) for x in g[k][:20])
    if 'Accept' in dec or 'Abandon' in dec or 'request' in dec.lower():
        print(f'  G{k}: "{dec}"')
print()
# The 6 leading zeros + > + ... = G411 itself. So renderer drew the *table group* G411.
# WHY would it draw G411? Because a UI-label slot resolved to G411 g0.
# Check pristine: did any table slot point to G411 g0 in pristine? In built?
# G411 g0 byte = s[411]. Search all 4 tables for a slot that resolves to s[411].
def tablebase(t): return s[t]+len(g[t])*2+2
for t in (346,381,411,442):
    base=tablebase(t)
    for i,v in enumerate(g[t]):
        if v==0:continue
        if base+v==s[411]:
            print(f'  TABLE G{t} slot[{i}]={v} -> G411 g0!')
