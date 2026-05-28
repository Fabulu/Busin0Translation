import json, struct, os

RES_DIR = "C:/Programmieren/wizardrytranslation/extracted/packdata_resources"

with open(os.path.join(RES_DIR, "manifest.json")) as f:
    manifest = json.load(f)

print("=== Step 2: Resources near font atlas (1268-1276) ===")
for r in manifest:
    if 1268 <= r["index"] <= 1276:
        sz = r.get("payload_size", 0)
        print("  idx=%d size=%d file=%s type=%d" % (r["index"], sz, r["filename"], r.get("type_code",0)))

print()
print("=== Step 3: Analyze resource 49 (3458 bytes) ===")
fpath = os.path.join(RES_DIR, "0049_type01.bin")
with open(fpath, "rb") as f:
    data = f.read()
print("  File size: %d bytes" % len(data))
print("  First 128 bytes hex:")
for row in range(0, 128, 16):
    hexpart = " ".join("%02x" % data[row+i] for i in range(16) if row+i < len(data))
    print("    %04x: %s" % (row, hexpart))

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
print("  Whole file uint16 LE: hira=%d kata=%d kanji=%d" % (sjis_all_hira, sjis_all_kata, sjis_all_kanji))

print()
print("  Trying various strides and offsets:")
for stride in [2, 4]:
    for hdr_off in range(0, 30, 2):
        nentries = (len(data) - hdr_off) // stride
        if nentries < 100:
            continue
        test_chars = []
        for i in range(hdr_off, min(hdr_off + stride*100, len(data) - 1), stride):
            v = struct.unpack_from("<H", data, i)[0]
            test_chars.append(v)
        hira = sum(1 for v in test_chars if 0x829F <= v <= 0x82F1)
        kata = sum(1 for v in test_chars if 0x8340 <= v <= 0x8396)
        kanji = sum(1 for v in test_chars if 0x889F <= v <= 0x9FFC)
        valid_sjis = sum(1 for v in test_chars if 0x8140 <= v <= 0xEAA4)
        if hira > 2 or kata > 2 or kanji > 3 or valid_sjis > 20:
            print("    stride=%d off=%d entries=%d: hira=%d kata=%d kanji=%d valid_sjis=%d" % (stride, hdr_off, nentries, hira, kata, kanji, valid_sjis))
            print("    First 30: %s" % " ".join("%04x" % v for v in test_chars[:30]))

print()
print("=== Analyze resource 36 (3390 bytes) ===")
fpath = os.path.join(RES_DIR, "0036_type01.bin")
with open(fpath, "rb") as f:
    data = f.read()
print("  File size: %d bytes" % len(data))
print("  First 128 bytes hex:")
for row in range(0, 128, 16):
    hexpart = " ".join("%02x" % data[row+i] for i in range(16) if row+i < len(data))
    print("    %04x: %s" % (row, hexpart))
vals36 = []
for i in range(0, min(len(data), 200), 2):
    v = struct.unpack_from("<H", data, i)[0]
    vals36.append(v)
print("  First 40 uint16 LE: %s" % " ".join("%04x" % v for v in vals36[:40]))

all_vals36 = []
for i in range(0, len(data) - 1, 2):
    v = struct.unpack_from("<H", data, i)[0]
    all_vals36.append(v)
sjis_hira36 = sum(1 for v in all_vals36 if 0x829F <= v <= 0x82F1)
sjis_kata36 = sum(1 for v in all_vals36 if 0x8340 <= v <= 0x8396)
sjis_kanji36 = sum(1 for v in all_vals36 if 0x889F <= v <= 0x9FFC)
print("  Whole file uint16 LE: hira=%d kata=%d kanji=%d" % (sjis_hira36, sjis_kata36, sjis_kanji36))

print()
print("=== Analyze resource 45 (6950 bytes) ===")
fpath = os.path.join(RES_DIR, "0045_type01.bin")
with open(fpath, "rb") as f:
    data = f.read()
print("  File size: %d bytes" % len(data))
print("  First 128 bytes hex:")
for row in range(0, 128, 16):
    hexpart = " ".join("%02x" % data[row+i] for i in range(16) if row+i < len(data))
    print("    %04x: %s" % (row, hexpart))
all_vals45 = []
for i in range(0, len(data) - 1, 2):
    v = struct.unpack_from("<H", data, i)[0]
    all_vals45.append(v)
sjis_hira45 = sum(1 for v in all_vals45 if 0x829F <= v <= 0x82F1)
sjis_kata45 = sum(1 for v in all_vals45 if 0x8340 <= v <= 0x8396)
sjis_kanji45 = sum(1 for v in all_vals45 if 0x889F <= v <= 0x9FFC)
print("  Whole file uint16 LE: hira=%d kata=%d kanji=%d" % (sjis_hira45, sjis_kata45, sjis_kanji45))

print("Done step3.")
