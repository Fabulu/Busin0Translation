import sys, io, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

data = open("extracted/SLPM_653.78", "rb").read()

# Find all ASCII strings min 3 chars
def find_ascii(data, min_len=3):
    hits = []
    i = 0
    while i < len(data):
        if 0x20 <= data[i] <= 0x7E:
            start = i
            while i < len(data) and 0x20 <= data[i] <= 0x7E: i += 1
            s = data[start:i].decode("ascii")
            if len(s) >= min_len: hits.append((start, s))
        else: i += 1
    return hits

strings = find_ascii(data)

# File-related strings
print("=== FILE PATHS / EXTENSIONS ===")
for off, s in strings:
    sl = s.lower()
    if any(x in sl for x in [".dig", ".dsi", ".lzh", ".irx", ".img", ".tim", ".bin",
                              ".dat", ".pac", ".msg", ".scr", ".tbl", ".mdl",
                              "cdrom", "pack", "file", "path", "load", "open",
                              "read", "seek", ":/", "\\\\", "/"]):
        if len(s) > 3:
            print(f"  0x{off:08X}: {s}")

print("\n=== TEXT/MSG SYSTEM REFERENCES ===")
for off, s in strings:
    sl = s.lower()
    if any(x in sl for x in ["msg", "text", "font", "char", "glyph", "dialog",
                              "talk", "name", "item", "spell", "menu", "string",
                              "script", "event", "story"]):
        print(f"  0x{off:08X}: {s}")

print("\n=== FORMAT STRINGS (printf-style) ===")
for off, s in strings:
    if "%" in s and any(c in s for c in "dsfxXupl") and len(s) > 3:
        print(f"  0x{off:08X}: {s}")

print("\n=== DEBUG/ERROR MESSAGES ===")
for off, s in strings:
    sl = s.lower()
    if any(x in sl for x in ["error", "warn", "assert", "fail", "debug",
                              "abort", "panic", "fatal", "null", "invalid"]):
        print(f"  0x{off:08X}: {s}")

print("\n=== ARCHIVE/DATA STRUCTURE HINTS ===")
for off, s in strings:
    sl = s.lower()
    if any(x in sl for x in ["header", "entry", "index", "table", "offset",
                              "size", "count", "compress", "decomp", "lz",
                              "pack", "unpack", "sector", "block", "chunk"]):
        print(f"  0x{off:08X}: {s}")

# Look for potential offset tables pointing into PACKDATA.DIG
PACKDATA_SIZE = 839661568
print(f"\n=== POTENTIAL PACKDATA OFFSET TABLES ===")
print(f"(Looking for sequences of 4+ LE uint32 values in range 0-{PACKDATA_SIZE:,})")
for i in range(0, len(data) - 32, 4):
    vals = [struct.unpack_from("<I", data, i + j*4)[0] for j in range(8)]
    # Check if values look like ascending offsets into PACKDATA
    if all(0 < v < PACKDATA_SIZE for v in vals):
        if all(vals[j] < vals[j+1] for j in range(7)):
            if vals[1] - vals[0] > 0x100:  # reasonable gap
                print(f"  0x{i:08X}: ascending offsets: {[hex(v) for v in vals]}")
                if sum(1 for _ in range(i, min(i+200, len(data)-4), 4)) > 10:
                    break  # just show first match

print("\n=== PS2 SDK / SYSTEM REFERENCES ===")
for off, s in strings:
    sl = s.lower()
    if any(x in sl for x in ["sce", "iop", "ee ", "dma", "vu0", "vu1",
                              "gs ", "gif", "vif", "spu", "cdvd"]):
        if len(s) > 3:
            print(f"  0x{off:08X}: {s}")
