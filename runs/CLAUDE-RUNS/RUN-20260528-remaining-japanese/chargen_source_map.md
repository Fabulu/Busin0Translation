# Chargen Screen: Definitive Visual Element Source Map

**Date**: 2026-05-28
**Analyst**: Claude Opus 4.6
**Sources**: Save states 19-1 through 19-8, savestate_analysis_19_1.md, chargen_ui_layout.md, r38_vs_exe_crossref.md, exe_chargen_deep.md, analysis_composite_atlas.md, debug_name_entry_tabs.md

---

## Legend

| Abbreviation | Meaning | Translation Method |
|---|---|---|
| **R37** | PACKDATA resource 37, type-01 MSG glyph stream | Replace glyph IDs in chunk_r37_*.json |
| **R38** | PACKDATA resource 38, type-01 MSG glyph stream | Replace glyph IDs in chunk_r38_fix.json |
| **R1188** | PACKDATA resource 1188, 1024x1024 PSMT4 bitmap atlas | Edit pixel data at correct UV + fix header UVs, or PCSX2 tex replacement |
| **R1272** | PACKDATA resource 1272, 256x512 PSMT4 font atlas | Replace 12x12 tile bitmaps for composite tiles |
| **EXE** | SLPM_653.78 data section (menu structs, glyph tables) | Patch glyph ID references or 56-byte menu struct records |
| **TEX** | Pre-rendered decorative texture (embedded in a PACKDATA resource) | Already English in original game |

### Status Key

| Symbol | Meaning |
|---|---|
| OK | Correctly translated and rendering in English |
| BUG | Translation data exists but renders incorrectly (wrong mapping, overflow, etc.) |
| JP | Still displays Japanese -- no translation wired in |
| N/A | Language-neutral or intentionally Japanese (kana input grids) |

---

## PHASE 1: Name Entry Screen (Save State 19-1)

```
+==============================================================+
|  [A: 新規登録]  [B: 名前を入力してください。]                   |
|  (red banner)   [B: (男名・女名＝名前を自動で入力)]             |
|                                                              |
|  [C: *Name*]                   _ _ _ _ _ _   [C: Level 1]    |
|                                                              |
|  +--[D: character grid]-----+  [E: カナ]                     |
|  | A B C D E  a b c d e     |  [E: かな]                     |
|  | F G H I J  f g h i j     |  [E: 英数]                     |
|  | K L M N O  k l m n o     |  [E: 記号]                     |
|  | P Q R S T  p q r s t     |                                |
|  | U V W X Y  u v w x y     |  [E: 男名]                    |
|  | Z          z             |  [E: 女名]                    |
|  | 1 2 3 4 5  6 7 8 9 0     |  [E: 決定]                    |
|  +---------------------------+                                |
|  [ornamental border - language neutral]                      |
+==============================================================+
```

