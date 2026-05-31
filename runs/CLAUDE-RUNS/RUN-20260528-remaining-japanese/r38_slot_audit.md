# R38 Slot Audit: Glyph Count vs English Translation Length

**Date:** 2026-05-28
**Resource:** 0038_type01 (character details / chargen / status screen labels)
**Format:** Type-1 MSG, Format A with offset table, 188 messages
**Pipeline:** build_full_english_v2.py (variable-size injection + offset table rebuild)

## Key Finding

**Slot overflow is NOT a problem for R38.** The v2 build pipeline uses variable-size
injection with automatic offset table rebuild. English translations can be any length --
the offset table is recalculated to accommodate the new glyph stream sizes.

## Summary

| Category | Count |
|---|---|
| Total messages | 188 |
| Translated | 135 |
| OK or EXACT fit | 56 |
| English longer than Japanese | 79 |
| No translation yet | 53 |

## Pipeline Confirmation

R38 is a **Format A** resource (offset table at payload start, `msg_count=188`).
The `inject_resource()` function in `build/build_full_english_v2.py`:

1. Parses the offset table to find FFFF-delimited message groups
2. Replaces translated groups with variable-length English glyph streams
3. **Rebuilds the offset table** with new byte offsets (`rebuild_offset_table()`)
4. Updates `payload_size` in the sub-header
5. Re-pads to sector boundary

Therefore, overflow in the "glyph slot count" sense is harmless. The real truncation
risks come from **UI rendering constraints** (pixel width on screen), not binary format.

## Full Message Table

Legend:
- **JP_Gly**: Number of content glyphs in original Japanese
- **EN_Chr**: Number of characters in English translation
- **Delta**: EN_Chr - JP_Gly (positive = English is longer)
- **Status**: OK / EXACT / OVERFLOW / NO_TRANS

### Attributes (MSG 0-7)

| MSG | JP_Gly | EN_Chr | Delta | Status | English | Japanese |
|-----|--------|--------|-------|--------|---------|----------|
| 0 | 2 | 2 | 0 | EXACT | HP | hp |
| 1 | 6 | 6 | 0 | EXACT | HP/MHP | hp/mhp |
| 2 | 1 | 3 | +2 | OVERFLOW | STR | 力 |
| 3 | 2 | 3 | +1 | OVERFLOW | INT | 知恵 |
| 4 | 3 | 3 | 0 | EXACT | FTH | 信仰心 |
| 5 | 3 | 3 | 0 | EXACT | VIG | 生命力 |
| 6 | 3 | 3 | 0 | EXACT | AGI | 敏捷度 |
| 7 | 3 | 3 | 0 | EXACT | LCK | 幸運度 |

### Stat Labels (MSG 8-17)

| MSG | JP_Gly | EN_Chr | Delta | Status | English | Japanese |
|-----|--------|--------|-------|--------|---------|----------|
| 8 | 2 | 4 | +2 | OVERFLOW | Name | 名前 |
| 9 | 3 | 5 | +2 | OVERFLOW | Level | レベル |
| 10 | 2 | 4 | +2 | OVERFLOW | Race | 種族 |
| 11 | 2 | 6 | +4 | OVERFLOW | Gender | 性別 |
| 12 | 2 | 9 | +7 | OVERFLOW | Alignment | 属性 |
| 13 | 2 | 5 | +3 | OVERFLOW | Class | 職業 |
| 14 | 2 | 11 | +9 | OVERFLOW | Personality | 性格 |
| 15 | 5 | 9 | +4 | OVERFLOW | Sorceries | 呪術魔法 |
| 16 | 4 | 10 | +6 | OVERFLOW | Holy Magic | 神聖魔法 |
| 17 | 3 | 10 | +7 | OVERFLOW | Attributes | 能力値 |

### Spell Levels (MSG 18-24)

