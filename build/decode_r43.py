import struct, json, os, sys

RES_PATH = "C:/Programmieren/wizardrytranslation/extracted/packdata_resources/0043_type01.bin"
GLYPH_MAP_PATH = "C:/Programmieren/wizardrytranslation/data/msg_glyph_map.json"
OUTPUT_PATH = "C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260522-1932-initial-recon/subagents/infer-r43/decoded_r43.json"
TEXT_PATH = "C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260522-1932-initial-recon/subagents/infer-r43/decoded_r43.txt"

with open(GLYPH_MAP_PATH, "r", encoding="utf-8") as f:
    glyph_map = json.load(f)

gm = {int(k): v for k, v in glyph_map.items()}

with open(RES_PATH, "rb") as f:
    data = f.read()

print(f"File size: {len(data)} bytes")

first_ffff = None
for off in range(0, len(data) - 1, 2):
    val = struct.unpack(">H", data[off:off+2])[0]
    if val == 0xFFFF:
        first_ffff = off
        break

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

decoded = []
unknown_ids = set()
lines = []
for mi, msg in enumerate(messages):
    text = ""
    unknowns = []
    for gi, gid in enumerate(msg):
        if gid in gm:
            text += gm[gid]
        else:
            text += "[" + str(gid) + "]"
            unknowns.append({"position": gi, "glyph_id": gid})
            unknown_ids.add(gid)
    decoded.append({
        "msg_index": mi,
        "glyph_ids": msg,
        "text": text,
        "unknowns": unknowns
    })
    lines.append(f"MSG {mi:3d}: {text}")

with open(TEXT_PATH, "w", encoding="utf-8") as f:
    for line in lines:
        f.write(line + "\n")

print(f"Unknown glyph IDs: {sorted(unknown_ids)}")
print(f"Total unknown IDs: {len(unknown_ids)}")
print(f"Wrote text to {TEXT_PATH}")

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump({"messages": decoded, "unknown_glyph_ids": sorted(unknown_ids)}, f, ensure_ascii=False, indent=2)
print(f"Saved to {OUTPUT_PATH}")