| ID | Visual Element | Japanese | Source | Glyph IDs / Detail | Status | Notes |
|----|---------------|----------|--------|-------------------|--------|-------|
| 1A | Red title banner | 新規登録 | **EXE** composite glyph IDs via R1272 font tiles | Rendered at GS page 0x2214 (120x24px); glyph IDs from EXE data section | **JP** | Requires EXE patch to swap glyph IDs to Latin, or R1272 tile replacement. PCSX2 tex replacement PNG exists. |
| 1B | Instruction line 1 | 名前を入力してください。 | **R37** MSG 2 | Glyph stream, chunk_r37_r48_r49 | **BUG** | Translated ("Enter your name.") but OVERFLOWS to 4 lines due to double word-wrapping in encode_text(). |
| 1B2 | Instruction line 2 | (男名・女名＝名前を自動で入力) | **R37** MSG 2 (continued) | Same message, second sentence | **BUG** | "m name/f name: auto-fill" -- overflow issue. |
| 1C1 | "Name" header | *Name* | **TEX** (pre-rendered, page 0x2254) | Decorative italic script texture | **OK** | Already English in original game. |
| 1C2 | "Level" label | Level 1 | **TEX** (pre-rendered, page 0x2254) | Decorative texture | **OK** | Already English in original game. |
| 1D | Character grid (ABC mode) | A-Z, a-z, 0-9 | **R37** MSG 20 + **R1272** main font | Latin glyphs already present | **OK** | Working. |
| 1D2 | Character grid (kana modes) | あいうえお / アイウエオ | **R37** MSG 18-19 + **EXE** 0x3C83C0 kana grid | Hiragana/katakana keyboard tiles | **N/A** | Intentionally Japanese -- kana input for JP character names. |
| 1D3 | Character grid (symbol mode) | Symbols | **R37** MSG 21 | Symbol characters | **OK** | Translated. |
| 1E1 | Tab: カナ | カナ (Katakana) | **R1188** glyph 6400 (group 0x19:0x00) | Bitmap sprite from R1188 atlas; R37 MSG 12 has "kana" but tab button uses R1188 bitmap | **JP** | R1188 bitmap not edited at correct UV. PCSX2 tex replacement exists. |
| 1E2 | Tab: かな | かな (Hiragana) | **R1188** glyph 6401 (group 0x19:0x01) | Same mechanism as 1E1; R37 MSG 13 = "kana" | **JP** | Same fix needed as 1E1. |
| 1E3 | Tab: 英数 | 英数 (Alphanumeric) | **R1188** glyph 6402 (group 0x19:0x02) | R37 MSG 15 = "abc" but tab uses R1188 bitmap | **JP** | Same fix needed. |
| 1E4 | Tab: 記号 | 記号 (Symbols) | **R1188** glyph 6403 (group 0x19:0x03) | R37 MSG 14 = "sym" but tab uses R1188 bitmap | **JP** | Same fix needed. R37 MSG 14 was previously "Count" (wrong), should be "sym". |
| 1E5 | Button: 決定 | 決定 (Confirm/OK) | **R1188** glyph 6405 (group 0x19:0x05) | R37 MSG 17 = "ok" but button uses R1188 bitmap | **JP** | Same fix needed. |
| 1E6 | Button: 男名 | 男名 (Male Name) | **R1188** glyph 6406 (group 0x19:0x06) | R37 MSG 122 = "M name" but button uses R1188 bitmap | **JP** | Same fix needed. |
| 1E7 | Button: 女名 | 女名 (Female Name) | **R1188** glyph 6407 (group 0x19:0x07) | R37 MSG 123 = "F name" but button uses R1188 bitmap | **JP** | Same fix needed. |
| 1F | Name display dashes | ------ | UI frame element | Language-neutral | **N/A** | |
| 1G | Ornamental frame | Decorative scroll | Pre-rendered texture | Language-neutral | **N/A** | |

---

## PHASE 2: Gender Selection (Save State 19-2)

| ID | Visual Element | Japanese | Source | Glyph IDs / Detail | Status | Notes |
|----|---------------|----------|--------|-------------------|--------|-------|
| 2A | Red title banner | 新規登録 | **EXE** composite glyphs via R1272 | Same as 1A -- persists all phases | **JP** | |
| 2B | Instruction text | 性別を選んでください。 | **R37** MSG 3 | "select gender." | **BUG** | Text appears stale (shows previous phase text). Likely save state timing artifact. |
| 2C | "Gender" header | *Gender* | **TEX** (pre-rendered, page 0x2254, 120x48) | Decorative italic script | **OK** | Already English. |
| 2D | Option: 男 (Male) | 男 | **R38** MSG 25 | GID 518 (男) | **BUG** | chunk_r38_fix.json has "lv.7" at MSG 25 instead of "male". Shows "lv.6" or "lv.7" in game. |
| 2E | Option: 女 (Female) | 女 | **R38** MSG 26 | GID 349 (女) -> "female" | **OK** | Correctly translated. |
| 2F | Description box | Gender description | **R38** MSGs 145-166 range | Glyph stream | **OK** | "Gender sets base stats. Men=strong, women=wise." |

---

## PHASE 3: Race Selection (Save State 19-3)