| MSG | JP_Gly | EN_Chr | Delta | Status | English | Japanese |
|-----|--------|--------|-------|--------|---------|----------|
| 18 | 3 | 3 | 0 | EXACT | Lv1 | lv1 |
| 19 | 3 | 3 | 0 | EXACT | Lv2 | lv2 |
| 20 | 3 | 3 | 0 | EXACT | Lv3 | lv3 |
| 21 | 3 | 3 | 0 | EXACT | Lv4 | lv4 |
| 22 | 3 | 3 | 0 | EXACT | Lv5 | lv5 |
| 23 | 3 | 3 | 0 | EXACT | Lv6 | lv6 |
| 24 | 3 | 3 | 0 | EXACT | Lv7 | lv7 |

### Gender (MSG 25-26)

| MSG | JP_Gly | EN_Chr | Delta | Status | English | Japanese |
|-----|--------|--------|-------|--------|---------|----------|
| 25 | 1 | 1 | 0 | EXACT | M (male symbol) | 男 |
| 26 | 1 | 1 | 0 | EXACT | F (female symbol) | 女 |

### Races (MSG 27-34)

| MSG | JP_Gly | EN_Chr | Delta | Status | English | Japanese |
|-----|--------|--------|-------|--------|---------|----------|
| 27 | 2 | 2 | 0 | EXACT | Io | イオ |
| 28 | 4 | 6 | +2 | OVERFLOW | Europa | エウロパ |
| 29 | 2 | 5 | +3 | OVERFLOW | Human | 人間 |
| 30 | 3 | 3 | 0 | EXACT | Elf | エルフ |
| 31 | 3 | 5 | +2 | OVERFLOW | Gnome | ノーム |
| 32 | 4 | 5 | +1 | OVERFLOW | Dwarf | ドワーフ |
| 33 | 4 | 6 | +2 | OVERFLOW | Hobbit | ホビット |
| 34 | 6 | 8 | +2 | OVERFLOW | Automata | オートマター |

### Basic Classes (MSG 37-42)

| MSG | JP_Gly | EN_Chr | Delta | Status | English | Japanese |
|-----|--------|--------|-------|--------|---------|----------|
| 37 | 2 | 7 | +5 | OVERFLOW | Fighter | 戦士 |
| 38 | 2 | 5 | +3 | OVERFLOW | Thief | 盗賊 |
| 39 | 3 | 8 | +5 | OVERFLOW | Magician | 呪術師 |
| 40 | 2 | 6 | +4 | OVERFLOW | Priest | 神聖 |
| 41 | 2 | 5 | +3 | OVERFLOW | Ninja | 忍者 |
| 42 | 1 | 7 | +6 | OVERFLOW | Samurai | 侍 |

### Advanced Classes (MSG 43-47)

| MSG | JP_Gly | EN_Chr | Delta | Status | English | Japanese |
|-----|--------|--------|-------|--------|---------|----------|
| 43 | 2 | 6 | +4 | OVERFLOW | Bishop | 司教 |
| 44 | 2 | 6 | +4 | OVERFLOW | Knight | 騎士 |
| 45 | 4 | 9 | +5 | OVERFLOW | Alchemist | 錬金術師 |
| 46 | 2 | 6 | +4 | OVERFLOW | Gizoku | 義賊 |
| 47 | 3 | 4 | +1 | OVERFLOW | Monk | モンク |

### Expert Classes (MSG 48-54)

| MSG | JP_Gly | EN_Chr | Delta | Status | English | Japanese |
|-----|--------|--------|-------|--------|---------|----------|
| 48 | 3 | 7 | +4 | OVERFLOW | Paladin | 聖騎士 |
| 49 | 3 | 11 | +8 | OVERFLOW | Dark Knight | 暗騎士 |
| 50 | 2 | 6 | +4 | OVERFLOW | Shogun | 将軍 |
| 51 | 2 | 10 | +8 | OVERFLOW | High Thief | (decode artifact) |
| 52 | 2 | 7 | +5 | OVERFLOW | Omnitsu | 隠密 |
| 53 | 3 | 7 | +4 | OVERFLOW | Samurai | 飽き性 |
| 54 | 2 | 8 | +6 | OVERFLOW | Militant | (武) |

