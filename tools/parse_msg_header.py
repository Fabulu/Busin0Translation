import struct
import os
import json

RESDIR = "C:/Programmieren/wizardrytranslation/extracted/packdata_resources"
CLASSIFICATION = "C:/Programmieren/wizardrytranslation/dumps/resource_classification.json"
OUTPUT = "C:/Programmieren/wizardrytranslation/dumps/msg_header_analysis.json"

with open(CLASSIFICATION, "r") as f:
    cls = json.load(f)
msg_indices = cls["msg_resource_indices"]

# Get type_groups for cross-referencing
msg_analysis_path = "C:/Programmieren/wizardrytranslation/dumps/msg_structure_analysis.json"
with open(msg_analysis_path, "r") as f:
    msg_analysis = json.load(f)
type_groups = msg_analysis["summary"]["type_groups"]

# Build index -> type_code map
idx_to_type = {}
for tcode, indices in type_groups.items():
    for idx in indices:
        idx_to_type[idx] = tcode

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
    for off in range(start, len(data) - 1, 2):
        val = struct.unpack(">H", data[off:off+2])[0]
        if val == 0xFFFF or val == 0xFFFE:
            return off
    return len(data)

def count_sequential_table(data):
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

# Check which type_codes have the matching offset pattern
print("=== Which type_codes have matching offset tables? ===")
# Matching resources from previous run: 34,35,39,46,47 and the non-table ones 36-45,48,49
matching_indices = set()
for idx in msg_indices:
    data = read_resource(idx)
    if data is None:
        continue
    n_table = count_sequential_table(data)
    table_end = n_table * 16
    glyph_start = scan_for_ffff_fffe(data)

    # Get FFFF+2 positions
    ffff_plus2 = []
    for off in range(glyph_start, len(data) - 1, 2):
        val = struct.unpack(">H", data[off:off+2])[0]
        if val == 0xFFFF:
            ffff_plus2.append(off + 2)

    if n_table > 0:
        between = data[table_end:glyph_start]
        n16 = len(between) // 2
        if n16 > 0:
            be16 = list(struct.unpack(f">{n16}H", between[:n16*2]))
            even_vals = be16[0::2]
            offsets = even_vals[1:]
            adjusted = [o + table_end for o in offsets]
            match = sum(1 for a, b in zip(adjusted, ffff_plus2) if a == b)
            total = min(len(adjusted), len(ffff_plus2))
            if total > 0 and match == total:
                matching_indices.add(idx)
    else:
        n16 = glyph_start // 2
        if n16 > 0:
            be16 = list(struct.unpack(f">{n16}H", data[:n16*2]))
            even_vals = be16[0::2]
            offsets = even_vals[1:]
            match = sum(1 for a, b in zip(offsets, ffff_plus2) if a == b)
            total = min(len(offsets), len(ffff_plus2))
            if total > 0 and match == total:
                matching_indices.add(idx)

print(f"Matching resources: {len(matching_indices)}")
# Group by type_code
matching_by_type = {}
nonmatching_by_type = {}
for idx in msg_indices:
    tc = idx_to_type.get(idx, "unknown")
    if idx in matching_indices:
        matching_by_type.setdefault(tc, []).append(idx)
    else:
        nonmatching_by_type.setdefault(tc, []).append(idx)

print("Matching by type:")
for tc, indices in sorted(matching_by_type.items()):
    print(f"  {tc}: {len(indices)} resources ({indices[:10]}{'...' if len(indices)>10 else ''})")
print("Non-matching by type:")
for tc, indices in sorted(nonmatching_by_type.items()):
    print(f"  {tc}: {len(indices)} resources ({indices[:10]}{'...' if len(indices)>10 else ''})")

# Now look at the non-matching resources more carefully
# For resources with msg_count_hdr=1152 (many type01 resources), the between region
# is NOT a BE uint16 offset table. What is it?
print("\n=== Non-matching type01 resource analysis ===")
type01_nonmatch = nonmatching_by_type.get("type01", [])
print(f"Non-matching type01: {len(type01_nonmatch)} resources")

# Look at one example
for idx in type01_nonmatch[:3]:
    data = read_resource(idx)
    if data is None:
        continue
    n_table = count_sequential_table(data)
    table_end = n_table * 16
    glyph_start = scan_for_ffff_fffe(data)
    between = data[table_end:glyph_start]

    print(f"\nRes {idx}: size={len(data)}, table_entries={n_table}, table_end={table_end}, glyph_start={glyph_start}")
    print(f"  Between: {len(between)} bytes")
    print(f"  Between hex (first 128): {between[:128].hex()}")

    # Try reading as mixed LE/BE
    # The between region for matching resources was all BE uint16 with [count, 0, off1, 0, off2, 0, ...]
    # For non-matching, it seems different. Let me check if the between region has a different structure.

    # Check as LE uint32
    n32 = len(between) // 4
    if n32 > 0:
        le32 = list(struct.unpack(f"<{n32}I", between[:n32*4]))
        print(f"  As LE uint32 (first 20): {[f'{v} (0x{v:08X})' for v in le32[:20]]}")

    # Check as LE uint16
    n16 = len(between) // 2
    if n16 > 0:
        le16 = list(struct.unpack(f"<{n16}H", between[:n16*2]))
        print(f"  As LE uint16 (first 30): {le16[:30]}")

    # Check as bytes
    print(f"  First 40 bytes: {list(between[:40])}")

    # The glyph_start for these is typically 98 bytes
    # Sequential table is 16 bytes (1 entry), between is 82 bytes
    # So the header is: [16 bytes table] [82 bytes config] [glyph stream]

    # Check if 0x0480 (32772) could be a dimension/size field
    # And following values look like GPU/display parameters

