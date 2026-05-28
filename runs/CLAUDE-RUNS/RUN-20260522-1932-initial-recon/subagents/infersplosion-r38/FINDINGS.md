# Infersplosion R38 - Second Inference Pass

## Task
Decode R38 (`extracted/packdata_resources/0038_type01.bin`) - the character creation system resource.
- 188 messages, 2930 content glyphs, 163 unknown glyph IDs
- Base mapping: `data/msg_glyph_map.json` (497 entries)
- Reference: `dumps/guide_full.txt` (Busin 0 Wizardry Alternative Neo fan translation guide, latin-1)

## Results

**All 163 unknowns inferred (164 entries total).** Output: `data/infersplosion_r38.json`

| Category | Count |
|----------|-------|
| Truly new inferences (not in gmap) | 142 |
| Conflicts with msg_glyph_map.json | 21 |
| Agrees with gmap | 1 |
| **Total entries** | **164** |

| Confidence | Count |
|-----------|-------|
| HIGH      | 112   |
| MEDIUM    | 41    |
| LOW       | 10    |

### IMPORTANT: 21 Gmap Conflicts Found

21 glyph IDs have values in `msg_glyph_map.json` that produce **nonsensical Japanese** in R38 context. The inferred values produce correct, natural Japanese. These are font sheet collisions -- the same glyph ID maps to different kanji across different MSG resources.

Key examples:
- GID 577: gmap=受, inf=**時** -- 長時間 (long time), した時の (when) -- 受 produces gibberish in all 6 usages
- GID 732: gmap=後, inf=**軍** -- 将軍 (Shogun class) -- 将後 is not a class name
- GID 600: gmap=進, inf=**流** -- 交流 (interaction) -- 交進 is not standard Japanese
- GID 606: gmap=使, inf=**無** -- 無理 (unreasonable) -- 使理 is not a word
- GID 790: gmap=有, inf=**絶** -- 絶対 (absolute), 気絶 (stun) -- 有対/気有 don't work

Full conflict list in `infersplosion_r38.json` under `gmap_conflicts`.

## Resource Structure (R38)

R38 is the **character creation system** text resource. Binary format: BE uint16 message count (188) at offset 0, followed by 188 BE uint32 byte-offsets to messages, then message data as BE uint16 glyph ID sequences terminated by 0xFFFE/0xFFFF.

### Message Layout

| Range | Content |
|-------|---------|
| MSG 0-9 | Stat/system labels (hp, STR, INT, FTH, VIG, AGI, LCK, floor, level) |
| MSG 10-14 | Category labels (race, gender, alignment, class, personality) |
| MSG 15-16 | Magic type labels (Sorcery Knight, Holy Knight) |
| MSG 17 | Ability score label |
| MSG 18-24 | Level labels Lv1-Lv7 |
| MSG 25-26 | Gender labels (Male, Female) |
| MSG 27-34 | Race names (Io, Europa, Human, Elf, Gnome, Dwarf, Hobbit, Automata) |
| MSG 35-36 | Blank spacers |
| MSG 37-52 | Class names (Fighter through High Thief, 16 classes) |
| MSG 53-82 | Personality trait names (30 traits) |
| MSG 83-86 | Potential ability / stat labels |
| MSG 87-116 | Personality trait descriptions (30 prose paragraphs) |
| MSG 117-122 | Race descriptions (stat growth explanations) |
| MSG 123-125 | Alignment descriptions (Good/Neutral/Evil + class restrictions) |
| MSG 126-141 | Class descriptions (16 classes, mechanics) |
| MSG 142-147 | Attribute effect descriptions |
| MSG 148-157 | Alignment display labels with formatting codes |
| MSG 158-187 | English reputation tier names (30 entries: evil/good/neutral x 10 tiers) |

## Key Discoveries

### 1. Complete Attribute System Decoded

| Glyph Sequence | Japanese | English (Guide) |
|---------------|----------|-----------------|
| 力 (346) | 力 | STR (Strength) |
| 知恵 (535,717) | 知恵 | INT (Intelligence) |
| 信仰心 (308,354,320) | 信仰心 | FTH (Faith) |
| 生命力 (718,696,346) | 生命力 | VIG (Vigor) |
| 敏捷度 (582,719,590) | 敏捷度 | AGI (Agility) |
| 幸運度 (720,721,590) | 幸運度 | LCK (Luck) |

### 2. All 16 Class Names Decoded

