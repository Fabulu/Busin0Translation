import zipfile
import struct
import json

def read_ee_ram(p2s_path):
    with zipfile.ZipFile(p2s_path, "r") as z:
        with z.open("eeMemory.bin") as f:
            return f.read()

kata_ram = read_ee_ram("C:/Programmieren/wizardrytranslation/Nameentrystate.p2s")
hira_ram = read_ee_ram("C:/Programmieren/wizardrytranslation/NameEntryHiraganamode.p2s")

print(f"Katakana RAM size: {len(kata_ram)} bytes")
print(f"Hiragana RAM size: {len(hira_ram)} bytes")

kata_offset = 0x4C9AB0
print(f"\n=== Katakana table at 0x{kata_offset:08X} ===")
for row in range(10):
    vals = []
    base = kata_offset + row * 12
    for col in range(6):
        v = struct.unpack_from("<H", kata_ram, base + col*2)[0]
        vals.append(v)
    print(f"Row {row:2d} (0x{base:08X}): {vals}")

candidates = [kata_offset + 1200, kata_offset + 2400, kata_offset + 3600, kata_offset - 1200]
for cand in candidates:
    print(f"\n=== Checking 0x{cand:08X} (offset from kata: {cand - kata_offset}) ===")
    valid_groups = 0
    for row in range(10):
        vals = []
        base = cand + row * 12
        for col in range(6):
            v = struct.unpack_from("<H", kata_ram, base + col*2)[0]
            vals.append(v)
        if all(0 < v < 1000 for v in vals):
            valid_groups += 1
        print(f"Row {row:2d} (0x{base:08X}): {vals}")
    print(f"Valid groups (all values 1-999): {valid_groups}/10")

print("\n\n=== Broad search ===")
kata_values = []
for row in range(100):
    base = kata_offset + row * 12
    for col in range(6):
        v = struct.unpack_from("<H", kata_ram, base + col*2)[0]
        kata_values.append(v)
print(f"Katakana range: {min(kata_values)}-{max(kata_values)}")
print(f"First 20: {kata_values[:20]}")

for addr in range(0x4C0000, 0x4E0000, 4):
    if abs(addr - kata_offset) < 1200:
        continue
    try:
        vals = []
        ok = True
        for row in range(10):
            base = addr + row * 12
            for col in range(6):
                v = struct.unpack_from("<H", kata_ram, base + col*2)[0]
                vals.append(v)
                if v == 0 or v > 900:
                    ok = False
                    break
            if not ok:
                break
        if ok and len(set(vals)) > 30:
            all_vals = []
            all_ok = True
            for row in range(100):
                base = addr + row * 12
                for col in range(6):
                    v = struct.unpack_from("<H", kata_ram, base + col*2)[0]
                    all_vals.append(v)
                    if v == 0 or v > 900:
                        all_ok = False
                        break
                if not all_ok:
                    break
            if all_ok:
                print(f"  Candidate at 0x{addr:08X}: {len(set(all_vals))} unique, range {min(all_vals)}-{max(all_vals)}")
                for row in range(5):
                    rv = []
                    base = addr + row * 12
                    for col in range(6):
                        v = struct.unpack_from("<H", kata_ram, base + col*2)[0]
                        rv.append(v)
                    print(f"    Row {row}: {rv}")
    except:
        pass
print("Done.")
