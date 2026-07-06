import struct, json

b = open('extracted/packdata_raw/0039_type15.raw', 'rb').read()
m = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))
gid2ch = {int(k): v for k, v in m.items()}

# --- Overrides for the spell font, derived from on-screen ground truth (bigboo capture)
# Teal description in RAM = 692 17 672 133 317 515 511 ... and the screen showed
#   敵1体にM雷属性ダメージを与える  (Deals M lightning-element damage to a single enemy)
# So the following gids render differently on the magic screen than the global map claims:
OVR = {
    692: '敵',   # enemy  (global map mis-labels as 宝)
    317: 'M',    # magnitude tier M
    987: 'S',    # magnitude tier S  (variant slot)
    331: 'L',    # magnitude tier L  (variant slot)
    606: '無',   # non-element 無(属性) variant
    515: '雷',   # lightning element (global map mis-labels as 炎)
    768: '体',   # target-counter variant (容->体)
    653: '全',   # 全(体)/全(員) "all"
    988: '？',   # unknown glyph placeholder
}
# NOTE: element/tier slot values 317/987/331/606/515 are POSITIONAL in the
# "敵N体に[TIER][ELEM]属性ダメージを与える" template. Different spells fill them
# with the actual tier/element glyph; the override above reflects the Teal record.
# For other elements the same template slot holds a different gid (火/氷/風/土/聖/闇)
# which the global map already covers where present.


def ch(v):
    if v in OVR:
        return OVR[v]
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


def is_offset_table(g):
    # g0 is the offset table: alternating value,0 with increasing values
    if len(g) < 6:
        return False
    nz = [x for x in g if x != 0]
    return len(nz) > 3 and all(g[i] == 0 for i in range(1, len(g), 2)) is False and sorted(nz) == nz


out = []
NAMES_BLK = 1
DESC_BLK = 2
for label, bi in [('NAMES', NAMES_BLK), ('DESCRIPTIONS', DESC_BLK)]:
    gs = block_groups(bi)
    out.append('==== %s (block %d) ====' % (label, bi))
    for gi, g in enumerate(gs):
        if gi == 0:
            continue  # offset table
        txt = ''.join(ch(v) for v in g if v != 0)
        if not txt:
            continue
        out.append('g%d\t%s\tids=%s' % (gi, txt, g))

open('build/_spell_decoded_v2.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('wrote build/_spell_decoded_v2.txt')
print('NAMES groups:', len(block_groups(NAMES_BLK)) - 1)
print('DESC groups:', len(block_groups(DESC_BLK)) - 1)
