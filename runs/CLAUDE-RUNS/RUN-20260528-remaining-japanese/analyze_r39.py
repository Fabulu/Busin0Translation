#!/usr/bin/env python3
"""Comprehensive R39 analysis for recon report.

Key discovery: Offset table values are relative to the offset table start
(byte 240), NOT to payload start (byte 16). The glyph stream extends
BEYOND the declared payload_size into the "extra data" region.
"""
import struct, json, sys, os
sys.stdout.reconfigure(encoding='utf-8')

BASE = 'C:/Programmieren/wizardrytranslation'
raw = open(f'{BASE}/extracted/packdata_raw/0039_type15.raw', 'rb').read()
glyph_map = json.load(open(f'{BASE}/data/msg_glyph_map.json', encoding='utf-8'))
eng_table = json.load(open(f'{BASE}/data/english_glyph_table.json', encoding='utf-8'))

# Build reverse lookups
jp_rev = {}
for char, gid_str in glyph_map.items():
    try:
        jp_rev[int(gid_str)] = char
    except (ValueError, TypeError):
        pass

en_rev = {}
for char, gid in eng_table.items():
    en_rev[int(gid)] = char

# Parse sub-header
h0, payload_size, stride, h3 = struct.unpack_from('<IIII', raw, 0)
payload_start = 16
payload_end = 16 + payload_size

# Sequential table
seq_count = 0
first_val = struct.unpack_from('<I', raw, 16)[0]
if first_val == 1:
    for e in range(256):
        if 16 + (e+1)*16 > len(raw):
            break
        eid = struct.unpack_from('<I', raw, 16 + e * 16)[0]
        if eid == e + 1:
            seq_count = e + 1
        else:
            break

OT_START = 16 + seq_count * 16  # = 240
seq_data_end = OT_START

# Parse offset table
msg_count = struct.unpack_from('>H', raw, OT_START)[0]
ot_flags0 = struct.unpack_from('>H', raw, OT_START + 2)[0]
offsets = []      # raw offset values (OT-relative)
offset_flags = []
for i in range(msg_count):
    pos = OT_START + 4 + i * 4
    val = struct.unpack_from('>H', raw, pos)[0]
    flags = struct.unpack_from('>H', raw, pos + 2)[0]
    offsets.append(val)
    offset_flags.append(flags)
    if flags == 0xFFFF:
        break

OT_SIZE = 4 + len(offsets) * 4
STREAM_START = OT_START + OT_SIZE  # = 632

# Convert OT offsets to absolute file positions
ot_abs = [OT_START + off for off in offsets]

# Find actual glyph stream end: scan from last OT target forward for FFFF
last_ot_target = max(ot_abs)
stream_end = last_ot_target
p = last_ot_target
while p < len(raw) - 1:
    v = struct.unpack_from('>H', raw, p)[0]
    if v == 0xFFFF:
        stream_end = p + 2  # include the FFFF
        break
    p += 2

# Parse ALL FFFF groups in the extended stream range
groups = []  # list of (start, end) absolute byte positions, excluding FFFF terminator
grp_start = STREAM_START
pos = STREAM_START
while pos < stream_end:
    if pos + 2 > len(raw):
        break
    val = struct.unpack_from('>H', raw, pos)[0]
    if val == 0xFFFF:
        groups.append((grp_start, pos))
        grp_start = pos + 2
    pos += 2

# Map each OT entry to its FFFF group and offset within
ot_mapping = []  # (group_idx, offset_within_group)
for oi, abs_off in enumerate(ot_abs):
    found = False
    for gi, (gs, ge) in enumerate(groups):
        if gs <= abs_off < ge:
            ot_mapping.append((gi, abs_off - gs))
            found = True
            break
        elif abs_off == ge:
            # Points at the FFFF itself - treat as end of group
            ot_mapping.append((gi, abs_off - gs))
            found = True
            break
    if not found:
        # Maybe points to the start of a new group after FFFF
        for gi, (gs, ge) in enumerate(groups):
            if abs_off == gs:
                ot_mapping.append((gi, 0))
                found = True
                break
    if not found:
        ot_mapping.append((-1, 0))

