# Resource 39 (0039_type15.bin) Inference Findings

## Resource Overview

- **File**: `extracted/packdata_resources/0039_type15.bin` (type15, 2462 bytes)
- **Structure**: 14 sequential table entries (224 bytes header), 97 messages in offset table, 94 decoded messages
- **Purpose**: Party management, equipment, and knight order menu system

## Content Analysis

Resource 39 contains the game's **camp/party management menu text**. Messages cover:

1. **Equipment operations** (msgs 2, 26, 28, 32, 46, 57, 74-78): equipping, swapping, and removing equipment
2. **Party formation** (msgs 34, 45, 47-49, 51): forming and disbanding party squads
3. **Item usage** (msgs 1, 11, 12, 18-20, 30-31, 50, 81-86): using items, checking inventory
4. **Recovery/healing** (msgs 15-16, 29): HP recovery status
5. **Knight order management** (msgs 53-64): changing knight order type
6. **Class names** (msgs 58-71): Japanese class names displayed during knight order changes
7. **Confirmation prompts** (msgs 8-10, 28, 56, 74, 87): yes/no confirmations
8. **Error messages** (msgs 22-23, 25-27, 29-31, 33, 51, 75-78): insufficient resources, restrictions
9. **Menu labels** (msgs 35-39): single-glyph labels, likely for UI elements

## MAJOR DISCOVERY: Complete Katakana Block (193-273)

The MSG resource katakana follow standard gojuuon order starting at glyph ID 193:

- **Basic katakana** (193-238): ア through ン, sequential
- **Dakuten katakana** (239-263): ガ through ポ, sequential  
- **Small katakana** (264-268+): ャ,ュ,ョ,ッ?,ィ, then ヴ at 273

**Verification**: 8 pre-existing mappings in msg_glyph_map.json (197=オ, 226=メ, 238=ン, 239=ガ, 249=ダ, 254=バ, 268=ィ, 273=ヴ) all match this pattern perfectly.

**Cross-validated game terms**:
- アイテム (Item): [193,194,211,225] - appears in 7+ messages
- アレイドアクション (Alleid Action): [193,234,194,253,193,200,204,266,238] - msg 24
- スペシャルパワー (Special Power): [205,262,204,264,233,259,236,93] - msg 27
- オートマタ (Automata): [197,93,212,223,208,93] - msg 52
- モンスター (Monster): [227,238,205,208,93] - msg 89
- キャラ (Character): [199,264,231] - msg 82

This discovery yields **38 new katakana mappings** on top of the 8 already known.

## Key Inferred Mappings (33 HIGH confidence kanji)

| Glyph ID | Character | Word Context | Evidence |
|----------|-----------|--------------|----------|
| 193 | ア | アイテム (item) | 4-glyph sequence [193][194][211][225] in 9 equipment msgs |
| 194 | イ | アイテム | Paired with 193 |
| 211 | テ | アイテム | Paired in sequence |
| 225 | ム | アイテム | Paired in sequence |
| 332 | 装 | 装備 (equip) | [332][602] in msgs 2, 26, 28 |
| 602 | 備 | 装備 | Paired with 332 |
| 346 | 侍 | 侍 (samurai) | Single-char class name in msgs 59, 62, 66 |
| 421 | 編 | 編隊 (formation) | [421]隊 in msgs 34, 45, 47-49, 51 |
| 621 | 解 | 解除 (cancel) | [621][351] in msgs 21, 42, 43, 52 |
| 351 | 除 | 解除 | Paired with 621 |
| 775 | 回 | 回復 (recover) | [775][428] in msgs 7, 15, 16, 29 |
| 428 | 復 | 回復 | Paired with 775 |
| 855 | 更 | 変更 (change) | 変[855] in 10 msgs about knight order change |
| 367 | 行 | 行う (carry out) | [367]いますか in msgs 47, 56 |
| 707 | 選 | 選ぶ (select) | [707]んで in msgs 48, 82, 83, 86, 88 |
| 709 | 必 | 必要 (necessary) | [709][710]な in msgs 25, 88 |
| 710 | 要 | 必要 | Paired with 709 |
| 712 | 足 | 足りません (insufficient) | [712]りません in msgs 22, 25, 51 |
| 728 | 入 | 入れ替える (swap/replace) | [728]れ[800]え in 6 msgs |
| 800 | 替 | 着替え | Paired with 728 |
| 737 | 決 | 決める (decide) | [737]めて in msg 53 |
| 543 | 仲 | 仲間 (companion) | [543][544] in msg 13 |
| 544 | 間 | 仲間 | Paired with 543 |
| 572 | 何 | 何も (nothing) | [572]も in msg 33 |
| 656 | 誰 | 誰 (who) | [656]が in msgs 47, 85 |
| 693 | 今 | 今すぐ (right now) | [693]すぐ in msg 50 |
| 508 | 部 | 部隊 (unit) | [508]隊 in msg 24 |
| 370 | 成 | 成功 (success) | [370][682] in msg 45 |
| 682 | 功 | 成功 | Paired with 370 |
| 854 | 組 | 組み合わせ (combination) | [854]み in msg 48 |
| 767 | 内 | 内容 (content) | [767][768] in msg 8 |
| 768 | 容 | 内容 | Paired with 767 |
| 287 | 者 | 者 (person) | msg 29 context |

