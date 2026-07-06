"""Decode pristine R39 block2 records using msg_glyph_map (ascii region only)."""
import struct, json

PRISTINE = 'C:/programmieren/wizardrytranslation/extracted/packdata_raw/0039_type15.raw'
raw = open(PRISTINE, 'rb').read()
m = json.load(open('C:/programmieren/wizardrytranslation/data/msg_glyph_map.json', encoding='utf-8'))

header = [struct.unpack_from('<4I', raw, i*16) for i in range(15)]
B2_OFF, B2_SIZE = header[2][2], header[2][1]
block2 = raw[B2_OFF:B2_OFF+B2_SIZE]

recs, cur, pos = [], [], 0
while pos+1 < len(block2):
    w = struct.unpack_from('>H', block2, pos)[0]
    if w == 0xFFFF:
        recs.append(cur); cur = []
    else:
        cur.append(w)
    pos += 2

def gid_to_ascii(gid):
    v = m.get(str(gid))
    if isinstance(v, str) and len(v) == 1:
        o = ord(v)
        if 0x21 <= o <= 0x7E:
            return v
        if 0xFF01 <= o <= 0xFF5E:
            return chr(o-0xFEE0)
        return '?'  # non-ascii (kanji/kana)
    if gid == 0:
        return ' '
    return '?'

# decode g3..g58, showing only ascii-mappable; '?' = JP glyph
for g in [3,11,27,35,41,53]:  # sample including HP ones
    r = recs[g-1]
    s = ''
    for c in r:
        if c == 0xFFFE: s += '|'
        else: s += gid_to_ascii(c)
    asciicount = sum(1 for c in r if c != 0xFFFE and gid_to_ascii(c) not in ('?',))
    print(f"g{g}: ({len(r)} cells) {s!r}  ascii_glyphs={asciicount}")
