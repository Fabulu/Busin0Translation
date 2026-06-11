"""
inject_r39_quest.py - Inject English quest UI labels and quest titles into R39 (type-15).

This script handles the quest data block in R39 starting at byte 20420:
  G411  (20420): Offset table for quest UI labels -> points into G412-G441
  G412  (20556): [separator]
  G413-G441:     Quest UI labels (Accept/Abandon/Yes/No/Client/Reward etc.)
  G442  (21052): Offset table for quest titles -> points into G443-G476+
  G443  (21196): [separator]
  G444-G476:     Individual quest titles

Both G411 and G442 are offset tables with (value, 0) pairs where `value` is a
uint16 byte offset from the byte immediately after the respective table's FFFF.

Strategy:
1. Keep G411 SAME SIZE (67 glyph slots = 134 bytes + 2 FFFF).
2. Keep G442 SAME SIZE (71 glyph slots = 142 bytes + 2 FFFF).
3. Rebuild G412-G441 (UI labels) with English text.
4. Rebuild G443-G476 (quest titles) with English text.
5. Rebuild G411 offset values to match new byte positions of each semantic target.
6. Rebuild G442 offset values to match new byte positions of each semantic target.
7. Update all groups AFTER G476 accordingly (they stay the same content, just shift position).

Output: build/packdata_resources/0039_type15.raw (same format, potentially different size)
The file size must stay within sector boundaries (26624 = 13 sectors; up to 28672 = 14 sectors).
"""

import struct, json, os, sys, math

BASE = 'C:/Programmieren/wizardrytranslation'
os.chdir(BASE)
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

SECTOR = 2048

# ---------------------------------------------------------------------------
# 1. Load the already-patched R39 from the previous build step
#    (inject_r39_v2.py must have run first to produce this file)
# ---------------------------------------------------------------------------
patched_path = 'build/packdata_resources/0039_type15.raw'
orig_path = 'extracted/packdata_raw/0039_type15.raw'

if os.path.exists(patched_path):
    raw = bytearray(open(patched_path, 'rb').read())
    # Trim to original size if it was padded by inject_r39_v2.py
    # inject_r39_v2.py produces exactly 26624 bytes (same as original)
    if len(raw) > 26624:
        raw = raw[:26624]
    print(f"R39 from previous step: {len(raw)} bytes (from {patched_path})")
else:
    raw = bytearray(open(orig_path, 'rb').read())
    print(f"R39 from original: {len(raw)} bytes (inject_r39_v2.py not yet run)")

assert len(raw) == 26624, f"Unexpected R39 size: {len(raw)}"

# ---------------------------------------------------------------------------
# 2. Load translations
# ---------------------------------------------------------------------------
trans_b = json.load(open('data/type2_translated/batch_r39_equip_b.json', encoding='utf-8'))
trans_dict = {e['msg_index']: e for e in trans_b if e.get('english', '').strip()}
print(f"Loaded {len(trans_dict)} translations from batch_r39_equip_b.json")

# ---------------------------------------------------------------------------
# 3. Load glyph table
# ---------------------------------------------------------------------------
glyph_table = json.load(open('data/english_glyph_table.json', encoding='utf-8'))

def encode_english(text):
    """Encode English text to glyph list. Newlines and ' / ' become FFFE."""
    text = text.replace(' / ', '\n')
    parts = text.split('\n')
    glyphs = []
    for pi, part in enumerate(parts):
        if pi > 0:
            glyphs.append(0xFFFE)
        for ch in part.strip() if pi > 0 else part:
            g = glyph_table.get(ch)
            if g is not None:
                glyphs.append(int(g))
            elif ch == ' ':
                glyphs.append(0)
            else:
                glyphs.append(31)  # '?' fallback
    return glyphs

# ---------------------------------------------------------------------------
# 4. Scan ALL FFFF groups from byte 632
# ---------------------------------------------------------------------------
pos = 632
groups = []      # groups[i] = list of glyph values (FFFF excluded)
group_starts = []  # byte position where group i's first glyph is (right after prev FFFF)
cur_group = []
cur_start = pos
while pos + 1 < len(raw):
    w = struct.unpack_from('>H', raw, pos)[0]
    if w == 0xFFFF:
        groups.append(list(cur_group))
        group_starts.append(cur_start)
        cur_group = []
        cur_start = pos + 2
    else:
        cur_group.append(w)
    pos += 2

print(f"Total FFFF groups in stream: {len(groups)}")

# Verify key positions
assert group_starts[411] == 20420, f"G411 expected at 20420, got {group_starts[411]}"
assert len(groups[411]) == 67, f"G411 expected 67 glyphs, got {len(groups[411])}"
assert group_starts[442] == 21052, f"G442 expected at 21052, got {group_starts[442]}"
assert len(groups[442]) == 71, f"G442 expected 71 glyphs, got {len(groups[442])}"
assert group_starts[412] == 20556, f"G412 expected at 20556, got {group_starts[412]}"
assert group_starts[443] == 21196, f"G443 expected at 21196, got {group_starts[443]}"