# Helpers
def decode_glyphs(glyph_list, rev):
    decoded = ''
    for g in glyph_list:
        if g == 0xFFFE:
            decoded += ' / '
        elif g == 0xFFFD:
            decoded += '[FFFD]'
        else:
            ch = rev.get(g)
            if ch:
                decoded += ch
            else:
                decoded += f'[{g:04X}]'
    return decoded

def read_glyphs(start, end):
    glyphs = []
    p = start
    while p < end:
        if p + 2 > len(raw):
            break
        g = struct.unpack_from('>H', raw, p)[0]
        glyphs.append(g)
        p += 2
    return glyphs

def is_japanese(glyph_list):
    for g in glyph_list:
        if g in (0xFFFE, 0xFFFD, 0xFFFF):
            continue
        ch = jp_rev.get(g)
        if ch and ord(ch[0]) > 127:
            return True
        if ch is None and g > 0x005F:  # beyond ASCII range in eng_table
            return True
    return False

# Decode all groups
group_data = []
for gi, (gs, ge) in enumerate(groups):
    glyphs = read_glyphs(gs, ge)
    ot_refs = [oi for oi, (g, w) in enumerate(ot_mapping) if g == gi and w == 0]
    mid_refs = [(oi, w) for oi, (g, w) in enumerate(ot_mapping) if g == gi and w > 0]
    group_data.append({
        'idx': gi,
        'start': gs,
        'end': ge,
        'glyphs': glyphs,
        'jp_decode': decode_glyphs(glyphs, jp_rev),
        'en_decode': decode_glyphs(glyphs, en_rev),
        'is_jp': is_japanese(glyphs),
        'ot_start_refs': ot_refs,
        'ot_mid_refs': mid_refs,
        'in_extra': gs >= payload_end,
    })

# Decode logical messages (one per OT entry)
logical_msgs = []
for oi, abs_off in enumerate(ot_abs):
    # Read from abs_off until next FFFF
    glyphs = []
    p = abs_off
    while p < len(raw) - 1:
        g = struct.unpack_from('>H', raw, p)[0]
        if g == 0xFFFF:
            break
        glyphs.append(g)
        p += 2
    gi, within = ot_mapping[oi]
    logical_msgs.append({
        'ot_idx': oi,
        'offset': offsets[oi],
        'abs_offset': abs_off,
        'group': gi,
        'within': within,
        'glyphs': glyphs,
        'jp_decode': decode_glyphs(glyphs, jp_rev),
        'en_decode': decode_glyphs(glyphs, en_rev),
        'is_jp': is_japanese(glyphs),
        'is_empty': len(glyphs) == 0,
    })

# Stats
jp_msgs = [m for m in logical_msgs if m['is_jp']]
en_msgs = [m for m in logical_msgs if not m['is_jp'] and not m['is_empty']]
empty_msgs = [m for m in logical_msgs if m['is_empty']]

mid_group_entries = [(oi, gi, w) for oi, (gi, w) in enumerate(ot_mapping) if w > 0]
groups_with_midref = set(gi for _, gi, _ in mid_group_entries)

# Check existing translations
r39_translations = []
for i in range(10):
    fp = f'{BASE}/data/translate_chunks/chunk_{i:02d}_translated.json'
    if os.path.exists(fp):
        try:
            chunk = json.load(open(fp, encoding='utf-8'))
            r39_entries = [e for e in chunk if e.get('resource') == 39]
            r39_translations.extend(r39_entries)
        except:
            pass

# =========================================================================
# BUILD REPORT
# =========================================================================
out = []
def pr(s=''):
    out.append(s)

pr("# R39 Recon Report (Resource Index 39, Type 15)")
pr()
pr("Generated: 2026-05-28")
pr()

pr("## 1. Binary Format Documentation")
pr()
pr("### 1.1 File Layout Overview")
pr("```")
pr(f"Total file size:       {len(raw)} bytes ({len(raw)//2048} sectors)")
pr(f"Sub-header:            bytes 0..15     (16 bytes, LE uint32 x 4)")
pr(f"Sequential ID table:   bytes 16..{seq_data_end-1}   ({seq_count} entries x 16 bytes = {seq_count*16} bytes)")
pr(f"Offset table:          bytes {OT_START}..{STREAM_START-1}  ({OT_SIZE} bytes)")
pr(f"Glyph stream:          bytes {STREAM_START}..{stream_end-1} ({stream_end - STREAM_START} bytes)")
pr(f"Remaining data:        bytes {stream_end}..{len(raw)-1} ({len(raw) - stream_end} bytes)")
pr(f"Declared payload_size: {payload_size} (covers bytes 16..{payload_end-1})")
pr(f"NOTE: Glyph stream EXTENDS {stream_end - payload_end} bytes beyond payload_end!")
pr("```")
pr()