| ID | Visual Element | Japanese | Source | Glyph IDs / Detail | Status | Notes |
|----|---------------|----------|--------|-------------------|--------|-------|
| 3A | Red title banner | 新規登録 | **EXE** composite glyphs | Same as 1A | **JP** | |
| 3B | Instruction text | 種族を選んでください。 | **R37** MSG 4 | "select a race." | **BUG** | Shows stale "select gender." in save state. |
| 3C | "Race" header | *Race* | **TEX** (pre-rendered, page 0x2254, 88x48) | Decorative italic script | **OK** | Already English. |
| 3D1 | Option: 人間 | 人間 (Human) | **R38** MSG 29 | GIDs 319,519 -> "human" | **OK** | |
| 3D2 | Option: エルフ | エルフ (Elf) | **R38** MSG 30 | GIDs 196,233,220 -> "elf" | **OK** | |
| 3D3 | Option: ノーム | ノーム (Gnome) | **R38** MSG 31 | GIDs 217,93,225 -> "gnome" | **OK** | |
| 3D4 | Option: ドワーフ | ドワーフ (Dwarf) | **R38** MSG 32 | GIDs 253,236,93,220 -> "dwarf" | **OK** | |
| 3D5 | Option: ホビット | ホビット (Hobbit) | **R38** MSG 33 | GIDs 222,255,272,212 -> "hobbit" | **OK** | |
| 3D6 | Option: オートマター | オートマター (Automata) | **R38** MSG 34 | GIDs 197,93,212,223,208,93 -> "automata" | **OK** | |
| 3E | Description box | Race descriptions | **R38** MSGs 145-166 | Glyph stream | **OK** | Long English descriptions working. |
| 3F1 | Sidebar: 性別 | 性別 (Gender) | **EXE** menu struct rec 38 @ 0x3C3850 | Tile IDs 759,760 in R1272 | **JP** | EXE menu struct label; independent from R38 MSG 11. |
| 3F2 | Sidebar: 種族 | 種族 (Race) | **EXE** menu struct rec 33 @ 0x3C3738 | Tile IDs 749,750 in R1272 | **JP** | EXE menu struct label. |
| 3G | Sidebar value: gender | Shows "lv.6" | **R38** MSG 25 (looked up by index) | BUG: wrong msg_index | **BUG** | Same root cause as 2D. |
| 3H | Sidebar value: race | Shows "human" | **R38** MSG 29 (looked up by index) | Correct | **OK** | |

---

## PHASE 4: Alignment Selection (Save State 19-4)

| ID | Visual Element | Japanese | Source | Glyph IDs / Detail | Status | Notes |
|----|---------------|----------|--------|-------------------|--------|-------|
| 4A | Red title banner | 新規登録 | **EXE** composite glyphs | Same as 1A | **JP** | |
| 4B | Instruction text | 属性を選んでください。 | **R37** MSG 5 | "select alignment." | **BUG** | Shows stale "select a race." in save state. |
| 4C | "Attribute" header | *Attribute* | **TEX** (pre-rendered, page 0x2254, 152x48) | Decorative italic script | **OK** | Original game uses "Attribute" for alignment. |
| 4D1 | Option: 善「g」 | 善「g」 (Good "g") | **R38** MSG 148 | GIDs 520,8,39,9 -> good "g" | **OK** | First alignment label correct. |
| 4D2 | Option: 中立「n」 | 中立「n」 (Neutral "n") | **R38** MSG 149 | GIDs 337,340,8,46,9 | **BUG** | Shows "good \"g\"" -- shifted by one in chunk. Should be neutral "n". |
| 4D3 | Option: 悪「e」 | 悪「e」 (Evil "e") | **R38** MSG 150 | GIDs 289,8,37,9 | **BUG** | Shows "neutral \"n\"" -- shifted by one. Should be evil "e". |
| 4E | Description box | Alignment descriptions | **R38** MSGs 145-166 range | Glyph stream | **OK** | English descriptions working but garbled class list formatting noted. |
| 4F1 | Sidebar: 性別 | 性別 (Gender) | **EXE** menu struct rec 38 | Tile IDs 759,760 | **JP** | |
| 4F2 | Sidebar: 種族 | 種族 (Race) | **EXE** menu struct rec 33 | Tile IDs 749,750 | **JP** | |

---

## PHASE 5: Class Selection & Stat View (Save State 19-5)

