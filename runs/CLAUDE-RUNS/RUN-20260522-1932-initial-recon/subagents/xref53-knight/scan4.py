import struct, os, json
RESDIR = r'C:/Programmieren/wizardrytranslation/extracted/packdata_resources'
with open(r'C:/Programmieren/wizardrytranslation/dumps/resource_classification.json') as f:
    cls = json.load(f)
msg_indices = cls['msg_resource_indices']
def find_resource_file(idx):
    for fname in os.listdir(RESDIR):
        if fname.startswith(str(idx).zfill(4) + '_'):
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
            messages.append((mg, fc, i))
            i = j
        else:
            i += 2
    return messages
total_msgs = 0
results = []
for idx in msg_indices:
    path = find_resource_file(idx)
    if not path:
        continue
    with open(path, 'rb') as f:
        data = f.read()
    messages = parse_messages(data)
    total_msgs += len(messages)
    for mi, (mg, fc, off) in enumerate(messages):
        tg = [x for x in mg if x != 'FFFE']
        if fc == 2 and 30 <= len(tg) <= 50:
            lines = []
            cur = []
            for g in mg:
                if g == 'FFFE':
                    lines.append(cur)
                    cur = []
                else:
                    cur.append(g)
            lines.append(cur)
            ll = [len(l) for l in lines]
            results.append([idx, mi, len(tg), ll, lines])
print('Total messages: ' + str(total_msgs))
print('Candidates (2 FFFE, 30-50 glyphs): ' + str(len(results)))
for entry in results:
    print('  Res %d msg %d: %d glyphs, lines=%s' % (entry[0], entry[1], entry[2], str(entry[3])))
with open(r'C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260522-1932-initial-recon/subagents/xref53-knight/c4.json', 'w') as f:
    json.dump(results, f, indent=2, default=str)