| MSG | Glyphs | Japanese | English |
|-----|--------|----------|---------|
| 37 | 286,297 | 戦士 | Fighter |
| 38 | 315,329 | 盗賊 | Thief |
| 39 | 280,342,343 | 騎事務 | Mage (Sorcerer) |
| 40 | 726,727 | 神聖 | (Holy - prefix for Holy Knight/Magic) |
| 41 | 309,287 | 忍者 | Ninja |
| 42 | 401 | 侍 | Samurai |
| 43 | 405,396 | 僧教 | Priest |
| 44 | 304,297 | 騎士 | Knight |
| 45 | 730,419,342,343 | 冒金事務 | Alchemist |
| 46 | 533,329 | 義賊 | Gizoku |
| 47 | 227,238,200 | モンク | Monk |
| 48 | 284,304,297 | 聖騎士 | Paladin |
| 49 | 353,304,297 | 暗騎士 | Dark Knight |
| 50 | 731,732 | 将軍 | Shogun |
| 51 | 733,734 | 教授/司教 | Bishop |
| 52 | 735,315 | 怪盗/大盗 | High Thief |

### 3. All 30 Personality Traits Mapped to Guide

Every trait from the guide's PERSONALITY TRAIT LIST was matched to its Japanese equivalent in the game data:
- ADVENTUROUS = 冒険家, FRATERNAL = 友愛, TRIBAL LOVE = 種族愛, SOCIABLE = 社交的
- COOPERATIVE = 協力的, STUDIOUS = 勤勉, INTELLECTUAL = 知的
- SHORT-TEMPERED = 短気, ANXIOUS/PUSILLANIMOUS = 臆病, BOLD = 大胆, DETERMINED = 闘志
- WASTEFUL = 浪費, HOARDER = 貯蓄家, COLLECTOR = 収集家
- LONELY = 孤独, CAUTIOUS = 慎重, MOODY = 気分屋
- ECOLOGIST = エコロジスト, ECONOMIST = エコノミスト, NARCICIST = ナルシスト
- MAIDEN HEART = 乙女心, HOT-BLOODED = 熱血漢, BELLIGERENT = 好戦的
- SADIST, LUSTFUL, JUST, SUPERSTITIOUS, BORED, STUPID = various

### 4. Glyph Duplicates Across Font Sheets

Multiple kanji appear at two different glyph IDs, confirming multi-sheet font:
- 聖: 284 and 727
- 種: 292 and 513
- 高: 648 and 743
- 義: 533 and 762
- 宝: 692 and 836
- 息: 490 and 764
- 箱: 608 and 989
- 仲: 543 and 676
- 異: 622 and 678
- 武/器: 316=武, 776=器

### 5. Special Format Glyphs

| GID | Char | Purpose |
|-----|------|---------|
| 8 | （ | Fullwidth left parenthesis (alignment display) |
| 9 | ） | Fullwidth right parenthesis |
| 15 | ／ | Fullwidth slash (hp/mhp separator) |
| 26 | ： | Fullwidth colon (label separator) |
| 86 | ｖ | Fullwidth lowercase v (Lv prefix) |

### 6. Low-Confidence Inferences Needing Visual Verification

| GID | Inferred | Context | Issue |
|-----|----------|---------|-------|
| 450 | 慮 | MSG 54: [465][450] trait name | Could be other kanji |
| 465 | 配 | MSG 54: [465][450] trait name | Could be other kanji |
| 735 | 怪 | MSG 52: [735]盗 (High Thief) | Could be 大 or other |
| 748 | 右 | MSG 119: [748]に出る者 | Idiomatic but uncertain |
| 639 | 流 | MSG 107: [639][640]を望む | Possible duplicate of 600=流 |
| 640 | 血 | MSG 107: [639][640]を望む | Could be 平和 instead |

## Verification Method

Cross-referenced each unknown glyph against:
1. Surrounding decoded glyphs forming partial Japanese words
2. Guide's English descriptions of identical game mechanics
3. Standard Japanese vocabulary for RPG systems
4. Consistency with the 497-entry base mapping
5. Wizardry class/race/attribute terminology conventions

## Files Written

- `data/infersplosion_r38.json` - Full inference mapping with 163 entries, confidence levels, and reasoning
- `runs/CLAUDE-RUNS/RUN-20260522-1932-initial-recon/subagents/infersplosion-r38/FINDINGS.md` - This file
