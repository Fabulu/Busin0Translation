import struct, os, json
from collections import Counter
RESDIR = r"C:/Programmieren/wizardrytranslation/extracted/packdata_resources"
HDR_F = r"C:/Programmieren/wizardrytranslation/dumps/msg_header_analysis.json"
with open(HDR_F) as f: hdr = json.load(f)
gs_map = {r["index"]: r.get("glyph_start_offset", 0) for r in hdr["resources"]}
def frf(idx):
    p = "%04d_" % idx
    for fn in os.listdir(RESDIR):
        if fn.startswith(p) and fn.endswith(".bin"): return os.path.join(RESDIR, fn)
    return None
# Only dialogue resources 34-49
consec = Counter()
for idx in range(34, 50):
    fp = frf(idx)
    if not fp: continue
    data = open(fp, "rb").read()
    gs = gs_map.get(idx, 0)
    region = data[gs:]
    if len(region) % 2: region = region[:-1]
    n = len(region) // 2
    if n < 2: continue
    vals = list(struct.unpack(">%dH" % n, region))
    msgs, cur = [], []
    for v in vals:
        if v == 0xFFFF:
            if cur: msgs.append(cur)
            cur = []
        else: cur.append(v)
    if cur: msgs.append(cur)
    for mi, msg in enumerate(msgs):
        gl = [v for v in msg if 0 < v < 0xFFC0]
        for i in range(len(gl) - 1):
            if gl[i] == gl[i+1] and 86 <= gl[i] <= 300:
                consec[gl[i]] += 1
print("Consecutive dupes in resources 34-49 (filtered to glyph messages):")
for v, c in consec.most_common(20):
    print("  %d (0x%04X): %d times" % (v, v, c))
