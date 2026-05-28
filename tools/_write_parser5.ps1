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

# HYPOTHESIS: offsets are absolute byte positions of each FFFF separator
# For non-table resources, the first offset should point to the SECOND FFFF
# (the first FFFF is at glyph_start, implicit)

print("=== ABSOLUTE OFFSET VERIFICATION ===")
for idx in [36, 37, 38, 40, 41, 42, 43, 44, 45, 48, 49]:
    data = read_resource(idx)
    if data is None:
        continue
    glyph_start = scan_for_ffff_fffe(data)

    # Read header as BE uint16, take even-indexed (non-zero) values
    n16 = glyph_start // 2
    be16 = list(struct.unpack(f">{n16}H", data[:n16*2]))
    even_vals = be16[0::2]

    msg_count = even_vals[0]
    offsets = even_vals[1:]

    # Get all FFFF positions (absolute)
    ffff_pos = []
    for off in range(glyph_start, len(data) - 1, 2):
        val = struct.unpack(">H", data[off:off+2])[0]
        if val == 0xFFFF:
            ffff_pos.append(off)

    # Check if offsets match FFFF absolute positions (skipping first FFFF)
    ffff_after_first = ffff_pos[1:] if len(ffff_pos) > 1 else []
    match = sum(1 for a, b in zip(offsets, ffff_after_first) if a == b)
    total = min(len(offsets), len(ffff_after_first))

    # Also try: offsets point to the byte AFTER each FFFF (the message start)
    ffff_plus2 = [p + 2 for p in ffff_pos]
    match2 = sum(1 for a, b in zip(offsets, ffff_plus2) if a == b)

    # Also try: offsets point to first byte of each message (after initial FFFF 0000 FFFE)
    # Look at actual data at each offset
    what_at_offset = []
    for off_val in offsets[:5]:
        if off_val + 2 <= len(data):
            w = struct.unpack(">H", data[off_val:off_val+2])[0]
            what_at_offset.append(f"0x{w:04X}")
        else:
            what_at_offset.append("OOB")

    print(f"Res {idx}: count={msg_count}, #offsets={len(offsets)}, #FFFF={len(ffff_pos)}")
    print(f"  First FFFF pos: {ffff_pos[0] if ffff_pos else 'N/A'} (glyph_start={glyph_start})")
    print(f"  First 5 offsets: {offsets[:5]}")
    print(f"  First 5 FFFF after first: {ffff_after_first[:5]}")
    print(f"  First 5 FFFF+2: {ffff_plus2[:5]}")
    print(f"  Match vs FFFF[1:]: {match}/{total}")
    print(f"  Match vs FFFF+2: {match2}/{min(len(offsets), len(ffff_plus2))}")
    print(f"  Values at offsets: {what_at_offset}")

# Key observation: for res 36, offsets start at 636, first FFFF is at 634.
# 636 = 634 + 2 = position right AFTER first FFFF
# Next offset 642 = 640 + 2? Let me check...

print("\n=== DETAILED GLYPH STREAM FOR RESOURCE 36 ===")
data = read_resource(36)
glyph_start = scan_for_ffff_fffe(data)
# Show every word from glyph_start to glyph_start + 60
for off in range(glyph_start, min(glyph_start + 80, len(data)), 2):
    w = struct.unpack(">H", data[off:off+2])[0]
    marker = ""
    if w == 0xFFFF:
        marker = " <-- FFFF"
    elif w == 0xFFFE:
        marker = " <-- FFFE"
    print(f"  byte {off}: 0x{w:04X}{marker}")

# Check: maybe each FFFF is followed by a 0x0000, then FFFE, then actual glyphs
# And the offsets point to the start of glyph data within each message

