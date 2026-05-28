import zipfile, struct, json, os
z = zipfile.ZipFile("C:/Programmieren/wizardrytranslation/fight1.p2s", "r")
data = z.read("eeMemory.bin")
with open("C:/Programmieren/wizardrytranslation/ee_memory_fight1.bin", "wb") as f:
    f.write(data)
print(f"EE memory size: {len(data)} bytes")
target_sub = bytes([0x6e, 0x00, 0x88, 0x00, 0x63, 0x00, 0x82, 0x00])
hits_ri = []
all_hits = []
pos = 0
while True:
    pos = data.find(target_sub, pos)
    if pos == -1:
        break
    ctx_start = max(0, pos - 16)
    ctx_end = min(len(data), pos + 8 + 16)
    ctx_bytes = data[ctx_start:ctx_end]
    n_vals = len(ctx_bytes) // 2
    ctx_vals = struct.unpack_from(f"<{n_vals}H", ctx_bytes, 0)
    pre_count = (pos - ctx_start) // 2
    all_hits.append((pos, ctx_vals, pre_count))
    if pos >= 4:
        ri_val = struct.unpack_from("<H", data, pos - 4)[0]
        if ri_val == 137:
            start = pos - 4 - 2 - 2
            if start >= 0:
                vals = struct.unpack_from("<8H", data, start)
                hits_ri.append((start, hex(start), vals))
    pos += 1
print(f"All su-ra-i-mu hits ({len(all_hits)}):")
for offset, ctx, pre in all_hits[:60]:
    print(f"  offset={hex(offset)} context={ctx} (target@idx={pre})")
print(f"With ri prefix ({len(hits_ri)}):")
for start, hexaddr, vals in hits_ri:
    print(f"  offset={hexaddr} ba={vals[0]} bu={vals[1]} ri={vals[2]} dash={vals[3]} su={vals[4]} ra={vals[5]} i={vals[6]} mu={vals[7]}")

