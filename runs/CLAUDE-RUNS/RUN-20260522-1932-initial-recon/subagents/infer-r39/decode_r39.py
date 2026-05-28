import struct, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RESFILE = "C:/Programmieren/wizardrytranslation/extracted/packdata_resources/0039_type15.bin"
GMAP_FILE = "C:/Programmieren/wizardrytranslation/data/msg_glyph_map.json"
with open(RESFILE, "rb") as f:
    data = f.read()
with open(GMAP_FILE, encoding="utf-8") as f:
    gmap = json.load(f)
n_table = 0
for e in range(256):
    off = e * 16
    if off + 16 > len(data): break
    entry = struct.unpack("<4I", data[off:off+16])
    if entry[0] == e + 1:
        n_table = e + 1
    else:
        break
table_end = n_table * 16
print(f"Table entries: {n_table}, table_end: {table_end}")
glyph_start = len(data)
for off in range(table_end, len(data) - 1, 2):
    val = struct.unpack(">H", data[off:off+2])[0]
    if val == 0xFFFF or val == 0xFFFE:
        glyph_start = off
        break
print(f"Glyph start: {glyph_start}")
between = data[table_end:glyph_start]
n16 = len(between) // 2
if n16 > 0:
    be16 = list(struct.unpack(f">{n16}H", between[:n16*2]))
    print(f"Header msg count: {be16[0]}")
messages = []
i = glyph_start
current_msg = []
while i < len(data) - 1:
    val = struct.unpack(">H", data[i:i+2])[0]
    if val == 0xFFFF:
        if current_msg:
            messages.append(current_msg)
        current_msg = []
    elif val == 0xFFFE:
        if current_msg:
            messages.append(current_msg)
            current_msg = []
    else:
        current_msg.append((val, gmap.get(str(val))))
    i += 2
if current_msg:
    messages.append(current_msg)
print(f"Total messages: {len(messages)}")
all_unknowns = set()
for idx, msg in enumerate(messages):
    decoded = ""
    unknowns = []
    for val, g in msg:
        if g:
            decoded += g
        else:
            decoded += f"[{val}]"
            unknowns.append(val)
    print(f"  Msg {idx}: {decoded}")
    if unknowns:
        print(f"    Unknown IDs: {unknowns}")
        all_unknowns.update(unknowns)
print(f"All unknown glyph IDs: {sorted(all_unknowns)}")
print(f"Count of unknown IDs: {len(all_unknowns)}")

