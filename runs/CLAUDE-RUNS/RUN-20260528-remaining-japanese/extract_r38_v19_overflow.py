#!/usr/bin/env python3
"""
Extract R38 from v19 ISO and decode EVERY message with overflow analysis.
Focus on line counts, max line lengths, and description overflow (MSG 87-148).
"""
import struct, json, sys, os, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SECTOR = 2048
ISO_PATH = "C:/Programmieren/wizardrytranslation/build/BUSIN0_EN_v19.iso"
GLYPH_MAP_PATH = "C:/Programmieren/wizardrytranslation/data/msg_glyph_map.json"
OUTPUT_PATH = "C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/v19_r38_overflow_check.md"
TOC_ENTRIES = 2883
R38_INDEX = 38

# Load glyph map
with open(GLYPH_MAP_PATH, "r", encoding="utf-8") as f:
    raw_map = json.load(f)
glyph_map = {int(k): v for k, v in raw_map.items()}

def glyph_to_char(gid):
    if 0 <= gid <= 94:
        return chr(gid + 0x20)
    if gid in glyph_map:
        return glyph_map[gid]
    return f"[{gid}]"

def is_japanese_char(ch):
    cp = ord(ch)
    return (0x3040 <= cp <= 0x309F or 0x30A0 <= cp <= 0x30FF or
            0x4E00 <= cp <= 0x9FFF or 0xFF00 <= cp <= 0xFFEF)

# Open ISO and extract R38
with open(ISO_PATH, "rb") as f:
    # PVD
    f.seek(16 * SECTOR)
    pvd = f.read(SECTOR)
    root_rec = pvd[156:156+34]
    root_extent = struct.unpack_from('<I', root_rec, 2)[0]
    root_size = struct.unpack_from('<I', root_rec, 10)[0]

    # Find PACKDATA.DIG
    f.seek(root_extent * SECTOR)
    root_data = f.read(root_size)
    packdata_extent = None
    pos = 0
    while pos < len(root_data):
        rec_len = root_data[pos]
        if rec_len == 0:
            break
        name_len = root_data[pos + 32]
        name = root_data[pos + 33: pos + 33 + name_len]
        if b'PACKDATA' in name:
            packdata_extent = struct.unpack_from('<I', root_data, pos + 2)[0]
            break
        pos += rec_len

    if packdata_extent is None:
        print("ERROR: PACKDATA.DIG not found")
        sys.exit(1)

    packdata_base = packdata_extent * SECTOR
    print(f"PACKDATA.DIG at LBA {packdata_extent}")

    # TOC entry for R38
    f.seek(packdata_base + R38_INDEX * 12)
    toc_data = f.read(12)
    sector_offset, sector_count, type_code = struct.unpack('<III', toc_data)
    abs_offset = packdata_base + sector_offset * SECTOR
    print(f"R38: sector_off=0x{sector_offset:X}, sectors={sector_count}, type={type_code}")

    # Sub-header
    f.seek(abs_offset)
    sub_header = f.read(16)
    z1, payload_size, stride, z2 = struct.unpack('<IIII', sub_header)
    print(f"Payload size: {payload_size}")

    payload = f.read(payload_size)

# Parse BE uint16 stream
glyphs = []
for i in range(0, len(payload) - 1, 2):
    glyphs.append(struct.unpack_from('>H', payload, i)[0])

# Split at FFFF
messages = []
current_msg = []
for g in glyphs:
    if g == 0xFFFF:
        messages.append(current_msg)
        current_msg = []
    else:
        current_msg.append(g)
if current_msg:
    messages.append(current_msg)

print(f"Total messages: {len(messages)}")

# Decode and analyze each message
results = []
for idx, msg in enumerate(messages):
    lines = [""]  # current lines being built
    decoded_full = []
    has_jp = False
    jp_glyphs = []
    unmapped = []
    ctrl_codes = []

    for g in msg:
        if g == 0xFFFE:
            lines.append("")
            decoded_full.append("\\n")
        elif g == 0xFFD2:
            lines.append("")  # page break = new line too
            decoded_full.append("[PAGE]")
        elif 0xFFC0 <= g <= 0xFFFD:
            ctrl_codes.append(g)
            decoded_full.append(f"[{g:04X}]")
        else:
            ch = glyph_to_char(g)
            lines[-1] += ch
            decoded_full.append(ch)
            if g >= 95:
                for c in ch:
                    if is_japanese_char(c):
                        has_jp = True
                        jp_glyphs.append((g, ch))
                        break
            if ch.startswith("[") and ch.endswith("]") and g >= 95:
                unmapped.append(g)

    text = "".join(decoded_full)
    line_count = len(lines)
    line_lengths = [len(l) for l in lines]
    max_line_len = max(line_lengths) if line_lengths else 0

    # For Japanese chars, each kanji occupies ~2 glyph widths in the game
    # but in our glyph system they're single glyphs, so count them as-is
    # The game renders with fixed-width tiles, so count = visual width

    results.append({
        'idx': idx,
        'text': text,
        'lines': lines,
        'line_count': line_count,
        'line_lengths': line_lengths,
        'max_line_len': max_line_len,
        'has_jp': has_jp,
        'jp_glyphs': jp_glyphs,
        'unmapped': unmapped,
        'ctrl_codes': ctrl_codes,
        'raw': msg,
    })

