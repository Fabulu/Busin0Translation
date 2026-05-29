# EXE Remaining Japanese Glyph Scan - Final Report

**Date:** 2026-05-28  
**EXE:** `extracted/SLPM_653.78`  
**Scan range:** `0x3B0000` - `0x3FD000` (EXE data section)  
**Method:** LE uint16 glyph ID cluster detection + manual analysis

---

## Already Handled Regions

| Region | Offset | Description |
|--------|--------|-------------|
| Menu structs | `0x3C3000`-`0x3C5300` | Menu tile replacement (done) |
| Chargen grid | `0x3C83C0`-`0x3C93A0` | Character creation grid (R38, done) |
| Tab labels | `0x3C9DA0`-`0x3C9DFC` | Name entry tab IDs (Table 2E, done) |

---

## Results Summary

After scanning the full 0x3B0000-0x3FD000 range and filtering false positives from MIPS code coincidences and struct data, the following genuine glyph-ID regions were identified:

| Priority | Region | Offset | Type | Action |
|----------|--------|--------|------|--------|
| -- | A | `0x3B3226`-`0x3B368A` | Font glyph ordering table | No action (infrastructure) |
| -- | B | `0x3B3690`-`0x3B3752` | Glyph width/repeat table | No action (infrastructure) |
| LOW | C | `0x3B376A`-`0x3B3838` | UI label glyph index arrays | Investigate |
| LOW | D | `0x3B3DAE`-`0x3B3E90` | String index/lookup tables | Investigate |
| -- | E | `0x3B5FC0`-`0x3B6136` | Kana sort order table | No action (infrastructure) |
| MED | F | `0x3C5F00`-`0x3C6700` | Name entry keyboard grids | Needs update if replacing name input |
| -- | G | `0x3C8180`-`0x3C83C0` | Pre-chargen kana grid extension | Likely handled with R38 |
| -- | H | `0x3C9A34`-`0x3C9D54` | Glyph cross-reference table | No action (font mapping infrastructure) |
| -- | I | `0x3DDC40`-`0x3DE0D6` | Struct byte data (false positive) | No action (raw bytes 00-04) |
| LOW | J | `0x3DEFA2`-`0x3DEFBC` | Character creation flags | Investigate |
| -- | CODE | `0x3B8000`-`0x3BD000` | MIPS code section | No action (false positives) |

---

## Detailed Analysis

### Region A: Font Glyph Ordering Table (`0x3B3226`-`0x3B368A`)

**1124 bytes, 544 consecutive kanji glyph IDs**

This is the master glyph ordering table for the font atlas. Contains every hiragana, katakana, and kanji glyph ID in sequential order. Used internally by the font rendering system to map character codes to glyph positions.

**Content (first portion):** あいうえお...かきくけこ...さしすせそ...たちつてと... (full kana + all kanji)

**Action:** NO ACTION NEEDED - this is font infrastructure, not displayed text.

---

### Region B: Glyph Width/Repeat Table (`0x3B3690`-`0x3B3752`)

**~200 bytes, paired glyph IDs**

Each glyph ID appears 2-3 times in sequence (e.g., 中中, 込込, 遺遺王王王). This pattern suggests a width/spacing table or rendering configuration where each glyph has associated metadata.

Contains: 中, 込, 遺, 王, 噂, 彼, 対, 無, 光, 冒, 険, 広, 刻, 息, 登, 録, 開, 帰, 専, 所, 出, 新, 兵, 召, 喚, 能, 力, 職, 地, 削, 除, 部, 隊, 前, 性

These correspond to the kanji used in menu labels like:
- 冒険 (adventure), 登録 (register), 新兵 (recruit), 召喚 (summon)
- 能力 (ability), 職 (class), 削除 (delete), 部隊 (party)

**Action:** NO ACTION NEEDED - rendering metadata, not standalone text. The actual menu labels that use these glyphs are in the menu structs (0x3C3000-0x3C5300, already handled).

---

### Region C: UI Label Glyph Index Arrays (`0x3B376A`-`0x3B3838`)

**~206 bytes, three sub-tables**

