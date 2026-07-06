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
# CLIENT table G381 raw
print("G381 (CLIENT) raw glyphs:", groups[381])
print("decoded:", ''.join(gchar(g) for g in groups[381]))
print(f"len={len(groups[381])}, all-pairs-of-(v,0)? checking...")
v=groups[381]
nonzero=[x for x in v if x!=0]
print("nonzero values:", nonzero)
# header count: how many leading u16 before first offset region. Compare to other tables.
# DESC header = first 4 u16 (2 pair slots = o=0,o=0) then slot2 o=34 still header. exact base=gstarts+8 => 4 u16.
# Print first 8 u16 of each table to see the header structure
for t in [346,381,411,442]:
    print(f"\nG{t} first 8 u16: {groups[t][:8]}  decoded: '{''.join(gchar(g) for g in groups[t][:8])}'")
    print(f"   gstarts={gstarts[t]}, K(=exactbase-gstarts): DESC8/UI12/TITLE4")
