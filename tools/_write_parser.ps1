$code = @"
import struct
import os
import json

RESDIR = "C:/Programmieren/wizardrytranslation/extracted/packdata_resources"
CLASSIFICATION = "C:/Programmieren/wizardrytranslation/dumps/resource_classification.json"
OUTPUT = "C:/Programmieren/wizardrytranslation/dumps/msg_header_analysis.json"

with open(CLASSIFICATION, "r") as f:
    cls = json.load(f)
msg_indices = cls["msg_resource_indices"]
print(f"Total MSG resources: {len(msg_indices)}")

def find_resource_file(idx):
    for fname in os.listdir(RESDIR):
        if fname.startswith(f"{idx:04d}_"):
            return os.path.join(RESDIR, fname)
    return None

def read_resource(idx):
    path = find_resource_file(idx)
    if not path:
        return None
    with open(path, "rb") as f:
        return f.read()

def scan_for_glyph_start(data):
    """Scan for where glyph stream starts - look for FFFF or FFFE as BE uint16."""
    for off in range(0, len(data) - 1, 2):
        val = struct.unpack(">H", data[off:off+2])[0]
        if val == 0xFFFF or val == 0xFFFE:
            return off
    return len(data)

def scan_for_glyph_start_v2(data):
    """Alternative: look for sequences of values in glyph range."""
    for off in range(0, len(data) - 5, 2):
        v1 = struct.unpack(">H", data[off:off+2])[0]
        v2 = struct.unpack(">H", data[off+2:off+4])[0]
        v3 = struct.unpack(">H", data[off+4:off+6])[0]
        if ((v1 <= 0x035A or v1 >= 0xFFFE) and
            (v2 <= 0x035A or v2 >= 0xFFFE) and
            (v3 <= 0x035A or v3 >= 0xFFFE)):
            return off
    return len(data)