pr("### 1.2 Sub-Header (16 bytes, all LE uint32)")
pr("```")
pr(f"  [0x00] h0:            {h0}")
pr(f"  [0x04] payload_size:  {payload_size} (0x{payload_size:04X})")
pr(f"  [0x08] stride:        {stride} (0x{stride:02X}) = sequential table size + 16-byte sub-header")
pr(f"  [0x0C] h3:            {h3}")
pr("```")
pr()

pr("### 1.3 Sequential ID Table (bytes 16..239)")
pr(f"- {seq_count} entries, each 16 bytes")
pr(f"- Format: LE u32 sequential_id (1,2,3,...) + 12 bytes data")
pr(f"- Must be preserved byte-for-byte during injection")
pr()

pr("### 1.4 Offset Table (Format A, bytes 240..631)")
pr()
pr("#### Structure")
pr("```")
pr(f"Header:   BE u16 msg_count = {msg_count}, BE u16 flags = 0x{ot_flags0:04X}")
pr(f"Entries:  {len(offsets)} x (BE u16 offset, BE u16 flags)")
pr(f"Size:     {OT_SIZE} bytes total")
pr("```")
pr()
pr("#### CRITICAL: Offset Base")
pr(f"All offset values are relative to the OFFSET TABLE START (byte {OT_START}),")
pr(f"NOT to payload_start (byte 16). To get absolute file position:")
pr(f"  abs_pos = {OT_START} + offset_value")
pr()
pr(f"The v2 pipeline (build_full_english_v2.py line 392) computes offsets as:")
pr(f"  payload_rel_offsets = [glyph_stream_base + goff for goff in new_ffff_positions]")
pr(f"where glyph_stream_base = seq_size + new_ot_size")
pr(f"This produces PAYLOAD-RELATIVE offsets (relative to byte 16), which is WRONG")
pr(f"for R39 where offsets are OT-RELATIVE (relative to byte {OT_START}).")
pr()

pr("#### All Offset Table Entries")
pr("```")
pr(f"{'OT':>5s}  {'Offset':>8s}  {'AbsPos':>7s}  {'Region':>8s}  {'Group':>6s}  {'Within':>7s}  {'Flags':>6s}")
pr(f"{'---':>5s}  {'------':>8s}  {'------':>7s}  {'------':>8s}  {'-----':>6s}  {'------':>7s}  {'-----':>6s}")
for oi in range(len(offsets)):
    off = offsets[oi]
    flg = offset_flags[oi]
    abs_pos = ot_abs[oi]
    gi, within = ot_mapping[oi]
    region = "STREAM" if abs_pos < payload_end else "EXTRA"
    mid = " *MID*" if within > 0 else ""
    pr(f"[{oi:3d}]  0x{off:04X}    {abs_pos:5d}    {region:>6s}   G{gi:03d}    +{within:4d}{mid}    0x{flg:04X}")
pr("```")
pr()

pr("### 1.5 Glyph Stream")
pr(f"- Starts at byte {STREAM_START}")
pr(f"- Extends to byte {stream_end} (past declared payload_end at {payload_end})")
pr(f"- Total: {stream_end - STREAM_START} bytes = {(stream_end - STREAM_START)//2} uint16 words")
pr(f"- Contains {len(groups)} FFFF-delimited groups")
pr(f"- Groups in main payload: {sum(1 for g in group_data if not g['in_extra'])}")
pr(f"- Groups in extra region: {sum(1 for g in group_data if g['in_extra'])}")
pr(f"- Special tokens: 0xFFFF=group-end, 0xFFFE=line-break")
pr()

# Multi-entry group analysis
pr("### 1.6 Multi-Entry Groups")
pr(f"The offset table has {len(offsets)} entries but only {len(groups)} FFFF groups.")
pr(f"{len(mid_group_entries)} OT entries point to mid-group positions.")
pr(f"{len(groups_with_midref)} groups have mid-group references.")
pr()
pr("Groups with mid-group OT references:")
pr("```")
for gi in sorted(groups_with_midref):
    refs = [(oi, w) for oi, (g, w) in enumerate(ot_mapping) if g == gi]
    ref_str = ', '.join(f'OT[{oi}]+{w}' for oi, w in refs)
    pr(f"  G{gi:03d}: {ref_str}")
