import struct, os, json
RESDIR = r'C:\Programmieren\wizardrytranslation\extracted\packdata_resources'
with open(r'C:\Programmieren\wizardrytranslation\dumps\resource_classification.json') as f:
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
            msg_glyphs = []
            fffe_count = 0
            j = i + 2
            while j < len(data) - 1:
                v = struct.unpack('>H', data[j:j+2])[0]
                if v == 0xFFFF:
                    break
                elif v == 0xFFFE:
                    msg_glyphs.append('FFFE')
                    fffe_count += 1
                else:
                    msg_glyphs.append(v)
                j += 2
            messages.append({'glyphs': msg_glyphs, 'fffe_count': fffe_count, 'offset': i})
            i = j
        else:
            i += 2
    return messages
found = []
for idx in msg_indices:
    path = find_resource_file(idx)
    if not path:
        continue
    with open(path, 'rb') as f:
        data = f.read()
    messages = parse_messages(data)
    for mi, msg in enumerate(messages):
        glyphs = msg['glyphs']
        text_glyphs = [g for g in glyphs if g != 'FFFE']
        if len(text_glyphs) != 38 or msg['fffe_count'] != 2:
            continue
        lines = []
        current_line = []
        for g in glyphs:
            if g == 'FFFE':
                lines.append(current_line)
                current_line = []
            else:
                current_line.append(g)
        lines.append(current_line)
        if len(lines) != 3:
            continue
        if len(lines[0]) != 11 or len(lines[1]) != 15 or len(lines[2]) != 12:
            continue
        has_repeat = lines[0][1] == lines[0][8]
        found.append({'resource': idx, 'msg_index': mi, 'has_repeat_pos1_8': has_repeat, 'lines': lines})
        print(f'Res {idx} msg {mi}: repeat={has_repeat} L0={lines[0]} L1={lines[1]} L2={lines[2]}')
print(f'\nTotal found: {len(found)}')
print(f'With repeat at pos 1,8: {sum(1 for f in found if f[has_repeat_pos1_8])}')
with open(r'C:\Programmieren\wizardrytranslation\runs\CLAUDE-RUNS\RUN-20260522-1932-initial-recon\subagents\xref53-knight\candidates2.json', 'w') as f:
    json.dump(found, f, indent=2, default=str)