# Write output
with open(OUTPUT_PATH, "w", encoding="utf-8") as out:
    out.write("# R38 v19 ISO - Complete Overflow Check\n\n")
    out.write(f"**Source:** `{ISO_PATH}`\n")
    out.write(f"**Total messages:** {len(results)}\n")
    out.write(f"**Date:** 2026-05-28\n\n")

    # ======== OVERFLOW FLAGS SUMMARY ========
    overflow_msgs = [r for r in results if r['line_count'] > 3 or r['max_line_len'] > 18]
    out.write(f"## Overflow Flags Summary\n\n")
    out.write(f"Messages with >3 lines OR any line >18 chars: **{len(overflow_msgs)}**\n\n")

    if overflow_msgs:
        out.write("| MSG | Lines | Max Line Len | Longest Line Content | Flag |\n")
        out.write("|-----|-------|-------------|---------------------|------|\n")
        for r in overflow_msgs:
            flags = []
            if r['line_count'] > 3:
                flags.append(f"LINES={r['line_count']}")
            for i, ll in enumerate(r['line_lengths']):
                if ll > 18:
                    flags.append(f"L{i+1}={ll}ch")
            longest_line = r['lines'][r['line_lengths'].index(r['max_line_len'])] if r['lines'] else ""
            longest_esc = longest_line.replace("|", "\\|")[:50]
            flag_str = ", ".join(flags)
            out.write(f"| {r['idx']} | {r['line_count']} | {r['max_line_len']} | `{longest_esc}` | {flag_str} |\n")

    # ======== DESCRIPTIONS (MSG 87-148) DETAIL ========
    out.write(f"\n## Descriptions (MSG 87-148) - Chargen Display Detail\n\n")
    out.write("These are shown in the character generation description box.\n")
    out.write("Overflow risk: >3 lines or any line >18 chars.\n\n")

    for r in results:
        if 87 <= r['idx'] <= 148:
            flags = []
            if r['line_count'] > 3:
                flags.append("**TOO MANY LINES**")
            for i, ll in enumerate(r['line_lengths']):
                if ll > 18:
                    flags.append(f"**LINE {i+1} TOO LONG ({ll} chars)**")
            if r['has_jp']:
                flags.append("JAPANESE")
            if r['unmapped']:
                flags.append(f"UNMAPPED:{r['unmapped']}")

            flag_str = " | ".join(flags) if flags else "OK"
            out.write(f"### MSG {r['idx']} [{flag_str}]\n")
            out.write(f"- Lines: {r['line_count']}, Max line: {r['max_line_len']} chars\n")
            for i, line in enumerate(r['lines']):
                marker = " **<<OVERFLOW**" if len(line) > 18 else ""
                out.write(f"- L{i+1} ({len(line):2d} ch): `{line}`{marker}\n")
            out.write(f"- Raw: `{' '.join(f'{g:04X}' for g in r['raw'][:40])}`{'...' if len(r['raw'])>40 else ''}\n\n")

    # ======== COMPLETE MESSAGE DUMP ========
    out.write(f"\n## Complete Message Dump (All {len(results)} Messages)\n\n")

    # Sections
    sections = [
        ("MSG 0: Empty/Header", 0, 0),
        ("Stat Labels (MSG 1-7)", 1, 7),
        ("Field Labels (MSG 8-16)", 8, 16),
        ("Other Labels (MSG 17-26)", 17, 26),
        ("Gender (MSG 27-28)", 27, 28),
        ("Race Names (MSG 29-34)", 29, 34),
        ("Class Names (MSG 35-52)", 35, 52),
        ("Personality Traits (MSG 53-86)", 53, 86),
        ("Descriptions (MSG 87-148)", 87, 148),
        ("Other (MSG 149+)", 149, 999),
    ]

    for section_name, start, end in sections:
        section_msgs = [r for r in results if start <= r['idx'] <= end]
        if not section_msgs:
            continue
        out.write(f"\n### {section_name}\n\n")
        out.write("| MSG | Lines | MaxLen | Text | Flags |\n")
        out.write("|-----|-------|--------|------|-------|\n")
        for r in section_msgs:
            flags = []
            if r['line_count'] > 3:
                flags.append(f"LINES={r['line_count']}")
            if r['max_line_len'] > 18:
                flags.append(f"WIDE={r['max_line_len']}")
            if r['has_jp']:
                flags.append("JP")
            if r['unmapped']:
                flags.append("UNMAP")
            flag_str = ", ".join(flags) if flags else "ok"
            text_esc = r['text'].replace("|", "\\|")[:80]
            out.write(f"| {r['idx']} | {r['line_count']} | {r['max_line_len']} | `{text_esc}` | {flag_str} |\n")

    # ======== RAW GLYPH IDS ========
    out.write(f"\n## Raw Glyph IDs\n\n")
    out.write("```\n")
    for r in results:
        raw_ids = [g for g in r['raw'] if g < 0xFFC0]  # exclude control codes
        line_breaks = [i for i, g in enumerate(r['raw']) if g == 0xFFFE]
        extra = f"  LF@{line_breaks}" if line_breaks else ""
        out.write(f"MSG {r['idx']:3d} ({r['line_count']}L, max{r['max_line_len']:2d}): {raw_ids}{extra}\n")
    out.write("```\n")

    # ======== Japanese remaining ========
    jp_msgs = [r for r in results if r['has_jp']]
    out.write(f"\n## Messages Still Containing Japanese ({len(jp_msgs)})\n\n")
    if jp_msgs:
        out.write("| MSG | Text | JP Glyphs |\n")
        out.write("|-----|------|-----------|\n")
        for r in jp_msgs:
            text_esc = r['text'].replace("|", "\\|")[:60]
            jp_detail = ", ".join(f"{g}={ch}" for g, ch in r['jp_glyphs'][:10])
            out.write(f"| {r['idx']} | `{text_esc}` | {jp_detail} |\n")
    else:
        out.write("None - all messages are English!\n")

    # ======== Unmapped glyphs ========
    unmap_msgs = [r for r in results if r['unmapped']]
    out.write(f"\n## Messages with Unmapped Glyphs ({len(unmap_msgs)})\n\n")
    if unmap_msgs:
        out.write("| MSG | Text | Unmapped IDs |\n")
        out.write("|-----|------|--------------|\n")
        for r in unmap_msgs:
            text_esc = r['text'].replace("|", "\\|")[:60]
            out.write(f"| {r['idx']} | `{text_esc}` | {r['unmapped']} |\n")
    else:
        out.write("None - all glyphs mapped!\n")

