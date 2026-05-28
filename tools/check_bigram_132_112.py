import struct, os, json
from collections import Counter

RESDIR = "C:/Programmieren/wizardrytranslation/extracted/packdata_resources"
with open("C:/Programmieren/wizardrytranslation/dumps/resource_classification.json") as f:
    cls = json.load(f)
msg_indices = cls["msg_resource_indices"]

files = os.listdir(RESDIR)
fmap = {}
for f in files:
    try:
        fmap[int(f[:4])] = os.path.join(RESDIR, f)
    except:
        pass

bigram_count = 0
for idx in msg_indices:
    if idx not in fmap:
        continue
    with open(fmap[idx], "rb") as fh:
        data = fh.read()
    i = 0
    while i < len(data) - 3:
        a = struct.unpack(">H", data[i:i+2])[0]
        b = struct.unpack(">H", data[i+2:i+4])[0]
        if a == 132 and b == 112:
            bigram_count += 1
        i += 2

print("Raw bigram (132, 112) count in all MSG resources: %d" % bigram_count)

# Also check (112, 132) reversed
rev_count = 0
for idx in msg_indices:
    if idx not in fmap:
        continue
    with open(fmap[idx], "rb") as fh:
        data = fh.read()
    for off in range(0, len(data) - 3, 2):
        a = struct.unpack(">H", data[off:off+2])[0]
        b = struct.unpack(">H", data[off+2:off+4])[0]
        if a == 112 and b == 132:
            rev_count += 1

print("Raw bigram (112, 132) count: %d" % rev_count)

# Check what most commonly follows 132 (な)
na_followers = Counter()
for idx in msg_indices:
    if idx not in fmap:
        continue
    with open(fmap[idx], "rb") as fh:
        data = fh.read()
    for off in range(0, len(data) - 3, 2):
        a = struct.unpack(">H", data[off:off+2])[0]
        b = struct.unpack(">H", data[off+2:off+4])[0]
        if a == 132 and b < 0xFFC0 and b >= 5:
            na_followers[b] += 1

print()
print("Top followers of 132 (na):")
for g, c in na_followers.most_common(15):
    print("  132->%d = %d" % (g, c))
print("DONE")