| ID | Visual Element | Japanese | Source | Glyph IDs / Detail | Status | Notes |
|----|---------------|----------|--------|-------------------|--------|-------|
| 5A | Red title banner | 新規登録 | **EXE** composite glyphs | Same as 1A | **JP** | |
| 5B | Instruction text | 職業を選んでください。 | **R37** MSG 6 | "select a class." | **OK** | Correct for this phase. |
| 5C | "Class&Parameter" header | *Class&Parameter* | **TEX** (pre-rendered, page 0x2254, 248x48) | Decorative italic script | **OK** | Already English. |
| 5D | Class names (all 16) | 戦士, 盗賊, 呪術師... | **R38** MSGs 37-52 | GID sequences -> "fighter", "thief", "mage", etc. | **OK** | All 16 translated correctly. |
| 5E1 | Stat: 力 | 力 (STR) | **R38** MSG 2 | GID 346 -> "str" | **OK** in R38 data | **JP on screen** -- chargen stat display uses R1188 bitmap atlas, NOT R38. R38 version only used on party status screen. |
| 5E2 | Stat: 知恵 | 知恵 (INT) | **R38** MSG 3 | GIDs 535,717 -> "int" | **OK** in R38 data | **JP on screen** -- same R1188 issue. |
| 5E3 | Stat: 信仰心 | 信仰心 (FTH) | **R38** MSG 4 | GIDs 308,354,320 -> "fth" | **OK** in R38 data | **JP on screen** -- same R1188 issue. |
| 5E4 | Stat: 生命力 | 生命力 (VIT) | **R38** MSG 5 | GIDs 718,696,346 -> "vit" | **OK** in R38 data | **JP on screen** -- same R1188 issue. |
| 5E5 | Stat: 敏捷度 | 敏捷度 (AGI) | **R38** MSG 6 | GIDs 582,719,590 -> "agi" | **OK** in R38 data | **JP on screen** -- same R1188 issue. |
| 5E6 | Stat: 幸運度 | 幸運度 (LCK) | **R38** MSG 7 | GIDs 720,721,590 -> "lck" | **OK** in R38 data | **JP on screen** -- same R1188 issue. |
| 5F | Description box | Class descriptions | **R38** MSGs 167-218 | Glyph stream | **OK** | English descriptions working. |
| 5G | "Bonus Point" label | bonus point | **R37** MSG 9 | Already ASCII in original | **OK** | |
| 5H1 | Sidebar: 性別 | 性別 (Gender) | **EXE** menu struct rec 38 | Tile IDs 759,760 | **JP** | |
| 5H2 | Sidebar: 種族 | 種族 (Race) | **EXE** menu struct rec 33 | Tile IDs 749,750 | **JP** | |
| 5H3 | Sidebar: 属性 | 属性 (Alignment) | **EXE** menu struct (alignment rec) | Tile IDs from R1272 | **JP** | |
| 5I | 決定 (OK) button | 決定 | **R1188** or **EXE** | Context-dependent | **JP** | Confirm button on stat allocation. |

---

## PHASE 6: Personality Selection (no dedicated save state)

| ID | Visual Element | Japanese | Source | Glyph IDs / Detail | Status | Notes |
|----|---------------|----------|--------|-------------------|--------|-------|
| 6A | Red title banner | 新規登録 | **EXE** composite glyphs | Same as 1A | **JP** | |
| 6B | "Personality" header | *Personality* | **TEX** (pre-rendered, page 0x2254, 168x48) | Decorative italic script | **OK** | Already English. |
| 6C | 34 personality traits | 飽き性, 浪費, 孤独... | **R38** MSGs 53-86 | GID sequences -> "militant", "wasteful", "lonely", etc. | **OK** | All translated. |
| 6D | Personality descriptions | Long text | **R38** MSGs 87-144 | Glyph stream | **OK** | English descriptions working. |
| 6E1 | Sidebar: 性別 | 性別 | **EXE** menu struct | Same as previous phases | **JP** | |
| 6E2 | Sidebar: 種族 | 種族 | **EXE** menu struct | Same | **JP** | |
| 6E3 | Sidebar: 属性 | 属性 | **EXE** menu struct | Same | **JP** | |
| 6E4 | Sidebar: 職業 | 職業 (Class) | **EXE** menu struct rec 37 @ 0x3C3818 | Tile IDs 757,758 | **JP** | |

---

## PHASE 7: Stat Allocation (Save State 19-8)

