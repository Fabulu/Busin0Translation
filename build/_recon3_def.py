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
allstarts=set(gstarts); s2g={gstarts[i]:i for i in range(len(gstarts))}
def dec(gi): return ''.join(gchar(x) for x in groups[gi])
tables={346:'DESC',381:'CLIENT',411:'UILABEL',442:'TITLE'}
for t,name in tables.items():
    vals=groups[t]
    offs=[vals[i*2] for i in range(len(vals)//2)]
    # find base maximizing # offsets on group starts
    best=None
    for B in range(gstarts[t]-20,gstarts[t]+300):
        h=sum(1 for o in offs if o!=0 and (B+o) in allstarts)
        if best is None or h>best[1]: best=(B,h)
    B=best[0]
    rel=B-gstarts[t]
    print(f"\n=== G{t} {name}: BASE={B} (gstarts+{rel}), {best[1]} of {sum(1 for o in offs if o!=0)} nonzero offsets land on START ===")
    seq=[]
    for i,o in enumerate(offs):
        if o==0:
            seq.append((i,o,'HDR'))
            continue
        tg=B+o
        if tg in s2g:
            gi=s2g[tg]; seq.append((i,o,gi))
        else:
            # which group + idx
            for gi2,gs in enumerate(gstarts):
                if gs<=tg<gs+len(groups[gi2])*2+2:
                    seq.append((i,o,f"G{gi2}+{(tg-gs)//2}")); break
    # print compact
    for i,o,g in seq:
        if g=='HDR': print(f"   slot[{i:2d}] o=0 (header/empty)")
        elif isinstance(g,int): print(f"   slot[{i:2d}] o={o:5d} -> G{g} START  '{dec(g)[:34]}'")
        else: print(f"   slot[{i:2d}] o={o:5d} -> {g} (not a start)")
