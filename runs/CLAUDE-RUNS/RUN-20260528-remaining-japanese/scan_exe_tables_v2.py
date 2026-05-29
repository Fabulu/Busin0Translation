#!/usr/bin/env python3
"""Scan SLPM_653.78 data section for Japanese text tables (LE uint16 glyph ID arrays).
v2: Better filtering, merge adjacent runs, focus on large/important tables."""

import struct, json, sys, os
from collections import Counter

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
    for k, v in raw.items():
        glyph_map[int(k)] = v
except Exception as e:
    print(f"Warning: could not load glyph map: {e}", file=sys.stderr)

def glyph_to_char(gid):
    if gid == 0:
        return ''
    if 1 <= gid <= 95:
        return chr(gid + 0x20)
    if gid in glyph_map:
        return glyph_map[gid]
    return f'[{gid}]'

def decode_glyphs(gids):
    return ''.join(glyph_to_char(g) for g in gids)

def is_text_glyph(gid):
    if gid == 0: return True
    if 1 <= gid <= 95: return True
    if 96 <= gid <= 8000: return True
    return False

def has_japanese(gids):
    return any(g >= 96 for g in gids)

# Read EXE
with open(EXE_PATH, 'rb') as f:
    data = f.read()

# ============================================================
# Scan: find null-terminated strings of LE uint16 glyph IDs
# ============================================================
# Strategy: scan for sequences of valid glyph IDs terminated by 0x0000
# Group nearby strings into "tables"

strings_found = []  # (offset, glyph_ids[])

i = SCAN_START
while i < SCAN_END - 1:
    val = struct.unpack_from('<H', data, i)[0]
    if val != 0 and is_text_glyph(val):
        # Start collecting a string
        start = i
        gids = []
        j = i
        while j < SCAN_END - 1:
            v = struct.unpack_from('<H', data, j)[0]
            if v == 0:
                # null terminator
                if gids:
                    strings_found.append((start, gids[:]))
                i = j + 2
                break
            elif is_text_glyph(v):
                gids.append(v)
                j += 2
            else:
                # invalid glyph - not a text string
                if len(gids) >= 2 and has_japanese(gids):
                    strings_found.append((start, gids[:]))
                i = j + 2
                break
        else:
            if gids and len(gids) >= 2:
                strings_found.append((start, gids[:]))
            i = j + 2
    else:
        i += 2

print(f"Found {len(strings_found)} individual strings", file=sys.stderr)

# Filter to strings with at least 1 Japanese glyph and length >= 2
jp_strings = [(off, gids) for off, gids in strings_found if has_japanese(gids) and len(gids) >= 2]
print(f"Of which {len(jp_strings)} contain Japanese glyphs (len>=2)", file=sys.stderr)

# ============================================================
# Group strings into tables (clusters within 32 bytes of each other)
# ============================================================
GAP_THRESHOLD = 64  # bytes between end of one string and start of next

tables = []
if jp_strings:
    current_table = [jp_strings[0]]
    for j in range(1, len(jp_strings)):
        prev_off, prev_gids = current_table[-1]
        prev_end = prev_off + len(prev_gids) * 2 + 2  # +2 for null term
        curr_off, curr_gids = jp_strings[j]
        if curr_off - prev_end <= GAP_THRESHOLD:
            current_table.append(jp_strings[j])
        else:
            tables.append(current_table)
            current_table = [jp_strings[j]]
    tables.append(current_table)

print(f"Grouped into {len(tables)} tables", file=sys.stderr)

# ============================================================
# Known areas - detailed decode
# ============================================================

def decode_area_strings(start, end):
    """Extract all null-terminated uint16 strings from an area."""
    result = []
    i = start
    while i < end - 1:
        v = struct.unpack_from('<H', data, i)[0]
        if v != 0 and is_text_glyph(v):
            s_start = i
            gids = []
            j = i
            while j < end - 1:
                vv = struct.unpack_from('<H', data, j)[0]
                if vv == 0:
                    if gids:
                        result.append((s_start, gids[:], decode_glyphs(gids)))
                    j += 2
                    break
                elif is_text_glyph(vv):
                    gids.append(vv)
                    j += 2
                else:
                    if gids:
                        result.append((s_start, gids[:], decode_glyphs(gids)))
                    j += 2
                    break
            i = j
        else:
            i += 2
    return result

chargen_strings = decode_area_strings(0x3C844A, 0x3C8F64)
menu_strings = decode_area_strings(0x3C3026, 0x3C5174)

# ============================================================
# Build report
# ============================================================

lines = []
lines.append("# EXE Data Section: Japanese Text Table Reconnaissance")
lines.append("")
lines.append(f"- **EXE**: `SLPM_653.78` ({len(data):,} bytes)")
lines.append(f"- **Scan range**: 0x{SCAN_START:06X} - 0x{SCAN_END:06X} ({SCAN_END-SCAN_START:,} bytes)")
lines.append(f"- **Glyph mappings**: {len(glyph_map)}")
lines.append(f"- **Individual JP strings found**: {len(jp_strings)}")
lines.append(f"- **Tables (clustered groups)**: {len(tables)}")
lines.append(f"- **Date**: 2026-05-28")
lines.append("")

