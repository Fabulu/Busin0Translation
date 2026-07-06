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

# TITLE table G442: full raw and check delta between consecutive nonzero offsets
print("=== G442 TITLE: consecutive nonzero offset deltas vs target group sizes ===")
vals=groups[442]; base=bases[442]
offs=[vals[i*2] for i in range(len(vals)//2)]
print("offsets:", offs)
print("deltas :", [offs[i+1]-offs[i] for i in range(len(offs)-1)])
# Each title group's byte size (len*2). Map slot->group, see if delta == group byte size
print("\nTITLE groups G444..G477 byte sizes (len*2):")
for gi in range(444,478):
    print(f"  G{gi}: len={len(groups[gi])} bytes={len(groups[gi])*2}")

# Now: hypothesis - the FIRST nonzero offset points into the FIRST title group region.
# base for G442 = 21196 = start of G443. So offset 0 = G443 (' |' separator),
# offset = byte from G443 start.
# slot1 v=34: 21196+34=21230. G444 start=21202, len10 -> ends 21202+22=21224. G445 start 21224.
# 21230 = G445 idx 3. Hmm. But maybe the renderer reads the offset as: title k = offset[k],
# and the offsets should land at GROUP STARTS if the data were laid out 1 title per slot
# in ORDER. Let's check: do offsets correspond to cumulative group sizes from G444?
print("\n=== Cumulative byte position of each title group start, relative to base(21196) ===")
for gi in range(443,478):
    rel = gstarts[gi]-base
    print(f"  G{gi} start rel={rel}  (matches an offset? {rel in offs})")
