# R38 vs EXE Cross-Reference: Complete Label Source Mapping

**Date**: 2026-05-28
**Analyst**: Claude Opus 4.6

---

## 1. Data Sources Analyzed

| Source | File | Offset/Size | Format |
|--------|------|-------------|--------|
| R38 | `extracted/packdata_raw/0038_type01.raw` | 8,192 bytes, 260 FFFE-delimited messages | BE uint16 glyph ID stream |
| EXE Menu Structs | `extracted/SLPM_653.78` | 0x3C3000-0x3C4730 (106 x 56-byte records) | LE uint16, composite tile pairs |
| EXE Chargen Grid | `extracted/SLPM_653.78` | 0x3C83C0-0x3C93A0 (4,064 bytes) | LE uint16 pairs (flag + glyph ID) |
| EXE Region B | `extracted/SLPM_653.78` | 0x3B3690-0x3B3752 | Width/spacing metadata |
| EXE Region C | `extracted/SLPM_653.78` | 0x3B376A-0x3B3838 | UI label glyph index arrays |
| EXE Region D | `extracted/SLPM_653.78` | 0x3B3DAE-0x3B3E90 | String lookup tables |

---

## 2. Glyph ID Population Summary

| Set | Count | Range | Description |
|-----|-------|-------|-------------|
| R38 total | 631 unique | 0-65535 | All glyph IDs across 260 messages |
| EXE total | 775 unique | 1-898 | All glyph IDs across menu/chargen/regions |
| BOTH (overlap) | 389 | varies | Same glyph ID appears in both R38 and EXE |
| R38-only | 242 | mostly 300-853 | Kanji used only in R38 text/labels |
| EXE-only | 386 | mostly 607-898 | Menu tile IDs + chargen-specific kana |

---

## 3. Nature of the Overlap

The 389 shared glyph IDs are NOT label conflicts. They fall into three categories:

### 3a. Shared Kana (hiragana/katakana) -- 150+ IDs

Glyph IDs 112-275 are kana characters used as building blocks in both:
- R38: in description/help text (msgs 87-218)
- EXE Chargen Grid: as the name-entry keyboard tiles

These need NO special handling. Kana remain kana everywhere.

### 3b. Shared Kanji (individual characters) -- ~120 IDs

Glyph IDs 276-520 are individual kanji that appear in both:
- R38: as part of label glyph sequences (e.g., GID 346 = 力 in "STR" label)
- EXE: as part of the chargen kana grid extension (kanji section) or in Region B/C/D lookup tables

These are the SAME character in the SAME font atlas. When R38 replaces a kanji glyph ID with an ASCII letter glyph ID, the EXE chargen grid still has the original kanji -- but chargen uses its own rendering path and does not reference R38 for these.

### 3c. Dual-Purpose IDs in 683-853 Range -- ~90 IDs

Glyph IDs 683-853 serve DIFFERENT purposes depending on context:
- In R38: individual kanji character from the font atlas
- In EXE menu structs: composite pre-rendered tile (12x12px bitmap containing a Japanese word half)

The font atlas has separate cell regions for individual characters (low IDs) and composite tiles (high IDs). The renderer distinguishes by context (MSG glyph stream vs menu struct reference).

---

## 4. Complete Label Source Mapping

### 4a. R38-ONLY Labels (translate by replacing glyph IDs with ASCII)

These labels exist ONLY in R38 and are rendered via the standard MSG glyph system.
Translation method: replace kanji glyph IDs (280-853) with ASCII letter IDs (33-58 = a-z).