# Now check between_size distribution for type01 non-matching
between_sizes_nonmatch = {}
for idx in type01_nonmatch:
    data = read_resource(idx)
    if data is None:
        continue
    n_table = count_sequential_table(data)
    table_end = n_table * 16
    glyph_start = scan_for_ffff_fffe(data)
    bs = glyph_start - table_end
    between_sizes_nonmatch[bs] = between_sizes_nonmatch.get(bs, 0) + 1
print(f"\nType01 non-matching between-size distribution:")
for bs, cnt in sorted(between_sizes_nonmatch.items(), key=lambda x: -x[1]):
    print(f"  {bs} bytes: {cnt} resources")

# Final comprehensive parse
print("\n=== FINAL COMPREHENSIVE PARSE ===")
results = []

for idx in msg_indices:
    data = read_resource(idx)
    if data is None:
        results.append({"index": idx, "error": "not found"})
        continue

    first4_le = struct.unpack("<I", data[0:4])[0]
    n_table = count_sequential_table(data)
    table_end = n_table * 16
    glyph_start = scan_for_ffff_fffe(data)
    type_code = idx_to_type.get(idx, "unknown")

    # Count FFFF and FFFE
    ffff_count = 0
    fffe_count = 0
    for off in range(glyph_start, len(data) - 1, 2):
        val = struct.unpack(">H", data[off:off+2])[0]
        if val == 0xFFFF:
            ffff_count += 1
        elif val == 0xFFFE:
            fffe_count += 1

    has_offset_table = idx in matching_indices
    between_size = glyph_start - table_end if table_end < glyph_start else 0

    # Parse table entries
    table_data = []
    for e in range(min(n_table, 64)):
        off = e * 16
        entry = list(struct.unpack("<4I", data[off:off+16]))
        table_data.append(entry)

    # Parse offset table for matching resources
    msg_count_hdr = 0
    if has_offset_table:
        if n_table > 0:
            between = data[table_end:glyph_start]
            n16 = len(between) // 2
            if n16 > 0:
                be16 = list(struct.unpack(f">{n16}H", between[:n16*2]))
                msg_count_hdr = be16[0]
        else:
            n16 = glyph_start // 2
            if n16 > 0:
                be16 = list(struct.unpack(f">{n16}H", data[:n16*2]))
                msg_count_hdr = be16[0]

    entry_result = {
        "index": idx,
        "type_code": type_code,
        "file_size": len(data),
        "has_sequential_table": n_table > 0,
        "table_entries": n_table,
        "table_end_offset": table_end,
        "header_size": glyph_start,
        "glyph_start_offset": glyph_start,
        "between_size": between_size,
        "has_offset_table": has_offset_table,
        "message_count": ffff_count,
        "fffe_count": fffe_count,
        "msg_count_from_header": msg_count_hdr if has_offset_table else None
    }

    if n_table > 0 and n_table <= 64:
        entry_result["table_data"] = table_data

    results.append(entry_result)

# Summary statistics
type_code_stats = {}
for r in results:
    tc = r.get("type_code", "unknown")
    if tc not in type_code_stats:
        type_code_stats[tc] = {"count": 0, "has_seq_table": 0, "has_offset_table": 0, "header_sizes": set()}
    type_code_stats[tc]["count"] += 1
    if r.get("has_sequential_table"):
        type_code_stats[tc]["has_seq_table"] += 1
    if r.get("has_offset_table"):
        type_code_stats[tc]["has_offset_table"] += 1
    type_code_stats[tc]["header_sizes"].add(r.get("header_size", 0))

print(f"\nTotal parsed: {len(results)}")
print(f"\nBy type_code:")
for tc, stats in sorted(type_code_stats.items()):
    hs = sorted(stats["header_sizes"])
    print(f"  {tc}: count={stats['count']}, seq_table={stats['has_seq_table']}, offset_table={stats['has_offset_table']}, header_sizes={hs[:10]}")

# Save
output_data = {
    "summary": {
        "total_parsed": len(results),
        "resources_with_offset_table": len(matching_indices),
        "resources_without_offset_table": len(results) - len(matching_indices),
        "structure_description": {
            "format_A_with_offset_table": {
                "description": "Resources where the header contains a BE uint16 message offset table",
                "count": len(matching_indices),
                "types": list(sorted(matching_by_type.keys())),
                "sequential_table_header": "16-byte entries: [id(LE32), field1(LE32), field2(LE32), field3(LE32)]",
                "offset_table": "BE uint16 pairs: [msg_count, 0, offset1, 0, offset2, 0, ...] where each offset is byte position of message start (FFFF+2). For seq-table resources, offsets relative to table_end; for flat, absolute.",
                "glyph_stream": "Messages delimited by FFFF (start) / FFFE (end), glyphs as BE uint16"
            },
            "format_B_without_offset_table": {
                "description": "Resources with different between-region structure (config/params, not offset table)",
                "count": len(results) - len(matching_indices),
                "types": list(sorted(nonmatching_by_type.keys())),
                "note": "These have a fixed-size config block between table and glyph stream. Common between_size is 82 bytes for type01."
            }
        },
        "type_code_stats": {tc: {"count": s["count"], "has_seq_table": s["has_seq_table"], "has_offset_table": s["has_offset_table"], "header_sizes": sorted(s["header_sizes"])} for tc, s in sorted(type_code_stats.items())}
    },
    "resources": results
}

with open(OUTPUT, "w") as f:
    json.dump(output_data, f, indent=2)
print(f"\nSaved to {OUTPUT}")
