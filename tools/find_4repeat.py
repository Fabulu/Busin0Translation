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

for idx in list(range(34, 50)) + [636, 638]:
    if idx not in fmap:
        continue
    with open(fmap[idx], "rb") as fh:
        data = fh.read()
    i = 0
    sn = 0
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
            tg = [g for g in gl if g < 0xFF00]
            if 28 <= len(tg) <= 45:
                c = Counter(tg)
                has4 = any(v >= 4 for v in c.values())
                count3 = sum(1 for v in c.values() if v >= 3)
                count2 = sum(1 for v in c.values() if v >= 2)
                if has4 and count2 >= 4:
                    g4 = [k for k,v in c.items() if v>=4]
                    print("res=%d s=%d off=0x%X tlen=%d repeat4=%s c2=%d c3=%d" % (idx, sn, i, len(tg), g4, count2, count3))
                    print("  gl=%s" % gl)
            sn += 1
            i = j
        else:
            i += 2
print("DONE")
