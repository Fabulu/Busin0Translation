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
                        if tg[0] > 200 and tg[3] > 200:
                            print(f'SPEAKER: res={idx} off=0x{i:X} gl={tg} shi={shi_id}')
                            k = j
                            if k < len(data) - 1 and struct.unpack('>H', data[k:k+2])[0] == 0xFFFF:
                                ng = []
                                m = k + 2
                                while m < len(data) - 1:
                                    g2 = struct.unpack('>H', data[m:m+2])[0]
                                    if g2 == 0xFFFF:
                                        break
                                    ng.append(g2)
                                    m += 2
                                ntg = [g for g in ng if g < 0xFF00]
                                print(f'  NEXT: tlen={len(ntg)} gl={ng[:50]}')
            i = j
        else:
            i += 2
print('DONE')
