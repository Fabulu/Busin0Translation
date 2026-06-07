#!/usr/bin/env python3
"""
Extract all untranslated Japanese text from PACKDATA resources into a markdown file.
Outputs: data/untranslated_for_review.md
"""

import struct, json, glob, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE)

# ── Load glyph map ──
glyph_map = json.load(open('data/msg_glyph_map.json', 'r', encoding='utf-8'))

def decode_glyphs(data, start, end):
    """Decode a BE u16 glyph stream to Japanese text."""
    chars = []
    for p in range(start, end, 2):
        if p + 2 > len(data):
            break
        gid = struct.unpack_from('>H', data, p)[0]
        if gid == 0xFFFE:
            chars.append(' / ')
        elif gid == 0xFFD2:
            chars.append('[PB]')
        elif gid <= 94:
            chars.append(chr(gid + 0x20))
        else:
            ch = glyph_map.get(str(gid))
            if ch:
                chars.append(ch)
            else:
                chars.append('[{:04X}]'.format(gid))
    return ''.join(chars)


def parse_ffff_groups_from_raw(raw_data, scan_start=0, scan_end=None):
    """Parse FFFF-delimited groups from raw binary data."""
    if scan_end is None:
        scan_end = len(raw_data)
    groups = []
    grp_start = scan_start
    off = scan_start
    while off < scan_end - 1:
        val = struct.unpack_from('>H', raw_data, off)[0]
        if val == 0xFFFF:
            groups.append((grp_start, off))
            grp_start = off + 2
        off += 2
    return groups


