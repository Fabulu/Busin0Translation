#!/usr/bin/env python3
"""
Scan EXE data section for remaining Japanese glyph ID clusters (v3).
Focus on true data sections, require high kanji density, filter code-like patterns.
"""
import json, struct, sys
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

EXE_PATH = "C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78"
GLYPH_MAP_PATH = "C:/Programmieren/wizardrytranslation/data/msg_glyph_map.json"
OUT_PATH = "C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/exe_glyph_scan.md"

# Known/handled regions to skip
SKIP_REGIONS = [
    (0x3C3000, 0x3C5300, "menu structs (already handled)"),
    (0x3C83C0, 0x3C93A0, "chargen grid (R38, already handled)"),
    (0x3C9DA0, 0x3C9DFC, "name entry tab IDs (Table 2E)"),
]

GLYPH_MAX = 881

def in_skip_region(offset):
    for start, end, _ in SKIP_REGIONS:
        if start <= offset < end:
            return True
    return False

def main():
    glyph_map = json.load(open(GLYPH_MAP_PATH, 'r', encoding='utf-8'))

    with open(EXE_PATH, 'rb') as f:
        exe_data = f.read()

    # Build set of known glyph IDs for fast lookup
    known_glyphs = set()
    for k in glyph_map:
        known_glyphs.add(int(k))
    # Add ASCII range (1-94)
    for i in range(1, 95):
        known_glyphs.add(i)
    known_glyphs.add(0)  # null/space

    def is_known_glyph(val):
        return val in known_glyphs

    def is_kanji(val):
        return 95 <= val <= GLYPH_MAX and str(val) in glyph_map

    def decode(val):
        if val == 0:
            return '\u00B7'  # middle dot for null
        if 1 <= val <= 94:
            return chr(val + 0x20)
        ch = glyph_map.get(str(val))
        return ch if ch else f'[?{val}]'

    # Scan approach: look for runs of uint16 where most values decode to known glyphs
    # Focus on data-heavy regions
    scan_ranges = [
        (0x3C0000, 0x3C3000, "pre-menu data"),
        (0x3C5300, 0x3C83C0, "mid-data (post-menu, pre-chargen)"),
        (0x3C93A0, 0x3C9DA0, "post-chargen data"),
        (0x3C9DFC, 0x3FD000, "late data section"),
        # Also scan code section but with stricter criteria
        (0x3B0000, 0x3C0000, "code/early data"),
    ]

    all_clusters = []

    for range_start, range_end, range_name in scan_ranges:
        is_code_region = "code" in range_name
        min_run = 5 if is_code_region else 4
        min_kanji = 3 if is_code_region else 2
        min_ratio = 0.5 if is_code_region else 0.3

        data = exe_data[range_start:range_end]
        data_len = len(data)

        i = 0
        while i < data_len - 1:
            file_off = range_start + i
            if in_skip_region(file_off):
                i += 2
                continue

            # Try to build a run of known glyphs
            run = []
            j = i
            while j < data_len - 1:
                val = struct.unpack_from('<H', data, j)[0]
                if is_known_glyph(val):
                    run.append((range_start + j, val))
                    j += 2
                else:
                    break

            if len(run) >= min_run:
                kanji_count = sum(1 for _, v in run if is_kanji(v))
                ratio = kanji_count / len(run)

                if kanji_count >= min_kanji and ratio >= min_ratio:
                    # Filter: skip if it looks like code (many repeated small values,
                    # or values that form arithmetic patterns)
                    vals = [v for _, v in run]
                    unique_ratio = len(set(vals)) / len(vals)

                    # Skip if too many zeros (likely struct padding)
                    zero_count = sum(1 for v in vals if v == 0)
                    if zero_count / len(vals) > 0.5:
                        i = j
                        continue

                    decoded = ''.join(decode(v) for _, v in run)
                    kanji_text = ''.join(decode(v) for _, v in run if is_kanji(v))

                    all_clusters.append({
                        'start': run[0][0],
                        'end': run[-1][0] + 2,
                        'size': run[-1][0] + 2 - run[0][0],
                        'count': len(run),
                        'kanji_count': kanji_count,
                        'ratio': ratio,
                        'decoded': decoded,
                        'kanji_text': kanji_text,
                        'range': range_name,
                        'vals': vals,
                    })

            i = max(i + 2, j)

    # Sort by offset
    all_clusters.sort(key=lambda c: c['start'])

    # Merge adjacent clusters (within 16 bytes)
    merged = []
    for cl in all_clusters:
        if merged and cl['start'] - merged[-1]['end'] <= 16:
            prev = merged[-1]
            # Merge: extend previous
            prev['end'] = cl['end']
            prev['size'] = prev['end'] - prev['start']
            prev['count'] += cl['count']
            prev['kanji_count'] += cl['kanji_count']
            prev['decoded'] += ' | ' + cl['decoded']
            prev['kanji_text'] += cl['kanji_text']
            prev['vals'].extend(cl['vals'])
        else:
            merged.append(dict(cl))

    print(f"Total clusters after merge: {len(merged)}")

    # Now classify and filter further
    # Remove clusters that are clearly just code constants
    final = []
    for cl in merged:
        # Skip very short clusters in code region unless they contain real words
        if 'code' in cl['range'] and cl['count'] < 8:
            # Only keep if the kanji text forms recognizable words
            kt = cl['kanji_text']
            if len(kt) < 3:
                continue
            # Check if any 2-char substring is a real word pattern
            has_word = False
            for word in ['攻撃', '防御', '魔法', '呪文', '装備', '道具', '戦闘',
                         '経験', 'レベル', '回復', '解除', '状態', '効果',
                         '仲間', '冒険', '迷宮', '宝箱', '武器', '防具',
                         'アイテム', 'ステータス', 'パーティ', 'セーブ', 'ロード',
                         '確認', '選択', '決定', 'キャンセル', '戻る',
                         '名前', '性別', '種族', '職業', '性格',
                         '善', '悪', '中立', '男', '女',
                         '人間', 'エルフ', 'ドワーフ', 'ノーム', 'ホビット',
                         '戦士', '魔術', '僧侶', '盗賊', '侍', '忍者', '君主', '司教',
                         '毒', '麻痺', '石化', '睡眠', '沈黙', '混乱', '死亡', '呪い',
                         '成功', '失敗', '発見', '罠', '鍵', '扉',
                         'ゴールド', 'ゴールド',]:
                if word in kt or word in cl['decoded']:
                    has_word = True
                    break
            if not has_word:
                continue

        purpose = classify(cl)
        cl['purpose'] = purpose
        cl['index'] = len(final)
        final.append(cl)

    print(f"After filtering: {len(final)}")

    for cl in final:
        trunc = cl['decoded'][:80]
        print(f"\n[{cl['index']:3d}] 0x{cl['start']:06X}-0x{cl['end']:06X} ({cl['count']}g/{cl['kanji_count']}k) [{cl['range']}]")
        print(f"      Purpose: {cl['purpose']}")
        print(f"      {trunc}")

    write_report(final)
    print(f"\nReport: {OUT_PATH}")