base_411 = 20556  # byte after G411 FFFF
base_442 = 21196  # byte after G442 FFFF

print("Structure assertions passed.")

# ---------------------------------------------------------------------------
# 5. Build semantic maps for G411 and G442 offset tables
# ---------------------------------------------------------------------------

def build_offset_semantics(table_raw_values, base, groups, group_starts):
    """
    For each non-zero value in table_raw_values, find which group+glyph_idx it points to.
    Returns list of (slot_index, orig_offset, group_idx, glyph_idx).
    """
    semantics = []
    for slot_i, v in enumerate(table_raw_values):
        if v != 0 and v != 0xFFFF and v != 0xFFFE:
            target = base + v
            found = False
            for gi, gs in enumerate(group_starts):
                ge = gs + len(groups[gi]) * 2 + 2
                if gs <= target < ge:
                    glyph_idx = (target - gs) // 2
                    semantics.append((slot_i, v, gi, glyph_idx))
                    found = True
                    break
            if not found:
                print(f"  WARNING: offset {v} -> target {target} not found in any group")
                semantics.append((slot_i, v, -1, 0))
    return semantics

# G411 raw values (67 uint16)
g411_raw = [struct.unpack_from('>H', raw, 20420 + i*2)[0] for i in range(67)]
g411_semantics = build_offset_semantics(g411_raw, base_411, groups, group_starts)
print(f"G411: {len(g411_semantics)} non-zero offset entries")

# G442 raw values (71 uint16)
g442_raw = [struct.unpack_from('>H', raw, 21052 + i*2)[0] for i in range(71)]
g442_semantics = build_offset_semantics(g442_raw, base_442, groups, group_starts)
print(f"G442: {len(g442_semantics)} non-zero offset entries")

# ---------------------------------------------------------------------------
# 6. Build new group content for G412-G476
# ---------------------------------------------------------------------------

# Groups to translate (replace Japanese with English):
# G412-G441: quest UI labels (msg_index = group_idx)
# G443-G476: quest titles
# G411 (67 slots) and G442 (71 slots): offset tables, handled separately

TRANSLATE_GROUPS = set(range(412, 477))  # G412-G476 inclusive
TRANSLATE_GROUPS.discard(442)  # G442 is an offset table, not plain text

new_groups = {i: list(groups[i]) for i in range(len(groups))}  # copy all

translated = 0
kept_original = 0

for gi in sorted(TRANSLATE_GROUPS):
    msg_idx = gi
    entry = trans_dict.get(msg_idx)
    if entry and entry.get('english', '').strip():
        en = entry['english'].strip()
        en_glyphs = encode_english(en)
        # Add FFFE at end to match Japanese pattern (groups end with FFFE before FFFF)
        if en_glyphs and en_glyphs[-1] != 0xFFFE:
            en_glyphs.append(0xFFFE)
        new_groups[gi] = en_glyphs
        translated += 1
    else:
        kept_original += 1

print(f"Translated: {translated} groups, kept original: {kept_original} groups")

# ---------------------------------------------------------------------------
# 7. Compute new byte positions for all groups from G411 onwards
# ---------------------------------------------------------------------------

def group_byte_size(gi):
    """Total bytes for group gi including FFFF: len(glyphs)*2 + 2."""
    return len(new_groups[gi]) * 2 + 2

# G411 starts at 20420 (unchanged)
original_prefix_end = 20420
new_group_starts = {i: group_starts[i] for i in range(411)}  # unchanged groups

current_pos = original_prefix_end
for gi in range(411, len(groups)):
    new_group_starts[gi] = current_pos
    current_pos += group_byte_size(gi)

new_file_len = current_pos

old_total = len(raw)
print(f"Old end: {old_total} bytes, New end: {new_file_len} bytes (delta: {new_file_len - old_total:+d})")

# ---------------------------------------------------------------------------
# 8. Compute new G411 offset values
# ---------------------------------------------------------------------------

# G411 stays at 20420, has 67 glyphs (unchanged size), so base_411 stays 20556
new_base_411 = new_group_starts[411] + group_byte_size(411)
assert new_base_411 == base_411, f"G411 base changed: {new_base_411} vs {base_411}"

