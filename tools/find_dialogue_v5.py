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

# Concatenate all text glyphs from each FFFF block (filtering ALL >= 0xFFC0)
# Then search for the 33-char structural pattern at any offset

results = []
for idx in msg_indices:
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
            
            tg = [g for g in gl if g < 0xFFC0]
            
            for off in range(0, max(1, len(tg) - 32)):
                if off + 32 >= len(tg):
                    break
                t = tg[off:off+33]
                if len(t) < 33:
                    break
                
                if t[0] != t[21] or t[0] != t[25] or t[0] != t[27]:
                    continue
                if t[1] != t[15]:
                    continue
                if t[2] != t[12] or t[2] != t[24]:
                    continue
                if t[6] != t[14]:
                    continue
                if t[8] != t[31]:
                    continue
                if t[10] != t[32]:
                    continue
                
                groups = set([t[0], t[1], t[2], t[6], t[8], t[10]])
                if len(groups) == 6:
                    results.append((idx, sn, i, off, t, len(tg)))
            
            sn += 1
            i = j
        else:
            i += 2

print("Found %d matches" % len(results))
for idx, sn, foff, toff, t, tglen in results[:20]:
    print("res=%d s=%d foff=0x%X toff=%d tglen=%d" % (idx, sn, foff, toff, tglen))
    print("  t=%s" % t)
    na, a, comma, ku, yo, maru = t[0], t[1], t[2], t[6], t[8], t[10]
    print("  na=%d a=%d comma=%d ku=%d yo=%d maru=%d" % (na, a, comma, ku, yo, maru))
print("DONE")
