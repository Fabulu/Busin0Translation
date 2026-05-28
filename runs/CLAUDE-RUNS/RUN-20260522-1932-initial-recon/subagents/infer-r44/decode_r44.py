import struct, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("C:/Programmieren/wizardrytranslation/extracted/packdata_resources/0044_type01.bin", "rb") as f:
    data = f.read()

with open("C:/Programmieren/wizardrytranslation/data/msg_glyph_map.json", "r", encoding="utf-8") as f:
    glyph_map = {int(k): v for k, v in json.load(f).items()}

print(f"File size: {len(data)} bytes")

header_end = 234
n32 = header_end // 4
print(f"Header as LE uint32 ({n32} entries):")
for i in range(n32):
    val = struct.unpack("<I", data[i*4:i*4+4])[0]
    print(f"  [{i}] = {val} (0x{val:04X})")

stream = data[header_end:]
n_vals = len(stream) // 2
vals = struct.unpack(f">{n_vals}H", stream[:n_vals*2])

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

all_unknown = set()
for mi, msg in enumerate(messages):
    decoded = []
    unknowns_in_msg = []
    for g in msg:
        if g in glyph_map:
            decoded.append(glyph_map[g])
        else:
            decoded.append(f"[{g}]")
            unknowns_in_msg.append(g)
            all_unknown.add(g)
    text = "".join(decoded)
    print(f"Msg {mi}: {text}")
    if unknowns_in_msg:
        print(f"  Unknown glyphs: {unknowns_in_msg}")

print(f"\nAll unknown glyph IDs ({len(all_unknown)}): {sorted(all_unknown)}")
