# Chargen Text Overflow Audit -- Final Results

**Date**: 2026-05-28
**Analyst**: Claude Opus 4.6
**Pipeline**: build_full_english_v2.py (encode_text with max_chars_per_line=20, max_lines_per_page=3)

---

## Audit Scope

Decoded ALL messages from the BUILT packdata_resources for:
- R38 (0038_type01.raw) -- 190 messages: stat labels, race/class/alignment names, chargen descriptions
- R37 (0037_type01.raw) -- 129 messages: chargen prompts, keyboard grids, name pools
- R39 (0039_type15.raw) -- 565 messages: NOT a chargen text resource (type 15, structured data with dungeon/story text)

Also scanned ALL other built type01 resources for English text overflow.

---

## R38 Results: ZERO OVERFLOW

All 190 messages pass both constraints:
- **Line width**: No English line exceeds 20 characters
- **Line count**: All description messages (msgs 117-148) fit within 3 lines (max 2 FFFE breaks)

### Chargen Description Messages (117-148) -- All Clean

| MSG | Lines | Max Line Len | Text |
|-----|-------|-------------|------|
| 117 | 2 | 18 | Use everything you / own. Never hoard. |
| 118 | 3 | 18 | Gender sets base / stats. Men=strong, / women=wise. |
| 119 | 3 | 17 | Human: High faith / & balanced stats / overall. |
| 120 | 3 | 19 | Elf: High INT & VIT / but frail. Best / at magic. |
| 121 | 3 | 17 | Gnome: High faith / & agility. Suited / for Priests. |
| 122 | 3 | 16 | Dwarf: Slow but / strong with deep / faith. Fighters. |
| 123 | 3 | 17 | Hobbit: Small but / agile and lucky. / Born thieves. |
| 124 | 3 | 18 | Good=justice. May / turn Evil. FIG MAG / PRI SAM GIZ BIS+ |
| 125 | 3 | 16 | Neutral=no bias. / FIG THI MAG SAM / GIZ ALC MON |
| 126 | 3 | 18 | Evil=self-serving. / FIG THI MAG PRI / NIN BIS ALC |
| 127 | 3 | 16 | Combat expert. / Cannot learn any / magic spells. |
| 128 | 3 | 17 | Lowers trap level / & finds chests. / Sorcery Lv3. |
| 129 | 3 | 18 | Master of Sorcery. / Can learn all / Sorcery spells. |
| 130 | 3 | 18 | Holy magic master. / Can Dispel undead. / All Holy spells. |
| 131 | 3 | 19 | Great EXP gain. Can / instant-kill foes. / Sorcery up to Lv2. |
| 132 | 3 | 19 | Knight gear usable. / Learns Sorcery / up to Lv5. |
| 133 | 3 | 19 | Restores HP. Dispel / vs undead. Sorc & / Holy Magic Lv6. |
| 134 | 3 | 17 | Poleaxe weapons. / Dispel vs undead. / Holy Magic Lv5. |
| 135 | 3 | 17 | Handles alchemy. / Sorc & Holy Magic / up to Lv4. |
| 136 | 3 | 20 | Longbow user. Lowers / traps, steals items / Sorc+Holy Lv3. |
| 137 | 3 | 18 | Staffs & knuckles. / Dispel vs undead. / Holy Magic Lv5. |
| 138 | 3 | 19 | Holy aura heals HP. / Can learn Dispel. / Sorc+Holy Lv6. |
| 139 | 3 | 19 | Removes curses from / equipped items. / Sorcery Lv6. |
| 140 | 3 | 18 | Great EXP & insta- / kill. Sees in fog. / Sorcery Lv5. |
| 141 | 3 | 19 | Dual wields same / weapon type. Learns / Sorcery Lv6. |
| 142 | 3 | 19 | Longbow. Best trap / skill. Steals items / Sorc+Holy Lv4. |
| 143 | 2 | 20 | Affects damage dealt / with weapons. |
| 144 | 3 | 15 | Affects Sorcery / power and / resistance. |
| 145 | 3 | 18 | Affects Holy Magic / power and / resistance. |
| 146 | 3 | 20 | Affects max HP, / status resistance, / and revival success. |
| 147 | 2 | 18 | Affects turn order / in battle. |
| 148 | 3 | 19 | Affects breath / resist and critical / hit chance. |

---

## R37 Results: ZERO OVERFLOW (chargen text)

All 129 messages pass constraints. The only multi-line messages are:

### Keyboard Grids (msgs 19-22) -- Intentionally Multi-Line

These are character input palettes for the name entry screen. The original Japanese versions have 10+ FFFE breaks (hiragana/katakana grid). The English versions have 5 FFFE breaks (6 lines), which is FEWER than the originals. These are NOT overflow -- they are intentional keyboard layouts.

| MSG | FFFE | Content |
|-----|------|---------|
| 19 | 5 | abcdefghij / klmnopqrst / uvwxyz.,!? / abcdefghij / klmnopqrst / uvwxyz -' |
| 20 | 5 | ABCDEFGHIJ / KLMNOPQRST / UVWXYZ.,!? / abcdefghij / klmnopqrst / uvwxyz -' |
| 21 | 5 | abcdefghij / klmnopqrst / uvwxyz.,!? / ABCDEFGHIJ / KLMNOPQRST / UVWXYZ -' |
| 22 | 3 | 1234567890 / +=#$&@*^~! / <>(){}[]|_ / :;,.?!'"-%  |

### Prompt Messages (msgs 2-11) -- All Within Limits

All chargen prompts ("Enter your name.", "select gender.", "select a race.", etc.) fit on single lines within 20 chars.

---

## R39 Results: NOT A CHARGEN TEXT RESOURCE

R39 is type 15 (structured data), not type 01 (MSG glyph stream). It contains dungeon/story text and item menus. The few English entries injected (msgs 1-84: "Use", "Equip", "Unequip", etc.) are short menu labels that do not overflow. The remaining 480+ messages are still in Japanese with high glyph IDs.

---

## Other Built Resources: No English Overflow Found

Scanned all 40+ built type01 resources. Three false positives were identified (R45 MSG 161, R1272 MSG 3, R2124 MSG 18) but all contain Japanese glyph IDs, not English text.

---

## Conclusion

**No text overflow remains in chargen screens.** The v2 pipeline's `clean_and_encode()` function (with `max_chars_per_line=20`, `max_lines_per_page=3`, trailing FFFE stripping) has successfully constrained all R37 and R38 English translations within the game's display limits.

The earlier overflow analysis (chargen_overflow_analysis.md) identified 22 overflowing messages, but those have ALL been fixed in the current chunk_r38_fix.json translations. Every description now fits within 3 lines of 20 characters or fewer.

### Remaining Chargen Issues (NOT overflow-related)

Per chargen_source_map.md, these issues remain but are NOT text overflow:
1. R38 MSG 25 shows "lv.7" instead of "Male" (wrong message index mapping)
2. EXE menu struct labels (gender/race/alignment/class sidebar) still display Japanese via R1272 composite tiles
3. R1188 bitmap tab buttons on name entry screen still show Japanese
4. Stat labels on chargen use R1188 bitmaps (patched separately via patch_r1188_stats.py)
