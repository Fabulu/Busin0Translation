# Chargen (Character Creation) Screen -- Complete Visual Element Audit

**Date**: 2026-05-28
**Analyst**: Claude Opus 4.6
**Sources**: PCSX2 texture dumps (build/pcsx2_dumps/), R37, R38, R1188 analysis, in-game screenshots

---

## Screen-by-Screen Breakdown

The character creation flow has 7 distinct screens/phases. Each is analyzed below with every visible text element catalogued.

---

### PHASE 1: Name Entry Screen

**Screenshots**: `nameentry_screenshot.png`, `NameEntryEuropean.png`, `NameEntryHiraganamode.png`

| Visual Element | Japanese Text | Source | Translation Status | Notes |
|---------------|--------------|--------|-------------------|-------|
| Red title banner | 新規登録 | R37 MSG via glyph renderer (page 0x2214) | NOT TRANSLATED (R37 MSG 0-1 are palette, no dedicated msg) | This is glyph-rendered text, NOT a baked texture. Need to find which R37 message supplies it. |
| Instruction line 1 | 名前を入力してください。 | R37 MSG 2 | TRANSLATED ("enter a name.") via chunk_r37_r48_r49 | |
| Instruction line 2 | (男名・女名＝名前を自動で入力) | R37 MSG 2 (second line) | TRANSLATED ("m name, f name: auto-fill") | |
| "Name" header (italic script) | *Name* | Pre-rendered texture (page 0x2254) | ALREADY ENGLISH | Original game uses English decorative headers |
| "Level" label | Level 1 | Pre-rendered texture (page 0x2254) | ALREADY ENGLISH | |
| Tab: カナ | カナ (Katakana) | R1188 bitmap glyph 6400 + R37 MSG 12 | R37 MSG 12 TRANSLATED ("kana"), R1188 texture NOT EDITED | Glyph-rendered from R37 for the label text; R1188 supplies the tab button graphic |
| Tab: かな | かな (Hiragana) | R1188 bitmap glyph 6401 + R37 MSG 13 | R37 MSG 13 TRANSLATED ("kana") | Same dual-source |
| Tab: 英数 | 英数 (Alphanumeric) | R1188 bitmap glyph 6402 + R37 MSG 15 | R37 MSG 15 TRANSLATED ("abc") | |
| Tab: 記号 | 記号 (Symbols) | R1188 bitmap glyph 6403 + R37 MSG 14 | R37 MSG 14 TRANSLATED ("Count" -- WRONG, should be "sym") | Translation error: 記号 means "symbols", not "count" |
| Button: 決定 | 決定 (Confirm) | R1188 bitmap glyph 6405 + R37 MSG 17 | R37 MSG 17 TRANSLATED ("ok") | |
| Button: 男名 | 男名 (Male Name) | R1188 bitmap glyph 6406 + R37 MSG 122 | R37 MSG 122 TRANSLATED ("M name") | |
| Button: 女名 | 女名 (Female Name) | R1188 bitmap glyph 6407 + R37 MSG 123 | R37 MSG 123 TRANSLATED ("F name") | |
| Character grid (kana modes) | あいうえお... / アイウエオ... | R37 MSG 18-19 (kana grids) + main font R1272 | Stays Japanese (kana input for JP names) | Not translatable -- these ARE the kana characters |
| Character grid (ABC mode) | A-Z, a-z, 0-9 | R1189 texture atlas + R37 MSG 20 | ALREADY ENGLISH | Latin chars already present |
| Character grid (symbol mode) | Symbols | R37 MSG 21 | TRANSLATED | |
| Dashes (name display) | ------ | UI frame element | Language-neutral | |
| Ornamental frame border | Decorative scroll border | Pre-rendered texture | Language-neutral | |

**Key findings for name entry**:
1. The tab labels (カナ/かな/英数/記号/決定/男名/女名) have a DUAL rendering path: R37 supplies the text content via glyph rendering, AND R1188 supplies pre-rendered bitmap versions used as tab button graphics. Both need to match.
2. R37 translations ARE wired into the build pipeline and cover all messages.
3. R1188 bitmap tab labels are STILL JAPANESE (M3 in REMAINING_WORK.md).
4. The 新規登録 title banner source needs clarification -- it renders at glyph page 0x2214 but may use a different R37 message or a separate mechanism.

---

### PHASE 2: Gender Selection

| Visual Element | Japanese Text | Source | Translation Status | Notes |
|---------------|--------------|--------|-------------------|-------|
| "Gender" header (italic script) | *Gender* | Pre-rendered texture (page 0x2254, 120x48) | ALREADY ENGLISH | |
| Instruction text | 性別を選んでください。 | R37 MSG 3 | TRANSLATED ("select gender.") | |
| Option: 男 | 男 (Male) | R38 MSG 25 | BUG: mapped to "lv.7" instead of "male" | See M2 in REMAINING_WORK.md |
| Option: 女 | 女 (Female) | R38 MSG 26 | TRANSLATED ("female") | |
| Red title banner | 新規登録 | Same as Phase 1 | Same status | Persists across all phases |

