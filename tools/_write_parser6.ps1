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

# For sequential-table resources, check if offset + table_end + 2 = FFFF position + 2
# i.e., offset + table_end = FFFF position
# Res 34: table_end=304, offset[0]=200, 200+304=504 vs FFFF+2[0]=504. Yes!
# Res 35: table_end=16, offset[0]=104, 104+16=120 vs FFFF+2[0]=120. Yes!
# Res 46: table_end=32, offset[0]=396, 396+32=428 vs FFFF+2[0]=428. Yes!

print("=== VERIFY: offset + table_end = FFFF+2 position ===")
for idx in [34, 35, 46, 39, 47, 720, 985, 1186]:
    data = read_resource(idx)
    if data is None:
        continue
    n_table = count_sequential_table(data)
    table_end = n_table * 16
    glyph_start = scan_for_ffff_fffe(data)

    # Read between region as BE uint16, take even values
    between = data[table_end:glyph_start]
    n16 = len(between) // 2
    if n16 == 0:
        continue
    be16 = list(struct.unpack(f">{n16}H", between[:n16*2]))
    even_vals = be16[0::2]

    msg_count = even_vals[0]
    offsets = even_vals[1:]

    # Get all FFFF+2 positions
    ffff_plus2 = []
    for off in range(glyph_start, len(data) - 1, 2):
        val = struct.unpack(">H", data[off:off+2])[0]
        if val == 0xFFFF:
            ffff_plus2.append(off + 2)

    # Check: offset + table_end == FFFF+2
    adjusted = [o + table_end for o in offsets]
    match = sum(1 for a, b in zip(adjusted, ffff_plus2) if a == b)
    total = min(len(adjusted), len(ffff_plus2))

    print(f"Res {idx}: table_end={table_end}, count={msg_count}, #offsets={len(offsets)}, #FFFF={len(ffff_plus2)}")
    print(f"  Match (offset+table_end == FFFF+2): {match}/{total}")
    if match < total:
        print(f"  First 5 adjusted: {adjusted[:5]}")
        print(f"  First 5 FFFF+2: {ffff_plus2[:5]}")
        # Show mismatches
        for i, (a, b) in enumerate(zip(adjusted[:10], ffff_plus2[:10])):
            if a != b:
                print(f"    Mismatch at [{i}]: adjusted={a}, FFFF+2={b}, diff={b-a}")

# For non-table resources, the offsets are already absolute (table_end=0)
print("\n=== NON-TABLE: Verify offset == FFFF+2 ===")
for idx in [36, 37, 40, 41, 42]:
    data = read_resource(idx)
    glyph_start = scan_for_ffff_fffe(data)

    n16 = glyph_start // 2
    be16 = list(struct.unpack(f">{n16}H", data[:n16*2]))
    even_vals = be16[0::2]
    offsets = even_vals[1:]

    ffff_plus2 = []
    for off in range(glyph_start, len(data) - 1, 2):
        val = struct.unpack(">H", data[off:off+2])[0]
        if val == 0xFFFF:
            ffff_plus2.append(off + 2)

    match = sum(1 for a, b in zip(offsets, ffff_plus2) if a == b)
    total = min(len(offsets), len(ffff_plus2))
    print(f"Res {idx}: match {match}/{total}")

# Now parse ALL 296 resources with this understanding
print("\n=== FULL PARSE: All 296 resources ===")
results = []
match_count = 0
mismatch_list = []