def classify(cl):
    text = cl['decoded']
    kt = cl['kanji_text']

    checks = [
        (['攻撃', '防御', '魔法', '呪文', '詠唱', '戦闘', '逃走', '行動'], 'Battle/combat'),
        (['毒', '麻痺', '石化', '睡眠', '沈黙', '混乱', '死亡', '呪い', '恐怖'], 'Status effects'),
        (['戦士', '魔術師', '僧侶', '盗賊', '侍', '忍者', '君主', '司教', '錬金術師', '召喚師', '修道'], 'Class names'),
        (['人間', 'エルフ', 'ドワーフ', 'ノーム', 'ホビット', 'フェルパー', 'ドラコン', 'リカント', '種族'], 'Race names'),
        (['力', '知恵', '信仰', '生命', '速さ', '運', '素早'], 'Stat labels'),
        (['善', '悪', '中立', '性格'], 'Alignment'),
        (['装備', '武器', '防具', '道具', '剣', '盾', '鎧', '兜', '杖', 'アイテム'], 'Equipment/items'),
        (['レベル', '経験', '経験値'], 'Level/XP'),
        (['名前', '性別', '男', '女'], 'Character creation'),
        (['はい', 'いいえ', '確認', 'キャンセル', '決定', '選択', '戻る'], 'UI labels'),
        (['迷宮', '階', '地下', 'ダンジョン', '宝箱', '罠', '鍵', '扉'], 'Dungeon'),
        (['セーブ', 'ロード', 'データ', 'メモリ'], 'Save/Load'),
        (['回復', '治療', '蘇生', '解除', '解毒'], 'Healing'),
        (['仲間', 'パーティ', '冒険', '酒場', '宿屋', '訓練', '寺院', '城'], 'Town/party'),
        (['ゴールド', '金貨', '所持金', '価格', '値段', '売', '買'], 'Gold/shop'),
    ]

    for patterns, label in checks:
        for p in patterns:
            if p in text or p in kt:
                return label

    if cl['count'] >= 20:
        return 'Long text (needs investigation)'
    if cl['count'] >= 8:
        return 'Medium text (needs investigation)'
    return 'Short text (needs investigation)'


