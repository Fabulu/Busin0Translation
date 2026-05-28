# Infersplosion: Second Inference Pass for R39, R40, R48

**Date:** 2026-05-22
**Method:** BE uint16 glyph parsing with 497-entry base mapping + 380 previous inferences, cross-referenced against English guide (guide_full.txt, latin-1) and Japanese Wizardry vocabulary.

## Summary

| Resource | Context | Msgs | Glyphs | Unknowns Before | Unknowns After | New Inferences |
|----------|---------|------|--------|-----------------|----------------|----------------|
| 0039_type15.bin | Party management | 91 | 732 | 30 (6 after prev pass) | 4 (control codes) | 2 kanji |
| 0040_type01.bin | Adventurer's Guild | 57 | 753 | 23 (0 after prev pass) | 0 | 0 (confirmed) |
| 0048_type01.bin | Shop upgrades | 107 | 663 | 29 | 0 | 27 kanji |

**Total new inferences:** 29 glyphs
**Corrections to base map:** 4 glyphs
**Cross-resource confirmations:** 3 glyphs

## New Inferences (29 glyphs)

### HIGH confidence (21)

| Glyph ID | Char | Reading | Evidence |
|----------|------|---------|----------|
| 275 | 小 | shou/ko | 小屋 (shed), おんぼろ小屋 (dilapidated shed) |
| 354 | 仰 | gyou/kou | 信仰心 (faith/piety) - core Wizardry FTH stat |
| 411 | 町 | chou/machi | 町の (town's) - branch location prefix, 7 occurrences |
| 433 | 質 | shitsu/shichi | 質屋 (pawn shop) - matches guide PAWN SHOP |
| 495 | 専 | sen | 専門店 (specialty store), 3 messages |
| 524 | 家 | ka/ie | 民家 (private home) - matches guide PRIVATE HOME |
| 606 | 有 | yuu/aru | 有名店 (famous store), ちょう有名店 (super famous store) |
| 629 | 界 | kai | 異界の (other world's) - branch location, 7 occurrences |
| 686 | 巨 | kyo | 巨大ゴミ (giant garbage) - matches guide OVERSIZED GARBAGE |
| 697 | 市 | shi/ichi | 市場 (marketplace), 市の (city's) - location prefix |
| 744 | 焼 | shou/yaku | 焼却場 (incineration plant) - matches guide |
| 755 | 都 | to/miyako | 都の (capital's) - location hierarchy |
| 760 | 近 | kin/chika | 近所の (neighborhood's) - matches guide NEIGHBORHOOD |
| 873 | 置 | chi/oku | 置き場 (storage place) in ゴミ置き場 |
| 894 | 級 | kyuu | 低級 (low-grade), 下級/上級 (lower/upper grade) |
| 936 | 棄 | ki | 投棄 (dumping), 廃棄品 (waste products) |
| 960 | 門 | mon | 専門 (specialty) compound |
| 966 | 民 | min | 民家 (private home) |
| 995 | 著 | cho | 著名 (notable/famous) - higher tier than 有名 |
| 1017 | 国 | koku/kuni | 国の (country's) - location hierarchy |
| 1023 | 却 | kyaku | 焼却 (incineration) compound |

### MEDIUM confidence (6)

| Glyph ID | Char | Reading | Evidence |
|----------|------|---------|----------|
| 385 | 地 | chi/ji | 地下の (underground) - 3rd variant of 地 glyph |
| 848 | 棒 | bou | どろ棒市場 (thief's market) - ateji for 泥棒 |
| 915 | 遺 | i | 異界遺跡 (otherworld ruins) |
| 916 | 跡 | seki/ato | 遺跡 (ruins) compound |
| 945 | 住 | juu/sumi | 住宅 (residence) |
| 954 | 築 | chiku | 建築 (construction) in 違法建築 |

### LOW confidence (2, control codes)

| Glyph ID | Char | Type | Evidence |
|----------|------|------|----------|
| 11 | (space) | control | UI placeholder in equipment screen |
| 15 | + | control | UI icon placeholder |
| 108 | L2 | control | Button label near L1(106)/R1(107) |
| 109 | R2 | control | Button label near L1(106)/R1(107) |

## Corrections to Base Map (4 glyphs)

These are cases where the existing 497-entry base map had incorrect assignments, discovered through contextual analysis.

| Glyph ID | Was | Should Be | Confidence | Key Evidence |
|----------|-----|-----------|------------|--------------|
| **314** | 階 | **名** | HIGH | 観光名所 (tourist landmark), 自慢の名店 (famous store), 名前を削除 (delete name). 978 is the actual 階 glyph. |
| **320** | (芽, prev inf) | **心** | HIGH | 信仰心 (faith/piety stat). 心のめばえていない (heart hasn't awakened) for automata makes more sense. |
| **326** | 士 | **法** | HIGH | 不法投棄場 (illegal dumping ground). 297 already maps to 士 - this was a suspicious duplicate. |
| **443** | 編 | **投** | HIGH | 不法投棄 (illegal dumping). 421 already maps to 編 - another suspicious duplicate. |

## Cross-Resource Confirmations (3 glyphs)

| Glyph ID | Char | Confirmed In | Evidence |
|----------|------|-------------|----------|
| 348 | 光 | R48 | 観光名所 (tourist landmark) |
| 581 | 品 | R48 | 廃棄品処理場 (waste disposal site) |
| 628 | 異 | R48 | 異界の (other world's) |

## Key Decoded Content

### R48: Shop Name Hierarchy (Vigger Shop Upgrades)

The shop naming system uses a combination of reputation-based names and geographic-scale branch prefixes.

**Facility types** (for branch shops):
- 不法投棄場 = Illegal Dumping Ground
- 廃棄品処理場 (しょ理場) = Waste Disposal Site
- ゴミ焼却場 = Garbage Incineration Plant
- ゴミ捨て場 = Garbage Dump

**Location prefixes** (ascending scale):
1. 近所の (neighborhood)
2. 町の (town)
3. 街の (city district)
4. 市の (city)
5. 都の (capital)
6. 国の (country)
7. 大陸の (continent, already decoded)
8. 異界の (other world)
9. 地下の (underground)

**Shop names by reputation** (sample):
- Negative: ばったもん屋, おんぼろ小屋, 不法投棄場, 違法建築
- Low: 小屋, 民家, 住宅, 質屋
- Mid: 商店, ありふれた店, ディスカウント店, よろず屋
- High: 有名店, 専門店, マニアな店, 信頼のおける店
- Top: ちょう有名店, 著名商店, 著名専門店, 著名デパート

### R39: Wizardry Stats Confirmed

The stat change menu uses 信仰心 (faith/piety = FTH), confirming:
- 354 = 仰 (in 信仰)
- 320 = 心 (corrected from 芽)

## Output Files

- `data/infersplosion_r39_r40_r48.json` - Complete inference data with evidence
- This file: `FINDINGS.md`