def parse_type01_resource(raw):
    """Parse a type-01 resource (sub-header + sequential table + offset table + glyph stream)."""
    h0, h_ps, h2, h3 = struct.unpack_from('<IIII', raw, 0)
    payload_end = 16 + h_ps

    # Count sequential table
    seq_count = 0
    start = 16
    if len(raw) >= start + 16:
        first = struct.unpack_from('<I', raw, start)[0]
        if first == 1:
            for e in range(min(256, (len(raw) - start) // 16)):
                eid = struct.unpack_from('<I', raw, start + e * 16)[0]
                if eid == e + 1:
                    seq_count = e + 1
                else:
                    break

    after_seq = 16 + seq_count * 16

    # Try to parse offset table
    ot_start = after_seq
    stream_start = None
    if ot_start + 4 <= len(raw):
        first_val = struct.unpack_from('>H', raw, ot_start)[0]
        first_flags = struct.unpack_from('>H', raw, ot_start + 2)[0]
        if first_flags == 0x0000 and 1 <= first_val <= 500:
            i = ot_start + 4
            for e in range(first_val):
                if i + 4 > len(raw):
                    break
                flags = struct.unpack_from('>H', raw, i + 2)[0]
                i += 4
                if flags == 0xFFFF:
                    break
            stream_start = i

    if stream_start is None:
        # Scan for first FFFF/FFFE
        for off in range(after_seq, min(len(raw) - 1, payload_end), 2):
            val = struct.unpack_from('>H', raw, off)[0]
            if val == 0xFFFF or val == 0xFFFE:
                stream_start = off
                break

    if stream_start is None:
        stream_start = after_seq

    # Parse groups from stream_start to end of file (not just payload_end)
    # Type-20 resources (like R34) have data beyond the payload
    return parse_ffff_groups_from_raw(raw, stream_start, len(raw))


def parse_type02_resource(raw):
    """Parse a type-02 resource. Section 1 = group 0 (opcodes), rest = text groups."""
    return parse_ffff_groups_from_raw(raw, 0, len(raw))


def parse_type03_resource(raw):
    """Parse a type-03 resource (sub-header + glyph streams)."""
    h0, h_ps, h2, h3 = struct.unpack_from('<IIII', raw, 0)
    # Parse all FFFF groups from byte 16 to end of file
    return parse_ffff_groups_from_raw(raw, 16, len(raw))


# ── Load ALL existing translations ──
print("Loading existing translations...")

# From chunk files (type-01 resources: R34-R49, R1053, R1908, R2124, R2654)
chunk_trans = {}  # (resource, message) -> {'japanese': ..., 'english': ...}
for f in sorted(glob.glob('data/translate_chunks/chunk_*_translated.json') +
                glob.glob('data/translate_chunks/chunk_*_fix.json') +
                glob.glob('data/translate_chunks/chunk_*_extra.json')):
    dd = json.load(open(f, 'r', encoding='utf-8'))
    for e in dd:
        r = e.get('resource')
        m = e.get('message')
        if r is not None and m is not None:
            chunk_trans[(r, m)] = {
                'japanese': e.get('japanese', ''),
                'english': e.get('english', '')
            }
print(f"  Chunk translations: {len(chunk_trans)} entries")

# From type-2 batch files
type2_trans = {}  # (resource, msg_index) -> {'japanese': ..., 'english': ...}
for f in sorted(glob.glob('data/type2_translated/batch_*.json')):
    dd = json.load(open(f, 'r', encoding='utf-8'))
    for e in dd:
        r = e.get('resource')
        m = e.get('msg_index', e.get('message'))
        if r is not None and m is not None and m >= 0:
            type2_trans[(r, m)] = {
                'japanese': e.get('japanese', ''),
                'english': e.get('english') or ''
            }
print(f"  Type-2 translations: {len(type2_trans)} entries")

# ── Context labels for resources ──
RESOURCE_CONTEXT = {
    34: "Item/Spell names and descriptions",
    35: "Short item/spell labels",
    36: "Character class/race descriptions",
    37: "Character names and title text",
    38: "Chargen/stat screen text",
    39: "Equipment names and descriptions",
    40: "Shop and merchant dialogue",
    41: "Guild/party management text",
    42: "Temple/resurrection text",
    43: "Combat messages and effects",
    44: "Dungeon event text",
    45: "Skill/ability descriptions",
    46: "Bulletin board messages (page 1)",
    47: "Bulletin board messages (page 2)",
    48: "System/menu messages",
    49: "Misc UI and status messages",
    1195: "Debug/test dialogue",
    1352: "Debug camera/render settings",
}

# ── Extract from type-01 MSG resources (R34-R49 + others) ──
MSG_RESOURCES_TYPE01 = [34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49]

entries_by_resource = {}  # resource -> list of (msg_id, japanese, english_or_None, status)

for ridx in MSG_RESOURCES_TYPE01:
    raws = glob.glob(f'extracted/packdata_raw/{ridx:04d}_type*.raw')
    if not raws:
        continue
    raw = open(raws[0], 'rb').read()
    type_code = os.path.basename(raws[0]).split('_type')[1].split('.')[0]

    if type_code in ('01', '20', '15'):
        groups = parse_type01_resource(raw)
    elif type_code == '03':
        groups = parse_type03_resource(raw)
    elif type_code == '02':
        groups = parse_type02_resource(raw)
    else:
        groups = parse_type01_resource(raw)

    resource_entries = []
    for gi, (gs, ge) in enumerate(groups):
        japanese = decode_glyphs(raw, gs, ge)
        # Check if translated
        trans = chunk_trans.get((ridx, gi))
        if trans:
            eng = trans['english']
            if eng and eng.strip():
                status = 'TRANSLATED'
            else:
                status = 'EMPTY_ENGLISH'
        else:
            # Also check type2 translations for R39
            trans2 = type2_trans.get((ridx, gi))
            if trans2:
                eng = trans2['english']
                if eng and eng.strip():
                    status = 'TRANSLATED'
                else:
                    status = 'EMPTY_ENGLISH'
            else:
                status = 'UNTRANSLATED'
                eng = ''

        resource_entries.append({
            'msg': gi,
            'japanese': japanese.strip(),
            'english': eng.strip() if eng else '',
            'status': status,
        })

    entries_by_resource[ridx] = resource_entries
    total = len(resource_entries)
    translated = sum(1 for e in resource_entries if e['status'] == 'TRANSLATED')
    untrans = sum(1 for e in resource_entries if e['status'] == 'UNTRANSLATED')
    empty = sum(1 for e in resource_entries if e['status'] == 'EMPTY_ENGLISH')
    print(f"  R{ridx}: {total} groups, {translated} translated, {untrans} untranslated, {empty} empty")


# ── Extract type-02 resources (R1352, R1195) ──
TYPE2_RESOURCES = [1195, 1352]

for ridx in TYPE2_RESOURCES:
    raws = glob.glob(f'extracted/packdata_raw/{ridx:04d}_type*.raw')
    if not raws:
        continue
    raw = open(raws[0], 'rb').read()
    groups = parse_type02_resource(raw)

    # For type-02, group 0 is section 1 (opcodes). Text msg_index 0 = FFFF group 1 in raw.
    # But the batch files use msg_index starting from 0 for TEXT groups.
    # We need to figure out where section 2 starts.
    # Convention: skip group 0 (opcodes), text groups start from group 1
    # msg_index in batch = raw_group_index - 1

    resource_entries = []
    for gi in range(1, len(groups)):
        gs, ge = groups[gi]
        japanese = decode_glyphs(raw, gs, ge)
        msg_idx = gi - 1  # 0-indexed text message

        trans = type2_trans.get((ridx, msg_idx))
        if trans:
            eng = trans['english']
            if eng and eng.strip():
                status = 'TRANSLATED'
            else:
                status = 'EMPTY_ENGLISH'
        else:
            status = 'UNTRANSLATED'
            eng = ''

        resource_entries.append({
            'msg': msg_idx,
            'japanese': japanese.strip(),
            'english': eng.strip() if eng else '',
            'status': status,
        })

    entries_by_resource[ridx] = resource_entries
    total = len(resource_entries)
    translated = sum(1 for e in resource_entries if e['status'] == 'TRANSLATED')
    untrans = sum(1 for e in resource_entries if e['status'] == 'UNTRANSLATED')
    print(f"  R{ridx}: {total} text groups, {translated} translated, {untrans} untranslated")


# ── Also check type-2 batch files for empty English ──
print("\nChecking type-2 batches for empty English...")
type2_empty = {}  # (resource, msg_index) -> japanese
for f in sorted(glob.glob('data/type2_translated/batch_*.json')):
    dd = json.load(open(f, 'r', encoding='utf-8'))
    for e in dd:
        r = e.get('resource')
        m = e.get('msg_index', e.get('message'))
        jp = e.get('japanese') or ''
        eng = e.get('english') or ''
        if r and m is not None and m >= 0 and jp.strip() and not eng.strip():
            type2_empty[(r, m)] = jp
if type2_empty:
    print(f"  Found {len(type2_empty)} type-2 entries with empty English")

# ── Also check for R39 equipment gaps ──
print("\nChecking R39 equipment gaps...")
r39_empty_from_batches = []
for f in ['data/type2_translated/batch_r39_equip_a.json', 'data/type2_translated/batch_r39_equip_b.json']:
    dd = json.load(open(f, 'r', encoding='utf-8'))
    for e in dd:
        eng = e.get('english') or ''
        if not eng.strip():
            r39_empty_from_batches.append(e)
if r39_empty_from_batches:
    print(f"  R39 equipment entries with empty English: {len(r39_empty_from_batches)}")


# ── Generate markdown ──
print("\nGenerating markdown...")

out_lines = []

out_lines.append("# Busin 0: Wizardry Alternative Neo - Untranslated Text")
out_lines.append("")
out_lines.append("This file contains all untranslated Japanese text from the game's PACKDATA resources.")
out_lines.append("A translator should fill in the `English:` field for each entry.")
out_lines.append("")
out_lines.append("## Format")
out_lines.append("")
out_lines.append("Each entry follows this format:")
out_lines.append("```")
out_lines.append("### R{resource}:M{message} ({context})")
out_lines.append("- Japanese: {decoded Japanese text}")
out_lines.append("- English: {fill this in}")
out_lines.append("```")
out_lines.append("")
out_lines.append("### Conventions")
out_lines.append("- ` / ` = line break (FFFE token). Keep line breaks in English translations.")
out_lines.append("- `[PB]` = page break (FFD2 token). Keep page breaks in translations.")
out_lines.append("- `[XXXX]` = unmapped glyph ID. Leave as-is in translations.")
out_lines.append("- Entries marked `[TRANSLATED]` already have English text and can be skipped.")
out_lines.append("- Entries marked `[EMPTY]` have a translation slot but the English is blank.")
out_lines.append("- Entries with blank/whitespace-only Japanese can be skipped (control entries).")
out_lines.append("")
out_lines.append("### Line length guideline")
out_lines.append("- Dialogue: ~20 characters per line, max 3 lines per page")
out_lines.append("- Item names: Keep concise (under 20 chars)")
out_lines.append("- Use ` / ` to separate lines")
out_lines.append("")

# Summary
total_untrans = 0
total_translated = 0
total_empty = 0
for ridx in sorted(entries_by_resource.keys()):
    entries = entries_by_resource[ridx]
    for e in entries:
        if e['status'] == 'UNTRANSLATED' and e['japanese'].strip():
            total_untrans += 1
        elif e['status'] == 'TRANSLATED':
            total_translated += 1
        elif e['status'] == 'EMPTY_ENGLISH':
            total_empty += 1

out_lines.append("## Summary")
out_lines.append("")
out_lines.append(f"| Status | Count |")
out_lines.append(f"|--------|-------|")
out_lines.append(f"| Translated | {total_translated} |")
out_lines.append(f"| Untranslated (needs work) | {total_untrans} |")
out_lines.append(f"| Empty English (needs work) | {total_empty} |")
out_lines.append(f"| **Total entries** | **{total_translated + total_untrans + total_empty}** |")
out_lines.append("")

# Resource summary table
out_lines.append("### Per-resource breakdown")
out_lines.append("")
out_lines.append("| Resource | Context | Total | Translated | Untranslated | Empty |")
out_lines.append("|----------|---------|-------|------------|--------------|-------|")
for ridx in sorted(entries_by_resource.keys()):
    entries = entries_by_resource[ridx]
    ctx = RESOURCE_CONTEXT.get(ridx, "Unknown")
    total = len(entries)
    tr = sum(1 for e in entries if e['status'] == 'TRANSLATED')
    ut = sum(1 for e in entries if e['status'] == 'UNTRANSLATED' and e['japanese'].strip())
    em = sum(1 for e in entries if e['status'] == 'EMPTY_ENGLISH')
    out_lines.append(f"| R{ridx} | {ctx} | {total} | {tr} | {ut} | {em} |")
out_lines.append("")

# ── Output each resource ──
for ridx in sorted(entries_by_resource.keys()):
    entries = entries_by_resource[ridx]
    ctx = RESOURCE_CONTEXT.get(ridx, "Unknown")

    out_lines.append(f"---")
    out_lines.append(f"")
    out_lines.append(f"## R{ridx} - {ctx}")
    out_lines.append(f"")

    tr_count = sum(1 for e in entries if e['status'] == 'TRANSLATED')
    ut_count = sum(1 for e in entries if e['status'] == 'UNTRANSLATED' and e['japanese'].strip())
    em_count = sum(1 for e in entries if e['status'] == 'EMPTY_ENGLISH')
    out_lines.append(f"Total: {len(entries)} messages | Translated: {tr_count} | Untranslated: {ut_count} | Empty: {em_count}")
    out_lines.append(f"")

    for e in entries:
        msg = e['msg']
        jp = e['japanese']
        eng = e['english']
        status = e['status']

        # Skip empty/whitespace-only Japanese entries (control groups)
        if not jp.strip() and status != 'EMPTY_ENGLISH':
            continue

        if status == 'TRANSLATED':
            out_lines.append(f"### R{ridx}:M{msg} ({ctx}) [TRANSLATED]")
            out_lines.append(f"- Japanese: {jp}")
            out_lines.append(f"- English: {eng}")
            out_lines.append(f"")
        elif status == 'EMPTY_ENGLISH':
            out_lines.append(f"### R{ridx}:M{msg} ({ctx}) [EMPTY]")
            out_lines.append(f"- Japanese: {jp}")
            out_lines.append(f"- English: ")
            out_lines.append(f"")
        else:
            out_lines.append(f"### R{ridx}:M{msg} ({ctx})")
            out_lines.append(f"- Japanese: {jp}")
            out_lines.append(f"- English: ")
            out_lines.append(f"")

# ── Type-2 empty English entries (from batch files, not already in entries_by_resource) ──
# These are from resources not in MSG_RESOURCES_TYPE01 or TYPE2_RESOURCES
covered_resources = set(entries_by_resource.keys())
extra_type2_empty = {k: v for k, v in type2_empty.items() if k[0] not in covered_resources}
if extra_type2_empty:
    out_lines.append("---")
    out_lines.append("")
    out_lines.append("## Type-2 Dialogue Resources - Empty English")
    out_lines.append("")
    out_lines.append("These entries are from type-2 dialogue batch files where the English translation is blank.")
    out_lines.append("")

    by_res = {}
    for (r, m), jp in sorted(extra_type2_empty.items()):
        by_res.setdefault(r, []).append((m, jp))

    for r in sorted(by_res.keys()):
        entries = by_res[r]
        out_lines.append(f"### Resource R{r}")
        out_lines.append("")
        for m, jp in sorted(entries):
            out_lines.append(f"### R{r}:M{m} (Type-2 dialogue) [EMPTY]")
            out_lines.append(f"- Japanese: {jp}")
            out_lines.append(f"- English: ")
            out_lines.append("")

# ── R39 equipment empty from batch files (already in entries_by_resource but flag them) ──
if r39_empty_from_batches:
    out_lines.append("---")
    out_lines.append("")
    out_lines.append("## R39 Equipment - Empty Translations in Batch Files")
    out_lines.append("")
    out_lines.append("These R39 entries exist in equipment batch files but have empty English.")
    out_lines.append("")
    for e in r39_empty_from_batches:
        mid = e.get('msg_index', e.get('message', -1))
        jp = e.get('japanese', '')
        out_lines.append(f"### R39:M{mid} (Equipment name/desc) [EMPTY-BATCH]")
        out_lines.append(f"- Japanese: {jp}")
        out_lines.append(f"- English: ")
        out_lines.append("")

# Write output
output_path = 'data/untranslated_for_review.md'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(out_lines))

print(f"\nWrote {len(out_lines)} lines to {output_path}")
total_size = os.path.getsize(output_path)
print(f"File size: {total_size:,} bytes ({total_size/1024:.1f} KB)")
