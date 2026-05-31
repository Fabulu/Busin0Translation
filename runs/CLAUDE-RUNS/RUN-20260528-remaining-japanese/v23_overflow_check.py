#!/usr/bin/env python3
"""Extract R38 from v23 ISO and check chargen textbox overflow."""
import struct, json, sys, os, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SECTOR = 2048
ISO_PATH = "C:/Programmieren/wizardrytranslation/build/BUSIN0_EN_v23.iso"
GLYPH_MAP_PATH = "C:/Programmieren/wizardrytranslation/data/msg_glyph_map.json"
TOC_ENTRIES = 2883
R38_INDEX = 38

with open(GLYPH_MAP_PATH, "r", encoding="utf-8") as f:
    gmap = json.load(f)

with open(ISO_PATH, "rb") as iso:
    iso.seek(16 * SECTOR)
    pvd = iso.read(SECTOR)
    root_lba = struct.unpack_from('<I', pvd, 158)[0]
    root_size = struct.unpack_from('<I', pvd, 166)[0]

    iso.seek(root_lba * SECTOR)
    root_dir = iso.read(root_size)
    pack_lba = None
    pos = 0
    while pos < len(root_dir):
        rec_len = root_dir[pos]
        if rec_len == 0:
            break
        name_len = root_dir[pos + 32]
        name = root_dir[pos + 33:pos + 33 + name_len].decode('ascii', errors='replace')
        file_lba = struct.unpack_from('<I', root_dir, pos + 2)[0]
        file_size = struct.unpack_from('<I', root_dir, pos + 10)[0]
        if 'PACKDATA' in name:
            pack_lba = file_lba
            pack_size = file_size
        pos += rec_len

    if pack_lba is None:
        print("ERROR: PACKDATA.DIG not found!")
        sys.exit(1)

    pack_offset = pack_lba * SECTOR

    iso.seek(pack_offset + R38_INDEX * 12)
    toc_entry = iso.read(12)
    r38_so, r38_sc, r38_tc = struct.unpack('<III', toc_entry)

    r38_abs = pack_offset + r38_so * SECTOR
    iso.seek(r38_abs)
    r38_raw = iso.read(r38_sc * SECTOR)

    _, h_payload_size, _, _ = struct.unpack_from('<IIII', r38_raw, 0)
    payload = r38_raw[16:16 + h_payload_size]