| ID | Visual Element | Japanese | Source | Glyph IDs / Detail | Status | Notes |
|----|---------------|----------|--------|-------------------|--------|-------|
| 7A | Red title banner | 新規登録 | **EXE** composite glyphs | Same as 1A | **JP** | |
| 7B | Instruction text | 能力値を振り分けてください。 | **R37** MSG 7 | "allocate stat points." | **OK** | Correct. |
| 7C | "Status" header | *Status* | **TEX** (pre-rendered, page 0x2254, 168x56) | Decorative italic script | **OK** | Already English. |
| 7D | "Bonus point" label | bonus point | **R37** MSG 9 | Already ASCII | **OK** | |
| 7E1-6 | Stat labels (all 6) | 力, 知恵, 信仰心, 生命力, 敏捷度, 幸運度 | **R1188** bitmap atlas | Bitmap sprites at UV coords from R1188 header | **JP** | R38 has English but chargen renders from R1188 bitmap. |
| 7F1 | Sidebar: 性別 | 性別 | **EXE** menu struct | Tile IDs 759,760 | **JP** | |
| 7F2 | Sidebar: 種族 | 種族 | **EXE** menu struct | Tile IDs 749,750 | **JP** | |
| 7F3 | Sidebar: 属性 | 属性 | **EXE** menu struct | Tile IDs for alignment | **JP** | |
| 7F4 | Sidebar: 職業 | 職業 | **EXE** menu struct | Tile IDs 757,758 | **JP** | |
| 7G | HP/MAX label | HP / MAX | Original game | Already English | **OK** | |

---

## PHASE 8: Confirmation (Save State 19-7)

| ID | Visual Element | Japanese | Source | Glyph IDs / Detail | Status | Notes |
|----|---------------|----------|--------|-------------------|--------|-------|
| 8A | Red title banner | 新規登録 | **EXE** composite glyphs | Same as 1A | **JP** | |
| 8B | Confirmation prompt | これでよろしいですか？ | **R37** MSG 8 | "Is this OK?" | **OK** | |
| 8C | Yes option | はい | **R37** MSG 10 | "yes" | **OK** | |
| 8D | No option | いいえ | **R37** MSG 11 | "no" | **OK** | |
| 8E | Final confirm instruction | ○ボタンか×ボタンをおすと... | **R37** MSG 124 | "Press O or X button to confirm your choices." | **OK** | |
| 8F1-6 | Stat labels (all 6) | Same as 7E | **R1188** bitmap | Same as Phase 7 | **JP** | |
| 8G1-4 | Sidebar labels (all 4) | Same as 7F | **EXE** menu structs | Same as Phase 7 | **JP** | |
| 8H | Sidebar: 性格 | 性格 (Personality) | **EXE** menu struct rec 36 @ 0x3C37E0 | Tile IDs 755,756 | **JP** | Only appears on confirmation screen. |
| 8I | Personality text | Personality trait + descriptions | **R38** MSGs 53-86 | Glyph stream | **OK** | "believes in mystic power. loves magic." etc. |
| 8J | Character name | (entered name) | Player input / R37 auto-name | Shows "F name" in 19-7 | **BUG** | Test artifact: auto-name pulled from R37 MSG 123 ("F name") instead of actual name pool. |
| 8K | Gender value | Shows "lv.6" | **R38** MSG 25 | Same BUG as 2D | **BUG** | |
| 8L | Race value | human | **R38** MSG 29 | Correct | **OK** | |
| 8M | Class value + icon | fighter / FIG | **R38** MSG 37 + icon | Correct | **OK** | |

---

## Summary by Source Type

### SOURCE: R37 (PACKDATA resource 37 -- chargen prompts/labels)

| MSG | Japanese | English | Status | Phase(s) |
|-----|----------|---------|--------|----------|
| 2 | 名前を入力してください。(男名・女名＝名前を自動で入力) | Enter your name. [M name/F name: Auto-fill] | **BUG** (overflow) | 1 |
| 3 | 性別を選んでください。 | select gender. | OK | 2 |
| 4 | 種族を選んでください。 | select a race. | OK | 3 |
| 5 | 属性を選んでください。 | select alignment. | OK | 4 |
| 6 | 職業を選んでください。 | select a class. | OK | 5 |
| 7 | 能力値を振り分けてください。 | allocate stat points. | OK | 7 |
| 8 | これでよろしいですか？ | Is this OK? | OK | 8 |
| 9 | bonus point | bonus point | OK | 5,7 |
| 10 | はい | yes | OK | 8 |
| 11 | いいえ | no | OK | 8 |
| 12 | カナ | kana | OK (but R1188 tab is JP) | 1 |
| 13 | かな | kana | OK (but R1188 tab is JP) | 1 |
| 14 | 記号 | sym | OK (was "Count", now fixed) | 1 |
| 15 | 英数 | abc | OK (but R1188 tab is JP) | 1 |
| 17 | 決定 | ok | OK (but R1188 button is JP) | 1 |
| 18-21 | Keyboard grids | Latin + kana + symbols | OK / N/A | 1 |
| 122 | 男名 | M name | OK (but R1188 button is JP) | 1 |
| 123 | 女名 | F name | OK (but R1188 button is JP) | 1 |
| 124 | ○ボタンか×ボタン... | Press O or X button... | OK | 8 |
| 22-121 | Character name pools | Abel, Ash, Arno... (98 names) | OK | 1 (auto-name) |

