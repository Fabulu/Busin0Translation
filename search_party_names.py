import struct, gzip, json, os

SAVE = "C:/Programmieren/wizardrytranslation/normaldungeonscreen.p2s"

with open(SAVE, "rb") as f:
    raw = f.read()

if raw[:2] == b"\x1f\x8b":
    raw = gzip.decompress(raw)
    print(f"Decompressed to {len(raw)} bytes")
else:
    print(f"Raw size: {len(raw)} bytes")

target_ia = struct.pack("<HH", 99, 98)
print(f"Searching for pattern: {target_ia.hex()}")

hits = []
pos = 0
while True:
    idx = raw.find(target_ia, pos)
    if idx == -1:
        break
    hits.append(idx)
    pos = idx + 1

print(f"Found {len(hits)} occurrences of [99,98] as uint16 LE")

for hit in hits:
    start = max(0, hit - 400)
    end = min(len(raw), hit + 400)
    chunk = raw[start:end]
    vals = []
    for i in range(0, len(chunk) - 1, 2):
        vals.append(struct.unpack_from("<H", chunk, i)[0])
    found_others = 0
    if 107 in vals and 97 in vals:
        found_others += 1
    if 125 in vals and 137 in vals:
        found_others += 1
    if 101 in vals:
        found_others += 1
    if 110 in vals:
        found_others += 1
    if 136 in vals:
        found_others += 1
    if found_others >= 3:
        rel = hit - start
        print(f"")
        print(f"*** PROMISING HIT at offset 0x{hit:08X} (found_others={found_others}) ***")
        for i in range(0, len(vals), 16):
            addr = start + i * 2
            line_vals = vals[i:i+16]
            print(f"  0x{addr:08X}: {line_vals}")