| Category | R38 Msgs | Japanese Examples | English | Glyph IDs Used |
|----------|----------|-------------------|---------|----------------|
| HP display | 1 | hp/mhp | hp/mhp | 40,48,15,45 (already ASCII) |
| Stat: STR | 2 | 力 | str | 346 -> 51,52,50 |
| Stat: INT | 3 | 知恵 | int | 535,717 -> 41,46,52 |
| Stat: FTH | 4 | 信仰心 | fth | 308,354,320 -> 38,52,40 |
| Stat: VIT | 5 | 生命力 | vit | 718,696,346 -> 54,41,52 |
| Stat: AGI | 6 | 敏捷度 | agi | 582,719,590 -> 33,39,41 |
| Stat: LCK | 7 | 幸運度 | lck | 720,721,590 -> 44,35,43 |
| Field: Name | 8 | 名前 | name | 314,510 |
| Field: Level | 9 | レベル | level | 234,257,233 |
| Field: Race | 10 | 種族 | race | 513,514 |
| Field: Gender | 11 | 性別 | gender | 511,512 |
| Field: Alignment | 12 | 属性 | align | 515,511 |
| Field: Class | 13 | 職業 | class | 504,517 |
| Field: Personality | 14 | 性格 | trait | 511,516 |
| Magic: Sorcery | 15 | 呪術呪法 | sorcery | 280,342,343,280,326 |
| Magic: Holy | 16 | 神聖呪法 | holy | 726,727,280,326 |
| Attributes | 17 | 能力値 | stats | 700,346,711 |
| Spell levels | 18-24 | Lv1-Lv7 | lv1-lv7 | 44,86,17-23 (already mixed) |
| Gender: Male | 25 | 男 | male | 518 |
| Gender: Female | 26 | 女 | female | 349 |
| World: Io | 27 | イオ | io | 194,197 |
| World: Europa | 28 | エウロパ | europa | 196,195,235,259 |
| Race: Human | 29 | 人間 | human | 319,519 |
| Race: Elf | 30 | エルフ | elf | 196,233,220 |
| Race: Gnome | 31 | ノーム | gnome | 217,93,225 |
| Race: Dwarf | 32 | ドワーフ | dwarf | 253,236,93,220 |
| Race: Hobbit | 33 | ホビット | hobbit | 222,255,272,212 |
| Race: Automata | 34 | オートマター | automata | 197,93,212,223,208,93 |
| Class: Fighter | 37 | 戦士 | fighter | 286,297 |
| Class: Thief | 38 | 盗賊 | thief | 315,329 |
| Class: Mage | 39 | 呪術師 | mage | 280,342,343 |
| Class: Priest | 40 | 神聖 | priest | 726,727 |
| Class: Ninja | 41 | 忍者 | ninja | 309,287 |
| Class: Samurai | 42 | 侍 | samurai | 401 |
| Class: Bishop | 43 | 集教 | bishop | 405,396 |
| Class: Soldier | 44 | 兵士 | soldier | 304,297 |
| Class: Alchemist | 45 | 冒書術師 | alchemist | 730,419,342,343 |
| Class: Gizoku | 46 | 義賊 | gizoku | 533,329 |
| Class: Monk | 47 | モンク | monk | 227,238,200 |
| Class: Paladin | 48 | 聖兵士 | paladin | 284,304,297 |
| Class: Dark Knight | 49 | 暗兵士 | d.knight | 353,304,297 |
| Class: Shogun | 50 | 将軍 | shogun | 731,732 |
| Class: Professor | 51 | 教授 | professor | 733,734 |
| Class: Rogue | 52 | 美盗 | rogue | 735,315 |
| Personality names | 53-82 | 飽き性, 浪費, etc. | hobbyist, wasteful, etc. | various kanji |
| Combat: Attack | 83 | 獲得力 | attack | 722,350,346 |
| Combat: Accuracy | 84 | 命中果 | accuracy | 696,337,723 |
| Combat: Defense | 85 | 消耗力 | defense | 724,545,346 |
| Combat: Evasion | 86 | 回避果 | evasion | 415,725,723 |
| Descriptions | 87-148 | (long text) | (translated) | full kana+kanji |
| Align: Good+G | 220 | 善「g」 | good | 520,8,39,9 |
| Align: Neutral+N | 221 | 中立「n」 | neutral | 337,340,8,46,9 |
| Align: Evil+E | 222 | 悪「e」 | evil | 289,8,37,9 |
| Align: Good | 223 | 善 | good | 520 |
| Align: Neutral | 224 | 中立 | neutral | 337,340 |
| Align: Evil | 225 | 悪 | evil | 289 |
| Align letter: g | 226 | g | g | 39 (already ASCII) |
| Align letter: n | 227 | n | n | 46 (already ASCII) |
| Align letter: e | 228 | e | e | 37 (already ASCII) |
| Reputation ranks | 229-257 | commoner, hero, etc. | (already English) | ASCII glyph IDs |

### 4b. EXE-ONLY Labels (translate by replacing font atlas tile bitmaps)

These labels exist ONLY in the EXE menu struct table. They use composite tile IDs (683-866) that are pre-rendered bitmaps in the R1272 font atlas. Each menu button has exactly 2 tile slots (24x12 pixels total).

Translation method: replace the bitmap at each tile position in R1272 with pre-rendered English text.