## Additional Inferences (MEDIUM confidence)

| Glyph ID | Character | Context |
|----------|-----------|---------|
| 490 | 用 | 使用 (use) - msgs 50, 85 |
| 605 | 持 | 持てる (can hold) - msgs 6, 13 |
| 647 | 買 or 使 | 買う/使う - msgs 1, 19, 31, 50, 85 |
| 666 | 異 | 異なる (differ) - msg 77 |
| 668 | 持 | 持っている (have) - msg 33 |
| 708 | 択 | 選択 (selection) - msgs 82, 83 |
| 316 | 職 | 職業 (class) - msgs 76, 77 |
| 776 | 業 | 職業 | |
| 722 | 属 | 属性 (attribute) - msg 77 |
| 911 | 確 | 確認 (confirm) - msgs 81, 84 |
| 587 | 認 | 確認 | |
| 839 | 下 | 殿下 (Your Highness) - msg 4 |
| 507 | 増 | 増えた (increased) - msg 89 |
| 339 | 経 | 経験 (experience) - msg 89 |
| 959 | 験 | 経験 | |
| 908 | 残 | 残り (remaining) - msg 92 |
| 535 | 忍 | 忍者 (ninja) - msgs 60, 67 |

## Class Name Identifications (from msgs 58-71)

| Pattern | Chars | Likely Class |
|---------|-------|-------------|
| [45][40][48] | 3 glyphs | Unknown - possibly katakana class abbreviation |
| [346] | 1 glyph | 侍 (Samurai) - HIGH confidence |
| [535][717] | 2 glyphs | 忍者 (Ninja) - MEDIUM |
| [308][354][320] | 3 glyphs | Possibly 僧侶 or 修道僧 - LOW |
| [718][696][346] | 3 glyphs | Unknown compound with 侍 |
| [582][719][590] | 3 glyphs | Possibly 暗黒騎 (Dark Knight) - LOW |
| [720][721][590] | 3 glyphs | Possibly 聖騎士 (Paladin) - LOW |

## Unresolved Issues

1. **Low-range glyph IDs (0-92)**: IDs like 33, 37, 40, 45, 48, 50-53 appear in class name and stat contexts. Mapping is unclear.
2. **Duplicate kanji mappings**: Multiple glyph IDs for same character (e.g., 281=使 and 647=使) are expected due to multiple font size sheets.
3. **Knight order types (msgs 58-64)**: Only 侍 (Samurai/346) confidently identified among the 7 class options.
4. **Katakana system (RESOLVED)**: Complete block at 193-273 mapped. Low-range katakana (59=イ, 61=ゴ) may be from a different font size.
5. **Small katakana 267, 269-272**: Tentative ordering; only 264=ャ, 266=ョ, 268=ィ verified by word context.

## Output

- Inferred mappings: `data/inferred_r39.json`
- Decode script: `runs/CLAUDE-RUNS/RUN-20260522-1932-initial-recon/subagents/infer-r39/decode_r39.py`
