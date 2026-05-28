import struct, json

with open('C:/Programmieren/wizardrytranslation/extracted/packdata_resources/0041_type01.bin', 'rb') as f:
    data = f.read()

print(f'File size: {len(data)} bytes')

first_ffff = None
for off in range(0, len(data) - 1, 2):
    val = struct.unpack('>H', data[off:off+2])[0]
    if val == 0xFFFF:
        first_ffff = off
        break

print(f'First FFFF at offset: {first_ffff}')

header_count = first_ffff // 4
offsets = []
for i in range(header_count):
    val = struct.unpack('>I', data[i*4:i*4+4])[0]
    offsets.append(val)

print(f'Header entries: {header_count}')
for i, o in enumerate(offsets):
    print(f'  [{i}] = 0x{o:04x} ({o})')

stream_data = data[first_ffff:]
n = len(stream_data) // 2
vals = list(struct.unpack(f'>{n}H', stream_data[:n*2]))

print(f'Glyph stream: {len(vals)} uint16 values')

messages = []
cur = []
for v in vals:
    if v == 0xFFFF:
        if cur:
            messages.append(cur)
        cur = []
    elif v == 0xFFFE:
        cur.append('LINEBREAK')
    elif v >= 0xFFC0:
        cur.append(f'CTRL_{v:04X}')
    else:
        cur.append(v)
if cur:
    messages.append(cur)

print(f'Messages found: {len(messages)}')
for i, msg in enumerate(messages):
    print(f'  MSG {i}: {msg}')