### Personality Traits (MSG 55-82)

| MSG | JP_Gly | EN_Chr | Delta | Status | English | Japanese |
|-----|--------|--------|-------|--------|---------|----------|
| 55 | 3 | 13 | +10 | OVERFLOW | Pusillanimous | 臆病 |
| 56 | 2 | 6 | +4 | OVERFLOW | Lonely | 孤独 |
| 57 | 3 | 8 | +5 | OVERFLOW | Sociable | 社交的 |
| 58 | 3 | 9 | +6 | OVERFLOW | Collector | 収集家 |
| 59 | 2 | 8 | +6 | OVERFLOW | Cautious | 慎重 |
| 60 | 3 | 7 | +4 | OVERFLOW | Hoarder | 貯蓄家 |
| 61 | 2 | 12 | +10 | OVERFLOW | Intellectual | 知的 |
| 62 | 3 | 11 | +8 | OVERFLOW | Belligerent | 好戦的 |
| 63 | 3 | 11 | +8 | OVERFLOW | Adventurous | 冒険家 |
| 64 | 3 | 13 | +10 | OVERFLOW | Superstitious | 迷信家 |
| 65 | 3 | 8 | +5 | OVERFLOW | Studious | 勤勉 |
| 66 | 3 | 6 | +3 | OVERFLOW | Stupid | (decode artifact) |
| 67 | 6 | 9 | +3 | OVERFLOW | Ecologist | エコロジスト |
| 68 | 3 | 12 | +9 | OVERFLOW | Maiden Heart | 乙女心 |
| 69 | 3 | 11 | +8 | OVERFLOW | Hot-Blooded | 熱血漢 |
| 70 | 3 | 4 | +1 | OVERFLOW | Just | 正義感 |
| 71 | 3 | 10 | +7 | OVERFLOW | Determined | 負けず嫌い |
| 72 | 3 | 11 | +8 | OVERFLOW | Cooperative | 協力的 |
| 73 | 2 | 9 | +7 | OVERFLOW | Fraternal | 友愛 |
| 74 | 2 | 14 | +12 | OVERFLOW | Short-Tempered | 短気 |
| 75 | 6 | 9 | +3 | OVERFLOW | Economist | エコノミスト |
| 76 | 2 | 7 | +5 | OVERFLOW | Lustful | 好色 |
| 77 | 5 | 9 | +4 | OVERFLOW | Narcicist | ナルシスト |
| 78 | 3 | 5 | +2 | OVERFLOW | Moody | 気分屋 |
| 79 | 3 | 6 | +3 | OVERFLOW | Sadist | 自己的 |
| 80 | 3 | 11 | +8 | OVERFLOW | Tribal Love | 種族愛 |
| 81 | 2 | 4 | +2 | OVERFLOW | Bold | 大胆 |
| 82 | 3 | 8 | +5 | OVERFLOW | Wasteful | 浪費家 |

### Combat Stats (MSG 83-86)

| MSG | JP_Gly | EN_Chr | Delta | Status | English | Japanese |
|-----|--------|--------|-------|--------|---------|----------|
| 83 | 3 | 3 | 0 | EXACT | OFE | 攻撃力 |
| 84 | 3 | 3 | 0 | EXACT | ACC | 命中率 |
| 85 | 3 | 3 | 0 | EXACT | DEF | 防御力 |
| 86 | 3 | 3 | 0 | EXACT | EVA | 回避率 |

### Personality Descriptions (MSG 87-116) -- NO TRANSLATION

All 30 personality descriptions (MSG 87-116) are untranslated. These are 17-47 glyphs
each, containing detailed Japanese text describing how each personality trait affects
gameplay behavior.

### Race Descriptions (MSG 117-122) -- NO TRANSLATION

6 race description messages are untranslated. These are 47-67 glyphs each.