sample_indices = [34, 35, 36, 46, 720, 899, 985, 1186, 1564, 2816]
print("\n=== PHASE 1: Detailed analysis of sample resources ===")
for idx in sample_indices:
    data = read_resource(idx)
    if data is None:
        print(f"\nResource {idx}: NOT FOUND")
        continue
    print(f"\nResource {idx}: size={len(data)}")
    n = min(16, len(data)//4)
    vals = struct.unpack(f"<{n}I", data[:n*4])
    print(f"  First {n} LE uint32:")
    for i, v in enumerate(vals):
        print(f"    [{i:2d}] off={i*4:4d}: {v:10d} (0x{v:08X})")
    gs1 = scan_for_glyph_start(data)
    gs2 = scan_for_glyph_start_v2(data)
    print(f"  Glyph start (FFFF/FFFE method): offset {gs1}")
    print(f"  Glyph start (glyph-range method): offset {gs2}")
    if n >= 7:
        for fi in [1,2,5,6]:
            for mult in [1, 2]:
                candidate = vals[fi] * mult
                if abs(candidate - gs1) < 16 or abs(candidate - gs2) < 16:
                    print(f"    ** header[{fi}]*{mult} = {candidate} matches glyph start!")

print("\n=== PHASE 2: Header table structure check ===")
for idx in [34, 35, 36, 46, 720, 985]:
    data = read_resource(idx)
    if data is None:
        continue
    first_val = struct.unpack("<I", data[0:4])[0]
    print(f"\nResource {idx}: first_val={first_val}, size={len(data)}")
    if first_val == 1:
        max_entries = min(64, len(data) // 16)
        table_entries = 0
        for e in range(max_entries):
            off = e * 16
            entry = struct.unpack("<4I", data[off:off+16])
            if entry[0] == e + 1:
                table_entries = e + 1
            else:
                break
        if table_entries > 0:
            print(f"  Sequential 16-byte table: {table_entries} entries")
            table_end = table_entries * 16
            print(f"  Table end offset: {table_end}")
            if table_end + 8 <= len(data):
                after = struct.unpack("<2I", data[table_end:table_end+8])
                print(f"  After table: {after[0]} (0x{after[0]:08X}), {after[1]} (0x{after[1]:08X})")
            gs = scan_for_glyph_start(data)
            print(f"  Glyph start: {gs}")
            for e in range(table_entries):
                off = e * 16
                entry = struct.unpack("<4I", data[off:off+16])
                print(f"    entry[{e}]: id={entry[0]}, f1={entry[1]}, f2={entry[2]}, f3={entry[3]}")
        else:
            print(f"  Not a sequential table")
    else:
        n = min(16, len(data)//4)
        vals = struct.unpack(f"<{n}I", data[:n*4])
        for i, v in enumerate(vals):
            print(f"    [{i:2d}] off={i*4:4d}: {v:10d} (0x{v:08X})")
        gs = scan_for_glyph_start(data)
        print(f"  Glyph start: {gs}")

print("\n=== PHASE 3: Parse all 296 MSG resources ===")
results = []
header_sizes = {}

for idx in msg_indices:
    data = read_resource(idx)
    if data is None:
        results.append({"index": idx, "error": "not found"})
        continue
    first4 = struct.unpack("<I", data[0:4])[0]
    gs_ffff = scan_for_glyph_start(data)
    gs_range = scan_for_glyph_start_v2(data)
    glyph_start = min(gs_ffff, gs_range)
    header_fields = []
    table_entries = 0
    if first4 == 1:
        max_entries = min(256, len(data) // 16)
        for e in range(max_entries):
            off = e * 16
            if off + 16 > len(data):
                break
            entry = struct.unpack("<4I", data[off:off+16])
            if entry[0] == e + 1:
                table_entries = e + 1
            else:
                break
        header_fields = []
        for e in range(table_entries):
            off = e * 16
            entry = list(struct.unpack("<4I", data[off:off+16]))
            header_fields.append(entry)
    else:
        n_hdr = glyph_start // 4
        if 0 < n_hdr <= 256:
            header_fields = list(struct.unpack(f"<{n_hdr}I", data[:n_hdr*4]))
        else:
            header_fields = [first4]
    msg_count = 0
    for off in range(glyph_start, len(data) - 1, 2):
        val = struct.unpack(">H", data[off:off+2])[0]
        if val == 0xFFFF:
            msg_count += 1
    entry_result = {
        "index": idx,
        "file_size": len(data),
        "first_uint32": first4,
        "header_size": glyph_start,
        "glyph_start_offset": glyph_start,
        "table_entries": table_entries,
        "message_count": msg_count
    }
    if isinstance(header_fields, list) and len(header_fields) <= 64:
        if table_entries > 0:
            entry_result["header_type"] = "sequential_table"
            entry_result["header_entries"] = header_fields
        else:
            entry_result["header_type"] = "flat"
            entry_result["header_fields"] = header_fields[:32]
    else:
        entry_result["header_type"] = "large"
        entry_result["header_field_count"] = len(header_fields) if isinstance(header_fields, list) else 0
    hs = glyph_start
    header_sizes[hs] = header_sizes.get(hs, 0) + 1
    results.append(entry_result)

print(f"\nTotal parsed: {len(results)}")
print(f"\nHeader size distribution (top 20):")
for hs, cnt in sorted(header_sizes.items(), key=lambda x: -x[1])[:20]:
    print(f"  {hs:6d} bytes: {cnt} resources")

type_counts = {}
for r in results:
    ht = r.get("header_type", "unknown")
    type_counts[ht] = type_counts.get(ht, 0) + 1
print(f"\nHeader type counts: {type_counts}")

print("\n=== PHASE 4: Check header fields as offset pointers ===")
pointer_hits = 0
for r in results:
    if r.get("header_type") == "sequential_table" and r.get("header_entries"):
        entries = r["header_entries"]
        gs = r["glyph_start_offset"]
        for entry in entries:
            if entry[2] * 2 == gs or entry[1] * 2 == gs:
                pointer_hits += 1
                break
print(f"Resources where a table entry field matches glyph_start: {pointer_hits}")

for r in results:
    if r.get("header_type") == "flat" and r.get("header_fields"):
        hf = r["header_fields"]
        gs = r["glyph_start_offset"]
        matches = []
        for i, v in enumerate(hf):
            if v > 0 and (v == gs or v * 2 == gs):
                matches.append((i, v))
        if matches:
            print(f"  Resource {r['index']}: field matches: {matches}")

print("\n=== PHASE 5: Sequential table analysis ===")
table_resource_count = 0
for r in results:
    if r.get("header_type") == "sequential_table":
        table_resource_count += 1
        idx = r["index"]
        entries = r["header_entries"]
        gs = r["glyph_start_offset"]
        table_end = len(entries) * 16
        print(f"  Resource {idx}: {len(entries)} table entries, table_end={table_end}, glyph_start={gs}, gap={gs - table_end}")
print(f"Total with sequential table: {table_resource_count}")

output_data = {
    "summary": {
        "total_parsed": len(results),
        "header_size_distribution": {str(k): v for k, v in sorted(header_sizes.items())},
        "header_type_counts": type_counts
    },
    "resources": results
}

with open(OUTPUT, "w") as f:
    json.dump(output_data, f, indent=2)
print(f"\nSaved to {OUTPUT}")
"@

Set-Content -Path "C:/Programmieren/wizardrytranslation/tools/parse_msg_header.py" -Value $code -Encoding UTF8
Write-Host "File written successfully"