---

### PHASE 3: Race Selection

| Visual Element | Japanese Text | Source | Translation Status | Notes |
|---------------|--------------|--------|-------------------|-------|
| "Race" header (italic script) | *Race* | Pre-rendered texture (page 0x2254, 88x48) | ALREADY ENGLISH | |
| Instruction text | 種族を選んでください。 | R37 MSG 4 | TRANSLATED ("select a race.") | |
| Option: 人間 | 人間 (Human) | R38 MSG 29 | TRANSLATED ("human") | |
| Option: エルフ | エルフ (Elf) | R38 MSG 30 | TRANSLATED ("elf") | |
| Option: ノーム | ノーム (Gnome) | R38 MSG 31 | TRANSLATED ("gnome") | |
| Option: ドワーフ | ドワーフ (Dwarf) | R38 MSG 32 | TRANSLATED ("dwarf") | |
| Option: ホビット | ホビット (Hobbit) | R38 MSG 33 | TRANSLATED ("hobbit") | |
| Option: オートマター | オートマター (Automata) | R38 MSG 34 | TRANSLATED ("automata") | |
| Description box | Race description text | R38 MSG 145-166 | TRANSLATED | Long descriptions |

---

### PHASE 4: Alignment Selection

| Visual Element | Japanese Text | Source | Translation Status | Notes |
|---------------|--------------|--------|-------------------|-------|
| "Attribute" header (italic script) | *Attribute* | Pre-rendered texture (page 0x2254, 152x48) | ALREADY ENGLISH | Original game uses "Attribute" for alignment |
| Instruction text | 属性を選んでください。 | R37 MSG 5 | TRANSLATED ("select alignment.") | |
| Option: 善「g」 | 善「g」 | R38 MSG 148 | TRANSLATED ("good \"g\"") | Correct |
| Option: 中立「n」 | 中立「n」 | R38 MSG 149 | BUG: shows "good \"g\"" | Shifted-by-one error |
| Option: 悪「e」 | 悪「e」 | R38 MSG 150 | BUG: shows "neutral \"n\"" | Shifted-by-one error |
| Description box | Alignment description | R38 MSG 145-166 range | TRANSLATED | |

---

### PHASE 5: Class Selection

| Visual Element | Japanese Text | Source | Translation Status | Notes |
|---------------|--------------|--------|-------------------|-------|
| "Class&Parameter" header (italic script) | *Class&Parameter* | Pre-rendered texture (page 0x2254, 248x48) | ALREADY ENGLISH | |
| Instruction text | 職業を選んでください。 | R37 MSG 6 | TRANSLATED ("select a class.") | |
| All 16 class names | 戦士, 盗賊, 呪術師... | R38 MSG 37-52 | TRANSLATED ("fighter", "thief", "mage"...) | |
| Stat labels | 力, 知恵, 信仰心... | R38 MSG 2-7 | TRANSLATED ("str", "int", "fth"...) | All lowercase |
| Description box | Class descriptions | R38 MSG 167-218 | TRANSLATED | |

---

### PHASE 6: Personality Selection

| Visual Element | Japanese Text | Source | Translation Status | Notes |
|---------------|--------------|--------|-------------------|-------|
| "Personality" header (italic script) | *Personality* | Pre-rendered texture (page 0x2254, 168x48) | ALREADY ENGLISH | |
| 34 personality trait names | Various kanji | R38 MSG 53-86 | TRANSLATED | "militant", "wasteful", "lonely"... |
| Personality descriptions | Long text | R38 MSG 87-144 | TRANSLATED | |

---

### PHASE 7: Stat Point Allocation / Confirmation

| Visual Element | Japanese Text | Source | Translation Status | Notes |
|---------------|--------------|--------|-------------------|-------|
| "Status" header (italic script) | *Status* | Pre-rendered texture (page 0x2254, 168x56) | ALREADY ENGLISH | |
| Instruction text | 能力値を振り分けてください。 | R37 MSG 7 | TRANSLATED ("allocate stat points.") | |
| Bonus point label | bonus point | R37 MSG 9 | TRANSLATED ("bonus point") | Already ASCII in original |
| Confirmation prompt | これでよろしいですか？ | R37 MSG 8 | TRANSLATED ("Is this OK?") | |
| Yes option | はい | R37 MSG 10 | TRANSLATED ("yes") | |
| No option | いいえ | R37 MSG 11 | TRANSLATED ("no") | |
| Final confirm instruction | ○ボタンか×ボタンをおすと最終確認へ移ります。 | R37 MSG 124 | TRANSLATED ("Press O or X button / to confirm your choices.") | |
| Stat labels | Same as Phase 5 | R38 MSG 2-7 | TRANSLATED | |
| Field labels (名前, レベル, 種族, 性別, 属性, 職業, 性格) | Various | R38 MSG 8-17 | TRANSLATED ("name", "level", "race", "gender", "alignment", "class", "personality") | |

---

## Summary: What Still Shows Japanese

### CRITICAL (visible to all players)

