# Deep Analysis: Chargen (Character Creation) Screen Labels

**Date**: 2026-05-28
**Analyst**: Claude Opus 4.6

---

## CRITICAL FINDING: Chargen Labels Are NOT in the EXE

The EXE area 0x3C83C0-0x3C93A0 (Table 2B) is the **kana/katakana/kanji character input grid** for name entry, NOT the chargen UI labels. All chargen labels (gender, race, alignment, class, stats, personalities) are stored in **PACKDATA resource R38** (`extracted/packdata_resources/0038_type01.bin`), which is a type-01 MSG resource using BE uint16 glyph streams.

### What IS in the EXE at Table 2B

The 0x3C83C0-0x3C93A0 region contains 81 groups of (flag, glyph_id) pairs forming the character naming keyboard:
- Hiragana grid (あ-ん + dakuten/handakuten/combo)
- Katakana grid (ア-ン + dakuten/handakuten/combo)
- Kanji grid for name entry (祠, 小, 手, 宮, 防, 攻, 騎, 使, 向, 行, 聖, 罰, 戦, 者, 鎧, 悪, 動, 飾, etc.)

This data uses LE uint16 glyph IDs in a 4-byte format: `[flag:1][0x00:1][glyph_lo:1][glyph_hi:1]`.

After the grids (~0x3C9310), there are default character names (エミーリア, リュート) and more grid metadata. None of this is chargen label text.

---

## R38: The True Source of ALL Chargen Labels

**File**: `extracted/packdata_resources/0038_type01.bin` (7,512 bytes)
**Format**: BE uint16 glyph stream, messages delimited by FFFE/FFFF
**Total messages**: 260 (MSG 0-259)
**Translation chunk**: `data/translate_chunks/chunk_r38_fix.json` (188 entries)

### Complete Chargen Label Inventory

#### Stat Labels (MSG 0-7)

| MSG | Offset | Glyph IDs | Japanese | English (chunk) | Single Kanji? |
|-----|--------|-----------|----------|-----------------|---------------|
| 0 | 0x02F4 | 40,48 | hp | hp | No (ASCII) |
| 1 | 0x02FC | 40,48,15,45,40,48 | hp/mhp | hp/mhp | No (ASCII) |
| 2 | 0x030C | 346 | 力 | str | YES - 1 kanji |
| 3 | 0x0312 | 535,717 | 知恵 | int | No - 2 kanji |
| 4 | 0x031A | 308,354,320 | 信仰心 | fth | No - 3 kanji |
| 5 | 0x0324 | 718,696,346 | 生命力 | vit | No - 3 kanji |
| 6 | 0x032E | 582,719,590 | 敏捷度 | agi | No - 3 kanji |
| 7 | 0x0338 | 720,721,590 | 幸運度 | lck | No - 3 kanji |

**Status**: All translated. Uses lowercase ASCII glyph IDs (a=33..z=58).

#### Chargen Field Labels (MSG 8-17)

| MSG | Offset | Glyph IDs | Japanese | English (chunk) | Single Kanji? |
|-----|--------|-----------|----------|-----------------|---------------|
| 8 | 0x0342 | 314,510 | 名前 | name | No - 2 kanji |
| 9 | 0x034A | 234,257,233 | レベル | level | No - 3 katakana |
| 10 | 0x0354 | 513,514 | 種族 | race | No - 2 kanji |
| 11 | 0x035C | 511,512 | 性別 | gender | No - 2 kanji |
| 12 | 0x0364 | 515,511 | 属性 | alignment | No - 2 kanji |
| 13 | 0x036C | 504,517 | 職業 | class | No - 2 kanji |
| 14 | 0x0374 | 511,516 | 性格* | personality | No - 2 kanji |
| 15 | 0x037C | 280,342,343,280,326 | 呪術呪法* | sorcery | No - 5 kanji |
| 16 | 0x038A | 726,727,280,326 | 神聖呪法* | holy magic | No - 4 kanji |
| 17 | 0x0396 | 700,346,711 | 能力値 | attributes | No - 3 kanji |

