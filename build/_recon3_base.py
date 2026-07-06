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

# For each table, brute-force a base that maximizes #offsets landing exactly on a group start (idx==0)
tableinfo = {
 346:(348,381),   # desc groups
 442:(444,478),   # title groups
 411:(413,442),   # ui label groups
 381:(383,411),   # client groups
}
allstarts = set(gstarts)
for t,(glo,ghi) in tableinfo.items():
    vals=groups[t]
    offs=[vals[i*2] for i in range(len(vals)//2)]
    nz=[o for o in offs if o!=0]
    # try a range of bases near group region
    best=None
    region_starts = [gstarts[gi] for gi in range(glo,ghi)]
    for B in range(gstarts[glo]-200, gstarts[ghi-1]+2):
        hits=sum(1 for o in offs if (B+o) in allstarts)
        # also count distinct group starts hit
        if best is None or hits>best[1]:
            best=(B,hits)
    B,hits=best
    print(f"\nTABLE G{t}: best base={B} hits={hits}/{len(offs)} offsets land on a group start")
    # show resulting mapping for that base
    for i,o in enumerate(offs):
        gi,gidx=find_group(B+o)
        mark = "START" if gidx==0 else f"idx{gidx}"
        print(f"   slot[{i:2d}] o={o:5d} -> G{gi} {mark}")
