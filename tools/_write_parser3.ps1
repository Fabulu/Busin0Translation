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

# Focus: understand the between region structure
print("=== BETWEEN REGION ANALYSIS ===")
print()

# The between region raw bytes for resource 34 showed BE uint16 pattern: 49, 0, 200, 0, 206, 0, ...
# Let me re-read them carefully as uint32 where the actual encoding might be big-endian uint32
for idx in [34, 35, 46, 720, 985, 1186, 1564, 2816, 36, 37, 38]:
    data = read_resource(idx)
    if data is None:
        continue
    first4 = struct.unpack("<I", data[0:4])[0]
    n_table = count_sequential_table(data)
    table_end = n_table * 16
    glyph_start = scan_for_ffff_fffe(data)

    print(f"Resource {idx}: size={len(data)}, table_entries={n_table}, table_end={table_end}, glyph_start={glyph_start}")

    # Count FFFF in glyph stream
    ffff_count = 0
    fffe_count = 0
    for off in range(glyph_start, len(data) - 1, 2):
        val = struct.unpack(">H", data[off:off+2])[0]
        if val == 0xFFFF:
            ffff_count += 1
        elif val == 0xFFFE:
            fffe_count += 1
    print(f"  FFFF count: {ffff_count}, FFFE count: {fffe_count}")

    if n_table > 0:
        between = data[table_end:glyph_start]
        blen = len(between)
        print(f"  Between region: {blen} bytes")

        # Try reading as BE uint32
        n32 = blen // 4
        if n32 > 0:
            be32 = list(struct.unpack(f">{n32}I", between[:n32*4]))
            print(f"  As BE uint32 (first 20): {be32[:20]}")

            # Check if first value could be a count
            first_be32 = be32[0]
            print(f"  First BE uint32: {first_be32}")
            print(f"  Remaining BE uint32 count: {n32 - 1}")

            # Check if first value equals FFFF count
            if first_be32 == ffff_count:
                print(f"  *** MATCH: first BE uint32 ({first_be32}) == FFFF count ({ffff_count})")

            # Check if remaining values are monotonically increasing
            remaining = be32[1:]
            is_mono = all(remaining[i] <= remaining[i+1] for i in range(len(remaining)-1)) if len(remaining) > 1 else True
            print(f"  Remaining values monotonic: {is_mono}")
            if len(remaining) > 0:
                print(f"  Range: {remaining[0]} to {remaining[-1]}")

                # Check if these are byte offsets into glyph stream
                # If so, remaining[-1] should be near (file_size - glyph_start)
                glyph_region_size = len(data) - glyph_start
                print(f"  Glyph region size: {glyph_region_size}")
                if remaining[-1] > 0:
                    print(f"  Last offset vs glyph_region: {remaining[-1]} vs {glyph_region_size}")

                # Are the values word offsets (multiply by 2 to get byte offset)?
                if remaining[-1] * 2 <= glyph_region_size + 10:
                    print(f"  Could be word offsets (last*2 = {remaining[-1]*2})")
                elif remaining[-1] <= glyph_region_size + 10:
                    print(f"  Could be byte offsets (last = {remaining[-1]})")

                # Verify: at glyph_start + offset, do we find FFFF?
                verified = 0
                for off_val in remaining[:10]:
                    check_pos = glyph_start + off_val
                    if check_pos + 2 <= len(data):
                        word = struct.unpack(">H", data[check_pos:check_pos+2])[0]
                        if word == 0xFFFF:
                            verified += 1
                        else:
                            pass
                    # Also try word offset
                    check_pos2 = glyph_start + off_val * 2
                    if check_pos2 + 2 <= len(data):
                        word2 = struct.unpack(">H", data[check_pos2:check_pos2+2])[0]
                        if word2 == 0xFFFF:
                            verified += 100  # distinguish
                print(f"  Offset verification (byte): {verified % 100}/10, (word): {verified // 100}/10")
    else:
        # Non-table resource
        print(f"  Non-table resource, header as BE uint32:")
        n32 = min(glyph_start // 4, 20)
        if n32 > 0:
            be32 = list(struct.unpack(f">{n32}I", data[:n32*4]))
            print(f"  {be32[:20]}")

            first_be32 = be32[0]
            print(f"  First BE uint32: {first_be32}")
            if first_be32 == ffff_count:
                print(f"  *** MATCH: first BE uint32 ({first_be32}) == FFFF count ({ffff_count})")

            remaining = be32[1:]
            is_mono = all(remaining[i] <= remaining[i+1] for i in range(len(remaining)-1)) if len(remaining) > 1 else True
            print(f"  Remaining monotonic: {is_mono}")
            if remaining:
                print(f"  Range: {remaining[0]} to {remaining[-1]}")
                glyph_region_size = len(data) - glyph_start
                print(f"  Glyph region size: {glyph_region_size}")
    print()

# Now let me check: for non-table resources (type 36,37,38), the first uint32 read as LE is large
# But as BE uint16, resource 36 starts with 0x009E = 158. Could that be message count?
# And resource 36 has FFFF count... let me check
print("=== NON-TABLE RESOURCE FFFF VERIFICATION ===")
for idx in [36, 37, 38, 40, 41, 42, 43, 44, 45, 48, 49]:
    data = read_resource(idx)
    if data is None:
        continue
    glyph_start = scan_for_ffff_fffe(data)
    ffff_count = 0
    for off in range(glyph_start, len(data) - 1, 2):
        val = struct.unpack(">H", data[off:off+2])[0]
        if val == 0xFFFF:
            ffff_count += 1

    # Read first BE uint32
    first_be32 = struct.unpack(">I", data[0:4])[0]
    # Read first BE uint16
    first_be16 = struct.unpack(">H", data[0:2])[0]
    # Read first LE uint16
    first_le16 = struct.unpack("<H", data[0:2])[0]

    print(f"Resource {idx}: ffff={ffff_count}, first_be32={first_be32}, first_be16={first_be16}, first_le16={first_le16}, glyph_start={glyph_start}, size={len(data)}")

    if first_be16 == ffff_count:
        print(f"  *** first BE uint16 matches FFFF count!")
    if first_le16 == ffff_count:
        print(f"  *** first LE uint16 matches FFFF count!")
    if first_be32 == ffff_count:
        print(f"  *** first BE uint32 matches FFFF count!")

    # For non-table: the header IS the entire region before glyph_start
    # It likely contains: [msg_count] [offset_table...]
    # Read header as BE uint32
    n32 = glyph_start // 4
    if 0 < n32 <= 200:
        hdr = list(struct.unpack(f">{n32}I", data[:n32*4]))
        # Check if hdr[0] == number of remaining entries
        if hdr[0] == n32 - 1:
            print(f"  Header[0] = {hdr[0]} matches remaining count {n32-1}")
        # Check remaining monotonic
        remaining = hdr[1:]
        is_mono = all(remaining[i] <= remaining[i+1] for i in range(len(remaining)-1)) if len(remaining) > 1 else True
        print(f"  Remaining ({len(remaining)} values) monotonic: {is_mono}")
        if remaining:
            print(f"  Range: {remaining[0]} to {remaining[-1]}")
            # Verify as byte offsets from glyph_start
            verified = 0
            for off_val in remaining[:10]:
                check_pos = glyph_start + off_val
                if check_pos + 2 <= len(data):
                    word = struct.unpack(">H", data[check_pos:check_pos+2])[0]
                    if word == 0xFFFF:
                        verified += 1
            print(f"  Byte offset verification: {verified}/10")

print()
print("=== FINAL SUMMARY ===")
# Now parse everything properly
results = []
header_sizes = {}
msg_count_match = 0
offset_verified = 0

for idx in msg_indices:
    data = read_resource(idx)
    if data is None:
        results.append({"index": idx, "error": "not found"})
        continue

    first4_le = struct.unpack("<I", data[0:4])[0]
    n_table = count_sequential_table(data)
    table_end = n_table * 16
    glyph_start = scan_for_ffff_fffe(data)

    # Count messages
    ffff_count = 0
    fffe_count = 0
    for off in range(glyph_start, len(data) - 1, 2):
        val = struct.unpack(">H", data[off:off+2])[0]
        if val == 0xFFFF:
            ffff_count += 1
        elif val == 0xFFFE:
            fffe_count += 1

    # Determine header type and parse
    if n_table > 0:
        header_type = "sequential_table"
        # Between region as BE uint32
        between = data[table_end:glyph_start]
        n32 = len(between) // 4
        offset_table = []
        msg_count_from_header = 0
        if n32 > 0:
            be32 = list(struct.unpack(f">{n32}I", between[:n32*4]))
            msg_count_from_header = be32[0]
            offset_table = be32[1:]

        if msg_count_from_header == ffff_count:
            msg_count_match += 1

        # Table entries
        table_data = []
        for e in range(n_table):
            off = e * 16
            entry = list(struct.unpack("<4I", data[off:off+16]))
            table_data.append(entry)

        entry_result = {
            "index": idx,
            "file_size": len(data),
            "header_type": "sequential_table",
            "table_entries": n_table,
            "table_end_offset": table_end,
            "glyph_start_offset": glyph_start,
            "header_size": glyph_start,
            "message_count": ffff_count,
            "fffe_count": fffe_count,
            "msg_count_from_header": msg_count_from_header,
            "msg_count_matches": msg_count_from_header == ffff_count,
            "offset_table_size": len(offset_table)
        }
        if n_table <= 64:
            entry_result["table_data"] = table_data
    else:
        header_type = "offset_table"
        # Read entire header as BE uint32
        n32 = glyph_start // 4
        if 0 < n32 <= 256:
            hdr = list(struct.unpack(f">{n32}I", data[:n32*4]))
            msg_count_from_header = hdr[0] if hdr else 0
            offset_table = hdr[1:] if len(hdr) > 1 else []
        else:
            msg_count_from_header = 0
            offset_table = []

        if msg_count_from_header == ffff_count:
            msg_count_match += 1

        entry_result = {
            "index": idx,
            "file_size": len(data),
            "header_type": "offset_table",
            "glyph_start_offset": glyph_start,
            "header_size": glyph_start,
            "message_count": ffff_count,
            "fffe_count": fffe_count,
            "msg_count_from_header": msg_count_from_header,
            "msg_count_matches": msg_count_from_header == ffff_count,
            "offset_table_size": len(offset_table)
        }
        if len(offset_table) <= 32:
            entry_result["header_fields_be32"] = [msg_count_from_header] + offset_table

    header_sizes[glyph_start] = header_sizes.get(glyph_start, 0) + 1
    results.append(entry_result)

print(f"Total parsed: {len(results)}")
print(f"Message count from header matches FFFF count: {msg_count_match}/{len(results)}")

# Print mismatches
mismatches = [r for r in results if not r.get("msg_count_matches", False) and "error" not in r]
print(f"\nMismatches ({len(mismatches)}):")
for r in mismatches[:20]:
    print(f"  Resource {r['index']}: header_msg={r['msg_count_from_header']}, ffff={r['message_count']}, type={r['header_type']}")

# Save
output_data = {
    "summary": {
        "total_parsed": len(results),
        "msg_count_matches_ffff": msg_count_match,
        "header_size_distribution": {str(k): v for k, v in sorted(header_sizes.items())},
    },
    "resources": results
}

with open(OUTPUT, "w") as f:
    json.dump(output_data, f, indent=2)
print(f"\nSaved to {OUTPUT}")
"@

Set-Content -Path "C:/Programmieren/wizardrytranslation/tools/parse_msg_header.py" -Value $code -Encoding UTF8
Write-Host "File written successfully"