### SOURCE: R38 (PACKDATA resource 38 -- stat/field/race/class labels)

| MSG | Japanese | English | Status | Phase(s) |
|-----|----------|---------|--------|----------|
| 0-1 | hp, hp/mhp | hp, hp/mhp | OK | 7,8 |
| 2-7 | 力, 知恵, 信仰心, 生命力, 敏捷度, 幸運度 | str, int, fth, vit, agi, lck | OK in data, **JP on chargen screen** (R1188 used instead) | 5,7,8 |
| 8-14 | 名前, レベル, 種族, 性別, 属性, 職業, 性格 | name, level, race, gender, alignment, class, personality | OK in data, **JP on chargen sidebar** (EXE menu structs used) | 7,8 |
| 18-24 | Lv1-Lv7 | lv1-lv7 | OK | 7,8 |
| 25 | 男 | **lv.7 (WRONG)** | **BUG** | 2,3,4,5,7,8 |
| 26 | 女 | female | OK | 2 |
| 29-34 | 人間, エルフ, ノーム, ドワーフ, ホビット, オートマター | human, elf, gnome, dwarf, hobbit, automata | OK | 3 |
| 37-52 | 戦士...美盗 (16 classes) | fighter...high thief | OK | 5 |
| 53-86 | Personality traits (34) | militant, wasteful, lonely... | OK | 6,8 |
| 87-144 | Personality descriptions | Long English text | OK | 6 |
| 145-166 | Race/alignment descriptions | Long English text | OK | 3,4 |
| 148 | 善「g」 | good "g" | OK | 4 |
| 149 | 中立「n」 | **good "g" (WRONG)** | **BUG** | 4 |
| 150 | 悪「e」 | **neutral "n" (WRONG)** | **BUG** | 4 |
| 151-156 | 善, 中立, 悪, g, n, e | **All shifted by one** | **BUG** | 4,8 |
| 167-218 | Class descriptions | Long English text | OK | 5 |

### SOURCE: R1188 (PACKDATA resource 1188 -- bitmap sprite atlas)

| Glyph ID | Japanese | English Target | Status | Phase |
|----------|----------|---------------|--------|-------|
| 6400 | カナ (Katakana tab) | KATA | **JP** | 1 |
| 6401 | かな (Hiragana tab) | HIRA | **JP** | 1 |
| 6402 | 英数 (Alphanumeric tab) | ABC | **JP** | 1 |
| 6403 | 記号 (Symbol tab) | SYM | **JP** | 1 |
| 6405 | 決定 (Confirm button) | OK | **JP** | 1 |
| 6406 | 男名 (Male Name button) | M.NAME | **JP** | 1 |
| 6407 | 女名 (Female Name button) | F.NAME | **JP** | 1 |
| 6408 | 一文字消す (Delete char) | DEL | **JP** | 1 |
| 6409 | 全削除 (Clear all) | CLR | **JP** | 1 |
| (stat area) | 力, 知恵, 信仰心, 生命力, 敏捷度, 幸運度 | STR, INT, FTH, VIT, AGI, LCK | **JP** | 5,7,8 |

**Fix approach**: Edit R1188 pixel data at correct UV positions (from R1188 header metadata at offsets 0x560-0x7C3), OR patch R1188 header UV data to redirect to English labels already rendered at y=1009-1020.

### SOURCE: EXE Menu Structs (SLPM_653.78 data section -- sidebar field labels)

| Record | EXE Offset | Tile IDs (R1272) | Japanese | English Target | Status | Phase(s) |
|--------|-----------|-----------------|----------|---------------|--------|----------|
| 30 | 0x3C3690 | 743,744 | 名前 (Name) | NAME | **JP** | 8 |
| 33 | 0x3C3738 | 749,750 | 種族 (Race) | RACE | **JP** | 3,4,5,6,7,8 |
| 36 | 0x3C37E0 | 755,756 | 性格 (Personality) | PERS | **JP** | 8 |
| 37 | 0x3C3818 | 757,758 | 職業 (Class) | CLASS | **JP** | 6,7,8 |
| 38 | 0x3C3850 | 759,760 | 性別 (Gender) | GENDR | **JP** | 3,4,5,6,7,8 |
| (align) | (varies) | (varies) | 属性 (Alignment) | ALIGN | **JP** | 5,6,7,8 |

