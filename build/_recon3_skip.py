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
bases={t:gstarts[t]+len(groups[t])*2+2 for t in [346,381,411,442]}
def find_group(target):
    for gi,gs in enumerate(gstarts):
        ge=gs+len(groups[gi])*2+2
        if gs<=target<ge: return gi,(target-gs)//2
    return -1,0
# For TITLE table: show prefix(skipped) | suffix(rendered) for each slot
print("=== TITLE G442 : prefix [skipped] || suffix [rendered from offset] ===")
vals=groups[442]; base=bases[442]
for si in range(len(vals)//2):
    v=vals[si*2]
    if v==0: continue
    tgt=base+v; gi,gidx=find_group(tgt)
    g=groups[gi]
    pre=''.join(gchar(x) for x in g[:gidx])
    suf=''.join(gchar(x) for x in g[gidx:])
    print(f"  slot[{si:2d}] G{gi} idx={gidx}: [{pre}] || {suf}")
print("\n=== UILABEL G411 : prefix [skipped] || suffix [rendered] ===")
vals=groups[411]; base=bases[411]
for si in range(len(vals)//2):
    v=vals[si*2]
    if v==0: continue
    tgt=base+v; gi,gidx=find_group(tgt)
    g=groups[gi]
    pre=''.join(gchar(x) for x in g[:gidx])
    suf=''.join(gchar(x) for x in g[gidx:])
    print(f"  slot[{si:2d}] G{gi} idx={gidx}: [{pre}] || {suf}")
print("\n=== DESC G346 : prefix [skipped] || suffix [rendered] (first 30 chars each) ===")
vals=groups[346]; base=bases[346]
for si in range(len(vals)//2):
    v=vals[si*2]
    if v==0: continue
    tgt=base+v; gi,gidx=find_group(tgt)
    g=groups[gi]
    pre=''.join(gchar(x) for x in g[:gidx])
    suf=''.join(gchar(x) for x in g[gidx:])
    print(f"  slot[{si:2d}] G{gi} idx={gidx}: [{pre[:30]}] || {suf[:30]}")
