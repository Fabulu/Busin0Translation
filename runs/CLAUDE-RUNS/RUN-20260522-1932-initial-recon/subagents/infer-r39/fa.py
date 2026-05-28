import struct, json, sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RESDIR = "C:/Programmieren/wizardrytranslation/extracted/packdata_resources"
GMAP_FILE = "C:/Programmieren/wizardrytranslation/data/msg_glyph_map.json"
with open(GMAP_FILE, encoding="utf-8") as f:
    gmap = json.load(f)
unknown_ids = set([0,11,13,15,16,33,37,40,45,48,50,51,52,53,92,108,109,193,194,199,200,204,205,208,211,212,223,225,227,231,233,234,236,253,259,262,264,266,276,278,287,288,308,316,320,332,339,346,350,351,354,365,367,370,421,428,436,443,490,507,508,535,543,544,572,581,582,587,590,593,597,600,602,605,619,620,621,638,647,656,666,668,682,693,696,698,700,704,707,708,709,710,712,717,718,719,720,721,722,728,737,767,768,775,776,800,836,839,849,850,851,853,854,855,908,911,941,959,969,989])
from collections import Counter
freq = Counter()
contexts = {}
for fname in sorted(os.listdir(RESDIR)):
    if not fname.endswith(".bin"): continue
    fpath = os.path.join(RESDIR, fname)
    with open(fpath, "rb") as f:
        data = f.read()
    if len(data) < 4: continue
    gs = len(data)
    for off in range(0, len(data) - 1, 2):
        val = struct.unpack(">H", data[off:off+2])[0]
        if val == 0xFFFF or val == 0xFFFE:
            gs = off
            break
    i = gs
    all_glyphs = []
    while i < len(data) - 1:
        val = struct.unpack(">H", data[i:i+2])[0]
        if val >= 0xFFC0:
            all_glyphs.append(("CTRL", val))
        else:
            all_glyphs.append(("GLYPH", val))
            if val in unknown_ids:
                freq[val] += 1
        i += 2
    for idx_g, (typ, val) in enumerate(all_glyphs):
        if typ == "GLYPH" and val in unknown_ids:
            ctx_start = max(0, idx_g - 3)
            ctx_end = min(len(all_glyphs), idx_g + 4)
            ctx = []
            for j in range(ctx_start, ctx_end):
                t2, v2 = all_glyphs[j]
                if t2 == "CTRL":
                    ctx.append("|")
                else:
                    g = gmap.get(str(v2))
                    if g: ctx.append(g)
                    else: ctx.append("[%d]" % v2)
            ctx_str = "".join(ctx)
            if val not in contexts: contexts[val] = []
            if len(contexts[val]) < 5:
                contexts[val].append("%s: %s" % (fname, ctx_str))
print("=== Frequency of unknown IDs ===")
for uid in sorted(unknown_ids):
    print("  %d: %d occurrences" % (uid, freq[uid]))
    if uid in contexts:
        for c in contexts[uid]:
            print("    %s" % c)
