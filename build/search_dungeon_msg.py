import struct, os, json

RES_DIR = r"C:/Programmieren/wizardrytranslation/extracted/packdata_resources"

def find_resource_file(idx):
    prefix = f"{idx:04d}_"
    for fn in os.listdir(RES_DIR):
        if fn.startswith(prefix) and fn.endswith(".bin"):
            return os.path.join(RES_DIR, fn)
    return None

def extract_glyph_stream(filepath):
    with open(filepath, "rb") as f:
        data = f.read()
    if len(data) < 4:
        return []
    first_ffff = None
    for off in range(0, len(data) - 1, 2):
        val = struct.unpack(">H", data[off:off+2])[0]
        if val == 0xFFFF:
            first_ffff = off
            break
    if first_ffff is None:
        return []
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
    return messages

results = []

for idx in range(0, 2883):
    fp = find_resource_file(idx)
    if fp is None:
        continue
    try:
        messages = extract_glyph_stream(fp)
    except:
        continue
    for mi, msg in enumerate(messages):
        if len(msg) == 12 and msg[11] == 87 and msg[7] == 95:
            hex_str = " ".join(f"{g:04X}" for g in msg)
            results.append({
                "resource": idx,
                "msg_index": mi,
                "glyphs": msg,
                "hex": hex_str
            })
            print(f"MATCH: res={idx} msg#{mi}: {hex_str}")

if not results:
    print("No exact match. Relaxing to: 12 glyphs, 87 at end, 95 anywhere...")
    for idx in range(0, 2883):
        fp = find_resource_file(idx)
        if fp is None:
            continue
        try:
            messages = extract_glyph_stream(fp)
        except:
            continue
        for mi, msg in enumerate(messages):
            if len(msg) == 12 and msg[-1] == 87 and 95 in msg:
                hex_str = " ".join(f"{g:04X}" for g in msg)
                results.append({
                    "resource": idx,
                    "msg_index": mi,
                    "glyphs": msg,
                    "hex": hex_str
                })
                print(f"MATCH: res={idx} msg#{mi}: {hex_str}")

if not results:
    print("Still no match. Showing all 12-glyph msgs ending in 87...")
    for idx in range(0, 2883):
        fp = find_resource_file(idx)
        if fp is None:
            continue
        try:
            messages = extract_glyph_stream(fp)
        except:
            continue
        for mi, msg in enumerate(messages):
            if len(msg) == 12 and msg[-1] == 87:
                hex_str = " ".join(f"{g:04X}" for g in msg)
                print(f"  res={idx} msg#{mi}: {hex_str}")

print(f"Total exact matches: {len(results)}")