def count_seq(data):
    if len(data) < 16:
        return 0
    if struct.unpack_from("<I", data, 0)[0] != 1:
        return 0
    count = 0
    for e in range(min(256, len(data) // 16)):
        if struct.unpack_from("<I", data, e * 16)[0] == e + 1:
            count = e + 1
        else:
            break
    return count

seq_count = count_seq(payload)
seq_table_size = seq_count * 16
glyph_region = payload[seq_table_size:]

first_ffff = None
for off in range(0, len(glyph_region) - 1, 2):
    if struct.unpack_from(">H", glyph_region, off)[0] == 0xFFFF:
        first_ffff = off
        break

stream = glyph_region[first_ffff:]
n = len(stream) // 2
vals = struct.unpack(f">{n}H", stream[:n*2])

messages = []
cur_glyphs = []
for v in vals:
    if v == 0xFFFF:
        if cur_glyphs:
            messages.append(cur_glyphs)
        cur_glyphs = []
    elif v == 0xFFFE:
        cur_glyphs.append(('LF', v))
    elif v == 0xFFD2:
        cur_glyphs.append(('PAGE', v))
    elif v >= 0xFFC0:
        cur_glyphs.append(('CTRL', v))
    else:
        cur_glyphs.append(('GLYPH', v))
if cur_glyphs:
    messages.append(cur_glyphs)

print(f"Total messages: {len(messages)}")

def decode_glyph(gid):
    ch = gmap.get(str(gid))
    if ch:
        return ch
    if 0 <= gid <= 94:
        return chr(gid + 0x20)
    return f"[{gid}]"

def analyze_message(glyphs):
    lines = [[]]
    text_parts = []
    lf_count = 0
    for typ, val in glyphs:
        if typ == 'LF':
            lines.append([])
            text_parts.append('\n')
            lf_count += 1
        elif typ == 'PAGE':
            lines.append([])
            text_parts.append('[PAGE]')
        elif typ == 'GLYPH':
            ch = decode_glyph(val)
            lines[-1].append(ch)
            text_parts.append(ch)
        elif typ == 'CTRL':
            text_parts.append(f'[{val:04X}]')

    line_lengths = [len(l) for l in lines]
    decoded = ''.join(text_parts)
    return decoded, line_lengths, lf_count

race_expected = {29: ("Human", 5), 30: ("Elf", 3), 31: ("Gnome", 5), 32: ("Dwarf", 5), 33: ("Hobbit", 6), 34: ("Automata", 8)}

print("\n=== RACE NAMES (MSG 29-34) ===")
race_issues = []
for idx in range(29, 35):
    if idx >= len(messages):
        print(f"  MSG {idx}: OUT OF RANGE")
        continue
    decoded, line_lengths, lf_count = analyze_message(messages[idx])
    total_glyphs = sum(line_lengths)
    expected_name, expected_len = race_expected.get(idx, ("?", 0))
    clean = decoded.replace('\n', ' ').strip()
    print(f"  MSG {idx} ({expected_name}): '{clean}' glyphs={total_glyphs} lines={len(line_lengths)} line_lengths={line_lengths}")
    if total_glyphs > 10:
        race_issues.append((idx, clean, f"LONG ({total_glyphs} glyphs)"))

print("\n=== PERSONALITY/RACE/CLASS DESCRIPTIONS (MSG 87-148) ===")
desc_issues = []
MAX_CHARS = 20

for idx in range(87, min(149, len(messages))):
    decoded, line_lengths, lf_count = analyze_message(messages[idx])
    clean = decoded.replace('\n', '|')

    problems = []
    if lf_count > 3:
        problems.append(f"TOO MANY LINES ({lf_count} breaks = {lf_count+1} lines)")
    elif lf_count > 2:
        problems.append(f"4 LINES ({lf_count} breaks)")

    for li, ll in enumerate(line_lengths):
        if ll > MAX_CHARS:
            problems.append(f"LINE {li+1} overflow ({ll} chars > {MAX_CHARS})")

    status = "FAIL" if problems else "OK"
    if problems:
        desc_issues.append((idx, clean, problems, line_lengths, lf_count))

    print(f"  MSG {idx} [{status}]: breaks={lf_count} lines={line_lengths} '{clean}'")
    if problems:
        for p in problems:
            print(f"    *** {p}")

print(f"\n=== SUMMARY ===")
print(f"Description messages checked: {min(149, len(messages)) - 87}")
print(f"Description overflow issues: {len(desc_issues)}")
print(f"Race name issues: {len(race_issues)}")

OUTPUT_PATH = "C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/v23_overflow_check.md"
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

with open(OUTPUT_PATH, "w", encoding="utf-8") as out:
    out.write("# v23 R38 Chargen Textbox Overflow Check\n\n")
    out.write(f"**Source:** `{ISO_PATH}`\n")
    out.write(f"**Date:** 2026-05-28\n\n")
    out.write("## Constraints\n\n")
    out.write("- Chargen description textbox: **3 lines** (max 2 FFFE line breaks)\n")
    out.write("- Max glyphs per line: **~20** (fullwidth glyphs)\n\n")

    out.write("## Race Names (MSG 29-34)\n\n")
    out.write("| MSG | Expected | Decoded | Glyphs | Status |\n")
    out.write("|-----|----------|---------|--------|--------|\n")
    for idx in range(29, 35):
        if idx >= len(messages):
            continue
        decoded, line_lengths, lf_count = analyze_message(messages[idx])
        clean = decoded.replace('\n', ' ').strip()
        expected_name = race_expected.get(idx, ("?", 0))[0]
        total = sum(line_lengths)
        status = "OK" if total <= 10 else "WARN"
        out.write(f"| {idx} | {expected_name} | `{clean}` | {total} | {status} |\n")

    out.write("\n## Description Messages (MSG 87-148)\n\n")

    if desc_issues:
        out.write(f"### Overflow Issues ({len(desc_issues)} found)\n\n")
        out.write("| MSG | Lines | Line Lengths | Problem | Text |\n")
        out.write("|-----|-------|-------------|---------|------|\n")
        for idx, text, problems, ll, lf in desc_issues:
            prob_str = "; ".join(problems)
            out.write(f"| {idx} | {lf+1} | {ll} | {prob_str} | `{text}` |\n")
    else:
        out.write("**No overflow issues found.**\n")

    out.write(f"\n### All Descriptions Detail\n\n")
    out.write("| MSG | Breaks | Lines | Max Line | Text |\n")
    out.write("|-----|--------|-------|----------|------|\n")
    for idx in range(87, min(149, len(messages))):
        decoded, line_lengths, lf_count = analyze_message(messages[idx])
        clean = decoded.replace('\n', '|')
        max_line = max(line_lengths) if line_lengths else 0
        flag = ""
        if lf_count > 2:
            flag = " **OVERFLOW**"
        elif max_line > 20:
            flag = " **WIDE**"
        out.write(f"| {idx} | {lf_count} | {lf_count+1} | {max_line} | `{clean}`{flag} |\n")

    out.write(f"\n## Summary\n\n")
    out.write(f"- Messages checked: {min(149, len(messages)) - 87}\n")
    out.write(f"- Overflow issues: {len(desc_issues)}\n")
    out.write(f"- Race name issues: {len(race_issues)}\n")

    if not desc_issues and not race_issues:
        out.write(f"\n**All R38 chargen descriptions fit within the 3-line textbox.**\n")

print(f"\nOutput written to: {OUTPUT_PATH}")
