import struct, os, json
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
count123 = 0
hits123 = []
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
        if vals[i] == 123 and vals[i+1] == 123:
            count123 += 1
            ctx = vals[max(0,i-5):min(len(vals),i+8)]
            hits123.append("res %d pos %d: %s" % (idx, i, ctx))
print("Consecutive 123,123:", count123)
for h in hits123[:10]:
    print(" ", h)