print(f"\nOutput written to: {OUTPUT_PATH}")

# Also print summary to console
print(f"\n{'='*70}")
print(f"OVERFLOW SUMMARY")
print(f"{'='*70}")
print(f"Total messages: {len(results)}")
print(f"Messages with >3 lines: {sum(1 for r in results if r['line_count'] > 3)}")
print(f"Messages with line >18 chars: {sum(1 for r in results if r['max_line_len'] > 18)}")
print(f"Messages with Japanese: {sum(1 for r in results if r['has_jp'])}")
print(f"Messages with unmapped glyphs: {sum(1 for r in results if r['unmapped'])}")

print(f"\n--- OVERFLOW FLAGS (>3 lines or >18 char line) ---")
for r in results:
    if r['line_count'] > 3 or r['max_line_len'] > 18:
        flags = []
        if r['line_count'] > 3:
            flags.append(f"LINES={r['line_count']}")
        for i, ll in enumerate(r['line_lengths']):
            if ll > 18:
                flags.append(f"L{i+1}={ll}ch")
        print(f"  MSG {r['idx']:3d}: {', '.join(flags)} | {r['text'][:60]}")

print(f"\n--- DESCRIPTIONS 87-148 DETAIL ---")
for r in results:
    if 87 <= r['idx'] <= 148:
        marker = ""
        if r['line_count'] > 3:
            marker += " [TOO MANY LINES]"
        if r['max_line_len'] > 18:
            marker += " [LINE TOO LONG]"
        if r['has_jp']:
            marker += " [JP]"
        print(f"  MSG {r['idx']:3d} ({r['line_count']}L, max={r['max_line_len']:2d}ch){marker}: {r['text'][:70]}")
