import json, struct, os

RES_DIR = "C:/Programmieren/wizardrytranslation/extracted/packdata_resources"

with open(os.path.join(RES_DIR, "manifest.json")) as f:
    manifest = json.load(f)

print("=== Step 1: Resources with sizes near multiples of 858 ===")
targets = [(858*2, "858x2"), (858*4, "858x4"), (858*8, "858x8"), (858*16, "858x16"), (858*28, "858x28")]
for r in manifest:
    for t, label in targets:
        if abs(r["payload_size"] - t) <= 100:
            idx = r["index"]
            sz = r["payload_size"]
            fn = r["filename"]
            tc = r["type_code"]
            print("  idx=%d size=%d (%s=%d) file=%s type=%d" % (idx, sz, label, t, fn, tc))

print()
print("=== Step 2: Resources near font atlas (1268-1276) ===")
for r in manifest:
    if 1268 <= r["index"] <= 1276:
        print("  idx=%d size=%d file=%s type=%d" % (r["index"], r["payload_size"], r["filename"], r["type_code"]))

print()
print("=== Step 3: Analyze resource 49 (3458 bytes) ===")
fpath = os.path.join(RES_DIR, "0049_type01.bin")
with open(fpath, "rb") as f:
    data = f.read()
print("  File size: %d bytes" % len(data))
print("  First 64 bytes hex: %s" % data[:64].hex())

vals = []
for i in range(0, min(len(data), 200), 2):
    v = struct.unpack_from("<H", data, i)[0]
    vals.append(v)
print("  First 40 uint16 LE: %s" % " ".join("%04x" % v for v in vals[:40]))

sjis_hira = [v for v in vals if 0x829F <= v <= 0x82F1]
sjis_kata = [v for v in vals if 0x8340 <= v <= 0x8396]
print("  SJIS hira in first 100: %d, kata: %d" % (len(sjis_hira), len(sjis_kata)))

all_vals = []
for i in range(0, len(data) - 1, 2):
    v = struct.unpack_from("<H", data, i)[0]
    all_vals.append(v)
sjis_all_hira = sum(1 for v in all_vals if 0x829F <= v <= 0x82F1)
sjis_all_kata = sum(1 for v in all_vals if 0x8340 <= v <= 0x8396)
sjis_all_kanji = sum(1 for v in all_vals if 0x889F <= v <= 0x9FFC)
print("  Whole file: hira=%d kata=%d kanji=%d" % (sjis_all_hira, sjis_all_kata, sjis_all_kanji))
print("  3458 - 858*4 = %d" % (3458 - 858*4))

print()
print("  Trying 4-byte stride (uint16 + uint16):")
for hdr_off in [0, 2, 4, 8, 16, 26]:
    if hdr_off + 858*4 <= len(data) + 100:
        test_chars = []
        for i in range(hdr_off, min(hdr_off + 400, len(data) - 3), 4):
            v = struct.unpack_from("<H", data, i)[0]
            test_chars.append(v)
        hira = sum(1 for v in test_chars if 0x829F <= v <= 0x82F1)
        kata = sum(1 for v in test_chars if 0x8340 <= v <= 0x8396)
        kanji = sum(1 for v in test_chars if 0x889F <= v <= 0x9FFC)
        if hira > 2 or kata > 2 or kanji > 3:
            print("    Offset %d: hira=%d kata=%d kanji=%d" % (hdr_off, hira, kata, kanji))
            print("    First 20: %s" % " ".join("%04x" % v for v in test_chars[:20]))

print()
print("=== Step 4: Scan ALL resources for SJIS hiragana sequences ===")
for r in manifest:
    fpath = os.path.join(RES_DIR, r["filename"])
    if not os.path.exists(fpath):
        continue
    with open(fpath, "rb") as f:
        data = f.read()
    if len(data) < 100:
        continue

    best_run = 0
    best_pos = 0
    best_stride = 0

    for stride in [2, 4, 6, 8]:
        search_limit = min(len(data) - stride * 5, 4000)
        if search_limit <= 0:
            continue
        for start in range(0, search_limit):
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
        print("  idx=%d file=%s size=%d: %d consecutive hiragana at offset %d stride=%d" % (r["index"], r["filename"], r["payload_size"], best_run, best_pos, best_stride))

print("Done.")
