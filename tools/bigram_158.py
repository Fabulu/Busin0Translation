import struct, os, json
from collections import Counter

RESDIR = "C:/Programmieren/wizardrytranslation/extracted/packdata_resources"
files = os.listdir(RESDIR)
fmap = {}
for f in files:
    try:
        fmap[int(f[:4])] = os.path.join(RESDIR, f)
    except:
        pass

bigrams = Counter()
for idx in range(34, 50):
    if idx not in fmap:
        continue
    with open(fmap[idx], "rb") as fh:
        data = fh.read()
    i = 0
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
            tg = [g for g in gl if 5 <= g < 0xFFC0]
            for k in range(len(tg)-1):
                bigrams[(tg[k], tg[k+1])] += 1
            i = j
        else:
            i += 2

# Bigrams involving specific glyphs of interest
for target in [158, 152, 168, 171, 191, 63, 31, 62]:
    print("=== Glyph %d ===" % target)
    before = [(a, c) for (a, b), c in bigrams.items() if b == target]
    before.sort(key=lambda x: -x[1])
    print("  X->%d (top 8): %s" % (target, [(a, c) for a, c in before[:8]]))
    
    after = [(b, c) for (a, b), c in bigrams.items() if a == target]
    after.sort(key=lambda x: -x[1])
    print("  %d->X (top 8): %s" % (target, [(b, c) for b, c in after[:8]]))

print("DONE")
