import struct, os, json

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

# Count how many times 132 (な) appears across different resources
for idx in range(34, 50):
    if idx not in fmap:
        continue
    with open(fmap[idx], "rb") as fh:
        data = fh.read()
    
    # Count glyph 132 in the entire binary (as BE uint16)
    total_132 = 0
    for off in range(0, len(data)-1, 2):
        v = struct.unpack(">H", data[off:off+2])[0]
        if v == 132:
            total_132 += 1
    
    # Also check blocks
    i = 0
    blocks_with_132 = 0
    max_132 = 0
    while i < len(data) - 1:
        val = struct.unpack(">H", data[i:i+2])[0]
        if val == 0xFFFF:
            gl = []
            j = i + 2
            while j < len(data) - 1:
                g = struct.unpack(">H", data[j:j+2])[0]
                if g == 0xFFFF:
                    break
                gl.append(g)
                j += 2
            tg = [g for g in gl if g < 0xFFC0]
            c = tg.count(132)
            if c > 0:
                blocks_with_132 += 1
                if c > max_132:
                    max_132 = c
            i = j
        else:
            i += 2
    
    if total_132 > 0:
        print("res=%d: total_132=%d blocks_with_132=%d max_per_block=%d" % (idx, total_132, blocks_with_132, max_132))

# Also check frequency of glyph 132 vs 113 in early resources
print()
print("Checking glyph frequencies in res 44-46:")
for idx in [44, 45, 46]:
    if idx not in fmap:
        continue
    with open(fmap[idx], "rb") as fh:
        data = fh.read()
    counts = {}
    i = 0
    while i < len(data) - 1:
        val = struct.unpack(">H", data[i:i+2])[0]
        if val == 0xFFFF:
            j = i + 2
            while j < len(data) - 1:
                g = struct.unpack(">H", data[j:j+2])[0]
                if g == 0xFFFF:
                    break
                if 5 <= g < 0xFFC0:
                    counts[g] = counts.get(g, 0) + 1
                j += 2
            i = j
        else:
            i += 2
    top20 = sorted(counts.items(), key=lambda x: -x[1])[:20]
    print("res=%d top20: %s" % (idx, top20))

print("DONE")