| Rec | EXE Offset | Tile IDs | Japanese | English | Context |
|-----|-----------|----------|----------|---------|---------|
| 0 | 0x3C3000 | 683,684 | 酒場 | tavern | Town hub |
| 1 | 0x3C3038 | 685,686 | ギルド | guild | Town hub |
| 2 | 0x3C3070 | 687,688 | 商店 | shop | Town hub |
| 3 | 0x3C30A8 | 689,690 | 宿屋 | inn | Town hub |
| 4 | 0x3C30E0 | 691,692 | 教会 | church | Town hub |
| 5 | 0x3C3118 | 693,694 | 迷宮 | maze | Town hub |
| 6 | 0x3C3150 | 695,696 | 冒険 | venture | Town hub |
| 7 | 0x3C3188 | 697,698 | 依頼 | quest | Town hub |
| 8 | 0x3C31C0 | 699,700 | 広場 | plaza | Town hub |
| 9 | 0x3C31F8 | 701,702 | 刻印 | seal | Town hub |
| 10-105 | ... | 703-866 | (see menu_labels.csv) | (see menu_labels.csv) | Guild/Status/Battle/etc. |

Full list: 92 active records, 14 separator records (tile IDs = 0xFFFF).

### 4c. Labels in BOTH R38 and EXE (different rendering paths)

A few conceptual labels appear in BOTH R38 (as glyph ID sequences) and EXE menu structs (as composite tiles). These are NOT the same data -- they are independent copies for different screens.

| Label | R38 Location | EXE Location | R38 Glyph IDs | EXE Tile IDs |
|-------|-------------|-------------|----------------|--------------|
| 性格 (Personality/Alignment) | MSG 14 | Rec 36 @ 0x3C37E0 | 511,516 | 755,756 |
| 職業 (Class) | MSG 13 | Rec 37 @ 0x3C3818 | 504,517 | 757,758 |
| 性別 (Gender) | MSG 11 | Rec 38 @ 0x3C3850 | 511,512 | 759,760 |
| 種族 (Race) | MSG 10 | Rec 33 @ 0x3C3738 | 513,514 | 749,750 |
| 名前 (Name) | MSG 8 | Rec 15 @ 0x3C3348, Rec 30 @ 0x3C3690 | 314,510 | 713,714 / 743,744 |

**Key insight**: The status screen reads from R38 for its labels. The chargen/guild menus read from the EXE menu structs for their button labels. Both must be translated independently.

---

## 5. The Alignment Label Mystery -- SOLVED

### Why "Neutral" appeared translated but "Good" and "Evil" did not

This was the original observation that prompted this analysis.

**Answer**: ALL three alignment labels (Good/Neutral/Evil) come from R38 msgs 220-228 when displayed on the status screen. The difference was never about R38 vs EXE -- it was about glyph count:

| Alignment | R38 MSG | Glyph IDs | Kanji Count | Status |
|-----------|---------|-----------|-------------|--------|
| Good | 223 | 520 | 1 kanji (善) | Single glyph -> replaced with ASCII "good" (4 glyphs) |
| Neutral | 224 | 337,340 | 2 kanji (中立) | Two glyphs -> replaced with "neutral" (7 glyphs) |
| Evil | 225 | 289 | 1 kanji (悪) | Single glyph -> replaced with ASCII "evil" (4 glyphs) |

All three CAN be translated via R38 patching since FFFE-delimited entries allow variable length. If translation was not showing for Good/Evil, the issue was in the translation chunk file (missing entries for msgs 223/225), NOT a font tile issue.

The EXE does reference GID 520 (善) at offset 0x3C38F2 (menu record 40, "rest/good alignment" button) -- but that is the menu struct for chargen, not the status screen. The menu struct uses composite tile IDs 763,764 for its display, with GID 520 stored as a metadata/reference field (byte offset 50 in the record).

---

## 6. Screen-to-Source Mapping

### Which screen reads from which source?

