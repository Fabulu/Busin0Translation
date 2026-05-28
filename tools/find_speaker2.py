import struct, os, json
RESDIR = 'C:/Programmieren/wizardrytranslation/extracted/packdata_resources'
with open('C:/Programmieren/wizardrytranslation/dumps/resource_classification.json') as f:
    cls = json.load(f)
msg_indices = cls['msg_resource_indices']
files = os.listdir(RESDIR)
fmap = {}
for f in files:
    try:
        fmap[int(f[:4])] = os.path.join(RESDIR, f)
    except:
        pass
hits = []
for idx in msg_indices:
    if idx not in fmap:
        continue
    with open(fmap[idx], 'rb') as fh:
        data = fh.read()
    i = 0
    while i < len(data) - 1:
        val = struct.unpack('>H', data[i:i+2])[0]
        if val == 0xFFFF:
            gl = []
            j = i + 2
            while j < len(data) - 1:
                g = struct.unpack('>H', data[j:j+2])[0]
                if g == 0xFFFF:
                    break
                gl.append(g)
                j += 2
            tg = [g for g in gl if g < 0xFF00]
            if len(tg) == 4:
                for shi_id in [126, 128]:
                    if tg[1] == shi_id and tg[2] == 87:
                        hits.append((idx, i, tg, shi_id))
            i = j
        else:
            i += 2
print(f'Found {len(hits)} matches')
for idx, off, tg, shi in hits[:20]:
    print(f'  res={idx} off=0x{off:X} gl={tg} shi={shi}')
print()
pair_hits = []
for idx in msg_indices:
    if idx not in fmap:
        continue
    with open(fmap[idx], 'rb') as fh:
        data = fh.read()
    i = 0
    while i < len(data) - 1:
        val = struct.unpack('>H', data[i:i+2])[0]
        if val == 0xFFFF:
            gl = []
            j = i + 2
            while j < len(data) - 1:
                g = struct.unpack('>H', data[j:j+2])[0]
                if g == 0xFFFF:
                    break
                gl.append(g)
                j += 2
            tg = [g for g in gl if g < 0xFF00]
            for p in range(len(tg) - 1):
                for shi_id in [126, 128]:
                    if tg[p] == shi_id and tg[p+1] == 87:
                        pair_hits.append((idx, i, p, len(tg), tg[:20]))
                        break
            i = j
        else:
            i += 2
print(f'Found {len(pair_hits)} shi+i pairs')
for idx, off, p, tlen, tg in pair_hits[:30]:
    print(f'  res={idx} off=0x{off:X} pos={p} tlen={tlen} gl={tg}')
print('DONE')
