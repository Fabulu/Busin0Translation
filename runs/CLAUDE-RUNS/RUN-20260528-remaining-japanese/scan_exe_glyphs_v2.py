#!/usr/bin/env python3
"""
Scan EXE data section for remaining Japanese glyph ID clusters (v2).
Tighter criteria: consecutive aligned uint16 values, high density.
"""
import json, struct, sys

sys.stdout.reconfigure(encoding='utf-8')

EXE_PATH = "C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78"
GLYPH_MAP_PATH = "C:/Programmieren/wizardrytranslation/data/msg_glyph_map.json"
OUT_PATH = "C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/exe_glyph_scan.md"

SCAN_START = 0x3B0000
SCAN_END   = 0x3FD000

# Known/handled regions to skip
SKIP_REGIONS = [
    (0x3C3000, 0x3C5300, "menu structs (already handled)"),
    (0x3C83C0, 0x3C93A0, "chargen grid (R38, already handled)"),
    (0x3C9DA0, 0x3C9DFC, "name entry tab IDs (Table 2E)"),
]

# Valid glyph range (0=space through 881)
GLYPH_MAX = 881

def in_skip_region(offset):
    for start, end, _ in SKIP_REGIONS:
        if start <= offset < end:
            return True
    return False

def is_text_glyph(val):
    """Check if a uint16 value looks like a valid text glyph ID."""
    return 0 <= val <= GLYPH_MAX

def is_kanji_glyph(val):
    """Check if a uint16 value is in the Japanese kanji range."""
    return 95 <= val <= GLYPH_MAX

def decode_glyph(val, glyph_map):
    """Decode a glyph ID to a character."""
    if val == 0:
        return ' '  # space/null
    if 1 <= val <= 94:
        return chr(val + 0x20)  # ASCII
    ch = glyph_map.get(str(val))
    if ch:
        return ch
    return f'[?{val}]'

def main():
    glyph_map = json.load(open(GLYPH_MAP_PATH, 'r', encoding='utf-8'))

    with open(EXE_PATH, 'rb') as f:
        exe_data = f.read()

    scan_data = exe_data[SCAN_START:SCAN_END]
    scan_len = len(scan_data)

    # Strategy: scan for runs of consecutive aligned uint16 values that are
    # valid glyph IDs (0-881), where at least some are kanji (95-881).
    # A "text string" should be mostly valid glyphs with few gaps.

    MIN_RUN_LEN = 4       # minimum consecutive valid glyph uint16s
    MIN_KANJI_COUNT = 2   # minimum kanji glyphs in a run
    MIN_KANJI_RATIO = 0.3 # at least 30% of glyphs should be kanji

    clusters = []

    i = 0
    while i < scan_len - 1:
        file_off = SCAN_START + i
        if in_skip_region(file_off):
            i += 2
            continue

        # Try to start a run of valid glyph IDs
        run_start = i
        run_vals = []
        j = i
        while j < scan_len - 1:
            val = struct.unpack_from('<H', scan_data, j)[0]
            if is_text_glyph(val):
                run_vals.append((SCAN_START + j, val))
                j += 2
            else:
                break

        run_len = len(run_vals)
        if run_len >= MIN_RUN_LEN:
            kanji_count = sum(1 for _, v in run_vals if is_kanji_glyph(v))
            kanji_ratio = kanji_count / run_len if run_len > 0 else 0

            if kanji_count >= MIN_KANJI_COUNT and kanji_ratio >= MIN_KANJI_RATIO:
                # Check it's not in a skip region
                start_off = run_vals[0][0]
                end_off = run_vals[-1][0] + 2
                if not in_skip_region(start_off):
                    clusters.append({
                        'vals': run_vals,
                        'kanji_count': kanji_count,
                        'kanji_ratio': kanji_ratio,
                    })

        i = max(i + 2, j)

    print(f"Clusters found: {len(clusters)}")

    # Merge clusters that are close together (within 8 bytes)
    # and decode
    results = []
    for ci, cl in enumerate(clusters):
        vals = cl['vals']
        start_off = vals[0][0]
        end_off = vals[-1][0] + 2

        decoded = ''.join(decode_glyph(v, glyph_map) for _, v in vals)
        kanji_only = ''.join(decode_glyph(v, glyph_map) for _, v in vals if is_kanji_glyph(v))

        # Raw hex for context
        raw = exe_data[start_off:end_off]
        hex_str = raw.hex(' ')

        purpose = guess_purpose(start_off, end_off, decoded, vals)

        results.append({
            'index': ci,
            'start': start_off,
            'end': end_off,
            'size': end_off - start_off,
            'glyph_count': len(vals),
            'kanji_count': cl['kanji_count'],
            'decoded': decoded,
            'kanji_only': kanji_only,
            'hex': hex_str,
            'purpose': purpose,
        })

    # Sort by offset
    results.sort(key=lambda r: r['start'])

    # Re-index
    for i, r in enumerate(results):
        r['index'] = i

    # Print summary
    for r in results:
        print(f"\n[{r['index']:3d}] 0x{r['start']:06X}-0x{r['end']:06X} ({r['glyph_count']}g/{r['kanji_count']}k) {r['purpose']}")
        print(f"      {r['decoded'][:80]}")

    write_report(results, glyph_map)
    print(f"\n\nReport written to {OUT_PATH}")
    print(f"Total clusters: {len(results)}")