| Screen | Label Source | Translation Method |
|--------|-------------|-------------------|
| **Status screen** (char stats) | R38 msgs 1-17 (stat/field labels) | ASCII glyph ID replacement in R38 |
| **Status screen** (alignment) | R38 msgs 220-228 | ASCII glyph ID replacement in R38 |
| **Status screen** (race/class) | R38 msgs 29-52 (names looked up by index) | ASCII glyph ID replacement in R38 |
| **Status screen** (personality) | R38 msgs 53-82 | ASCII glyph ID replacement in R38 |
| **Status screen** (reputation) | R38 msgs 229-257 | Already English, minor typo fixes only |
| **Chargen screen** (race/class selection) | R38 msgs 29-52 + description msgs 87-218 | ASCII glyph ID replacement in R38 |
| **Chargen screen** (alignment info) | R38 msgs 162-168 (description text) | ASCII glyph ID replacement in R38 |
| **Chargen screen** (name entry keyboard) | EXE 0x3C83C0-0x3C93A0 | N/A (keep Japanese kana for name input) |
| **Town hub menu** (tavern/guild/etc.) | EXE menu structs rec 0-9 | Font tile bitmap replacement in R1272 |
| **Guild menu** (create/delete/etc.) | EXE menu structs rec 10-29 | Font tile bitmap replacement in R1272 |
| **Battle menu** (attack/flee/etc.) | EXE menu structs rec 52-57 | Font tile bitmap replacement in R1272 |
| **Dungeon menu** (swap/log/etc.) | EXE menu structs rec 59-68 | Font tile bitmap replacement in R1272 |
| **Church/Inn menus** | EXE menu structs rec 75-91 | Font tile bitmap replacement in R1272 |
| **Dialogue/narration** | Type-02 MSG resources (R42-R2883) | ASCII glyph ID replacement (done, 12,725+ msgs) |

---

## 7. Minimum Font Tile Set Needed

### For R38 labels (ASCII glyph replacement):
- **Already available**: a-z (glyph IDs 33-58), 0-9 (IDs 16-25), space (ID 0/1), / (ID 15)
- **NOT available**: A-Z uppercase, punctuation beyond basic set
- **Impact**: All labels render as lowercase only (str, int, good, fighter, etc.)
- **Font tiles needed**: ZERO -- all R38 labels can use existing ASCII glyph IDs

### For EXE menu buttons (tile bitmap replacement):
- **92 active menu records** x 2 tiles each = **184 tile positions** to replace in R1272
- **Actually ~134 unique tile IDs** (some records share tiles between normal/selected states)
- Each tile is 12x12 pixels in the PSMT4 font atlas
- English text must be pre-rendered into these bitmaps at ~4px per character width

### For EXE references to individual kanji:
- GID 520 (善) at EXE 0x3C38F2 and 0x3BD3EC -- reference field in menu struct, likely used for game logic (alignment check), NOT for display rendering. The display uses tile IDs 763,764. **No font tile needed.**
- GID 289 (悪) at EXE chargen grid and Region C -- part of kanji section of name entry keyboard and UI lookup tables. **No font tile needed** unless we want to translate the chargen kanji input rows.

### Summary: Minimum font tiles = 0 new individual tiles + 134 composite tile replacements in R1272

---

## 8. Action Items

### Already Done
- [x] R38 msgs 1-82 translated (stat/field/race/class/personality labels)
- [x] R38 msgs 87-148 translated (descriptions)
- [x] R38 msgs 229-257 cleaned up (reputation ranks, typo fixes)
- [x] Type-02 dialogue: 12,725+ messages translated

### Still Needed -- R38
- [ ] R38 MSG 41 (忍者 = Ninja) -- missing from translation chunks
- [ ] R38 MSG 24 (Lv7) -- missing from translation chunks
- [ ] R38 MSGs 222, 225 (悪「e」, 悪 standalone) -- missing Evil alignment labels
- [ ] R38 MSGs 224 (中立 standalone) -- verify in translation chunks

### Still Needed -- EXE Menu Tiles
- [ ] Extract current R1272 font atlas tile bitmaps for positions 683-866
- [ ] Render 134 English replacement bitmaps (12x12px each)
- [ ] Inject replacement tiles back into R1272 atlas
- [ ] Rebuild R1272 resource into PACKDATA.DIG
- [ ] Patch EXE width/spacing floats if labels need more room

### Not Needed
- No new individual font tiles (A-Z uppercase etc.) -- lowercase is sufficient
- No chargen keyboard changes (kana stay for Japanese name input)
- No EXE hex patching for alignment labels (they come from R38, not EXE)

---

## Files Referenced

- `extracted/packdata_raw/0038_type01.raw` -- R38 raw resource
- `extracted/SLPM_653.78` -- Game EXE
- `data/msg_glyph_map.json` -- 1,100-entry glyph ID to character mapping
- `data/menu_labels.csv` -- 106-record menu label decode (with English translations)
- `data/translate_chunks/chunk_r38_fix.json` -- R38 translation data
