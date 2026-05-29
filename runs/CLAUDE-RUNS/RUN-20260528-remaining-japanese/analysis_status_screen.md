# Status/Character Screen -- Complete Japanese Label Analysis

**Date**: 2026-05-28
**Analyst**: Claude Opus 4.6

---

## Executive Summary

The status/character screen draws its Japanese labels from **three sources**:

| Source | Count | Translation Status |
|--------|-------|--------------------|
| R38 (type-01 MSG resource) | ~87 labels + ~55 descriptions | 178/190 messages translated in chunk_r38_fix.json |
| EXE Table 2C (menu label structs) | ~119 records (icon + 2 label glyphs each) | **0% translated** -- 359 unmapped glyph IDs |
| Textures (baked into PSMT4/PSMT8) | None for status screen | N/A -- cockpit/status labels are glyph-rendered, not texture-baked |

**No texture resources** contain status screen UI frames with Japanese text. All status screen labels are rendered at runtime from glyph IDs.

---

## Source 1: R38 (Resource 38, type-01 MSG)

**File**: `extracted/packdata_raw/0038_type01.raw` (8,192 bytes, 190 messages)

### R38 Message Map

#### Stat Labels (msgs 1-18) -- STATUS SCREEN CORE

| MSG | Japanese | English (translated) | Screen Location |
|-----|----------|---------------------|-----------------|
| 1 | HP | HP | Status: HP display (short form) |
| 2 | HP/MHP | HP/MHP | Status: HP/Max HP display |
| 3 | 力 | STR | Stat label |
| 4 | 知恵 | INT | Stat label |
| 5 | 信仰心 | FTH | Stat label |
| 6 | 生命力 | VIT | Stat label |
| 7 | 敏捷度 | AGI | Stat label |
| 8 | 幸運度 | LCK | Stat label |
| 9 | 名前 | Name | Status header |
| 10 | レベル | Level | Status header |
| 11 | 種族 | Race | Status header |
| 12 | 果別 | Gender | Status header |
| 13 | 条果 | Alignment | Status header |
| 14 | 職業 | Class | Status header |
| 15 | 果性 | Personality | Status header |
| 16 | 騎事務騎法 | Sorcery | Magic tab |
| 17 | 神聖騎法 | Holy Magic | Magic tab |
| 18 | 能力値 | Attributes | Status tab header |

#### Spell Level Labels (msgs 19-26)

| MSG | Japanese | English | Notes |
|-----|----------|---------|-------|
| 19 | Lv1 | Lv1 | Already ASCII-like |
| 20 | Lv2 | Lv2 | |
| 21 | Lv3 | Lv3 | |
| 22 | Lv4 | Lv4 | |
| 23 | Lv5 | Lv5 | |
| 24 | Lv6 | Lv6 | |
| 25 | Lv7 | Lv7 | **MISSING from chunk_r38_fix** |
| 26 | (unknown glyph 0206) | ? | **MISSING from chunk_r38_fix** |

#### Race Names (msgs 27-35)

| MSG | Japanese | English | Notes |
|-----|----------|---------|-------|
| 27 | イオ | Io | Moon race |
| 28 | エウロパ | Europa | Moon race |
| 29 | 人壁 | Human | |
| 30 | エルフ | Elf | |
| 31 | ノーム | Gnome | |
| 32 | ドワーフ | Dwarf | |
| 33 | ホビット | Hobbit | |
| 34 | オートマター | Automata | |
| 35 | (katakana string) | ? | **MISSING from chunk** -- likely "Celestia" or unused race |
| 36 | (null) | -- | Empty/spacer, **MISSING from chunk** |

#### Class Names (msgs 37-53)

| MSG | Japanese | English |
|-----|----------|---------|
| 37 | (null) | -- (spacer) |
| 38 | 戦士 | Fighter |
| 39 | 盗賊 | Thief |
| 40 | 騎事務 | Mage |
| 41 | 神聖 | Priest |
| 42 | 忍者 | Ninja | **MISSING from chunk** |
| 43 | 集教 | Bishop |
| 44 | 兵士 | Samurai |
| 45 | 冒金事務 | Alchemist |
| 46 | 義賊 | Gizoku |
| 47 | モンク | Monk |
| 48 | 聖兵士 | Paladin |
| 49 | 暗兵士 | Dark Knight |
| 50 | 将後 | Shogun |
| 51 | 教授 | Knight |
| 52 | 美盗 | High Thief |
| 53 | 飽き果 | Omnitsu |

#### Personality Names (msgs 54-82)

29 personality trait names. All translated in chunk_r38_fix.json. Examples:
- MSG 54: 武 -> Militant
- MSG 55: 浪費 -> Wasteful
- MSG 56: 孤独 -> Lonely
- MSG 57: 社交的 -> Sociable
- (full list in chunk_r38_fix.json)

#### Combat Stat Labels (msgs 83-87)

| MSG | Japanese | English |
|-----|----------|---------|
| 83 | 獲得力 | Attack |
| 84 | 命中果 | Accuracy |
| 85 | 解消力 | Defense |
| 86 | 回避果 | Evasion |
| 87 | (compound) | ? (battle stat) |