# ============================================================
# SECTION 1: Known Area - Chargen Stats
# ============================================================
lines.append("---")
lines.append("## 1. Chargen Stat Labels (0x3C844A - 0x3C8F64)")
lines.append("")
lines.append(f"**Size**: {0x3C8F64 - 0x3C844A} bytes, **Strings found**: {len(chargen_strings)}")
lines.append("")
lines.append("| # | Offset | Len | Raw Glyph IDs | Decoded |")
lines.append("|---|--------|-----|---------------|---------|")
for idx, (off, gids, dec) in enumerate(chargen_strings):
    gid_str = ','.join(str(g) for g in gids[:8])
    if len(gids) > 8:
        gid_str += '...'
    lines.append(f"| {idx+1} | 0x{off:06X} | {len(gids)} | {gid_str} | `{dec}` |")
lines.append("")

# ============================================================
# SECTION 2: Known Area - Menu Labels
# ============================================================
lines.append("---")
lines.append("## 2. Menu Label Pairs (0x3C3026 - 0x3C5174)")
lines.append("")
lines.append(f"**Size**: {0x3C5174 - 0x3C3026} bytes, **Strings found**: {len(menu_strings)}")
lines.append("")
lines.append("| # | Offset | Len | Decoded |")
lines.append("|---|--------|-----|---------|")
for idx, (off, gids, dec) in enumerate(menu_strings):
    lines.append(f"| {idx+1} | 0x{off:06X} | {len(gids)} | `{dec}` |")
lines.append("")

# ============================================================
# SECTION 3: All significant tables (5+ strings or 20+ JP glyphs)
# ============================================================
lines.append("---")
lines.append("## 3. All Significant Japanese Text Tables")
lines.append("")
lines.append("Tables with 3+ strings or 10+ total Japanese glyphs, excluding known areas.")
lines.append("")

sig_tables = []
for table in tables:
    total_jp = sum(1 for _, gids in table for g in gids if g >= 96)
    total_strings = len(table)
    if total_strings >= 3 or total_jp >= 10:
        t_start = table[0][0]
        t_end = table[-1][0] + len(table[-1][1]) * 2 + 2
        sig_tables.append({
            'start': t_start,
            'end': t_end,
            'strings': table,
            'num_strings': total_strings,
            'jp_glyphs': total_jp,
        })

lines.append(f"**Found {len(sig_tables)} significant tables.**")
lines.append("")

for tidx, t in enumerate(sig_tables):
    lines.append(f"### Table {tidx+1}: 0x{t['start']:06X} - 0x{t['end']:06X}")
    lines.append(f"- **Bytes**: {t['end']-t['start']}")
    lines.append(f"- **Strings**: {t['num_strings']}, **JP glyphs**: {t['jp_glyphs']}")

    # Show samples
    show = min(30, len(t['strings']))
    lines.append(f"- **Content** (showing {show} of {len(t['strings'])}):")
    lines.append("")
    lines.append("  | Offset | Len | Decoded |")
    lines.append("  |--------|-----|---------|")
    for off, gids in t['strings'][:show]:
        dec = decode_glyphs(gids)
        lines.append(f"  | 0x{off:06X} | {len(gids)} | `{dec}` |")
    if len(t['strings']) > show:
        lines.append(f"  | ... | ... | ({len(t['strings'])-show} more) |")
    lines.append("")

# ============================================================
# SECTION 4: Summary stats
# ============================================================
lines.append("---")
lines.append("## 4. Summary Statistics")
lines.append("")

all_jp_count = sum(1 for _, gids in jp_strings for g in gids if g >= 96)
all_total_glyphs = sum(len(gids) for _, gids in jp_strings)
lines.append(f"- **Total Japanese-containing strings in scan range**: {len(jp_strings)}")
lines.append(f"- **Total glyph IDs in those strings**: {all_total_glyphs}")
lines.append(f"- **Total Japanese glyphs**: {all_jp_count}")
lines.append(f"- **Significant tables (3+ strings or 10+ JP)**: {len(sig_tables)}")
lines.append(f"- **Chargen area strings**: {len(chargen_strings)}")
lines.append(f"- **Menu area strings**: {len(menu_strings)}")
lines.append("")

# Offset ranges that need patching
lines.append("### Offset Ranges Requiring Patching")
lines.append("")
lines.append("| Area | Start | End | Bytes | Strings | Notes |")
lines.append("|------|-------|-----|-------|---------|-------|")
for t in sig_tables:
    # Guess the category based on content
    sample = decode_glyphs(t['strings'][0][1]) if t['strings'] else ''
    lines.append(f"| Table | 0x{t['start']:06X} | 0x{t['end']:06X} | {t['end']-t['start']} | {t['num_strings']} | `{sample[:30]}...` |")
lines.append("")

output = '\n'.join(lines)
with open(OUT_PATH, 'w', encoding='utf-8') as f:
    f.write(output)

print(f"Report written to {OUT_PATH}", file=sys.stderr)
print(f"Sig tables: {len(sig_tables)}, Chargen: {len(chargen_strings)}, Menu: {len(menu_strings)}", file=sys.stderr)
