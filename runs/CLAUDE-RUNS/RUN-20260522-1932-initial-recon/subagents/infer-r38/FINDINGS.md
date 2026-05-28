# Resource 0038 Inference Findings

## Resource Overview
- **File**: `extracted/packdata_resources/0038_type01.bin` (7512 bytes)
- **Content**: Character creation, class descriptions, personality traits, alignment system
- **Messages**: 260 total, 2930 glyphs
- **Pre-existing coverage**: 156 confirmed mappings in `msg_glyph_map.json`

## Major Discoveries

### 1. Complete Katakana Grid (193-272) -- 80 new mappings
The single biggest discovery: the katakana syllabary is laid out sequentially starting at glyph 193.

| Range | Content | Count |
|-------|---------|-------|
| 193-237 | Basic katakana (ア-ヲ) | 45 |
| 238 | ン (already confirmed) | -- |
| 239-258 | Dakuten katakana (ガ-ボ) | 20 |
| 259-263 | Handakuten katakana (パ-ポ) | 5 |
| 264-272 | Small katakana (ャュョァィゥェォッ) | 9 |
| 273 | ヴ (already confirmed) | -- |

**Verification words decoded**:
- エコロジスト (Ecologist) = 196,202,235,245,205,212
- エコノミスト (Economist) = 196,202,217,224,205,212
- ナルシスト (Narcissist) = 213,233,204,205,212
- ドワーフ (Dwarf) = 253,236,93,220
- ノーム (Gnome) = 217,93,225
- ホビット (Hobbit) = 222,255,272,212
- アイテム (Item) = 193,194,211,225
- ディスペル (Dispel) = 252,268,205,262,233
- ダークゾーン (Dark Zone) = 249,93,200,248,93,238
- パーティ (Party) = 259,93,211,268
- モンク (Monk class) = 227,238,200
- トラップ (Trap) = 212,231,272,261

### 2. Latin Lowercase Grid (33-58) -- 26 new mappings
Lowercase letters a-z mapped sequentially: glyph = (letter position) + 32.

**Verification**: Messages 230-259 contain English reputation tier names that decode perfectly:
- commoner, hooligan, evil, venom fang, villain, gangster, hero, sage, god hand, etc.

### 3. Fullwidth Digits (17-23) -- 6 new mappings
Sequential fullwidth digits １-７ anchored on confirmed 18=２.
Used in level labels: Lv１ through Lv７.

### 4. Alignment System Kanji -- 4 new mappings
| Glyph | Char | Word |
|-------|------|------|
| 520 | 善 | Good alignment |
| 337 | 中 | Neutral (中立) |
| 340 | 立 | Neutral (中立) |
| 289 | 悪 | Evil alignment |

### 5. Game Vocabulary Kanji -- 8 new mappings
| Glyph | Char | Context | Confidence |
|-------|------|---------|------------|
| 286 | 戦 | 戦士 (Fighter class) | HIGH |
| 287 | 者 | Person/one-who (16 occurrences) | HIGH |
| 297 | 士 | 戦士, class names ending in 士 | HIGH |
| 401 | 侍 | Samurai class (standalone) | HIGH |
| 718 | 生 | 生きがい, 生まれつき | HIGH |
| 91 | ・ | List separator (26 occ) | HIGH |
| 610 | 思 | 思っている (thinking) | MEDIUM |
| 618 | 考 | 考え (thoughts) | MEDIUM |

### 6. Additional Medium-Confidence Kanji -- 5 mappings
| Glyph | Char | Context |
|-------|------|---------|
| 700 | 能 | 能力 (ability), 30 occurrences |
| 346 | 力 | 能力 (ability), 21 occurrences |
| 534 | 感 | 感じる (feel) |
| 720 | 幸 | 幸せ (happiness) |
| 613 | 許 | 許せない (cannot forgive) |

## Total New Mappings: ~125
- HIGH confidence: ~112 (katakana grid, Latin grid, digits, alignment, core kanji)
- MEDIUM confidence: ~13 (contextual kanji inferences)

## Message Structure Analysis
The 260 messages in resource 0038 serve the character creation and party management system:

1. **MSG 0-36**: System labels (HP, stats, levels)
2. **MSG 37-52**: Class/job names (戦士, 侍, モンク, etc.)
3. **MSG 53-86**: Personality trait names
4. **MSG 87-144**: Personality trait descriptions (matches guide's trait list)
5. **MSG 145-163**: Class descriptions and growth mechanics
6. **MSG 164-168**: Class restriction lists for abilities
7. **MSG 169-219**: Advanced class abilities and stat descriptions
8. **MSG 220-228**: Alignment labels with display format codes
9. **MSG 229**: Level prefix
10. **MSG 230-259**: English reputation tier names (30 tiers across Good/Neutral/Evil)

## Potential Map Errors Identified

1. **Glyph 369**: Confirmed as 明 but contextual usage (明つけて, 明ただけで) strongly suggests 見 (see/find). 見つけて (find) and 見ただけで (just by seeing) are standard Japanese; 明つけて is not.

2. **Glyph 659**: Confirmed as 城 but used as a verb (城る, 城ったり) which is not valid Japanese. Likely 帰 (return) instead: 帰る (return home) and 帰ったり (sometimes returning).

3. **Glyph 198**: Confirmed as 鍵 in msg_glyph_map, but the katakana grid predicts 198=カ. May indicate different glyph tables for different resource types, or a map error.

## Remaining Unknowns
After this analysis, approximately 200 unique glyph IDs remain unmapped. The highest-frequency unknowns are:
- Glyph 704 (20 occ) - appears in [704][700] compound, possibly 可 or 技
- Glyph 514 (19 occ) - appears as second char of class-related compounds
- Glyph 620 (17 occ) - appears in [619][620] verb pattern
- Glyph 619 (16 occ) - appears in [619][620] verb pattern
- Glyph 383 (14 occ) - appears after 隊 frequently
- Glyph 726/727 (15/13 occ) - 2-char compound, possibly a class name

## Output
- `data/inferred_r38.json` - Full inference results with confidence levels and reasoning