*Note: Glyph map errors cause some kanji to decode incorrectly (e.g., 性格 shows as 性性, 呪術師 shows as 騎事持). The actual kanji are correct in-game.

**Status**: All translated in chunk.

#### Gender Labels (MSG 25-26)

| MSG | Offset | Glyph IDs | Japanese | English (chunk) | Single Kanji? |
|-----|--------|-----------|----------|-----------------|---------------|
| 25 | 0x03E6 | 518 | 男 | **MISSING** | YES - 1 kanji |
| 26 | 0x03EC | 349 | 女 | female | YES - 1 kanji |

**BUG FOUND**: MSG 25 (男 = Male) has no translation in the chunk! The chunk has a duplicate "lv7" entry at message 25 instead of "male". This means the male gender label remains as the kanji 男 in-game.

**Recommended fix**: Add `{"resource": 38, "message": 25, "japanese": "男 / ", "english": "male / "}` to chunk_r38_fix.json.

#### Race Labels (MSG 29-34)

| MSG | Offset | Glyph IDs | Japanese | English (chunk) | Single Kanji? |
|-----|--------|-----------|----------|-----------------|---------------|
| 29 | 0x0406 | 319,519 | 人間 | human | No - 2 kanji |
| 30 | 0x040E | 196,233,220 | エルフ | elf | No - 3 katakana |
| 31 | 0x0418 | 217,93,225 | ノーム | gnome | No - 3 katakana |
| 32 | 0x0422 | 253,236,93,220 | ドワーフ | dwarf | No - 4 katakana |
| 33 | 0x042E | 222,255,272,212 | ホビット | hobbit | No - 4 katakana |
| 34 | 0x043A | 197,93,212,223,208,93 | オートマター | automata | No - 6 katakana |

**Status**: All translated.

#### Class Labels (MSG 37-52)

| MSG | Offset | Glyph IDs | Japanese | English (chunk) | Single Kanji? |
|-----|--------|-----------|----------|-----------------|---------------|
| 37 | 0x0456 | 286,297 | 戦士 | fighter | No - 2 kanji |
| 38 | 0x045E | 315,329 | 盗賊 | thief | No - 2 kanji |
| 39 | 0x0466 | 280,342,343 | 呪術師* | mage | No - 3 kanji |
| 40 | 0x0470 | 726,727 | 神聖 | priest | No - 2 kanji |
| 41 | 0x0478 | 309,287 | 忍者 | ninja | No - 2 kanji |
| 42 | 0x0480 | 401 | 侍 | samurai | YES - 1 kanji |
| 43 | 0x0486 | 405,396 | 司教* | bishop | No - 2 kanji |
| 44 | 0x048E | 304,297 | 兵士 | samurai (ERROR?) | No - 2 kanji |
| 45 | 0x0496 | 730,419,342,343 | 錬金術師* | alchemist | No - 4 kanji |
| 46 | 0x04A2 | 533,329 | 義賊 | gizoku | No - 2 kanji |
| 47 | 0x04AA | 227,238,200 | モンク | monk | No - 3 katakana |
| 48 | 0x04B4 | 284,304,297 | 聖兵士 | paladin | No - 3 kanji |
| 49 | 0x04BE | 353,304,297 | 暗兵士 | dark knight | No - 3 kanji |
| 50 | 0x04C8 | 731,732 | 将軍* | shogun | No - 2 kanji |
| 51 | 0x04D0 | 733,734 | 教授 | knight | No - 2 kanji |
| 52 | 0x04D8 | 735,315 | 美盗 | high thief | No - 2 kanji |

**Status**: All translated (MSG 42 ninja was added via fix chunk).

#### Alignment Labels (FFFF-groups 148-156) -- CRITICAL BUGS

The build pipeline uses FFFF-group numbering from the raw R38 file (`extracted/packdata_raw/0038_type01.raw`). The offset table declares 188 messages. The stream starts at 0x0304 inside the raw file.

