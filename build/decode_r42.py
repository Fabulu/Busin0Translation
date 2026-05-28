import struct, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
with open('C:/Programmieren/wizardrytranslation/data/msg_glyph_map.json', 'r', encoding='utf-8') as f:
    glyph_map = json.load(f)
with open('C:/Programmieren/wizardrytranslation/extracted/packdata_resources/0042_type01.bin', 'rb') as f:
    data = f.read()
values = struct.unpack(f'>{len(data)//2}H', data)
messages = []
current_msg = []
unknown_glyphs = set()
for v in values:
    if v == 0xFFFF:
        messages.append(current_msg)
        current_msg = []
    elif v == 0xFFFE:
        current_msg.append(('newline', v))
    elif v >= 0xFFC0:
        current_msg.append(('ctrl', v))
    elif str(v) in glyph_map:
        current_msg.append(('char', v, glyph_map[str(v)]))
    else:
        current_msg.append(('unknown', v))
        unknown_glyphs.add(v)
if current_msg:
    messages.append(current_msg)
out = open('C:/Programmieren/wizardrytranslation/build/r42_decoded.txt', 'w', encoding='utf-8')
out.write(f'Number of messages: {len(messages)}\n')
out.write(f'Unknown glyph IDs: {sorted(unknown_glyphs)}\n\n')
for i, msg in enumerate(messages):
    text = ''
    for token in msg:
        if token[0] == 'char':
            text += token[2]
        elif token[0] == 'newline':
            text += '\n'
        elif token[0] == 'ctrl':
            text += f'[CTRL:{token[1]:04X}]'
        elif token[0] == 'unknown':
            text += f'[?{token[1]}]'
    out.write(f'=== Message {i} ===\n')
    out.write(text + '\n\n')
out.close()
print('Done')
