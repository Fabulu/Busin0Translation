import struct, json, sys
sys.stdout.reconfigure(encoding='utf-8')
BASE = 'C:/Programmieren/wizardrytranslation'
with open(f'{BASE}/data/msg_glyph_map.json', 'r', encoding='utf-8') as f:
    glyph_map = json.load(f)
with open(f'{BASE}/extracted/packdata_resources/0041_type01.bin', 'rb') as f:
    data = f.read()
first_ffff = None
for off in range(0, len(data) - 1, 2):
    val = struct.unpack('>H', data[off:off+2])[0]
    if val == 0xFFFF:
        first_ffff = off
        break
stream_data = data[first_ffff:]
n = len(stream_data) // 2
vals = list(struct.unpack(f'>{n}H', stream_data[:n*2]))
messages_raw = []
cur = []
for v in vals:
    if v == 0xFFFF:
        if cur:
            messages_raw.append(cur)
        cur = []
    elif v == 0xFFFE:
        cur.append(('LB', None))
    elif v >= 0xFFC0:
        cur.append(('CT', v))
    else:
        cur.append(('G', v))
if cur:
    messages_raw.append(cur)
def dg(gid):
    s = str(gid)
    if s in glyph_map:
        return glyph_map[s]
    return None
all_unknown = set()
lines = []
for mi, msg in enumerate(messages_raw):
    decoded = []
    unknowns = []
    for typ, val in msg:
        if typ == 'LB':
            decoded.append('|')
        elif typ == 'CT':
            decoded.append(f'[C:{val:04X}]')
        elif typ == 'G':
            ch = dg(val)
            if ch:
                decoded.append(ch)
            else:
                decoded.append(f'[{val}]')
                unknowns.append(val)
                all_unknown.add(val)
    text = ''.join(decoded)
    lines.append(f'MSG {mi}: {text}')
    if unknowns:
        lines.append(f'  UNK: {unknowns}')
with open(f'{BASE}/build/r41_decoded.txt', 'w', encoding='utf-8') as f:
    f.write(f'Resource 0041: {len(messages_raw)} messages\n')
    for line in lines:
        f.write(line + '\n')
    f.write(f'Unknown IDs: {sorted(all_unknown)}\n')
    f.write(f'Count: {len(all_unknown)}\n')
print('Done')
