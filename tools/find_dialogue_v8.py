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

# For resources 34-49, dump ALL FFFF blocks with text length >= 20
# and show the repeat statistics

for idx in range(34, 50):
    if idx not in fmap:
        continue
    with open(fmap[idx], "rb") as fh:
        data = fh.read()
    
    i = 0
    sn = 0
    found_any = False
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
            
            if len(tg) >= 20:
                c = Counter(tg)
                max_count = max(c.values())
                if max_count >= 3:
                    top3 = c.most_common(3)
                    if not found_any:
                        print("=== Resource %d ===" % idx)
                        found_any = True
                    print("  s[%d] off=0x%X tlen=%d top=%s" % (sn, i, len(tg), top3))
                    # Show the text split by FFFE
                    parts = []
                    cur = []
                    for g in gl:
                        if g == 0xFFFE:
                            if cur:
                                parts.append([x for x in cur if 5 <= x < 0xFFC0])
                            cur = []
                        else:
                            cur.append(g)
                    if cur:
                        parts.append([x for x in cur if 5 <= x < 0xFFC0])
                    for pi, p in enumerate(parts):
                        if p:
                            print("    part[%d] len=%d: %s" % (pi, len(p), p))
            
            sn += 1
            i = j
        else:
            i += 2
    if found_any:
        print()

print("DONE")
