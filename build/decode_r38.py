import struct, json, sys
sys.stdout.reconfigure(encoding="utf-8")

with open("C:/Programmieren/wizardrytranslation/data/msg_glyph_map.json","r",encoding="utf-8") as f:
    gmap = json.load(f)

filepath = "C:/Programmieren/wizardrytranslation/extracted/packdata_resources/0038_type01.bin"
with open(filepath, "rb") as f:
    data = f.read()

first_ffff = None
for off in range(0, len(data) - 1, 2):
    val = struct.unpack(">H", data[off:off+2])[0]
    if val == 0xFFFF:
        first_ffff = off
        break

print(f"File size: {len(data)}")
print(f"First FFFF at offset: {first_ffff}")

stream_data = data[first_ffff:]
n = len(stream_data) // 2
vals = struct.unpack(f">{n}H", stream_data[:n*2])

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

print(f"Total messages: {len(messages)}")
total_glyphs = sum(len(m) for m in messages)
print(f"Total glyphs: {total_glyphs}")

for i, msg in enumerate(messages):
    decoded = []
    known = 0
    for g in msg:
        ch = gmap.get(str(g))
        if ch:
            decoded.append(ch)
            known += 1
        else:
            decoded.append(f"[{g}]")
    coverage = known / len(msg) * 100 if msg else 0
    text = "".join(decoded)
    print(f"MSG {i:3d} ({coverage:5.1f}%): {text}")

print("\n=== RAW GLYPH IDS ===")
for i, msg in enumerate(messages):
    print(f"MSG {i}: {msg}")

