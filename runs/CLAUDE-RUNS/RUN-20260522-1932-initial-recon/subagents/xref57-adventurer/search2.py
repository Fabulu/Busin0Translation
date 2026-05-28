import struct
import os
import json

RESDIR = "C:/Programmieren/wizardrytranslation/extracted/packdata_resources"
CLASSIFICATION = "C:/Programmieren/wizardrytranslation/dumps/resource_classification.json"

with open(CLASSIFICATION, "r") as f:
    cls = json.load(f)
msg_indices = cls["msg_resource_indices"]

def find_resource_file(idx):
    for fname in os.listdir(RESDIR):
        if fname.startswith(f"{idx:04d}_"):
            return os.path.join(RESDIR, fname)
    return None

def read_resource(idx):
    path = find_resource_file(idx)
    if not path:
        return None
    with open(path, "rb") as f:
        return f.read()

def extract_messages(data):
    messages = []
    pos = 0
    while pos < len(data) - 1:
        val = struct.unpack(">H", data[pos:pos+2])[0]
        if val == 0xFFFF:
            break
        pos += 2
    while pos < len(data) - 1:
        val = struct.unpack(">H", data[pos:pos+2])[0]
        if val != 0xFFFF:
            pos += 2
            continue
        msg_start = pos + 2
        glyphs = []
        fffe_count = 0
        p = msg_start
        while p < len(data) - 1:
            v = struct.unpack(">H", data[p:p+2])[0]
            if v == 0xFFFF:
                break
            if v == 0xFFFE:
                glyphs.append(0xFFFE)
                fffe_count += 1
            else:
                glyphs.append(v)
            p += 2
        if glyphs:
            messages.append({"offset": pos, "glyphs": glyphs, "fffe_count": fffe_count})
        pos = p
    return messages

results = []
for idx in msg_indices:
    data = read_resource(idx)
    if data is None:
        continue
    messages = extract_messages(data)
    for msg_idx, msg in enumerate(messages):
        g = msg["glyphs"]
        if msg["fffe_count"] != 2:
            continue
        has_kaka = False
        for i in range(len(g)-1):
            if g[i] == 91 and g[i+1] == 91:
                has_kaka = True
                break
        if not has_kaka:
            continue
        gset = set(g)
        if 95 not in gset or 89 not in gset or 126 not in gset:
            continue
        non_ctrl = [x for x in g if x != 0xFFFE]
        if len(non_ctrl) < 20 or len(non_ctrl) > 35:
            continue
        non_ctrl_start = [x for x in g[:5] if x != 0xFFFE]
        if 95 not in non_ctrl_start[:3]:
            continue
        results.append({
            "resource_idx": idx,
            "msg_idx": msg_idx,
            "offset": msg["offset"],
            "glyph_count": len(non_ctrl),
            "fffe_count": msg["fffe_count"],
            "glyphs": g
        })

print(f"Found {len(results)} matching messages")
for r in results:
    print(f"Resource {r['resource_idx']}, message {r['msg_idx']}, offset 0x{r['offset']:X}")
    print(f"  Glyph count: {r['glyph_count']}, FFFE count: {r['fffe_count']}")
    print(f"  Glyphs: {r['glyphs']}")

with open("C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260522-1932-initial-recon/subagents/xref57-adventurer/search_results.json", "w") as f:
    json.dump(results, f, indent=2)

