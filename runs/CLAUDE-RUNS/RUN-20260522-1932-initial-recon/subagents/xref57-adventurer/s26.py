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
# Top 20 glyphs by frequency
top20 = [0,1,255,3,113,136,158,152,93,130,123,132,63,156,62,2,142,127,117,133]
consec_count = Counter()
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
        if vals[i] == vals[i+1] and vals[i] in top20:
            consec_count[vals[i]] += 1
print("Consecutive duplicates for top 20 glyphs:")
for g in top20:
    c = consec_count.get(g, 0)
    print("  glyph %d: %d consecutive pairs" % (g, c))