pr("```")
pr()

pr("## 2. All 97 Messages (Offset-Table Indexed)")
pr()
pr(f"**Summary**: {len(logical_msgs)} total, {len(jp_msgs)} Japanese, {len(en_msgs)} English/symbol, {len(empty_msgs)} empty")
pr()

for m in logical_msgs:
    status = "JP" if m['is_jp'] else ("EMPTY" if m['is_empty'] else "EN")
    gi = m['group']
    within = m['within']
    mid = " (mid-group)" if within > 0 else ""
    glyph_hex = ' '.join(f'{g:04X}' for g in m['glyphs'][:25])
    if len(m['glyphs']) > 25:
        glyph_hex += ' ...'
    pr(f"### M{m['ot_idx']:03d} [{status}] G{gi:03d}+{within}{mid}")
    pr(f"- JP: `{m['jp_decode']}`")
    pr(f"- EN: `{m['en_decode']}`")
    pr(f"- Glyphs ({len(m['glyphs'])}): `{glyph_hex}`")
    pr()

pr("## 3. FFFF Group Details")
pr()
for g in group_data:
    ot_str = []
    for oi in g['ot_start_refs']:
        ot_str.append(f'OT[{oi}]')
    for oi, w in g['ot_mid_refs']:
        ot_str.append(f'OT[{oi}]+{w}')
    refs = ', '.join(ot_str) if ot_str else 'no OT ref'
    status = "JP" if g['is_jp'] else ("EMPTY" if not g['glyphs'] else "EN")
    extra = " [EXTRA-REGION]" if g['in_extra'] else ""
    pr(f"### G{g['idx']:03d} [{status}]{extra} ({refs})")
    pr(f"- JP: `{g['jp_decode']}`")
    pr(f"- EN: `{g['en_decode']}`")
    pr(f"- Bytes: {g['start']}..{g['end']} ({g['end']-g['start']} bytes)")
    glyph_hex = ' '.join(f'{gl:04X}' for gl in g['glyphs'])
    pr(f"- Raw: `{glyph_hex}`")
    pr()

pr("## 4. Translation Status")
pr()
if r39_translations:
    pr(f"Found {len(r39_translations)} existing R39 translations in chunks:")
    for e in r39_translations[:20]:
        pr(f"- M{e.get('message', '?')}: `{e.get('english', '')[:80]}`")
    if len(r39_translations) > 20:
        pr(f"... and {len(r39_translations)-20} more")
else:
    pr("**No existing R39 translations found in translate_chunks.**")
pr()

# Check inferred data
pr("### Inferred Glyph Mappings for R39")
try:
    inferred = json.load(open(f'{BASE}/data/inferred_r39.json', encoding='utf-8'))
    pr(f"Found inferred_r39.json: {len(inferred)} entries")
    for k, v in sorted(inferred.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0)[:15]:
        pr(f"- Glyph {k}: `{v}`")
    if len(inferred) > 15:
        pr(f"... and {len(inferred)-15} more")
except Exception as ex:
    pr(f"Error: {ex}")
pr()

pr("## 5. Root Cause Analysis: v2 Pipeline FFFF Bug (Tavern Softlock)")
pr()
pr("### Summary of Bugs")
pr()
pr("The v2 pipeline (build_full_english_v2.py) has THREE bugs affecting R39:")
pr()
pr("#### Bug 1: Wrong Offset Base")
pr(f"The pipeline computes offsets relative to payload start (byte 16),")
pr(f"but R39 offsets are relative to the offset table start (byte {OT_START}).")
pr(f"This means every injected offset is wrong by {OT_START - 16} bytes ({OT_START} - 16).")
pr()
pr("Specifically, line 392:")
pr("```python")
pr("payload_rel_offsets = [glyph_stream_base + goff for goff in new_ffff_positions]")
pr("```")
pr(f"produces offsets relative to byte 16, but the game reads them relative to byte {OT_START}.")
pr()