new_g411 = list(g411_raw)  # copy
changes_411 = 0
for slot_i, orig_v, gi, glyph_idx in g411_semantics:
    if gi < 0:
        continue
    new_gs = new_group_starts[gi]
    new_target = new_gs + glyph_idx * 2
    new_offset = new_target - new_base_411
    if new_offset < 0:
        print(f"  WARNING: G411 slot[{slot_i}]: negative offset {new_offset}")
        new_offset = 0
    elif new_offset > 65534:
        print(f"  WARNING: G411 slot[{slot_i}]: offset overflow {new_offset}")
        new_offset = 65534
    if g411_raw[slot_i] != new_offset:
        changes_411 += 1
    new_g411[slot_i] = new_offset

new_groups[411] = new_g411
print(f"G411: {changes_411} offset values updated")

# ---------------------------------------------------------------------------
# 9. Compute new G442 offset values
# ---------------------------------------------------------------------------

new_base_442 = new_group_starts[442] + group_byte_size(442)
print(f"G442 base: old={base_442}, new={new_base_442} (delta={new_base_442 - base_442:+d})")

new_g442 = list(g442_raw)  # copy
changes_442 = 0
for slot_i, orig_v, gi, glyph_idx in g442_semantics:
    if gi < 0:
        continue
    new_gs = new_group_starts[gi]
    new_target = new_gs + glyph_idx * 2
    new_offset = new_target - new_base_442
    if new_offset < 0:
        print(f"  WARNING: G442 slot[{slot_i}]: negative offset {new_offset}")
        new_offset = 0
    elif new_offset > 65534:
        print(f"  WARNING: G442 slot[{slot_i}]: offset overflow {new_offset}")
        new_offset = 65534
    if g442_raw[slot_i] != new_offset:
        changes_442 += 1
    new_g442[slot_i] = new_offset

new_groups[442] = new_g442
print(f"G442: {changes_442} offset values updated")

# ---------------------------------------------------------------------------
# 10. Rebuild the binary
# ---------------------------------------------------------------------------

out = bytearray()

# Prefix: bytes 0 to 20420 (unchanged)
out += raw[:original_prefix_end]

# Groups G411 onwards (rebuilt with new content and/or updated offsets)
for gi in range(411, len(groups)):
    glyph_data = new_groups[gi]
    for g in glyph_data:
        out += struct.pack('>H', g)
    out += struct.pack('>H', 0xFFFF)

assert len(out) == new_file_len, f"Size mismatch: {len(out)} vs {new_file_len}"

# Pad to sector boundary
sectors = math.ceil(len(out) / SECTOR)
padded_size = sectors * SECTOR
out += b'\x00' * (padded_size - len(out))

print()
print(f"Output: {len(out)} bytes ({sectors} sectors)")
if sectors > 14:
    print("  ERROR: Exceeds 14-sector limit! File too large.")
    sys.exit(1)
elif sectors > 13:
    print("  WARNING: Grew from 13 to 14 sectors -- PACKDATA TOC must be updated if building.")

# Write output
os.makedirs('build/packdata_resources', exist_ok=True)
out_path = 'build/packdata_resources/0039_type15.raw'
with open(out_path, 'wb') as f:
    f.write(out)
print(f"Written to {out_path}")

# ---------------------------------------------------------------------------
# 11. Verification: re-scan and check quest label groups
# ---------------------------------------------------------------------------
print()
print("=== Verification: quest label groups ===")
glyph_map_data = json.load(open('data/glyph_map_partial.json', encoding='utf-8'))

def decode_glyphs(glyphs):
    result = ''
    for g in glyphs:
        if g == 0xFFFE: result += '[LB]'
        elif g == 0xFFFF: result += '[END]'
        elif 0 <= g < 95: result += chr(0x20 + g)
        else: result += glyph_map_data.get(str(g), f'[{g:04X}]')
    return result

# Re-scan the output file
pos2 = 632
new_groups_scan = []
new_starts_scan = []
cur_g2 = []
cur_s2 = pos2
check_data = bytearray(out)
while pos2 + 1 < len(check_data):
    w = struct.unpack_from('>H', check_data, pos2)[0]
    if w == 0xFFFF:
        new_groups_scan.append(list(cur_g2))
        new_starts_scan.append(cur_s2)
        cur_g2 = []
        cur_s2 = pos2 + 2
    else:
        cur_g2.append(w)
    pos2 += 2

print(f"Re-scanned groups: {len(new_groups_scan)}")
print()

# Check key groups
check_indices = [413, 414, 415, 416, 417, 418, 419, 420, 421, 422, 424, 425, 426,
                 427, 428, 429, 430, 431, 432, 433, 436, 437, 438, 441,
                 444, 445, 446, 449, 450, 456, 460, 476]
for idx in check_indices:
    if idx < len(new_groups_scan):
        dec = decode_glyphs(new_groups_scan[idx])
        exp_en = trans_dict.get(idx, {}).get('english', '(no translation)')
        print(f"  G{idx}: '{dec}' | expected: '{exp_en}'")

print()
print("Done.")
