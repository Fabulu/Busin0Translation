import struct, os, json
RESDIR = r'C:/Programmieren/wizardrytranslation/extracted/packdata_resources'
with open(r'C:/Programmieren/wizardrytranslation/dumps/resource_classification.json') as f:
    cls = json.load(f)
msg_indices = cls['msg_resource_indices']
def find_resource_file(idx):
    for fname in os.listdir(RESDIR):
        if fname.startswith(f'{idx:04d}_'):
            return os.path.join(RESDIR, fname)
    return None
def parse_messages(data):
    messages = []
    i = 0
    while i < len(data) - 1:
        val = struct.unpack('>H', data[i:i+2])[0]
        if val == 0xFFFF:
            mg = []
            fc = 0
            j = i + 2
            while j < len(data) - 1:
                v = struct.unpack('>H', data[j:j+2])[0]
                if v == 0xFFFF:
                    break
                elif v == 0xFFFE:
                    mg.append('FFFE')
                    fc += 1
                else:
                    mg.append(v)
                j += 2
            messages.append({'g': mg, 'fc': fc, 'off': i})
            i = j
        else:
            i += 2
    return messages
total_msgs = 0
results_2fffe = []
for idx in msg_indices:
    path = find_resource_file(idx)
    if not path:
        continue
    with open(path, 'rb') as f:
        data = f.read()
    messages = parse_messages(data)
    total_msgs += len(messages)
    for mi, msg in enumerate(messages):
        tg = [x for x in msg['g'] if x != 'FFFE']
        if msg['fc'] == 2 and 30 <= len(tg) <= 50:
            lines = []
            cur = []
            for g in msg['g']:
                if g == 'FFFE':
                    lines.append(cur)
                    cur = []
                else:
                    cur.append(g)
            lines.append(cur)
            results_2fffe.append({'r': idx, 'm': mi, 'tg': len(tg), 'ls': [len(l) for l in lines], 'lines': lines})
print(f'Total messages: {total_msgs}')
print(f'Messages with 2 FFFE and 30-50 glyphs: {len(results_2fffe)}')
for r in results_2fffe:
    print(f'  Res {r[r]} msg {r[m]}: {r[tg]} glyphs, lines={r[ls]}')
with open(r'C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260522-1932-initial-recon/subagents/xref53-knight/c3.json', 'w') as f:
    json.dump(results_2fffe, f, indent=2, default=str)
