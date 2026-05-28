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

def scan_for_ffff_fffe(data, start=0):
    """Scan for first FFFF or FFFE as BE uint16 on 2-byte boundary."""
    for off in range(start, len(data) - 1, 2):
        val = struct.unpack(">H", data[off:off+2])[0]
        if val == 0xFFFF or val == 0xFFFE:
            return off
    return len(data)

def count_sequential_table(data):
    """Count 16-byte entries where field[0] == sequential id starting from 1."""
    first4 = struct.unpack("<I", data[0:4])[0]
    if first4 != 1:
        return 0
    max_entries = min(256, len(data) // 16)
    table_entries = 0
    for e in range(max_entries):
        off = e * 16
        if off + 16 > len(data):
            break
        entry = struct.unpack("<4I", data[off:off+16])
        if entry[0] == e + 1:
            table_entries = e + 1
        else:
            break
    return table_entries

def analyze_between_table_and_glyphs(data, table_end, glyph_start):
    """Analyze the bytes between the sequential table and the glyph stream."""
    if table_end >= glyph_start:
        return None
    between = data[table_end:glyph_start]
    n = len(between) // 4
    if n == 0:
        return None
    vals = list(struct.unpack(f"<{n}I", between[:n*4]))
    return vals

# Phase 1: Deep dive into resource 34 - the exemplar
print("=== DEEP DIVE: Resource 34 ===")
data = read_resource(34)
n_table = count_sequential_table(data)
print(f"Sequential table entries: {n_table}")
table_end = n_table * 16
glyph_start = scan_for_ffff_fffe(data)
print(f"Table end: {table_end}, Glyph start (FFFF): {glyph_start}")

# Print table entries
for e in range(n_table):
    off = e * 16
    entry = struct.unpack("<4I", data[off:off+16])
    print(f"  table[{e}]: id={entry[0]}, field1={entry[1]}, field2={entry[2]}, field3={entry[3]}")

# Print between region
print(f"\nBetween table end ({table_end}) and glyph start ({glyph_start}):")
between = data[table_end:glyph_start]
print(f"  {len(between)} bytes")
# Show as BE uint16
n_be = len(between) // 2
if n_be > 0:
    be_vals = struct.unpack(f">{n_be}H", between[:n_be*2])
    print(f"  As BE uint16 (first 50): {list(be_vals[:50])}")
# Also show as LE uint16
if n_be > 0:
    le_vals = struct.unpack(f"<{n_be}H", between[:n_be*2])
    print(f"  As LE uint16 (first 50): {list(le_vals[:50])}")
# Show raw hex
print(f"  Raw hex: {between[:100].hex()}")

# What's right before glyph_start?
print(f"\n20 bytes before glyph_start: {data[glyph_start-20:glyph_start].hex()}")
print(f"20 bytes at glyph_start: {data[glyph_start:glyph_start+20].hex()}")

# Print glyph stream as BE uint16
gs_vals = []
for off in range(glyph_start, min(glyph_start+60, len(data)), 2):
    v = struct.unpack(">H", data[off:off+2])[0]
    gs_vals.append(f"0x{v:04X}")
print(f"First 30 glyph values: {gs_vals}")

# Phase 2: Deep dive into a few more resources
print("\n=== DEEP DIVE: More resources ===")
for idx in [35, 46, 720, 985, 1186, 1564, 2816]:
    data = read_resource(idx)
    if data is None:
        continue
    n_table = count_sequential_table(data)
    glyph_start = scan_for_ffff_fffe(data)
    table_end = n_table * 16
    print(f"\nResource {idx}: size={len(data)}, table_entries={n_table}, table_end={table_end}, glyph_start={glyph_start}")

    # Print table entries
    for e in range(n_table):
        off = e * 16
        entry = struct.unpack("<4I", data[off:off+16])
        print(f"  table[{e}]: id={entry[0]}, f1={entry[1]}, f2={entry[2]}, f3={entry[3]}")

    # Between region
    if table_end < glyph_start:
        between = data[table_end:glyph_start]
        print(f"  Between ({len(between)} bytes): {between[:80].hex()}")
        # As LE uint32
        n32 = len(between) // 4
        if n32 > 0 and n32 <= 50:
            vals32 = list(struct.unpack(f"<{n32}I", between[:n32*4]))
            print(f"  As LE uint32: {vals32}")

    # Show glyph start
    gs_vals = []
    for off in range(glyph_start, min(glyph_start+40, len(data)), 2):
        v = struct.unpack(">H", data[off:off+2])[0]
        gs_vals.append(f"0x{v:04X}")
    print(f"  First glyph values: {gs_vals}")

# Phase 3: Check resource 36 (non-table format, first_val != 1)
print("\n=== DEEP DIVE: Non-table resources ===")
for idx in [36, 37, 38, 40, 899, 900, 901]:
    data = read_resource(idx)
    if data is None:
        continue
    first4 = struct.unpack("<I", data[0:4])[0]
    glyph_start = scan_for_ffff_fffe(data)
    print(f"\nResource {idx}: size={len(data)}, first_val={first4} (0x{first4:08X}), glyph_start={glyph_start}")

    # Try reading first bytes as BE uint16 instead
    n_be = min(32, len(data) // 2)
    be_vals = struct.unpack(f">{n_be}H", data[:n_be*2])
    print(f"  As BE uint16: {[f'0x{v:04X}' for v in be_vals[:20]]}")

    # Raw hex
    print(f"  Raw hex (first 64): {data[:64].hex()}")
    print(f"  Raw hex at glyph_start: {data[glyph_start:glyph_start+40].hex()}")

# Phase 4: Parse ALL resources with the corrected glyph start (FFFF/FFFE only)
print("\n=== PHASE 4: Full parse with FFFF/FFFE glyph detection ===")
results = []
header_sizes = {}

for idx in msg_indices:
    data = read_resource(idx)
    if data is None:
        results.append({"index": idx, "error": "not found"})
        continue

    first4 = struct.unpack("<I", data[0:4])[0]
    n_table = count_sequential_table(data)
    table_end = n_table * 16
    glyph_start = scan_for_ffff_fffe(data)

    # Count FFFF separators
    msg_count = 0
    for off in range(glyph_start, len(data) - 1, 2):
        val = struct.unpack(">H", data[off:off+2])[0]
        if val == 0xFFFF:
            msg_count += 1

    # Parse table entries
    table_data = []
    for e in range(n_table):
        off = e * 16
        entry = list(struct.unpack("<4I", data[off:off+16]))
        table_data.append(entry)

    # Between region as LE uint32
    between_fields = []
    if table_end < glyph_start:
        between = data[table_end:glyph_start]
        n32 = len(between) // 4
        if 0 < n32 <= 128:
            between_fields = list(struct.unpack(f"<{n32}I", between[:n32*4]))

    entry_result = {
        "index": idx,
        "file_size": len(data),
        "first_uint32": first4,
        "header_size": glyph_start,
        "glyph_start_offset": glyph_start,
        "table_entries": n_table,
        "table_end_offset": table_end,
        "between_size": glyph_start - table_end if table_end < glyph_start else 0,
        "message_count": msg_count
    }

    if n_table > 0:
        entry_result["header_type"] = "sequential_table"
        if n_table <= 64:
            entry_result["table_data"] = table_data
        if len(between_fields) <= 64:
            entry_result["between_fields"] = between_fields
    else:
        entry_result["header_type"] = "non_table"
        # Read header as flat fields
        n_hdr = min(glyph_start // 4, 32)
        if n_hdr > 0:
            entry_result["header_fields"] = list(struct.unpack(f"<{n_hdr}I", data[:n_hdr*4]))

    header_sizes[glyph_start] = header_sizes.get(glyph_start, 0) + 1
    results.append(entry_result)

print(f"\nTotal parsed: {len(results)}")
print(f"\nHeader size (glyph_start) distribution:")
for hs, cnt in sorted(header_sizes.items(), key=lambda x: -x[1])[:30]:
    print(f"  {hs:6d} bytes: {cnt} resources")

type_counts = {}
for r in results:
    ht = r.get("header_type", "unknown")
    type_counts[ht] = type_counts.get(ht, 0) + 1
print(f"\nHeader type counts: {type_counts}")

# Phase 5: Check if table field1 or field2 relate to glyph data
print("\n=== PHASE 5: Table field analysis ===")
# For resources with sequential tables, check if field2 values are cumulative offsets
for idx in [34, 46, 720, 985, 1186]:
    r = next((x for x in results if x["index"] == idx), None)
    if r and r.get("table_data"):
        print(f"\nResource {idx}: glyph_start={r['glyph_start_offset']}, file_size={r['file_size']}")
        for i, entry in enumerate(r["table_data"]):
            # Check if field2 could be byte offset from glyph_start
            print(f"  entry[{i}]: id={entry[0]}, f1={entry[1]}, f2={entry[2]}, f3={entry[3]}")
            print(f"    f1*2={entry[1]*2}, f2*2={entry[2]*2}")

# Phase 6: Look at the between_fields more carefully
print("\n=== PHASE 6: Between-fields analysis ===")
between_size_dist = {}
for r in results:
    bs = r.get("between_size", 0)
    between_size_dist[bs] = between_size_dist.get(bs, 0) + 1
print("Between-region size distribution:")
for bs, cnt in sorted(between_size_dist.items(), key=lambda x: -x[1])[:20]:
    print(f"  {bs:6d} bytes: {cnt} resources")

# Show between_fields for several resources
for idx in [34, 35, 46, 720, 985, 1186, 1564, 2816]:
    r = next((x for x in results if x["index"] == idx), None)
    if r and r.get("between_fields"):
        bf = r["between_fields"]
        print(f"\nResource {idx}: between_fields ({len(bf)} uint32):")
        for i, v in enumerate(bf):
            print(f"  [{i}] {v} (0x{v:08X})")

# Save
output_data = {
    "summary": {
        "total_parsed": len(results),
        "header_size_distribution": {str(k): v for k, v in sorted(header_sizes.items())},
        "header_type_counts": type_counts,
        "between_size_distribution": {str(k): v for k, v in sorted(between_size_dist.items())}
    },
    "resources": results
}

with open(OUTPUT, "w") as f:
    json.dump(output_data, f, indent=2)
print(f"\nSaved to {OUTPUT}")
"@

Set-Content -Path "C:/Programmieren/wizardrytranslation/tools/parse_msg_header.py" -Value $code -Encoding UTF8
Write-Host "File written successfully"