for idx in msg_indices:
    data = read_resource(idx)
    if data is None:
        results.append({"index": idx, "error": "not found"})
        continue

    first4_le = struct.unpack("<I", data[0:4])[0]
    n_table = count_sequential_table(data)
    table_end = n_table * 16
    glyph_start = scan_for_ffff_fffe(data)

    # Count FFFF and FFFE
    ffff_count = 0
    fffe_count = 0
    ffff_plus2 = []
    for off in range(glyph_start, len(data) - 1, 2):
        val = struct.unpack(">H", data[off:off+2])[0]
        if val == 0xFFFF:
            ffff_count += 1
            ffff_plus2.append(off + 2)
        elif val == 0xFFFE:
            fffe_count += 1

    if n_table > 0:
        header_type = "sequential_table"
        # Between region
        between = data[table_end:glyph_start]
        n16 = len(between) // 2
        if n16 > 0:
            be16 = list(struct.unpack(f">{n16}H", between[:n16*2]))
            even_vals = be16[0::2]
            odd_vals = be16[1::2]
            all_odd_zero = all(v == 0 for v in odd_vals)
        else:
            even_vals = []
            all_odd_zero = True

        if even_vals:
            msg_count_hdr = even_vals[0]
            offsets = even_vals[1:]
            adjusted = [o + table_end for o in offsets]
            match = sum(1 for a, b in zip(adjusted, ffff_plus2) if a == b)
            total = min(len(adjusted), len(ffff_plus2))
            offset_match_pct = match / total * 100 if total > 0 else 0
        else:
            msg_count_hdr = 0
            offsets = []
            offset_match_pct = 0

        # Table entries
        table_data = []
        for e in range(n_table):
            off = e * 16
            entry = list(struct.unpack("<4I", data[off:off+16]))
            table_data.append(entry)
    else:
        header_type = "flat_offset_table"
        # Read header as BE uint16
        n16 = glyph_start // 2
        if n16 > 0:
            be16 = list(struct.unpack(f">{n16}H", data[:n16*2]))
            even_vals = be16[0::2]
            odd_vals = be16[1::2]
            all_odd_zero = all(v == 0 for v in odd_vals)
        else:
            even_vals = []
            all_odd_zero = True

        if even_vals:
            msg_count_hdr = even_vals[0]
            offsets = even_vals[1:]
            match = sum(1 for a, b in zip(offsets, ffff_plus2) if a == b)
            total = min(len(offsets), len(ffff_plus2))
            offset_match_pct = match / total * 100 if total > 0 else 0
        else:
            msg_count_hdr = 0
            offsets = []
            offset_match_pct = 0
        table_data = []

    if offset_match_pct == 100:
        match_count += 1
    elif offset_match_pct < 100:
        mismatch_list.append((idx, offset_match_pct, msg_count_hdr, ffff_count, header_type))

    entry_result = {
        "index": idx,
        "file_size": len(data),
        "header_type": header_type,
        "header_size": glyph_start,
        "glyph_start_offset": glyph_start,
        "message_count": ffff_count,
        "fffe_count": fffe_count,
        "msg_count_from_header": msg_count_hdr,
        "offset_table_size": len(offsets),
        "offset_match_pct": offset_match_pct,
        "all_odd_zero": all_odd_zero
    }
    if n_table > 0:
        entry_result["table_entries"] = n_table
        entry_result["table_end_offset"] = table_end
        if n_table <= 64:
            entry_result["table_data"] = table_data
    if len(offsets) <= 32:
        entry_result["offset_table"] = offsets

    results.append(entry_result)

print(f"Total: {len(results)}")
print(f"Perfect offset match: {match_count}/{len(results)}")
print(f"\nMismatches ({len(mismatch_list)}):")
for idx, pct, hdr_count, ffff_count, htype in sorted(mismatch_list, key=lambda x: x[1]):
    print(f"  Res {idx}: match={pct:.1f}%, hdr_count={hdr_count}, ffff={ffff_count}, type={htype}")

# Save
output_data = {
    "summary": {
        "total_parsed": len(results),
        "perfect_offset_match": match_count,
        "header_format": {
            "sequential_table_resources": sum(1 for r in results if r.get("header_type") == "sequential_table"),
            "flat_offset_table_resources": sum(1 for r in results if r.get("header_type") == "flat_offset_table"),
        },
        "structure_description": {
            "sequential_table": "Starts with 16-byte entries: [id(LE32), field1(LE32), field2(LE32), field3(LE32)]. id starts at 1 and increments. Followed by offset table.",
            "flat_offset_table": "No sequential table prefix. Header is directly the offset table.",
            "offset_table_format": "BE uint16 pairs: [msg_count, 0, offset1, 0, offset2, 0, ...]. Offsets point to first glyph byte after each FFFF separator. For sequential_table resources, offsets are relative to table_end. For flat resources, offsets are absolute.",
            "glyph_stream": "Starts at first FFFF/FFFE. Messages separated by FFFF (start) and FFFE (end). Each glyph is a BE uint16 index."
        }
    },
    "resources": results
}

with open(OUTPUT, "w") as f:
    json.dump(output_data, f, indent=2)
print(f"\nSaved to {OUTPUT}")
"@

Set-Content -Path "C:/Programmieren/wizardrytranslation/tools/parse_msg_header.py" -Value $code -Encoding UTF8
Write-Host "File written successfully"
