import struct, os, json
RESDIR = r"C:/Programmieren/wizardrytranslation/extracted/packdata_resources"
HDR_F = r"C:/Programmieren/wizardrytranslation/dumps/msg_header_analysis.json"
with open(HDR_F) as f: hdr = json.load(f)
gs_map = {r["index"]: r.get("glyph_start_offset", 0) for r in hdr["resources"]}
idx = 45
import os as _os
fp = next(_os.path.join(RESDIR,fn) for fn in _os.listdir(RESDIR) if fn.startswith("0045_") and fn.endswith(".bin"))
data = open(fp, "rb").read()
gs = gs_map[idx]
region = data[gs:]
n = len(region)//2
vals = list(struct.unpack(">%dH"%n,region))
msgs,cur=[],[]
for v in vals:
    if v==0xFFFF:
        if cur: msgs.append(cur)
        cur=[]
    else: cur.append(v)
if cur: msgs.append(cur)
# Analyze msg7 and msg22 for internal consistency
for mi in [7, 22]:
    msg = msgs[mi]
    lines, cl = [], []
    for v in msg:
        if v == 0xFFFE: lines.append(cl); cl = []
        else: cl.append(v)
    lines.append(cl)
    print("msg#%d:" % mi)
    for i, l in enumerate(lines):
        gl = [v for v in l if 0 < v <= 0x035A]
        print("  line%d (%d glyphs): %s" % (i, len(gl), gl))
    # Check for repeated values within the message
    from collections import Counter
    flat = [v for v in msg if 0 < v <= 0x035A]
    c = Counter(flat)
    reps = {v: cnt for v, cnt in c.items() if cnt > 1}
    print("  Repeated glyphs: %s" % reps)
    print()