pr("#### Bug 2: Lost Mid-Group OT Entries")
pr(f"R39 has {len(mid_group_entries)} OT entries pointing to mid-group positions.")
pr("The pipeline only creates one OT entry per FFFF group, losing these entries entirely.")
pr(f"This changes msg_count from {msg_count} to {len(groups)}, corrupting the offset table.")
pr()

pr("#### Bug 3: Glyph Stream Truncation at payload_end")
pr(f"The pipeline uses payload_end (byte {payload_end}) as the stream boundary,")
pr(f"but R39's glyph stream extends to byte {stream_end}.")
pr(f"The last {sum(1 for g in group_data if g['in_extra'])} FFFF groups (containing ")
pr(f"OT entries {', '.join(str(oi) for oi in range(len(offsets)) if ot_abs[oi] >= payload_end)})")
pr(f"are in this extended region and would be ignored/corrupted.")
pr()

pr("### Why This Causes the Tavern Softlock")
pr("The game uses the offset table to look up menu/equipment text by index.")
pr("When the offset table has wrong values, the game reads garbage data as text,")
pr("which can include control codes that cause infinite loops or null pointer")
pr("dereferences in the text rendering engine.")
pr()

pr("## 6. Recommended Injection Strategy")
pr()
pr("### Option A: In-Place Fixed-Length Replacement (Safest)")
pr("```")
pr("For each FFFF group:")
pr("  1. Calculate original byte length")
pr("  2. Encode English translation")
pr("  3. If English <= original length: pad with 0x0000 (space)")
pr("  4. If English > original length: truncate or abbreviate")
pr("  5. Write at exact same position")
pr("  6. NO offset table changes needed")
pr("```")
pr("Pros: Zero risk of offset corruption")
pr("Cons: Limited by Japanese text length (but JP chars are 1 glyph each)")
pr()

pr("### Option B: Delta-Tracking Offset Recalculation")
pr("```")
pr("1. Record original position of every OT entry (abs = 240 + offset_value)")
pr("2. For each entry, note: which FFFF group, byte offset within group")
pr("3. Replace desired FFFF groups with new content")
pr("4. Track cumulative byte delta from group replacements")
pr("5. For each OT entry:")
pr(f"   - new_abs = original_group_new_start + within_offset")
pr(f"   - new_ot_value = new_abs - {OT_START}")
pr("6. If a replaced group has mid-group OT refs, SKIP that group")
pr("   or recalculate within_offset based on translation structure")
pr("7. Rebuild OT with ORIGINAL msg_count ({})".format(msg_count))
pr("8. Assemble: sub-header + seq_data + new_OT + new_stream")
pr("9. Update payload_size (must cover at least the main stream)")
pr("10. Preserve any data beyond the glyph stream")
pr("```")
pr()

safe_groups = sorted(set(range(len(groups))) - groups_with_midref)
pr(f"### Safe vs Unsafe Groups")
pr(f"- Safe for replacement (no mid-group OT refs): {len(safe_groups)} groups")
pr(f"- Unsafe (have mid-group OT refs): {len(groups_with_midref)} groups")
pr()
pr(f"Safe group indices: {safe_groups}")
pr(f"Unsafe group indices: {sorted(groups_with_midref)}")
pr()

pr("### Critical Implementation Notes")
pr(f"1. Offset base is byte {OT_START} (OT start), NOT byte 16 (payload start)")
pr(f"2. Glyph stream extends {stream_end - payload_end} bytes beyond payload_end")
pr(f"3. Must preserve {len(mid_group_entries)} mid-group OT entry relationships")
pr(f"4. msg_count must remain {msg_count}")
pr(f"5. Last OT entry flags must remain 0xFFFF")
pr(f"6. Data beyond byte {stream_end} (if any) must be preserved")
pr()

# Write
outpath = f'{BASE}/runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/recon_r39.md'
with open(outpath, 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))

print(f"Report written to {outpath}")
print(f"Lines: {len(out)}")
print(f"Messages: {len(logical_msgs)} total ({len(jp_msgs)} JP, {len(en_msgs)} EN, {len(empty_msgs)} empty)")
print(f"FFFF groups: {len(groups)} (OT entries: {len(offsets)}, mid-group: {len(mid_group_entries)})")
print(f"Groups with mid-refs: {len(groups_with_midref)}")
print(f"Safe for replacement: {len(safe_groups)}")
print(f"Stream extends {stream_end - payload_end} bytes beyond payload_end")