1. **Sub-table 1 (10 hiragana):** あけちのむるぐだべゅ
   - These are the 10 hiragana that correspond to katakana tab labels (あ=ア row, etc.)

2. **Sub-table 2 (katakana + kanji, 35 entries):** クチノムルグダベュヴ使悪士飲開頼賊中邪暗然見店地半侍願直約質大主
   - Katakana portion matches the kana keyboard tabs
   - Kanji: 使悪士飲開頼賊中邪暗然見店地半侍願直約質大主

3. **Sub-table 3 (46 kanji):** 刻出地種飽交間消屋色嫌受費属方箱看求突血高誰元体解街命可足幸聖美高器形内回失打先巨嘆護声穏空組草携札
   - These appear to be kanji used in game dialogue/descriptions

**Action:** INVESTIGATE - these are glyph ID lookup arrays. Sub-tables 2-3 contain kanji used in UI labels and game text. If the menu system references these arrays to render text, they may need updating. However, if the menu structs already contain the full glyph sequences for rendering, these may be unused secondary tables.

---

### Region D: String Index/Lookup Tables (`0x3B3DAE`-`0x3B3E90`)

**~226 bytes, multiple sub-tables**

Contains glyph IDs that appear to be indices into string/label arrays:

1. `0x3B3DAE`: ％かすとひめれぐぞびぺぅエサツノミランジドピァ祠使鎧大魔忍武力言中悔除外両苦転地報頼封復
   - Mix of kana and game-concept kanji (armor, magic, ninja, strength, curse, etc.)

2. `0x3B3E0A`: 紹大記会横辺王
3. `0x3B3E1A`: 広専能隊性怪交代仲追与己嫌同前度少品思看
4. `0x3B3E44`: 界違貴絆誰丁御仲功誓命日必高獲入美本答楽正内活響就華替巨打刻療
5. `0x3B3E84`: 穏部十突園法

The first sub-table's kanji maps to game concepts:
- 祠=shrine, 使=use, 鎧=armor, 魔=magic, 忍=ninja, 武=warrior
- 力=power, 言=speech, 中=middle, 悔=regret, 除=remove
- 外=outside, 両=both, 苦=suffering, 転=turn, 地=earth
- 報=report, 頼=trust, 封=seal, 復=restore

**Action:** INVESTIGATE - may be string hash/index tables for runtime text lookup. Low priority since the actual displayed text is likely in MSG resources, not here.

---

### Region E: Kana Sort Order Table (`0x3B5FC0`-`0x3B6136`)

**~374 bytes, full kana charset in sort order**

Contains all katakana and hiragana glyph IDs in Japanese sorting order (gojuuon). Used for string comparison/sorting operations.

**Action:** NO ACTION NEEDED - sorting infrastructure.

---

### Region F: Name Entry Keyboard Grids (`0x3C5F00`-`0x3C6700`)

**~2048 bytes, structured keyboard layout data**

Contains the character grids used for the name entry screen. Two grids detected:
- Grid 1 at `0x3C5F1E`: Hiragana input grid (あいうえお rows with positioning data)
- Grid 2 at `0x3C65D8`: Katakana input grid (similar structure)

Each entry appears to be 6 bytes: [x_pos, y_pos, glyph_id, glyph_id, ...] defining the screen position and character for each keyboard key.

**Action:** NEEDS UPDATE if the name entry system is being replaced with English/romaji input. If keeping Japanese name entry, no change needed.

---

### Region G: Pre-chargen Kana Grid (`0x3C8180`-`0x3C83C0`)

**~576 bytes**

Contains paired glyph IDs (each kana appears twice, likely rendering + collision data) for hiragana characters あ through に. This appears to be the character selection grid data immediately before the main chargen grid at 0x3C83C0.

**Action:** LIKELY HANDLED with the chargen grid (R38). Verify that the R38 replacement covers this region too.

---

### Region H: Glyph Cross-Reference Table (`0x3C9A34`-`0x3C9D54`)

**~800 bytes, structured records**

Initially looked like a vocabulary table, but analysis of the raw hex reveals this is a **glyph cross-reference/mapping table**. Each record contains 6 uint16 glyph IDs from different ranges in the font atlas:

