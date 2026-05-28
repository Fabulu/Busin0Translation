import struct, os
from collections import Counter

RES_DIR = r"C:/Programmieren/wizardrytranslation/extracted/packdata_resources"

def find_resource_file(idx):
    prefix = f"{idx:04d}_"
    for fn in os.listdir(RES_DIR):
        if fn.startswith(prefix) and fn.endswith(".bin"):
            return os.path.join(RES_DIR, fn)
    return None

glyph_counter = Counter()
for idx in [34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49]:
    fp = find_resource_file(idx)
    if fp is None:
        continue
    with open(fp, "rb") as f:
        data = f.read()
    first_ffff = None
    for off in range(0, len(data) - 1, 2):
        val = struct.unpack(">H", data[off:off+2])[0]
        if val == 0xFFFF:
            first_ffff = off
            break
    if first_ffff is None:
        continue
    stream_data = data[first_ffff:]
    n = len(stream_data) // 2
    vals = struct.unpack(f">{n}H", stream_data[:n*2])
    for v in vals:
        if v < 0xFFC0:
            glyph_counter[v] += 1

print("Range:", min(glyph_counter.keys()), "-", max(glyph_counter.keys()))
print("Unique:", len(glyph_counter))
print("Top 30:")
for gid, cnt in glyph_counter.most_common(30):
    print(f"  {gid}: {cnt}")
buckets = {}
for gid in glyph_counter:
    bucket = gid // 100 * 100
    buckets[bucket] = buckets.get(bucket, 0) + glyph_counter[gid]
print("By 100-bucket:")
for b in sorted(buckets):
    print(f"  {b}-{b+99}: {buckets[b]}")