**Fix approach**: Replace glyph IDs in EXE 56-byte menu struct records with ASCII letter glyph IDs (a=33..z=58), since composite tile theory was debunked -- these are individual kanji glyphs rendered side by side.

### SOURCE: TEX (Pre-rendered decorative textures -- already English)

| Element | Text | Phase(s) | Status |
|---------|------|----------|--------|
| Name header | *Name* | 1 | OK |
| Level label | Level | 1 | OK |
| Gender header | *Gender* | 2 | OK |
| Race header | *Race* | 3 | OK |
| Attribute header | *Attribute* | 4 | OK |
| Class&Parameter header | *Class&Parameter* | 5 | OK |
| Personality header | *Personality* | 6 | OK |
| Status header | *Status* | 7,8 | OK |

---

## Scorecard: Translation Completeness

| Category | Total Elements | OK | BUG | JP | N/A |
|----------|---------------|-----|-----|-----|-----|
| R37 prompts & labels | 17 | 14 | 1 (overflow) | 0 | 2 (kana grids) |
| R38 selection options | ~100 | 89 | 10 (male + alignment shift) | 0 | 0 |
| R38 descriptions | ~90 | 90 | 0 | 0 | 0 |
| R1188 bitmap buttons/tabs | 9 | 0 | 0 | 9 | 0 |
| R1188 stat labels | 6 | 0 | 0 | 6 | 0 |
| EXE sidebar field labels | 6 | 0 | 0 | 6 | 0 |
| EXE title banner | 1 | 0 | 0 | 1 | 0 |
| Pre-rendered headers (TEX) | 8 | 8 | 0 | 0 | 0 |
| **TOTAL** | **~237** | **~201** | **~11** | **~22** | **~2** |

---

## Fix Priority Matrix

### Priority 1: Data Bugs (fixable in JSON, ~15 min)

| Bug | File | Fix |
|-----|------|-----|
| Male = "lv.7" | chunk_r38_fix.json MSG 25 | Change to "male" |
| Alignment shifted x8 | chunk_r38_fix.json MSGs 149-156 | Correct all 8 entries |
| R37 MSG 2 overflow | inject_type2_dialogue.py line 111-136 | Skip auto-wrap when explicit ` / ` markers present |

### Priority 2: R1188 Bitmap Labels (15 elements, 4-8 hrs)

9 tab/button labels (name entry) + 6 stat labels (class/status screens).

Options ranked:
1. **Option D (BEST)**: Patch R1188 header UV data to point to English labels at y=1009-1020 (already rendered by patch_r1188_direct.py)
2. **Option A**: Deswizzle R1188, edit pixels at original UV positions, reswizzle
3. **Option C (quick workaround)**: PCSX2 texture replacement (already built, but emulator-only)

### Priority 3: EXE Menu Struct Labels (6 sidebar labels, 1-2 hrs)

Replace glyph ID references in EXE 56-byte records with ASCII letter glyph IDs. Tool needed: EXE patcher for offsets 0x3C3690-0x3C3850.

### Priority 4: Title Banner (1 element, 1-2 hrs)

新規登録 -> "New Character". Either EXE glyph ID patch or R1272 font tile replacement. PCSX2 tex replacement PNG already exists as fallback.

---

## File References

| Item | Path |
|------|------|
| Save states | RAMdumps/19-1.p2s through 19-8.p2s |
| R37 translation chunks | data/translate_chunks/chunk_r37_r48_r49.json, chunk_r37_extra.json |
| R38 translation chunk | data/translate_chunks/chunk_r38_fix.json |
| R1188 patcher | tools/patch_r1188_direct.py |
| R1272 font atlas | build/english_font_atlas.bin |
| Build pipeline | build/build_full_english_v2.py |
| EXE | extracted/SLPM_653.78 |
| PCSX2 tex replacements | build/pcsx2_texture_replacements/ |
| Glyph map | data/msg_glyph_map.json |
| Menu label decode | data/menu_labels.csv |