def write_report(results):
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        f.write("# EXE Remaining Japanese Glyph Scan Results\n\n")
        f.write("**Date:** 2026-05-28\n")
        f.write("**Method:** Consecutive aligned LE uint16 glyph runs, kanji density >= 30-50%\n")
        f.write(f"**Total actionable clusters:** {len(results)}\n\n")

        f.write("## Skip Regions (already handled)\n\n")
        for start, end, desc in SKIP_REGIONS:
            f.write(f"- `0x{start:06X}`-`0x{end:06X}`: {desc}\n")
        f.write("\n---\n\n")

        # Group by purpose
        by_purpose = defaultdict(list)
        for r in results:
            by_purpose[r['purpose']].append(r)

        f.write("## Summary by Category\n\n")
        f.write("| Category | Count |\n")
        f.write("|----------|-------|\n")
        for cat in sorted(by_purpose.keys()):
            f.write(f"| {cat} | {len(by_purpose[cat])} |\n")
        f.write("\n---\n\n")

        # Detailed listing grouped by category
        for cat in sorted(by_purpose.keys()):
            items = by_purpose[cat]
            f.write(f"## {cat} ({len(items)} clusters)\n\n")
            for r in items:
                f.write(f"### [{r['index']}] `0x{r['start']:06X}`-`0x{r['end']:06X}`\n\n")
                f.write(f"- **Region:** {r['range']}\n")
                f.write(f"- **Glyphs:** {r['count']} total, {r['kanji_count']} kanji\n")
                f.write(f"- **Decoded:** `{r['decoded'][:120]}`\n")
                if len(r['decoded']) > 120:
                    f.write(f"- **Full text truncated** (total {len(r['decoded'])} chars)\n")
                f.write(f"- **Kanji only:** `{r['kanji_text'][:80]}`\n")
                f.write("\n")
            f.write("---\n\n")

        # Priority action items
        f.write("## Priority Action Items\n\n")
        high_priority = ['Battle/combat', 'Status effects', 'Class names', 'Race names',
                         'Stat labels', 'Alignment', 'Equipment/items', 'UI labels',
                         'Town/party', 'Gold/shop', 'Healing', 'Save/Load',
                         'Level/XP', 'Dungeon', 'Character creation']
        for cat in high_priority:
            if cat in by_purpose:
                f.write(f"- [ ] **{cat}**: {len(by_purpose[cat])} cluster(s) at ")
                f.write(', '.join(f"`0x{r['start']:06X}`" for r in by_purpose[cat][:5]))
                f.write("\n")

        needs_inv = [cat for cat in by_purpose if 'investigation' in cat]
        if needs_inv:
            f.write(f"\n### Needs Investigation\n\n")
            for cat in needs_inv:
                f.write(f"- {len(by_purpose[cat])} clusters of {cat}\n")


if __name__ == '__main__':
    main()
