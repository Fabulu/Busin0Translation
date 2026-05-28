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

# Key insight: non-table resources have BE uint16 headers
# first_be16 = FFFF_count - 1 for non-table resources
# The header is a table of BE uint16 pairs: [count, 0, offset1, 0, offset2, 0, ...]

print("=== OFFSET TABLE VERIFICATION ===")
# For non-table resources, read the header as BE uint16 pairs
# The first pair is (msg_count, 0)
# Following pairs are (offset, 0) where offset is a byte offset from glyph_start
# to each FFFF separator

for idx in [36, 37, 38, 40, 41, 42]:
    data = read_resource(idx)
    if data is None:
        continue
    glyph_start = scan_for_ffff_fffe(data)

    # Read header as BE uint16
    n16 = glyph_start // 2
    be16 = list(struct.unpack(f">{n16}H", data[:n16*2]))

    # First value should be msg_count - 1
    msg_count_hdr = be16[0]

    # Check pattern: [count, 0, offset1, 0, offset2, 0, ...]
    # or: [count, offset1, offset2, ...] without zero padding?
    # From the raw hex of res 36: 009e0000027c0000028200000296...
    # That's: 0x009E, 0x0000, 0x027C, 0x0000, 0x0282, 0x0000, ...
    # So yes, alternating value and zero. But wait - the zeros might not be padding.
    # Let me check: maybe these are BE uint32 but the values happen to fit in 16 bits?

    print(f"\nResource {idx}: glyph_start={glyph_start}, header as BE uint16:")
    print(f"  First 30 values: {be16[:30]}")

    # Check: non-zero values only
    nz = [v for v in be16 if v > 0]
    print(f"  Non-zero values: count={len(nz)}, first={nz[0] if nz else 'N/A'}")

    # Check if the values at odd indices are all zero
    even_vals = be16[0::2]  # index 0, 2, 4, ...
    odd_vals = be16[1::2]   # index 1, 3, 5, ...
    all_odd_zero = all(v == 0 for v in odd_vals)
    print(f"  All odd-indexed values zero: {all_odd_zero}")

    if all_odd_zero:
        # The even values are: [count, offset1, offset2, ...]
        offsets = even_vals[1:]
        print(f"  Count from header: {even_vals[0]}")
        print(f"  Number of offsets: {len(offsets)}")

        # Count FFFF in glyph stream
        ffff_positions = []
        for off in range(glyph_start, len(data) - 1, 2):
            val = struct.unpack(">H", data[off:off+2])[0]
            if val == 0xFFFF:
                ffff_positions.append(off)
        print(f"  Actual FFFF count: {len(ffff_positions)}")
        print(f"  Header count vs FFFF: {even_vals[0]} vs {len(ffff_positions)}")

        # Try: offsets are byte offsets from start of file? Or from glyph_start?
        # Or word offsets from glyph_start?

        # Verify as byte offsets from glyph_start
        match_byte = 0
        for i, off_val in enumerate(offsets[:10]):
            check = glyph_start + off_val
            if check + 2 <= len(data):
                w = struct.unpack(">H", data[check:check+2])[0]
                if w == 0xFFFF:
                    match_byte += 1

        # Verify as word offsets from glyph_start
        match_word = 0
        for i, off_val in enumerate(offsets[:10]):
            check = glyph_start + off_val * 2
            if check + 2 <= len(data):
                w = struct.unpack(">H", data[check:check+2])[0]
                if w == 0xFFFF:
                    match_word += 1

        # Verify as absolute byte offsets
        match_abs = 0
        for i, off_val in enumerate(offsets[:10]):
            if off_val + 2 <= len(data):
                w = struct.unpack(">H", data[off_val:off_val+2])[0]
                if w == 0xFFFF:
                    match_abs += 1

        # Verify as absolute word offsets
        match_abs_word = 0
        for i, off_val in enumerate(offsets[:10]):
            check = off_val * 2
            if check + 2 <= len(data):
                w = struct.unpack(">H", data[check:check+2])[0]
                if w == 0xFFFF:
                    match_abs_word += 1

        print(f"  Offset verification: byte_from_gs={match_byte}/10, word_from_gs={match_word}/10, abs_byte={match_abs}/10, abs_word={match_abs_word}/10")

        # Hmm, none matching. Let me check what's AT those offset positions
        print(f"  First 5 offset values: {offsets[:5]}")
        for off_val in offsets[:5]:
            # Check what's at glyph_start + offset
            for base_name, base in [("from_gs_byte", glyph_start + off_val),
                                     ("from_gs_word", glyph_start + off_val * 2),
                                     ("abs_byte", off_val),
                                     ("abs_word", off_val * 2)]:
                if 0 <= base < len(data) - 2:
                    w = struct.unpack(">H", data[base:base+2])[0]
                    if w == 0xFFFF or w == 0xFFFE:
                        print(f"    offset {off_val}: {base_name}={base} -> 0x{w:04X} MATCH!")

# Maybe the between region for sequential-table resources should also be read as BE uint16
print("\n=== SEQUENTIAL TABLE: Between region as BE uint16 ===")
for idx in [34, 35, 46]:
    data = read_resource(idx)
    n_table = count_sequential_table(data)
    table_end = n_table * 16
    glyph_start = scan_for_ffff_fffe(data)
    between = data[table_end:glyph_start]

    n16 = len(between) // 2
    be16 = list(struct.unpack(f">{n16}H", between[:n16*2]))

    even_vals = be16[0::2]
    odd_vals = be16[1::2]
    all_odd_zero = all(v == 0 for v in odd_vals)

    ffff_count = sum(1 for off in range(glyph_start, len(data) - 1, 2)
                     if struct.unpack(">H", data[off:off+2])[0] == 0xFFFF)

    print(f"\nResource {idx}: table_entries={n_table}, between={len(between)} bytes")
    print(f"  BE uint16 even values (first 20): {even_vals[:20]}")
    print(f"  All odd zero: {all_odd_zero}")
    print(f"  First even value: {even_vals[0] if even_vals else 'N/A'}")
    print(f"  FFFF count: {ffff_count}")
    print(f"  Number of offsets (even values - 1): {len(even_vals) - 1}")

    if all_odd_zero and even_vals:
        offsets = even_vals[1:]
        # Try all offset interpretations
        ffff_positions = []
        for off in range(glyph_start, len(data) - 1, 2):
            val = struct.unpack(">H", data[off:off+2])[0]
            if val == 0xFFFF:
                ffff_positions.append(off - glyph_start)

        print(f"  FFFF byte positions (from gs): {ffff_positions[:20]}")
        print(f"  FFFF word positions (from gs): {[p//2 for p in ffff_positions[:20]]}")
        print(f"  Header offsets: {offsets[:20]}")

        # Direct comparison
        ffff_word_pos = [p // 2 for p in ffff_positions]
        match = sum(1 for a, b in zip(offsets, ffff_word_pos) if a == b)
        print(f"  Match as word offsets: {match}/{min(len(offsets), len(ffff_word_pos))}")

        ffff_byte_pos = ffff_positions
        match = sum(1 for a, b in zip(offsets, ffff_byte_pos) if a == b)
        print(f"  Match as byte offsets: {match}/{min(len(offsets), len(ffff_byte_pos))}")

print("\n=== DONE ===")
"@

Set-Content -Path "C:/Programmieren/wizardrytranslation/tools/parse_msg_header.py" -Value $code -Encoding UTF8
Write-Host "File written successfully"
