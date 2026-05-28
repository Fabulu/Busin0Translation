import struct, os, json
from collections import Counter
RESDIR = r"C:/Programmieren/wizardrytranslation/extracted/packdata_resources"
HDR_F = r"C:/Programmieren/wizardrytranslation/dumps/msg_header_analysis.json"
CLS_F = r"C:/Programmieren/wizardrytranslation/dumps/resource_classification.json"
with open(CLS_F) as f: cls = json.load(f)
mi_list = cls["msg_resource_indices"]
with open(HDR_F) as f: hdr = json.load(f)
gs_map = {r["index"]: r.get("glyph_start_offset", 0) for r in hdr["resources"]}
def frf(idx):
    p = "%04d_" % idx
    for fn in os.listdir(RESDIR):
        if fn.startswith(p) and fn.endswith(".bin"): return os.path.join(RESDIR, fn)
    return None
GM = 0x035A
# Find all consecutive duplicate glyphs in range 86-200
consec = Counter()
for idx in mi_list:
    fp = frf(idx)
    if not fp: continue
    data = open(fp, "rb").read()
    gs = gs_map.get(idx, 0)
    region = data[gs:]
    if len(region) % 2: region = region[:-1]
    n = len(region) // 2
    if n < 2: continue
    vals = list(struct.unpack(">%dH" % n, region))
    for i in range(len(vals) - 1):
        if vals[i] == vals[i+1] and 86 <= vals[i] <= 200:
            consec[vals[i]] += 1
print("Consecutive duplicate glyphs (86-200):")
for v, c in consec.most_common(30):
    print("  %d (0x%04X): %d times" % (v, v, c))
