import struct, os, json

RES_DIR = r"C:/Programmieren/wizardrytranslation/extracted/packdata_resources"

def find_resource_file(idx):
    prefix = f"{idx:04d}_"
    for fn in os.listdir(RES_DIR):
        if fn.startswith(prefix) and fn.endswith(".bin"):
            return os.path.join(RES_DIR, fn)
    return None

def extract_messages(filepath):
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

print("=== 12-glyph messages ending in glyph 87 ===")
count = 0
for idx in range(0, 2883):
    fp = find_resource_file(idx)
    if fp is None:
        continue
    try:
        messages = extract_messages(fp)
    except:
        continue
    for mi, msg in enumerate(messages):
        if len(msg) == 12 and msg[-1] == 87:
            print(f"  res={idx} msg#{mi}: {msg}")
            count += 1

print(f"Found {count} matches")
print("=== 12-glyph messages ending in glyph 144 ===")
count2 = 0
for idx in range(0, 2883):
    fp = find_resource_file(idx)
    if fp is None:
        continue
    try:
        messages = extract_messages(fp)
    except:
        continue
    for mi, msg in enumerate(messages):
        if len(msg) == 12 and msg[-1] == 144:
            print(f"  res={idx} msg#{mi}: {msg}")
            count2 += 1
print(f"Found {count2} matches")

