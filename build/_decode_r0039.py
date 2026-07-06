import struct, json, os

b = open('extracted/packdata_raw/0039_type15.raw', 'rb').read()
m = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))
gid2ch = {int(k): v for k, v in m.items()}

def decode_gid(v):
    if v == 0:
        return ''
    if v in (0xFFFF, 0xFFFE):
        return None
    ch = gid2ch.get(v)
    if ch:
        return ch
    return '〓'  # geta mark placeholder for unknown gid; record raw separately

# parse header
entries = []
o = 0
while o + 16 <= len(b):
    idx, size, off, z = struct.unpack_from('<IIII', b, o)
    if idx != len(entries) or off == 0 or off > len(b) or size == 0:
        break
    entries.append((idx, size, off)); o += 16

def u16be(buf, o):
    return (buf[o] << 8) | buf[o + 1]

out_lines = []
# Decode each block as type-01: leading u16BE offset table (byte offsets relative to block),
# then FFFE/FFFF-delimited glyph groups.
for (idx, size, off) in entries:
    blk = b[off:off + size]
    out_lines.append('==== BLOCK %d  off=%d size=%d ====' % (idx, off, size))
    # find the offset table: read u16BE until we hit a value that is FFFF or a glyph region.
    # Heuristic: offset table entries are increasing and < size. Stop at first 0xFFFF.
    # Then groups follow.
    # Split whole block into groups by 0xFFFF (group separator), each group may start FFFE.
    # We'll just scan u16BE, splitting on 0xFFFF.
    cells = [u16be(blk, p) for p in range(0, len(blk) - 1, 2)]
    # Detect offset-table prefix: leading run of strictly increasing values < size, ended by 0xFFFF
    groups = []
    cur = []
    raw_groups = []
    raw_cur = []
    for v in cells:
        if v == 0xFFFF:
            if raw_cur:
                raw_groups.append(raw_cur); raw_cur = []
        elif v == 0xFFFE:
            # group start marker; flush
            if raw_cur:
                raw_groups.append(raw_cur); raw_cur = []
        else:
            raw_cur.append(v)
    if raw_cur:
        raw_groups.append(raw_cur)
    for gi, g in enumerate(raw_groups):
        txt = ''.join(gid2ch.get(v, '') for v in g)
        unk = [v for v in g if v not in gid2ch and v != 0]
        # only show groups that decoded to something or look like text
        if not txt.strip() and not unk:
            continue
        out_lines.append('  g%d ids=%s' % (gi, g))
        out_lines.append('     JP=%s' % txt)
        if unk:
            out_lines.append('     UNK_IDS=%s' % unk)

open('build/_r0039_decoded.txt', 'w', encoding='utf-8').write('\n'.join(out_lines))
print('wrote build/_r0039_decoded.txt, blocks:', len(entries))
# Also dump a quick ascii count of unknown ids overall
all_unk = {}
for (idx, size, off) in entries:
    blk = b[off:off + size]
    for p in range(0, len(blk) - 1, 2):
        v = u16be(blk, p)
        if v not in (0, 0xFFFF, 0xFFFE) and v not in gid2ch:
            all_unk[v] = all_unk.get(v, 0) + 1
print('distinct unknown gids:', len(all_unk))