#### Personality Descriptions (msgs 88-116)

29 personality description paragraphs (1-2 lines each). All translated. Shown on character creation/inspection screens.

#### Gender/Race/Alignment Descriptions (msgs 117-125)

Help text for character creation. All translated.

#### Class Descriptions (msgs 126-142)

17 class description paragraphs. All translated. Shown during class selection.

#### Stat Explanations (msgs 143-148)

6 messages explaining what each stat does. All translated.

#### Alignment Display Labels (msgs 149-157)

| MSG | Japanese | English | Notes |
|-----|----------|---------|-------|
| 149 | 善 "G" | Good "G" | |
| 150 | 中立 "N" | Neutral "N" | |
| 151 | 悪 "E" | Evil "E" | **MISSING from chunk** |
| 152 | 善 | Good | Short form |
| 153 | 中立 | Neutral | **MISSING from chunk** (short form) |
| 154 | 悪 | Evil | **MISSING from chunk** (short form) |
| 155 | G | G | **MISSING** (already ASCII) |
| 156 | N | N | **MISSING** (already ASCII) |
| 157 | E | E | Already in chunk |

#### Title/Rank Names (msgs 158-189)

Reputation ranks. All already in English in the original game data (commoner, hooligan, evil, venom fang, villain, gangster, etc.). Some have original typos (e.g. "clurelty" for "cruelty", "norble" for "noble", "dengerous" for "dangerous"). chunk_r38_fix.json corrects these.

MSG 188: "god hand" -- last real entry
MSG 189: null padding (all zeros)

### R38 Translation Coverage

- **178 of 190 messages** have translations in chunk_r38_fix.json
- **12 messages missing** from chunk:
  - MSG 25: "Lv7" (spell level label)
  - MSG 26: Unknown single glyph 0x0206
  - MSG 35: Katakana race name (possibly unused)
  - MSG 36: Null/spacer
  - MSG 37: Null/spacer (class)
  - MSG 42: 忍者 = "Ninja"
  - MSG 151: 悪 "E" = Evil "E"
  - MSG 153: 中立 = "Neutral" (short)
  - MSG 154: 悪 = "Evil" (short)
  - MSG 155: "G" (single letter, already ASCII)
  - MSG 156: "N" (single letter, already ASCII)
  - MSG 188: "god hand" (already English)
  - MSG 189: Null padding

- **Critical missing**: MSG 25 (Lv7), MSG 42 (Ninja), MSG 151/153/154 (alignment labels)
- **Non-critical missing**: MSG 26, 35, 36, 37, 155, 156, 188, 189 (spacers/ASCII/padding)

---

## Source 2: EXE Table 2C -- Menu Label Structs

**File**: `extracted/SLPM_653.78`
**Offset**: 0x3C3000-0x3C5300 (8,960 bytes)
**Format**: 56-byte records, ~119 entries

### Structure

Each record contains:
- Icon glyph (1 kanji)
- Label pair (2 kanji, normal + selected states)
- Reference glyph (1 kanji)

These render the **menu option labels** seen throughout the game, including on the status screen tabs/buttons. All glyph IDs are in the 0x01DB-0x0376 range (475-886), which is **entirely unmapped** in msg_glyph_map.json.

### Status Screen Relevance

Table 2C contains labels for:
- Status screen tab buttons (Stats, Equipment, Skills, Magic, etc.)
- Menu actions available from the status screen (Equip, Unequip, Use, etc.)
- Sub-menu navigation labels

### Translation Status: **BLOCKED**

All 359 unique glyph IDs used in Table 2C are unmapped. Before any translation can proceed:
1. These glyph IDs must be visually identified from the font atlas
2. Added to `data/msg_glyph_map.json`
3. Then the menu labels can be decoded and translated
4. Finally, English glyph IDs must replace the Japanese ones in the EXE

### Known Record Purposes (from recon_exe_tables.md)

| Record Range | Likely Purpose |
|-------------|----------------|
| 0-5 | Main cockpit/hub menu buttons |
| 6-7 | Adventure start/end |
| 8-9 | Party management |
| 10-11 | Equipment/item management |
| 12-13 | Character naming |
| 14-16 | Options/settings |
| 17-28 | Sub-menu items (shopping, quest, etc.) |
| 29+ | Status screen and battle menu items |

---

## Source 3: Textures -- NOT a factor for status screen

Based on thorough investigation:

1. **R2118-R2124** are demo disc screens, not cockpit/status UI
2. **R1215-R1346** are NPC/monster portraits
3. **R1900** is a coffin/gravestone texture
4. **PCSX2 texture dumps** confirm status screen labels are glyph-rendered

**The status screen has NO texture-baked Japanese text.** All labels come from R38 or EXE glyph ID tables.

---

## Source 4: EXE Table 2B -- Chargen Kana Grid (NOT status screen)

**Offset**: 0x3C83C0-0x3C93A0

Despite initial assumption, this table is the **character name input kana grid**, not status screen labels. It contains hiragana/katakana for the name entry keyboard. Relevant to the name entry screen, not the status/character screen.