| Item | Japanese | Source | Fix Required | Priority |
|------|----------|--------|-------------|----------|
| R1188 tab labels | カナ/かな/英数/記号/決定/男名/女名 | R1188 bitmap atlas (1024x1024 PSMT4) | Deswizzle, edit pixel data, reswizzle | M3 |
| Male gender label | 男 | R38 MSG 25 | Fix chunk_r38_fix.json (mapped to "lv.7") | M2 |
| Alignment labels (Neutral/Evil) | 中立/悪 | R38 MSG 149-156 | Fix shifted entries in chunk_r38_fix.json | M2 |
| R37 MSG 14 wrong translation | 記号 shows as "Count" | R37 chunk_r37_extra.json | Should be "sym" or "symbols" | Minor |

### ALREADY ENGLISH (no work needed)

| Item | Text | Source |
|------|------|--------|
| Section headers | Name, Gender, Race, Attribute, Personality, Class&Parameter, Status, Level | Pre-rendered decorative textures (page 0x2254) |
| ABC character grid | A-Z, a-z, 0-9 | R1189 texture atlas |
| Bonus point label | bonus point | R37 MSG 9 (already ASCII) |
| Reputation labels | commoner, hooligan, adventurer, hero... | R38 MSG 230-257 |

### TRANSLATED (via R37/R38 glyph injection)

| Category | Count | Source |
|----------|-------|--------|
| Chargen instruction prompts | 7 messages (MSG 2-8) | R37 via chunk_r37_r48_r49 |
| Name entry labels | 8 messages (MSG 10-17, 122-126) | R37 via chunk_r37_extra + chunk_r37_r48_r49 |
| Character name pools | 98 names (MSG 22-121) | R37 via chunk_r37_extra |
| Stat labels | 8 messages (MSG 0-7) | R38 via chunk_r38_fix |
| Field labels | 10 messages (MSG 8-17) | R38 via chunk_r38_fix |
| Race names | 6 messages (MSG 29-34) | R38 via chunk_r38_fix |
| Class names | 16 messages (MSG 37-52) | R38 via chunk_r38_fix |
| Personality traits | 34 messages (MSG 53-86) | R38 via chunk_r38_fix |
| Descriptions | ~90 messages | R38 via chunk_r38_fix |
| Gender (female only) | 1 message (MSG 26) | R38 via chunk_r38_fix |
| Alignment (good only) | 1 message (MSG 148) | R38 via chunk_r38_fix |

### INTENTIONALLY JAPANESE (not translatable)

| Item | Reason |
|------|--------|
| Kana character grids (hiragana/katakana modes) | These ARE the Japanese input characters -- players may want Japanese names |
| Kanji name entry grid | Same reason |
| Ornamental frame borders | Language-neutral decorative art |

---

## Remaining Action Items for Chargen

1. **M2 (15 min)**: Fix 9 entries in `chunk_r38_fix.json`:
   - MSG 25: "lv.7" -> "male"
   - MSG 149-156: fix alignment label shift

2. **R37 MSG 14 (5 min)**: Fix in `chunk_r37_extra.json`:
   - MSG 14: "Count" -> "sym" (記号 = symbols, not count)

3. **M3 (4-8 hr)**: Edit R1188 1024x1024 PSMT4 texture:
   - Replace 7 bitmap tab labels with English equivalents
   - Requires: deswizzle -> image edit -> reswizzle -> inject

4. **N2 (1-2 hr, optional)**: Patch EXE to default name entry to ABC mode instead of katakana

5. **Title banner source (investigation)**: Determine if 新規登録 is rendered from a specific R37/R38 message or from a separate mechanism. The PCSX2 dump shows it at glyph page 0x2214 (120x24 pixels), suggesting it IS glyph-rendered. If so, it should be covered by R37 translation -- needs in-game verification after build.

---

## Visual Layout Reference

```
+==============================================================+
|  [新規登録]  名前を入力してください。                          |
|  (red banner)  (男名・女名＝名前を自動で入力)                  |
|                                                              |
|  *Name*                        _ _ _ _ _ _     Level 1       |
|                                                              |
|  +--[character grid]--------+  [カナ]  <- R1188 bitmap       |
|  | A B C D E  a b c d e     |  [かな]  <- R1188 bitmap       |
|  | F G H I J  f g h i j     |  [英数]  <- R1188 bitmap       |
|  | K L M N O  k l m n o     |  [記号]  <- R1188 bitmap       |
|  | P Q R S T  p q r s t     |                                |
|  | U V W X Y  u v w x y     |                                |
|  | Z          z             |  [男名]  <- R1188 bitmap       |
|  | 1 2 3 4 5  6 7 8 9 0     |  [女名]  <- R1188 bitmap       |
|  +---------------------------+  [決定]  <- R1188 bitmap       |
|                                                              |
|  [ornamental scroll border around entire screen]             |
+==============================================================+
```

Key: Items in brackets [] are Japanese that need translation.
Items in *italics* are already English decorative headers.
Items without markers are language-neutral or already translated.