print("\n=== CHECK FFFE POSITIONS ===")
for idx in [36, 37]:
    data = read_resource(idx)
    glyph_start = scan_for_ffff_fffe(data)
    n16 = glyph_start // 2
    be16 = list(struct.unpack(f">{n16}H", data[:n16*2]))
    even_vals = be16[0::2]
    offsets = even_vals[1:]

    # Get FFFE positions
    fffe_pos = []
    for off in range(glyph_start, len(data) - 1, 2):
        val = struct.unpack(">H", data[off:off+2])[0]
        if val == 0xFFFE:
            fffe_pos.append(off)

    # Get FFFF positions
    ffff_pos = []
    for off in range(glyph_start, len(data) - 1, 2):
        val = struct.unpack(">H", data[off:off+2])[0]
        if val == 0xFFFF:
            ffff_pos.append(off)

    # Maybe offsets point to the FFFE positions?
    match_fffe = sum(1 for a, b in zip(offsets, fffe_pos) if a == b)
    # Or FFFE+2?
    fffe_plus2 = [p + 2 for p in fffe_pos]
    match_fffe2 = sum(1 for a, b in zip(offsets, fffe_plus2) if a == b)

    print(f"\nRes {idx}: #offsets={len(offsets)}, #FFFE={len(fffe_pos)}, #FFFF={len(ffff_pos)}")
    print(f"  First 5 offsets: {offsets[:5]}")
    print(f"  First 5 FFFE: {fffe_pos[:5]}")
    print(f"  Match FFFE: {match_fffe}")
    print(f"  Match FFFE+2: {match_fffe2}")

    # Try: each message starts with FFFF, then some data, then FFFE terminates
    # The offset table might list positions within a virtual address space
    # or they could be absolute positions pointing to message data start

    # Let me look at what's right at each offset
    print(f"  Checking offset contents:")
    for off_val in offsets[:10]:
        if off_val + 6 <= len(data):
            words = struct.unpack(">3H", data[off_val:off_val+6])
            print(f"    offset {off_val}: {[f'0x{w:04X}' for w in words]}")

print("\n=== SEQUENTIAL TABLE: Full offset check ===")
# For sequential-table resources, between region starts with count (BE uint16 even)
# The offsets should be similar
for idx in [34, 35, 46]:
    data = read_resource(idx)
    n_table = count_sequential_table(data)
    table_end = n_table * 16
    glyph_start = scan_for_ffff_fffe(data)
    between = data[table_end:glyph_start]

    n16 = len(between) // 2
    be16 = list(struct.unpack(f">{n16}H", between[:n16*2]))
    even_vals = be16[0::2]

    msg_count = even_vals[0]
    offsets = even_vals[1:]

    # Get FFFF positions
    ffff_pos = []
    for off in range(glyph_start, len(data) - 1, 2):
        val = struct.unpack(">H", data[off:off+2])[0]
        if val == 0xFFFF:
            ffff_pos.append(off)

    # Try offsets as absolute
    match_abs = sum(1 for a, b in zip(offsets, ffff_pos[1:]) if a == b)
    match_abs_all = sum(1 for a, b in zip(offsets, ffff_pos) if a == b)

    print(f"\nRes {idx}: table={n_table}, count={msg_count}, #offsets={len(offsets)}, #FFFF={len(ffff_pos)}")
    print(f"  First 10 offsets: {offsets[:10]}")
    print(f"  First 10 FFFF pos: {ffff_pos[:10]}")
    print(f"  Match abs FFFF[1:]: {match_abs}")
    print(f"  Match abs FFFF[0:]: {match_abs_all}")

    # Check what's at each offset
    print(f"  Checking offset contents:")
    for off_val in offsets[:5]:
        if off_val + 6 <= len(data):
            words = struct.unpack(">3H", data[off_val:off_val+6])
            print(f"    offset {off_val}: {[f'0x{w:04X}' for w in words]}")
        elif off_val + 2 <= len(data):
            w = struct.unpack(">H", data[off_val:off_val+2])[0]
            print(f"    offset {off_val}: 0x{w:04X}")
        else:
            print(f"    offset {off_val}: OUT OF BOUNDS (file_size={len(data)})")

print("\n=== DONE ===")
"@

Set-Content -Path "C:/Programmieren/wizardrytranslation/tools/parse_msg_header.py" -Value $code -Encoding UTF8
Write-Host "File written successfully"