---

## Complete Label Inventory: Status/Character Screen

### From R38 (MSG glyph system, runtime-rendered)

| Category | Labels | Source | Translated? |
|----------|--------|--------|-------------|
| Character header | Name, Level, Race, Gender, Alignment, Class, Personality | R38 msgs 9-15 | YES |
| Core stats | STR, INT, FTH, VIT, AGI, LCK | R38 msgs 3-8 | YES |
| HP display | HP, HP/MHP | R38 msgs 1-2 | YES |
| Magic tabs | Sorcery, Holy Magic | R38 msgs 16-17 | YES |
| Attributes header | Attributes | R38 msg 18 | YES |
| Spell levels | Lv1-Lv7 | R38 msgs 19-25 | Lv1-6 YES, Lv7 MISSING |
| Combat stats | Attack, Accuracy, Defense, Evasion | R38 msgs 83-86 | YES |
| Race names | Human, Elf, Gnome, Dwarf, Hobbit, Automata, Io, Europa | R38 msgs 27-34 | YES |
| Class names | Fighter, Thief, Mage, Priest, Ninja, Bishop, Samurai, Alchemist, Gizoku, Monk, Paladin, Dark Knight, Shogun, Knight, High Thief, Omnitsu | R38 msgs 38-53 | Ninja MISSING, rest YES |
| Personality names | 29 traits (Militant through Hobbyist) | R38 msgs 54-82 | YES |
| Alignment labels | Good/Neutral/Evil (long + short + letter forms) | R38 msgs 149-157 | 5 of 9 translated |
| Stat descriptions | 6 stat help texts | R38 msgs 143-148 | YES |
| Class descriptions | 17 class help texts | R38 msgs 126-142 | YES |
| Personality descriptions | 29 personality help texts | R38 msgs 88-116 | YES |
| Race descriptions | 6 race help texts | R38 msgs 117-122 | YES |
| Alignment descriptions | 3 alignment help texts | R38 msgs 123-125 | YES |
| Gender description | 1 gender help text | R38 msg 117 | YES |
| Title ranks | 30 reputation titles | R38 msgs 158-188 | YES (already English) |

### From EXE Table 2C (hardcoded glyph IDs)

| Category | Labels | Source | Translated? |
|----------|--------|--------|-------------|
| Status screen tabs/buttons | ~20-30 menu option labels | EXE 0x3C3000+ | **NO -- all glyph IDs unmapped** |
| Sub-menu actions | Equip, Use, Drop, etc. | EXE 0x3C3000+ | **NO** |

### From EXE Other Tables

| Category | Labels | Source | Translated? |
|----------|--------|--------|-------------|
| Equipment type icons | 12 weapon/armor type labels | EXE Table 2J (0x3F9D00) | NO -- bitmap font refs |
| Name entry tabs | 10 tab labels (hiragana/katakana/etc.) | EXE Table 2E (0x3C9DA0) | NO -- bitmap font refs |
| NPC names | Emilia, Lute | EXE Table 2F (0x3C93B0) | NO -- need glyph replacement |

---

## Priority Action Items

### P0 -- Critical Missing Translations (R38)
1. Add MSG 42 (忍者 = Ninja) to chunk_r38_fix.json
2. Add MSG 25 (Lv7) to chunk_r38_fix.json
3. Add MSG 151 (悪 "E" = Evil "E") to chunk_r38_fix.json
4. Add MSG 153 (中立 = Neutral), MSG 154 (悪 = Evil) to chunk_r38_fix.json

### P1 -- EXE Table 2C Glyph Mapping
1. Map all 359 glyph IDs in the 0x01DB-0x0376 range
2. Decode every Table 2C record to readable Japanese
3. Create English translations for each menu label
4. Build EXE patcher to replace glyph IDs

### P2 -- EXE Bitmap Font References
1. Find the PACKDATA resources containing bitmap fonts for IDs 6400-6409 (tab labels) and 2036-2047 (equipment types)
2. Edit those textures to show English labels
3. Patch EXE references if texture layout changes

### P3 -- Minor EXE Strings
1. Patch NPC names (Emilia, Lute) from katakana to ASCII glyph IDs
2. Patch SJIS strings: "Continue Load", "No one to equip to"

---

## Files Referenced

- `extracted/packdata_raw/0038_type01.raw` -- R38 raw data
- `data/translate_chunks/chunk_r38_fix.json` -- R38 translations (178 entries)
- `data/translate_chunks/chunk_01_translated.json` -- R38 msgs 0-11
- `data/translate_chunks/chunk_02_translated.json` -- R38 msgs 12-130
- `data/translate_chunks/chunk_03_translated.json` -- R38 msgs 131-187
- `extracted/SLPM_653.78` -- Game EXE with Table 2C at 0x3C3000
- `data/msg_glyph_map.json` -- Glyph ID to character mapping (1100 entries)
- `runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/recon_exe_tables.md` -- Prior EXE table analysis
- `runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/recon_cockpit_textures.md` -- Texture analysis confirming no baked UI text
