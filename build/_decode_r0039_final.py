import struct, json

b = open('extracted/packdata_raw/0039_type15.raw', 'rb').read()
m = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))
gid2ch = {int(k): v for k, v in m.items()}

# Composite tier+element glyphs for the damage template (screenshot-confirmed: 317 == "M雷").
# These cells render a single pre-composed magnitude+element glyph on the magic screen.
COMPOSITE = {317: 'M雷', 987: 'S雷', 331: 'L雷', 606: '無'}


def ch(v):
    if v in COMPOSITE:
        return COMPOSITE[v]
    return gid2ch.get(v, '◇')


entries = []
o = 0
while o + 16 <= len(b):
    idx, size, off, z = struct.unpack_from('<IIII', b, o)
    if idx != len(entries) or off == 0 or size == 0:
        break
    entries.append((idx, size, off)); o += 16


def u16be(buf, o):
    return (buf[o] << 8) | buf[o + 1]


def block_groups(idx):
    _, size, off = entries[idx]
    blk = b[off:off + size]
    cells = [u16be(blk, p) for p in range(0, len(blk) - 1, 2)]
    gs = []; cur = []
    for v in cells:
        if v in (0xFFFF, 0xFFFE):
            if cur:
                gs.append(cur); cur = []
        else:
            cur.append(v)
    if cur:
        gs.append(cur)
    return gs


names = block_groups(1)[1:]
descs = block_groups(2)[1:]

result = {'names': [], 'descs': []}
for gi, g in enumerate(names):
    txt = ''.join(ch(v) for v in g if v != 0)
    result['names'].append({'g': gi + 2, 'jp': txt, 'ids': g})
for gi, g in enumerate(descs):
    txt = ''.join(ch(v) for v in g if v != 0)
    result['descs'].append({'g': gi + 2, 'jp': txt, 'ids': g})

json.dump(result, open('build/_spell_final.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('names', len(result['names']), 'descs', len(result['descs']))
