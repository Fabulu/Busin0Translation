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
# Hypothesis: each slot points just-after a | (line break) OR group start.
# Classify: is the glyph BEFORE the offset a 0xFFFE (line break) or is idx==0 (group start)?
for t in [346,442,411]:
    print(f"\n=== TABLE G{t} : is each offset a LINE-START? ===")
    vals=groups[t]; base=bases[t]
    for si in range(len(vals)//2):
        v=vals[si*2]
        if v==0: continue
        tgt=base+v; gi,gidx=find_group(tgt)
        g=groups[gi]
        prev = g[gidx-1] if gidx>0 else None
        is_start = (gidx==0)
        after_lb = (prev==0xFFFE)
        at_end = (gidx==len(g))  # points at FFFF
        cls = "GROUP-START" if is_start else ("LINE-START(after |)" if after_lb else ("AT-FFFF-END" if at_end else "MID-WORD"))
        suf=''.join(gchar(x) for x in g[gidx:gidx+8])
        print(f"  slot[{si:2d}] G{gi} idx={gidx}/{len(g)} {cls:20s} -> '{suf}'")
