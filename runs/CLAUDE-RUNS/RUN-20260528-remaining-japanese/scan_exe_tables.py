#!/usr/bin/env python3
"""Scan SLPM_653.78 data section for Japanese text tables (LE uint16 glyph ID arrays)."""

import struct, json, sys, os

EXE_PATH = "C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78"
GLYPH_MAP_PATH = "C:/Programmieren/wizardrytranslation/data/msg_glyph_map.json"
OUT_PATH = "C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/recon_exe_tables.md"

SCAN_START = 0x3B0000
SCAN_END   = 0x3FD000

# Load glyph map
glyph_map = {}
try:
    with open(GLYPH_MAP_PATH, encoding='utf-8') as f:
        raw = json.load(f)
    # keys are glyph IDs (as strings), values are characters
    for k, v in raw.items():
        glyph_map[int(k)] = v
    print(f"Loaded {len(glyph_map)} glyph mappings", file=sys.stderr)
except Exception as e:
    print(f"Warning: could not load glyph map: {e}", file=sys.stderr)

def glyph_to_char(gid):
    """Convert a glyph ID to a character."""
    if gid == 0:
        return '\u2400'  # null marker
    if 1 <= gid <= 95:
        return chr(gid + 0x20)  # ASCII: glyph_id = char_code - 0x20
    if gid in glyph_map:
        return glyph_map[gid]
    return f'[{gid}]'

def decode_glyphs(gids):
    """Decode a list of glyph IDs to a string."""
    return ''.join(glyph_to_char(g) for g in gids)

def is_text_glyph(gid):
    """Check if a glyph ID looks like valid text (ASCII printable or Japanese)."""
    if gid == 0:
        return True  # null terminator
    if 1 <= gid <= 95:
        return True  # printable ASCII
    if 96 <= gid <= 8000:
        return True  # Japanese range
    return False

# Read EXE
with open(EXE_PATH, 'rb') as f:
    data = f.read()

print(f"EXE size: {len(data)} bytes", file=sys.stderr)

# ============================================================
# PASS 1: Find contiguous runs of text-like uint16 values
# ============================================================
results = []

MIN_RUN = 4  # minimum number of uint16s to consider a "table"

i = SCAN_START
while i < SCAN_END - 1:
    val = struct.unpack_from('<H', data, i)[0]
    if is_text_glyph(val) and val != 0:
        # Start of potential run
        run_start = i
        run_values = []
        j = i
        zero_count = 0
        total_count = 0
        jp_count = 0
        while j < SCAN_END - 1:
            v = struct.unpack_from('<H', data, j)[0]
            if not is_text_glyph(v):
                break
            run_values.append(v)
            total_count += 1
            if v == 0:
                zero_count += 1
                # Allow up to 4 consecutive zeros (padding between strings)
                consec_zeros = 0
                for rv in reversed(run_values):
                    if rv == 0:
                        consec_zeros += 1
                    else:
                        break
                if consec_zeros > 4:
                    # Trim trailing zeros and stop
                    run_values = run_values[:-(consec_zeros-1)]
                    total_count = len(run_values)
                    j = run_start + total_count * 2
                    break
            if 96 <= v <= 8000:
                jp_count += 1
            j += 2

        non_zero = total_count - zero_count
        if non_zero >= MIN_RUN:
            # Split into individual strings at null terminators
            strings = []
            current = []
            for v in run_values:
                if v == 0:
                    if current:
                        strings.append(current)
                        current = []
                else:
                    current.append(v)
            if current:
                strings.append(current)

            jp_ratio = jp_count / non_zero if non_zero > 0 else 0
            results.append({
                'offset': run_start,
                'end': run_start + total_count * 2,
                'count': total_count,
                'non_zero': non_zero,
                'jp_count': jp_count,
                'jp_ratio': jp_ratio,
                'zero_count': zero_count,
                'strings': strings,
                'num_strings': len(strings),
            })
        i = j
    else:
        i += 2

print(f"Found {len(results)} candidate runs", file=sys.stderr)

# ============================================================
# PASS 2: Categorize and decode
# ============================================================

def categorize(entry):
    """Try to categorize what kind of text this is."""
    decoded_strings = [decode_glyphs(s) for s in entry['strings']]
    entry['decoded'] = decoded_strings

    text = ' '.join(decoded_strings)
    if any(x in text for x in ['STR', 'INT', 'VIT', 'DEX', 'SPD', 'LUK']):
        return 'stat_labels'
    if any(x in text for x in ['HP', 'MP', 'AC', 'LV']):
        return 'combat_stats'
    if entry['jp_ratio'] > 0.8 and entry['num_strings'] > 5:
        return 'japanese_text_table'
    if entry['jp_ratio'] > 0.5:
        return 'mixed_text'
    if entry['jp_ratio'] < 0.2:
        return 'ascii_text'
    return 'unknown'

for entry in results:
    entry['category'] = categorize(entry)

# ============================================================
# PASS 3: Detailed examination of known areas
# ============================================================

def examine_area(start, end, label):
    """Examine a specific area in detail."""
    area_data = data[start:end]
    entries = []
    strings = []
    current = []
    for i in range(0, len(area_data) - 1, 2):
        v = struct.unpack_from('<H', area_data, i)[0]
        entries.append(v)
        if v == 0:
            if current:
                strings.append((start + (i - len(current)*2), current[:]))
                current = []
        else:
            current.append(v)
    if current:
        strings.append((start + (len(area_data) - len(current)*2), current[:]))

    return {
        'label': label,
        'start': start,
        'end': end,
        'size': end - start,
        'num_uint16': len(entries),
        'strings': [(off, gids, decode_glyphs(gids)) for off, gids in strings],
    }