def guess_purpose(start, end, text, vals):
    """Classify cluster purpose by content and location."""
    # Location-based hints
    if 0x3B0000 <= start < 0x3C0000:
        loc = "code/early-data"
    elif 0x3C0000 <= start < 0x3C3000:
        loc = "pre-menu-data"
    elif 0x3C5300 <= start < 0x3C8000:
        loc = "mid-data"
    elif 0x3C9400 <= start < 0x3CA000:
        loc = "post-chargen"
    elif 0x3CA000 <= start:
        loc = "late-data"
    else:
        loc = "data"

    # Content-based classification
    for pattern, label in [
        ('攻撃', 'Battle label'), ('防御', 'Battle label'), ('魔法', 'Magic label'),
        ('呪文', 'Spell label'), ('詠唱', 'Cast label'),
        ('毒', 'Status effect'), ('麻痺', 'Status effect'), ('石化', 'Status effect'),
        ('睡眠', 'Status effect'), ('沈黙', 'Status effect'), ('混乱', 'Status effect'),
        ('死亡', 'Status effect'), ('呪い', 'Status effect'),
        ('戦士', 'Class name'), ('魔術師', 'Class name'), ('僧侶', 'Class name'),
        ('盗賊', 'Class name'), ('侍', 'Class name'), ('忍者', 'Class name'),
        ('君主', 'Class name'), ('司教', 'Class name'), ('錬金', 'Class name'),
        ('人間', 'Race name'), ('エルフ', 'Race name'), ('ドワーフ', 'Race name'),
        ('ノーム', 'Race name'), ('ホビット', 'Race name'), ('フェルパー', 'Race name'),
        ('ドラコン', 'Race name'), ('リカント', 'Race name'),
        ('力', 'Stat'), ('知恵', 'Stat'), ('信仰', 'Stat'), ('生命', 'Stat'),
        ('速さ', 'Stat'), ('運', 'Stat'),
        ('善', 'Alignment'), ('悪', 'Alignment'), ('中立', 'Alignment'),
        ('はい', 'UI label'), ('いいえ', 'UI label'),
        ('装備', 'Equipment'), ('武器', 'Equipment'), ('防具', 'Equipment'),
        ('道具', 'Item'), ('薬', 'Item'), ('巻物', 'Item'),
        ('迷宮', 'Dungeon'), ('階', 'Dungeon/floor'),
        ('レベル', 'Level label'), ('経験', 'XP label'),
    ]:
        if pattern in text:
            return f"{label} ({loc})"

    # Length-based hints
    glyph_count = len(vals)
    if glyph_count >= 20:
        return f"Long text string ({loc})"
    if glyph_count >= 8:
        return f"Medium text ({loc})"

    return f"Short text ({loc})"


def write_report(results, glyph_map):
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        f.write("# EXE Remaining Japanese Glyph Scan Results\n\n")
        f.write(f"**Date:** 2026-05-28\n")
        f.write(f"**Scan range:** 0x{SCAN_START:06X} - 0x{SCAN_END:06X}\n")
        f.write(f"**Method:** Consecutive aligned LE uint16 runs with >= 30% kanji density\n")
        f.write(f"**Total clusters found:** {len(results)}\n\n")

        f.write("## Skip regions (already handled)\n\n")
        for start, end, desc in SKIP_REGIONS:
            f.write(f"- 0x{start:06X}-0x{end:06X}: {desc}\n")
        f.write("\n")

        # Group by purpose category
        by_purpose = {}
        for r in results:
            cat = r['purpose'].split('(')[0].strip()
            by_purpose.setdefault(cat, []).append(r)

        f.write("## Summary by Category\n\n")
        f.write("| Category | Count | Offsets |\n")
        f.write("|----------|-------|--------|\n")
        for cat in sorted(by_purpose.keys()):
            items = by_purpose[cat]
            offsets = ', '.join(f"0x{r['start']:06X}" for r in items[:5])
            if len(items) > 5:
                offsets += f" (+{len(items)-5} more)"
            f.write(f"| {cat} | {len(items)} | {offsets} |\n")
        f.write("\n")

        f.write("## All Clusters\n\n")
        for r in results:
            f.write(f"### [{r['index']}] 0x{r['start']:06X}-0x{r['end']:06X}\n\n")
            f.write(f"- **Size:** {r['size']} bytes, {r['glyph_count']} glyphs ({r['kanji_count']} kanji)\n")
            f.write(f"- **Decoded:** `{r['decoded']}`\n")
            f.write(f"- **Purpose:** {r['purpose']}\n")
            f.write(f"- **Hex:** `{r['hex'][:80]}`\n")
            f.write("\n")

        # Action items
        f.write("## Action Items\n\n")
        f.write("Clusters that likely need English replacement:\n\n")
        action_cats = ['Battle label', 'Status effect', 'Class name', 'Race name',
                       'Stat', 'Alignment', 'UI label', 'Equipment', 'Item',
                       'Spell label', 'Magic label', 'Cast label', 'Level label',
                       'XP label', 'Dungeon', 'Long text string', 'Medium text']
        for cat in action_cats:
            if cat in by_purpose:
                items = by_purpose[cat]
                f.write(f"### {cat} ({len(items)} clusters)\n\n")
                for r in items:
                    f.write(f"- 0x{r['start']:06X}: `{r['decoded'][:60]}`\n")
                f.write("\n")


if __name__ == '__main__':
    main()
