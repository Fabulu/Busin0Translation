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
    # Search for pattern: glyph_95 ... 91 91 glyph glyph FFFF
    # where glyph_95 is within 12 positions before the 91 91
    for i in range(len(vals) - 4):
        if vals[i] == 91 and vals[i+1] == 91 and vals[i+2] <= GM and vals[i+3] <= GM:
            if vals[i+4] == 0xFFFF or (i+4 < len(vals) and vals[i+4] == 0xFFFE):
                for j in range(max(0, i-12), i):
                    if vals[j] == 95:
                        print("HIT: res %d pos %d context: %s" % (idx, i, vals[max(0,i-12):min(len(vals),i+6)]))
                        break