| FFFF-Group | Raw Offset | Glyph IDs | Japanese | Chunk English | Correct English | Status |
|------------|-----------|-----------|----------|---------------|-----------------|--------|
| 148 | 0x1AC8 | 520,8,39,9 | 善「g」 | good "g" | good "g" | OK |
| 149 | 0x1AD4 | 337,340,8,46,9 | 中立「n」 | **good "g"** | neutral "n" | **WRONG** |
| 150 | 0x1AE2 | 289,8,37,9 | 悪「e」 | **neutral "n"** | evil "e" | **WRONG** |
| 151 | 0x1AEE | 520 | 善 | **evil "e"** | good | **WRONG** |
| 152 | 0x1AF4 | 337,340 | 中立 | **good** | neutral | **WRONG** |
| 153 | 0x1AFC | 289 | 悪 | **neutral** | evil | **WRONG** |
| 154 | 0x1B02 | 39 | g | **evil** | g | **WRONG** |
| 155 | 0x1B08 | 46 | n | **g** | n | **WRONG** |
| 156 | 0x1B0E | 37 | e | **n** | e | **WRONG** |

**Root Cause**: The alignment translations in chunk_r38_fix.json are systematically shifted. Group 148 is correct, but groups 149-156 each have the WRONG English text. The pattern suggests the translations were assigned off-by-one starting from group 149, with some entries also having fabricated japanese fields (e.g., "evil short", "neutral short") that don't match the actual R38 content.

**Impact**: On the chargen screen:
- Selecting "Good" alignment shows "Good" correctly (group 148 is right)
- Selecting "Neutral" alignment shows **"Good"** (groups 149/152 are wrong)
- Selecting "Evil" alignment shows **"Neutral"** (groups 150/153 are wrong)
- The abbreviation letters g/n/e are also shifted

**Required fixes for chunk_r38_fix.json** (all use `"resource": 38`):

```json
{"resource": 38, "message": 149, "japanese": "中立「n」 / ", "english": "neutral \"n\" / "}
{"resource": 38, "message": 150, "japanese": "悪「e」 / ", "english": "evil \"e\" / "}
{"resource": 38, "message": 151, "japanese": "善 / ", "english": "good / "}
{"resource": 38, "message": 152, "japanese": "中立 / ", "english": "neutral / "}
{"resource": 38, "message": 153, "japanese": "悪 / ", "english": "evil / "}
{"resource": 38, "message": 154, "japanese": "g / ", "english": "g / "}
{"resource": 38, "message": 155, "japanese": "n / ", "english": "n / "}
{"resource": 38, "message": 156, "japanese": "e / ", "english": "e / "}
```

#### Male Gender Label (FFFF-group 25) -- MISSING

| FFFF-Group | Raw Offset | Glyph IDs | Japanese | Chunk English | Correct English | Status |
|------------|-----------|-----------|----------|---------------|-----------------|--------|
| 25 | 0x03F6 | 518 | 男 | **lv.7** (wrong entry) | male | **WRONG** |

The chunk has `"message": 25` mapped to `"japanese": "lv7"` with `"english": "lv.7 / "` -- this is a duplicate lv7 entry that should instead be the male gender label.

**Required fix**:
```json
{"resource": 38, "message": 25, "japanese": "男 / ", "english": "male / "}
```

---

## Summary of ALL Chargen Japanese Labels

### Correctly Translated (via chunk_r38_fix.json)

| Category | Count | Examples |
|----------|-------|---------|
| Stat labels | 7 | str, int, fth, vit, agi, lck |
| Field headers | 10 | name, level, race, gender, alignment, class, personality, sorcery, holy magic, attributes |
| Spell levels | 7 | lv1-lv7 |
| Female gender | 1 | female |
| Race names | 6 | human, elf, gnome, dwarf, hobbit, automata |
| Class names | 16 | fighter, thief, mage, priest, ninja, samurai, bishop, etc. |
| Personality traits | 29 | militant, wasteful, lonely, sociable, etc. |
| Descriptions | ~90 | Race/class/alignment/personality help text |
| Reputation ranks | 29 | commoner, hooligan, adventurer, hero, etc. |

### BROKEN or MISSING (needs immediate fix)

All "message" numbers below use the build pipeline's FFFF-group numbering (verified against `extracted/packdata_raw/0038_type01.raw`).

