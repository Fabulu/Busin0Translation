import struct, json

gmap = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))
rev = {v: int(k) for k, v in gmap.items()}

# Check R38 context
data = open('extracted/packdata_resources/0038_type01.bin', 'rb').read()
print(f'R38 size: {len(data)} bytes')

labels = {'職業': [rev[c] for c in '職業'], '知恵': [rev[c] for c in '知恵'],
          '敏捷度': [rev[c] for c in '敏捷度'], '幸運度': [rev[c] for c in '幸運度']}

for jp, ids in labels.items():
    target = b''.join(struct.pack('>H', g) for g in ids)
    pos = 0
    while True:
        pos = data.find(target, pos)
        if pos < 0: break
        start = max(0, pos - 20)
        end = min(len(data), pos + len(target) + 20)
        ctx = data[start:end]
        glyphs = []
        for i in range(0, len(ctx) - 1, 2):
            g = struct.unpack('>H', ctx[i:i+2])[0]
            ch = gmap.get(str(g), f'[{g}]')
            glyphs.append(ch)
        print(f'{jp} at offset {hex(pos)}: {"".join(glyphs)}')
        pos += 2

# Now check: are these labels in a MSG text format or raw binary table?
# Look at the R38 header
print(f'\nR38 first 64 bytes:')
for i in range(0, 64, 16):
    hex_str = ' '.join(f'{b:02x}' for b in data[i:i+16])
    print(f'  {i:04x}: {hex_str}')

# Check R39 (type15) - what type is this?
data39 = open('extracted/packdata_resources/0039_type15.bin', 'rb').read()
print(f'\nR39 size: {len(data39)} bytes, type15')
print(f'R39 first 64 bytes:')
for i in range(0, min(64, len(data39)), 16):
    hex_str = ' '.join(f'{b:02x}' for b in data39[i:i+16])
    print(f'  {i:04x}: {hex_str}')

# Where are the missing labels? Check if individual chars exist
missing_labels = {'種族': [rev[c] for c in '種族'], '属性': [rev[c] for c in '属性'],
                  '信仰心': [rev[c] for c in '信仰心'], '生命力': [rev[c] for c in '生命力']}

print('\nMissing label individual char search in R38:')
for jp, ids in missing_labels.items():
    for i, (ch, gid) in enumerate(zip(jp, ids)):
        target = struct.pack('>H', gid)
        count = data.count(target)
        print(f'  {ch} (glyph {gid}): {count} occurrences in R38')

# Try searching ALL resources for the single char 種 (glyph 967)
import os
print(f'\nSearching ALL resources for 種 (glyph 967):')
resdir = 'extracted/packdata_resources'
target_shuu = struct.pack('>H', 967)
for fname in sorted(os.listdir(resdir)):
    d = open(os.path.join(resdir, fname), 'rb').read()
    c = d.count(target_shuu)
    if c > 0:
        print(f'  {fname}: {c} occurrences')
