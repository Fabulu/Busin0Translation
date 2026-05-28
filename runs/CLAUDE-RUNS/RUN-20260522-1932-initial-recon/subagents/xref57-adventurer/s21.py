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
total91 = 0
total95 = 0
total89 = 0
total126 = 0
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
    total91 += vals.count(91)
    total95 += vals.count(95)
    total89 += vals.count(89)
    total126 += vals.count(126)
print("Glyph 91 total:", total91)
print("Glyph 95 total:", total95)
print("Glyph 89 total:", total89)
print("Glyph 126 total:", total126)