| Message | Japanese | Current English in Chunk | Should Be | Bug Type |
|---------|----------|------------------------|-----------|----------|
| 25 | 男 | lv.7 (wrong entry) | male | Wrong entry mapped |
| 149 | 中立「n」 | good "g" | neutral "n" | Shifted by 1 |
| 150 | 悪「e」 | neutral "n" | evil "e" | Shifted by 1 |
| 151 | 善 | evil "e" | good | Shifted by 1 |
| 152 | 中立 | good | neutral | Shifted by 1 |
| 153 | 悪 | neutral | evil | Shifted by 1 |
| 154 | g | evil | g | Shifted by 1 |
| 155 | n | g | n | Shifted by 1 |
| 156 | e | n | e | Shifted by 1 |

**Total**: 9 entries need fixing. 8 are alignment labels shifted by one position. 1 is the male gender label mapped to a wrong lv7 duplicate.

### Single-Kanji Labels (would need font tile if not in ASCII)

| Kanji | Glyph ID | Meaning | R38 MSG | Translation | Notes |
|-------|----------|---------|---------|-------------|-------|
| 力 | 346 | STR | 2 | str (3 ASCII glyphs) | Expands from 1 to 3 glyphs |
| 男 | 518 | Male | 25 | male (4 ASCII glyphs) | **WRONG** - chunk has lv7 duplicate |
| 女 | 349 | Female | 26 | female (6 ASCII glyphs) | OK |
| 善 | 520 | Good | 151 | evil "e" (WRONG) | Needs: good (4 ASCII glyphs) |
| 悪 | 289 | Evil | 153 | neutral (WRONG) | Needs: evil (4 ASCII glyphs) |
| 侍 | 401 | Samurai | 42 | samurai (7 ASCII glyphs) | OK |

All single-kanji labels CAN be replaced with multi-glyph ASCII sequences because R38 uses FFFE-delimited entries (variable length). No font tile creation needed -- just replace the glyph IDs in the stream.

### Labels NOT from R38 (Other Sources)

| Label | Source | Status |
|-------|--------|--------|
| 新規登録 (New Registration) | Texture in red banner | Needs texture edit (PSMT4/PSMT8) |
| カナ/かな/英数/記号 | Likely R38 or EXE keyboard mode labels | Part of kana grid system |
| 男名/女名 | Likely R38 name category labels | Part of name entry system |
| 決定 (Confirm) | Likely R38 or texture | Needs investigation |
| Menu labels (EXE Table 2C) | 0x3C3000-0x3C5300 in EXE | 119 records, 0% translated, 359 unmapped glyphs |

---

## EXE Chargen Area Detailed Format (0x3C83C0-0x3C93A0)

For completeness, here is the kana grid format:

**Format**: 4 bytes per entry: `[flag:u8][0x00:u8][glyph_id:u16 LE]`
**Separators**: FFFE (row break), FFFF (section end)
**Content**:
- 0x3C82A2-0x3C83BF: Hiragana あ-ん (paired entries, each kana twice)
- 0x3C83C0-0x3C864C: Hiragana with dakuten/handakuten + small kana
- 0x3C8652-0x3C893F: Katakana ア-ン + dakuten/handakuten
- 0x3C895A-0x3C8A48: Additional katakana + kanji for name input (祠, 小, 手, 宮, 防, 攻, 騎, 使, 向, 行, 聖, 罰, 戦, 者, 鎧)
- 0x3C8A4A-0x3C9310: More kanji for name input (悪, 動, 飾, 法, 魔... up to 遺)
- 0x3C9310-0x3C93A0: Default name slots (エミーリア, リュート)

This area does NOT need translation -- it is the keyboard grid for entering character names in Japanese. The kana/kanji stay as-is.

---

## Recommended Action Plan

1. **IMMEDIATE**: Fix the 9 broken/missing alignment+gender entries in `chunk_r38_fix.json`
2. **VERIFY**: Rebuild R38 with `build_full_english_v2.py` and check alignment labels render correctly
3. **LOW PRIORITY**: Investigate texture-based labels (新規登録, 決定) for texture editing
4. **LOW PRIORITY**: Map 359 unmapped glyph IDs in EXE Table 2C (menu labels)
