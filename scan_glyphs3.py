import json, struct, os

RES_DIR = "C:/Programmieren/wizardrytranslation/extracted/packdata_resources"

with open(os.path.join(RES_DIR, "manifest.json")) as f:
    manifest = json.load(f)

print("=== Scan ALL resources for SJIS hiragana sequences ===")
found_any = False
for r in manifest:
    if "filename" not in r:
        continue
    idx = r["index"]
    fpath = os.path.join(RES_DIR, r["filename"])
    if not os.path.exists(fpath):
        continue
    with open(fpath, "rb") as f:
        data = f.read()
    if len(data) < 20:
        continue

    best_run = 0
    best_pos = 0
    best_stride = 0

    for stride in [2, 4, 8]:
        search_limit = min(len(data) - stride * 5, 8000)
        if search_limit <= 0:
            continue
        for start in range(0, search_limit, 2):
            run = 0
            for k in range(83):
                pos = start + k * stride
                if pos + 1 >= len(data):
                    break
                v = struct.unpack_from("<H", data, pos)[0]
                if v == 0x829F + k:
                    run += 1
                else:
                    break
            if run > best_run:
                best_run = run
                best_pos = start
                best_stride = stride

    if best_run >= 5:
        found_any = True
        print("  idx=%d file=%s size=%d: %d consecutive hiragana at offset %d stride=%d" % (idx, r["filename"], r.get("payload_size",0), best_run, best_pos, best_stride))

if not found_any:
    print("  No resources found with 5+ consecutive hiragana sequences.")

print()
print("=== Resources with high SJIS density ===")
for r in manifest:
    if "filename" not in r:
        continue
    sz = r.get("payload_size", 0)
    if sz < 500 or sz > 30000:
        continue
    fpath = os.path.join(RES_DIR, r["filename"])
    if not os.path.exists(fpath):
        continue
    with open(fpath, "rb") as f:
        data = f.read()

    total = 0
    valid = 0
    hira = 0
    kata = 0
    kanji = 0
    for i in range(0, len(data) - 1, 2):
        v = struct.unpack_from("<H", data, i)[0]
        total += 1
        if 0x8140 <= v <= 0x84BE:
            valid += 1
            if 0x829F <= v <= 0x82F1:
                hira += 1
            if 0x8340 <= v <= 0x8396:
                kata += 1
        elif 0x889F <= v <= 0x9FFC:
            valid += 1
            kanji += 1
        elif 0xE040 <= v <= 0xEAA4:
            valid += 1
            kanji += 1

    if total > 0 and valid * 100 // total > 30:
        print("  idx=%d file=%s size=%d: %d/%d valid SJIS (%d%%) hira=%d kata=%d kanji=%d" % (r["index"], r["filename"], sz, valid, total, valid*100//total, hira, kata, kanji))

print("Done.")
