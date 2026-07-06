import struct, json, os, sys
os.chdir('C:/programmieren/wizardrytranslation')
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
raw = open('extracted/packdata_raw/0039_type15.raw','rb').read()
gm = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))
gm2 = json.load(open('data/glyph_map_partial.json', encoding='utf-8'))
def gchar(g):
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
# Treat each u16 as a flat slot. Find base maximizing nonzero u16 that land on a START.
for t in [346,381,411,442]:
    vals=groups[t]
    nz=[x for x in vals if x!=0]
    best=None
    for B in range(gstarts[t]-30,gstarts[t]+400):
        h=sum(1 for o in nz if (B+o) in allstarts)
        if best is None or h>best[1]: best=(B,h)
    B=best[0]
    print(f"\n=== G{t}: FLAT u16 slots, base={B} (gstarts+{B-gstarts[t]}), {best[1]}/{len(nz)} nonzero land on START ===")
    # map nonzero values to groups
    seq=[]
    for o in nz:
        tg=B+o
        if tg in s2g: seq.append((o,s2g[tg],True))
        else:
            for gi,gs in enumerate(gstarts):
                if gs<=tg<gs+len(groups[gi])*2+2:
                    seq.append((o,f"G{gi}+{(tg-gs)//2}",False)); break
    for o,g,ok in seq[:40]:
        if ok: print(f"   o={o:5d} -> G{g} START '{dec(g)[:30]}'")
        else: print(f"   o={o:5d} -> {g}")