chargen_area = examine_area(0x3C844A, 0x3C8F64, "Chargen Stat Labels")
menu_area = examine_area(0x3C3026, 0x3C5174, "Menu Label Pairs")

# ============================================================
# OUTPUT
# ============================================================

lines = []
lines.append("# EXE Data Section: Japanese Text Table Reconnaissance")
lines.append("")
lines.append(f"**EXE**: `SLPM_653.78` ({len(data):,} bytes)")
lines.append(f"**Scan range**: 0x{SCAN_START:06X} - 0x{SCAN_END:06X} ({SCAN_END-SCAN_START:,} bytes)")
lines.append(f"**Glyph mappings loaded**: {len(glyph_map)}")
lines.append(f"**Candidate text runs found**: {len(results)}")
lines.append("")

# Filter to significant tables (10+ non-zero values or high JP ratio)
significant = [r for r in results if r['non_zero'] >= 6 or (r['jp_ratio'] > 0.5 and r['non_zero'] >= 4)]
lines.append(f"## Summary: {len(significant)} Significant Text Runs")
lines.append("")
lines.append("| # | Offset | End | Bytes | Strings | JP% | Category |")
lines.append("|---|--------|-----|-------|---------|-----|----------|")
for idx, r in enumerate(significant):
    lines.append(f"| {idx+1} | 0x{r['offset']:06X} | 0x{r['end']:06X} | {r['end']-r['offset']} | {r['num_strings']} | {r['jp_ratio']*100:.0f}% | {r['category']} |")
lines.append("")

# Detailed listing of all significant tables
lines.append("## Detailed Table Listing")
lines.append("")
for idx, r in enumerate(significant):
    lines.append(f"### Table {idx+1}: 0x{r['offset']:06X} - 0x{r['end']:06X} ({r['category']})")
    lines.append(f"- **Byte range**: 0x{r['offset']:06X} to 0x{r['end']:06X} ({r['end']-r['offset']} bytes)")
    lines.append(f"- **Entries (uint16)**: {r['count']} total, {r['non_zero']} non-zero, {r['zero_count']} zeros")
    lines.append(f"- **Japanese glyphs**: {r['jp_count']} ({r['jp_ratio']*100:.1f}%)")
    lines.append(f"- **Strings**: {r['num_strings']}")
    # Show first 20 decoded strings
    sample = r['decoded'][:20]
    if sample:
        lines.append(f"- **Sample content** (first {min(20, len(r['decoded']))} of {len(r['decoded'])} strings):")
        for s in sample:
            lines.append(f"  - `{s}`")
    if len(r['decoded']) > 20:
        lines.append(f"  - ... and {len(r['decoded'])-20} more strings")
    lines.append("")

# ============================================================
# Known Areas
# ============================================================
lines.append("## Known Area: Chargen Stat Labels (0x3C844A - 0x3C8F64)")
lines.append("")
lines.append(f"- **Size**: {chargen_area['size']} bytes")
lines.append(f"- **Strings found**: {len(chargen_area['strings'])}")
lines.append("")
lines.append("| # | Offset | Length | Decoded |")
lines.append("|---|--------|--------|---------|")
for idx, (off, gids, decoded) in enumerate(chargen_area['strings']):
    lines.append(f"| {idx+1} | 0x{off:06X} | {len(gids)} | `{decoded}` |")
lines.append("")

lines.append("## Known Area: Menu Label Pairs (0x3C3026 - 0x3C5174)")
lines.append("")
lines.append(f"- **Size**: {menu_area['size']} bytes")
lines.append(f"- **Strings found**: {len(menu_area['strings'])}")
lines.append("")
lines.append("| # | Offset | Length | Decoded |")
lines.append("|---|--------|--------|---------|")
for idx, (off, gids, decoded) in enumerate(menu_area['strings']):
    lines.append(f"| {idx+1} | 0x{off:06X} | {len(gids)} | `{decoded}` |")
lines.append("")

# ============================================================
# Stats summary
# ============================================================
total_jp_glyphs = sum(r['jp_count'] for r in significant)
total_strings = sum(r['num_strings'] for r in significant)
total_bytes = sum(r['end'] - r['offset'] for r in significant)

lines.append("## Overall Statistics")
lines.append("")
lines.append(f"- **Total significant text runs**: {len(significant)}")
lines.append(f"- **Total strings across all tables**: {total_strings}")
lines.append(f"- **Total Japanese glyphs**: {total_jp_glyphs}")
lines.append(f"- **Total bytes occupied**: {total_bytes:,}")
lines.append(f"- **Coverage of scan range**: {total_bytes/(SCAN_END-SCAN_START)*100:.1f}%")
lines.append("")

# Category breakdown
from collections import Counter
cats = Counter(r['category'] for r in significant)
lines.append("### By Category")
lines.append("")
for cat, count in cats.most_common():
    cat_entries = [r for r in significant if r['category'] == cat]
    cat_strings = sum(r['num_strings'] for r in cat_entries)
    lines.append(f"- **{cat}**: {count} tables, {cat_strings} strings")
lines.append("")

output = '\n'.join(lines)
with open(OUT_PATH, 'w', encoding='utf-8') as f:
    f.write(output)

print(f"Report written to {OUT_PATH}", file=sys.stderr)
print(f"Significant tables: {len(significant)}", file=sys.stderr)
print(f"Total strings: {total_strings}", file=sys.stderr)
