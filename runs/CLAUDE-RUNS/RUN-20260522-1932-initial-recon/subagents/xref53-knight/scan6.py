import struct, os, json
RESDIR = r"C:/Programmieren/wizardrytranslation/extracted/packdata_resources"
with open(r"C:/Programmieren/wizardrytranslation/dumps/resource_classification.json") as f:
    cls = json.load(f)
msg_indices = cls["msg_resource_indices"]
def frf(idx):
    for fname in os.listdir(RESDIR):
        if fname.startswith(str(idx).zfill(4) + "_"):
            return os.path.join(RESDIR, fname)
    return None
def pm(data):
    msgs = []
    i = 0
    while i < len(data) - 1:
        val = struct.unpack(">H", data[i:i+2])[0]
        if val == 0xFFFF:
            mg = []
            fc = 0
            j = i + 2
            while j < len(data) - 1:
                v = struct.unpack(">H", data[j:j+2])[0]
                if v == 0xFFFF:
                    break
                elif v == 0xFFFE:
                    mg.append(-1)
                    fc += 1
                else:
                    mg.append(v)
                j += 2
            msgs.append((mg, fc, i))
            i = j
        else:
            i += 2
    return msgs
results = []
for idx in msg_indices:
    path = frf(idx)
    if not path:
        continue
    with open(path, "rb") as f:
        data = f.read()
    msgs = pm(data)
    for mi, (mg, fc, off) in enumerate(msgs):
        tg = [x for x in mg if x >= 0]
        if not (36 <= len(tg) <= 40 and fc <= 3):
            continue
        if any(g > 600 for g in tg):
            continue
        hr = tg[1] == tg[8]
        h24 = 24 in tg[14:20]
        results.append([idx, mi, len(tg), fc, hr, h24, mg])
print("Filtered: " + str(len(results)))
print("Repeat pos1=8: " + str(sum(1 for r in results if r[4])))
for r in results:
    if r[4]:
        print("  Res %d msg %d: %dg %df h24=%s gl=%s" % (r[0], r[1], r[2], r[3], r[5], str(r[6])))
with open(r"C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260522-1932-initial-recon/subagents/xref53-knight/c6.json", "w") as f:
    json.dump(results, f, indent=2)