### Alignment Descriptions (MSG 123-125) -- TRANSLATED BUT OVERFLOWING

| MSG | JP_Gly | EN_Chr | Delta | Status | English |
|-----|--------|--------|-------|--------|---------|
| 123 | 65 | 114 | +49 | OVERFLOW | Good: Values justice... |
| 124 | 40 | 71 | +31 | OVERFLOW | Neutral: Unbiased worldview... |
| 125 | 42 | 87 | +45 | OVERFLOW | Evil: Prefers rest... |

### Class Descriptions (MSG 126-141) -- NO TRANSLATION

16 class description messages are untranslated. These are 21-72 glyphs each.

### Stat Influence Descriptions (MSG 142-147) -- TRANSLATED BUT OVERFLOWING

| MSG | JP_Gly | EN_Chr | Delta | Status | English |
|-----|--------|--------|-------|--------|---------|
| 142 | 20 | 34 | +14 | OVERFLOW | STR: Affects weapon attack damage. |
| 143 | 18 | 42 | +24 | OVERFLOW | INT: Affects Sorcery power and resistance. |
| 144 | 17 | 45 | +28 | OVERFLOW | FTH: Affects Holy Magic power and resistance. |
| 145 | 33 | 56 | +23 | OVERFLOW | VIG: Affects HP, status resistance... |
| 146 | 17 | 34 | +17 | OVERFLOW | AGI: Affects turn order in battle. |
| 147 | 32 | 55 | +23 | OVERFLOW | LCK: Affects breath resistance... |

### Alignment Labels (MSG 148-156)

| MSG | JP_Gly | EN_Chr | Delta | Status | English | Japanese |
|-----|--------|--------|-------|--------|---------|----------|
| 148 | 4 | 8 | +4 | OVERFLOW | Good (G) | 善(g) |
| 149 | 5 | 11 | +6 | OVERFLOW | Neutral (N) | 中立(n) |
| 150 | 4 | 8 | +4 | OVERFLOW | Evil (E) | 悪(e) |
| 151 | 1 | 4 | +3 | OVERFLOW | Good | 善 |
| 152 | 2 | 7 | +5 | OVERFLOW | Neutral | 中立 |
| 153 | 1 | 4 | +3 | OVERFLOW | Evil | 悪 |
| 154 | 1 | 1 | 0 | EXACT | G | g |
| 155 | 1 | 1 | 0 | EXACT | N | n |
| 156 | 1 | 1 | 0 | EXACT | E | e |

### MSG 157 -- NO TRANSLATION

| 157 | 2 | --- | --- | NO_TRANS | (lv prefix) |

### Reputation Titles Evil (MSG 158-167) -- Already English in original

All EXACT fit. The original Japanese game already uses English for reputation titles.

### Reputation Titles Neutral (MSG 168-177) -- Already English in original

All EXACT fit.

### Reputation Titles Good (MSG 178-187) -- Already English in original

All EXACT fit.

## Untranslated Messages (53 total)

| Range | Count | Content |
|-------|-------|---------|
| MSG 35-36 | 2 | Empty/space glyphs (translated as empty) |
| MSG 87-116 | 30 | Personality trait descriptions (long paragraphs) |
| MSG 117-122 | 6 | Race descriptions |
| MSG 126-141 | 16 | Class descriptions |
| MSG 157 | 1 | "lv" prefix label |

## Conclusion

1. **Binary format is not a constraint.** R38 uses Format A with offset table rebuild
   in the v2 pipeline. Any English text length works.

2. **UI pixel width is the real constraint.** Labels like "Alignment" (9 chars vs 2 kanji)
   and "Personality" (11 chars vs 2 kanji) may not fit in the pixel space allocated on
   screen. This is a rendering/layout issue, not a binary format issue.

3. **53 messages still need translation.** The personality descriptions (30), race
   descriptions (6), and class descriptions (16) are substantial untranslated content.

4. **Reputation titles are already English** in the original Japanese game (MSG 158-187),
   so they required no translation work.
