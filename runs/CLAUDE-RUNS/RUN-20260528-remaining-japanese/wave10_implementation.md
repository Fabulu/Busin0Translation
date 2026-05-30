# Wave 10 Implementation Log

**Date**: 2026-05-28
**Build**: v19 (BUSIN0_EN_v9.iso)

---

## Changes Applied

### 1. R38 Fix: Gender Labels (MSG 25-26)

**Problem**: MSG 25 had "lv.6" instead of "male", MSG 26 had "lv.7" instead of "female". 
Entries 27-30 in the fix JSON contained shifted duplicates (male, female, io, europa) that were not needed.

**Fix**: Removed the 15 incorrect trailing entries (indices 167-181) from `chunk_r38_fix.json` and added 11 correct entries:
- MSG 25: "male"
- MSG 26: "female"
- MSG 148-156: Alignment labels corrected (good "g", neutral "n", evil "e", good, neutral, evil, g, n, e)

**File**: `data/translate_chunks/chunk_r38_fix.json` (178 entries total)

### 2. R38 Fix: Alignment Labels (MSG 148-156)

**Problem**: All 9 alignment entries were shifted by +2 positions. MSG 150 had "good g" (should be at 148), MSG 151 had "neutral n" (should be at 149), etc. MSG 148-149 had no entries at all.

**Fix**: Included in the same JSON edit above. All 9 entries now at correct positions.

### 3. Menu Labels CSV: Banner (rows 11, 12, 18, 19)

**Problem**: Rows 11, 12, 18, 19 had incorrect Japanese labels and English translations:
- Row 11: "party" (was for "current members") -- actual kanji is 登 (register)
- Row 12: "select" -- actual kanji is 録 (record)
- Row 18: "luck" -- actual kanji is 新 (new)
- Row 19: "obtain" -- actual kanji is 規 (rule)

**Fix**: Updated to spell "new  reg." across the banner:
- Row 18 (新, rendered first): "new" (abbrev)
- Row 19 (規, rendered second): "  " (space, abbrev)
- Row 11 (登, rendered third): "reg" (abbrev)
- Row 12 (録, rendered fourth): "." (abbrev)

Banner rendering order: rec18 -> rec19 -> rec11 -> rec12 = "new  reg."

### 4. Menu Labels CSV: Sidebar Records (rows 24, 31-38)

**Problem**: Each record represents ONE kanji, not a 2-kanji compound. The CSV had incorrect labels and translations.

**Fix**: Updated individual kanji records:
- Row 24 (職): "job" -- used as half of 職業 (class) label
- Row 31 (性): "sex" -- used in 性別, 属性, 性格
- Row 32 (別): "  " -- second half of 性別
- Row 33 (種): "rac" -- first half of 種族
- Row 34 (族): "e" -- completing "race"
- Row 35 (属): "ali" -- first half of 属性
- Row 36 (格): "pers" -- used in 性格 (personality)
- Row 37 (業): "  " -- second half of 職業
- Row 38 (性別): "gender" (tile_pair, kept as compound label)

### 5. Font Atlas Regenerated

184 menu tiles injected into R1272 atlas from updated CSV.

### 6. EXE Patch: Fixed Encoding Error

Fixed UnicodeEncodeError in `build/patch_exe.py` when printing Japanese characters to cp1252 console. Added UTF-8 stdout wrapper.

### 7. Full Build Completed

ISO built as `build/BUSIN0_EN_v9.iso` with all patches applied:
- R38 gender and alignment fixes
- Updated banner tiles in R1272
- Updated sidebar tiles in R1272
- R1188 English labels rendered at y=1009-1020 (for future UV redirect)
- PCSX2 texture replacements for R1188 tab/button/stat labels (16 files)
- EXE patches (save names, NPC names, SJIS strings)
- 12,860 type-2 dialogue messages
- Section 1 opcode patching for variable-size resources

---

## R1188 Tab Labels Status

### What Works Now
- PCSX2 texture replacement PNGs in `build/pcsx2_texture_replacements/` (16 files)
- English labels rendered into R1188 atlas bottom rows (y=1009-1020)
- These cover: Kana, Hira, ABC, Sym, OK, M.Name, F.Name, Delete, Clear, New Character
- Plus stat labels: Strength, IQ, Piety, Vitality, Agility, Luck

### What's Not Done
- **UV redirect**: The R1188 header metadata at 0xA60-0xBFF that controls per-glyph UV coordinates was NOT decoded. The data structure is complex (416 bytes, non-uniform layout) and doesn't match the hypothesized 8-byte-per-glyph format.
- Without UV redirect, the English labels at y=1009-1020 are not visible in-game (the game still reads UV coordinates pointing to the original Japanese character positions).
- The PCSX2 texture replacements work as a visual override but only in the emulator.

### Options for Future Work
1. **PCSX2 debugger tracing**: Set memory breakpoints on BSS 0x4EB100-0x4EB1FF to capture the actual UV data that gets loaded at runtime, then reverse the mapping
2. **EXE code patch**: Inject a small routine that redirects glyph IDs 6400-6412 to the new atlas positions
3. **Atlas cell overwrite**: If the exact atlas cells for each tab label character can be identified, overwrite those cells with English letters directly (affects keyboard grid too)

---

## File Changes

| File | Change |
|------|--------|
| `data/translate_chunks/chunk_r38_fix.json` | Fixed MSG 25-26 (gender), MSG 148-156 (alignment) |
| `data/menu_labels.csv` | Fixed rows 11,12,18,19 (banner), 24,31-38 (sidebar kanji) |
| `build/patch_exe.py` | Fixed UTF-8 encoding for console output |
| `build/english_font_atlas.bin` | Regenerated with updated menu tiles |
| `build/BUSIN0_EN_v9.iso` | Full rebuild with all fixes |

---

## Remaining Japanese Text in Chargen

| Element | Source | Status |
|---------|--------|--------|
| Tab labels (Kana/Hira/ABC/Sym) | R1188 bitmap | PCSX2 replacement only |
| Buttons (OK/M.Name/F.Name/Del/Clear) | R1188 bitmap | PCSX2 replacement only |
| Stat labels (STR/INT/FTH/VIT/AGI/LCK) | R1188 bitmap | PCSX2 replacement only |
| Banner (New Reg.) | R1272 tiles | FIXED in atlas |
| Sidebar (Gender/Race/Align/Class) | R38 MSG + R1272 tiles | FIXED in R38 + tiles |
| Male label | R38 MSG 25 | FIXED |
| Alignment labels | R38 MSG 148-156 | FIXED |