Record structure (12 bytes = 6 x uint16):
```
[padding] [padding] [glyph_col1] [glyph_col2] [glyph_col3] [glyph_col4]
```

Example record at 0x3C9A34:
```
Raw: 00 00 00 00 56 00 8F 00 C8 00 01 01
Values: 0, 0, 86(=み), 143(=ク), 200(=ベ), 257(=名)
```

The glyph IDs increment consistently across records, mapping between parallel glyph ranges. This is used by the font system to look up variant forms or related characters. Groups are separated by 8-byte null padding.

**Action:** NO ACTION NEEDED - this is font mapping infrastructure. The glyph IDs here are indices into the font atlas, not displayed text strings.

---

### Region I: Struct Byte Data (`0x3DDC40`-`0x3DE0D6`, FALSE POSITIVE)

Raw bytes: `00 01 02 02 03 03 03 03 04 04 04 04 04 04 04 04`

This is clearly incrementing byte data (0, 1, 2, 2, 3, 3, 3, 3, 4, 4...) that only coincidentally maps to glyph IDs when read as uint16 LE. The pattern `0x0100=256=ブ`, `0x0202=514=族`, `0x0303=771=下`, `0x0404=1028=難` is just byte pairs.

**Action:** NO ACTION NEEDED - false positive.

---

### Region J: Character Creation Flags (`0x3DEFA2`-`0x3DEFBC`)

**~26 bytes**

Contains: 男(518) 下(771) 性(516) 男(518) 下(771) 呪(772) 難(771) 下(771)

The values 771 (=0x0303) and 772 (=0x0304) appear suspicious - these could be struct data rather than glyph IDs. However, 518=男 and 516=性 are legitimate gender-related glyphs.

**Action:** LOW PRIORITY - investigate whether these are actual glyph references for gender labels or coincidental struct data.

---

### Isolated Code Section References

A few isolated kanji glyph IDs appear in the code section around `0x3BF100`:
- 発(661), 御(669), 意(673), 名(713), 期(687), 避(725), 町(411), 回(311), 種(513), 値(711), 足(712), 別(512)
- These may be hardcoded glyph IDs used in specific game functions (e.g., displaying status values, item names)

Also at `0x3BD6F0`: ボ(258), 属(515), 呪(772) - possibly used for attribute/spell type display

**Action:** LOW PRIORITY - these are isolated glyph references in code, possibly used for specific rendering calls. Would need cross-referencing with the MIPS disassembly to determine if they're used for displayed text.

---

## Priority Action Items

1. **[DONE] Menu structs (0x3C3000-0x3C5300)** - Already handled
2. **[DONE] Chargen grid (0x3C83C0-0x3C93A0)** - Already handled (R38)
3. **[DONE] Tab labels (0x3C9DA0-0x3C9DFC)** - Already handled (Table 2E)

4. **[MEDIUM] Name entry keyboards (Region F, 0x3C5F00-0x3C6700):**
   - Two keyboard grids (hiragana + katakana) for character name input
   - Needs updating if switching to English name entry

5. **[LOW] UI label index arrays (Region C, 0x3B376A-0x3B3838):**
   - Cross-reference with menu struct code to confirm if these are used independently

6. **[LOW] Isolated code references (0x3BF100, 0x3BD6F0):**
   - Cross-reference with disassembly to find rendering call sites

7. **[NO ACTION] Font infrastructure (Regions A, B, E, H):**
   - Glyph ordering, width tables, sort order, cross-reference mapping
   - These support the font system and don't contain user-facing text

## Conclusion

**The EXE has very few remaining Japanese glyph references that need translation.** The main regions (menu structs, chargen grid, tab labels) are already handled. The only medium-priority remaining item is the name entry keyboard grids (Region F) which would need updating for English name input. All other glyph regions are font infrastructure (ordering tables, width data, sort tables, cross-references) that don't contain displayed text strings.

The vast majority of displayed Japanese text in this game comes from the MSG resources in PACKDATA.DIG, not from hardcoded EXE data. The EXE glyph references are predominantly rendering infrastructure.
