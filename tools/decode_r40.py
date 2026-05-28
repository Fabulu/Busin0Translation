import struct, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

RES_PATH = 'C:/Programmieren/wizardrytranslation/extracted/packdata_resources/0040_type01.bin'
MAP_PATH = 'C:/Programmieren/wizardrytranslation/data/msg_glyph_map.json'

with open(RES_PATH, 'rb') as f:
    data = f.read()

with open(MAP_PATH, 'r', encoding='utf-8') as f:
    glyph_map = json.load(f)

print(f'File size: {len(data)} bytes')

first_ffff = None
for off in range(0, len(data) - 1, 2):
    val = struct.unpack('>H', data[off:off+2])[0]
    if val == 0xFFFF:
        first_ffff = off
        break

print(f'First FFFF at offset: {first_ffff}')

stream = data[first_ffff:]
n = len(stream) // 2
vals = struct.unpack(f'>{n}H', stream[:n*2])

messages = []
cur = []
for v in vals:
    if v == 0xFFFF:
        if cur:
            messages.append(cur)
        cur = []
    elif v == 0xFFFE:
        if cur:
            messages.append(cur)
        cur = []
    elif v >= 0xFFC0:
        pass
    else:
        cur.append(v)
if cur:
    messages.append(cur)

print(f'Number of messages: {len(messages)}')

all_unknowns = set()
for i, msg in enumerate(messages):
    decoded = ''
    unknowns = []
    for g in msg:
        gs = str(g)
        if gs in glyph_map:
            decoded += glyph_map[gs]
        else:
            decoded += f'[{g}]'
            unknowns.append(g)
    print(f'MSG {i:3d}: {decoded}')
    if unknowns:
        unique_unk = sorted(set(unknowns))
        print(f'         unknowns: {unique_unk}')
        all_unknowns.update(unknowns)

print(f'\nAll unknown glyph IDs: {sorted(all_unknowns)}')
print(f'Total unique unknowns: {len(all_unknowns)}')
