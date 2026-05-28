import struct, json, os, glob

gmap = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))
data = open('extracted/packdata_resources/0038_type01.bin', 'rb').read()

# Find first FFFF on 2-byte boundary
pos = 0
first_ffff = -1
while True:
    found = data.find(b'\xff\xff', pos)
    if found == -1:
        break
    if found % 2 == 0:
        first_ffff = found
        break
    pos = found + 1

print(f"R38 size: {len(data)}, first FFFF at: {hex(first_ffff)}")
print(f"Header size: {first_ffff} bytes")

# Show header bytes
print(f"\nR38 header ({first_ffff} bytes):")
for i in range(0, min(first_ffff, 128), 16):
    hex_str = ' '.join(f'{b:02x}' for b in data[i:i+16])
    print(f"  {i:04x}: {hex_str}")

# Decode entire glyph stream
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
        cur.append('|')  # newline marker
    elif v >= 0xFFC0:
        cur.append(f'<{v:04x}>')
    else:
        ch = gmap.get(str(v), f'[{v}]')
        cur.append(ch)
if cur:
    messages.append(cur)

print(f"\nR38 has {len(messages)} messages:")
for i, msg in enumerate(messages):
    text = ''.join(msg)
    if len(text) > 120:
        text = text[:120] + '...'
    print(f"  [{i:3d}] {text}")

# Now check: does the chargen screen use a DIFFERENT resource?
# Look at resources 35-45 which are in the chargen area
print("\n\n=== Checking nearby resources for chargen UI ===")
for rid in range(34, 50):
    fname = f'{rid:04d}'
    matches = glob.glob(f'extracted/packdata_resources/{fname}_*.bin')
    if matches:
        fpath = matches[0]
        ftype = os.path.basename(fpath).split('_')[1].replace('.bin','')
        fsize = os.path.getsize(fpath)
        print(f"  R{rid}: {ftype}, {fsize} bytes")
