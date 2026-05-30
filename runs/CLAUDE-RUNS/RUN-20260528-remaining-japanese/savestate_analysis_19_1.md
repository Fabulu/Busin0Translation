# Save State Analysis: Character Creation Flow (19-1 through 19-8)

**Date**: 2026-05-28
**Save states**: `RAMdumps/19-1.p2s` through `19-8.p2s`
**Build**: v17
**Method**: ZIP extraction of eeMemory.bin (32 MB EE RAM) + Screenshot.png from PCSX2 .p2s files

---

## Save State Format

PCSX2 .p2s files are ZIP archives (PK header, not gzip). Contents:
- `eeMemory.bin` (33,554,432 bytes) -- full EE RAM dump
- `Screenshot.png` -- in-game screenshot at save moment
- `iopMemory.bin`, `GS.bin`, register files, etc.

Successfully extracted and analyzed all 7 save states.

---

## Screenshot Analysis: Phase-by-Phase

### 19-1: Name Entry Screen
- **Title bar "新規登録"**: STILL JAPANESE (red banner, top-left)
- **Top textbox OVERFLOW**: Shows 4 lines instead of 3. Text reads:
  ```
  Enter your name.
  [M
  name/F name: Auto-
  fill]
  ```
  ROOT CAUSE: double word-wrapping (see Bug Analysis below)
- **Tab labels**: ALL JAPANESE -- カナ, かな, 英数, 記号
- **Bottom buttons**: 決定 (OK), 男名/女名 (M.Name/F.Name) -- JAPANESE
- **Character grid**: English letters working correctly (ABC mode active)
- **"Name" and "Level" headers**: Already English (pre-rendered decorative textures)

### 19-2: Gender Selection
- **Title**: Still Japanese (新規登録)
- **Top textbox**: STALE TEXT from previous screen ("enter a name. m name, f name: auto- fill") -- suggests textbox content not properly cleared between phases, or the wrong R37 message is being displayed
- **Gender labels**: First option shows "lv.6" instead of "male" -- WRONG MSG MAPPING
- **Description box**: English ("Gender sets base stats. Men=strong, women=wise.")
- **"Gender" header**: Already English (decorative)

### 19-3: Race Selection  
- **Top textbox**: "select gender." -- STALE (should say "select a race.")
- **Race names**: ALL ENGLISH (human, elf, gnome, dwarf, hobbit) -- WORKING
- **Right sidebar labels**: 性別 (gender) STILL JAPANESE, value shows "lv.6" (wrong)
- **種族 label**: STILL JAPANESE, value shows "human" (correct)
- **Description**: English ("Human: High faith & balanced stats overall.")

### 19-4: Alignment Selection
- **Top textbox**: "select a race." -- STALE (should say "select alignment.")
- **Alignment list WRONG ORDER**: Shows "neutral 'n'" first, then "evil 'e'", then "good" -- shifted-by-one error in R38 translation mapping
- **Right sidebar**: 性別, 種族 STILL JAPANESE
- **Description**: English but garbled class list formatting

### 19-5: Class & Parameter Selection
- **Top textbox**: "select a class." -- CORRECT for this phase
- **STAT LABELS ALL JAPANESE**: 力, 知恵, 信仰心, 生命力, 敏捷度, 幸運度
- **Right sidebar**: 性別, 種族, 属性 ALL JAPANESE
- **決定 (OK) button**: STILL JAPANESE
- **Class names**: English (fighter visible) -- WORKING
- **"Class&Parameter" header**: Already English
- **"Bonus Point" label**: English -- WORKING

### 19-7: Status Summary (pre-confirmation)
- **Top textbox**: "F name" -- This is the PROMPT TEXT leaking as character name!
- **STAT LABELS ALL JAPANESE**: Same as 19-5
- **HP/MAX**: Already English in original
- **Right sidebar**: 性別, 種族, 属性, 職業 ALL JAPANESE
- **性別 value**: Shows "lv.6" instead of "male" -- CONFIRMED BUG
- **種族 value**: "human" -- correct
- **Class value + icon**: "fighter" with FIG icon -- WORKING
- **Personality section**: English ("believes in mystic power. loves magic.", "omnitsu", "bores easily. return to town often.") -- WORKING

### 19-8: Stat Allocation
- **Top textbox**: "allocate stat points." -- CORRECT
- **"bonus point" label**: English -- WORKING
- **Stat labels**: STILL JAPANESE (same as 19-5, 19-7)
- **Right sidebar**: ALL JAPANESE

---

## EE RAM Analysis

### R37 Messages (Chargen Prompts) -- Found at 0x012AFF00

Messages as loaded in EE RAM at time of 19-1 save state:

| MSG | Content in RAM | Lines | Status |
|-----|---------------|-------|--------|
| 0 | (offset table - binary) | - | OK |
| 1 | ` \|` | 1 | spacer |
| 2 | `Enter your name.\|[M\|name/F name: Auto-\|fill]\|` | 5 | **OVERFLOW** |
| 3 | `enter a name. m\|name, f name:\|auto-\|fill\|` | 5 | **OVERFLOW** |
| 4 | `select gender.\|` | 2 | OK |
| 5 | `select a race.\|` | 2 | OK |
| 6 | `select alignment.\|` | 2 | OK |
| 7 | `select a class.\|` | 2 | OK |
| 8 | `allocate stat\|points.\|` | 3 | OK |
| 9 | `Is this OK?\|` | 2 | OK |
| 10 | `bonus point\|` | 2 | OK |
| 11 | `yes\|` | 1 | OK |
| 12 | `no\|` | 1 | OK |
| 13 | `kana\|` | 1 | OK |
| 14 | `kana\|` | 1 | OK (was "Count" before fix?) |
| 15 | `sym\|` | 1 | OK |
| 16 | `abc\|` | 1 | OK |
| 17 | `auto\|` | 1 | OK |
| 18 | `ok\|` | 1 | OK |
| 19-22 | keyboard grids (Latin alphabet) | - | WORKING |
| 23+ | character names (Abel, Ash, Arno...) | 1 each | WORKING |

### R38 Messages (Stat/Class/Race Labels) -- Found at 0xE14300

| MSG | Content | Status |
|-----|---------|--------|
| 1 | HP | OK |
| 2 | hp/mhp | OK |
| 3-8 | str, int, fth, vit, agi, lck | **IN RAM but not rendering** |
| 9 | name | OK |
| 10 | level | OK |
| 11-15 | race, gender, alignment, class, personality | **IN RAM but shows Japanese on screen** |
| 16-18 | sorcery, holy magic, attributes | OK |
| 19-27 | lv1 through lv.7 | OK |
| 28-29 | male, female | OK in RAM |
| 30-35 | human, elf, gnome, dwarf, hobbit, automata | WORKING |
| 38-54 | fighter through omnitsu (class names) | WORKING |
| 55-77 | personality traits | WORKING |

### Alignment Labels -- Found at 0xE15E26

Three copies of `good "g"` followed by `neutral "n"` then `evil "e"` -- confirms shifted-by-one error in translation mapping.

---

## Bug Analysis

### BUG 1: Double Word-Wrapping (Top textbox 4 lines instead of 3)

**Root cause**: `clean_and_encode()` in `inject_type2_dialogue.py` (line 111-136)

When English text contains ` / ` markers (manually placed line breaks), the function:
1. Splits on ` / ` 
2. Inserts 0xFFFE between parts
3. Calls `encode_text(part, max_chars_per_line=18)` on EACH part

But `encode_text()` adds its own 0xFFFE line breaks when a part exceeds 18 chars. This causes DOUBLE wrapping.

Example: `"Medals from the / floor boss were / offered to the gods."`
- Part "offered to the gods." = 21 chars > 18, so encode_text wraps it
- Result: 4 lines instead of intended 3

**Impact**: 4,596 out of 13,682 messages (33.6%) produce more than 3 lines.

**Fix**: When text has explicit ` / ` markers, trust them and skip auto-wrapping. Change `encode_text` call to a simple character-by-character encode without word wrap, or set `max_chars_per_line=999`.

### BUG 2: Stat Labels Show Japanese Despite English in RAM

**Symptom**: 力, 知恵, 信仰心, 生命力, 敏捷度, 幸運度 visible on screen, but R38 messages str/int/fth/vit/agi/lck ARE present in EE RAM.

**Root cause**: The stat labels on the Class & Status screens are NOT rendered from R38 glyph streams. They are rendered from **R1188 bitmap atlas** (PSMT4 texture). R38 stat labels may only be used in certain contexts (e.g., party menus), while the chargen screen uses pre-baked bitmap labels from the texture atlas.

The PCSX2 texture replacement PNGs exist in `build/pcsx2_texture_replacements/` but these only work with PCSX2's texture replacement feature enabled -- they are NOT injected into the ISO/PACKDATA.DIG. The `patch_r1188_direct.py` tool writes English labels into atlas rows y=1009-1020, but this requires a companion EXE UV-redirect patch that does not yet exist.

**Fix options**:
1. **Short-term**: Tell users to enable PCSX2 texture replacement (already built)
2. **Long-term**: Implement EXE patch to redirect stat label UV lookups to the English-labeled rows in R1188 atlas

### BUG 3: Name Entry Tab Labels Still Japanese

**Symptom**: カナ, かな, 英数, 記号, 決定, 男名, 女名 tabs on right side of name entry screen

**Root cause**: Same as Bug 2. Tab labels are bitmap sprites from R1188 texture atlas, not glyph-rendered text. R37 messages 12-18 supply the glyph-rendered text content, but the actual tab button graphics come from R1188 bitmap positions.

The R37 translations ARE in RAM (kana, sym, abc, ok, etc.) but the TAB BUTTONS use bitmap sprites from R1188 which are still Japanese.

**Fix**: Same as Bug 2 -- PCSX2 texture replacement or EXE UV patch.

### BUG 4: Gender Label Shows "lv.6" / "lv.7" Instead of "male"

**Symptom**: On gender selection and in right sidebar, male shows as "lv.6" or "lv.7"

**Root cause**: R38 message index mapping error. The R38 translation has `lv.6` and `lv.7` at indices 26-27, and "male"/"female" at indices 28-29. But the game expects "male" at index 25 (where "lv7" currently sits).

In the EE RAM dump, the sequence is: lv1, lv2, lv3, lv4, lv5, lv6, lv7, lv.6, lv.7, male, female. The game reads the gender value from an earlier index than where "male" landed.

**Fix**: Correct the R38 translation JSON to put "male" at the correct msg_index (25 in the original R38 numbering).

### BUG 5: Alignment Labels Shifted By One

**Symptom**: First option shows "neutral 'n'" instead of "good 'g'"

**Root cause**: The alignment label translations are off by one position. Three copies of `good "g"` appear in RAM followed by `neutral "n"` then `evil "e"`, meaning the translation placed "good" in positions meant for something else, pushing neutral and evil down.

**Fix**: Correct the msg_index mapping in the R38 translation batch.

### BUG 6: "新規登録" Title Banner Still Japanese

**Symptom**: Red banner top-left on all chargen screens

**Root cause**: This is a glyph-rendered string using composite glyph IDs (Japanese word glyphs 480+) from the EXE's hardcoded data section. Translation requires replacing the font texture tiles for these composite glyphs, or implementing EXE patches to swap the glyph IDs to spell "New Character" using individual Latin glyphs.

**Fix**: EXE patch (not yet implemented). The PCSX2 texture replacement for this (`a2d3fce36c8c719d-...120x24...png`) exists but only works with PCSX2 replacement enabled.

### BUG 7: Right Sidebar Field Labels Still Japanese

**Symptom**: 性別, 種族, 属性, 職業 labels on the right side of chargen screens

**Root cause**: Same as Bug 6 -- these are composite glyph IDs from the EXE data section, not R38 glyph-stream text. The R38 translations (name, level, race, gender...) may only be used in different UI contexts (e.g., party management screens).

**Fix**: EXE composite glyph replacement or font texture editing.

### BUG 8: "F name" Appearing as Character Name (19-7)

**Symptom**: Status summary screen shows "F name" where the character name should be

**Root cause**: The R37 message for the female auto-name button ("F name") is being displayed as the character's actual name. This suggests the name input defaulted to or was populated from the wrong R37 message index. Likely the user didn't enter a name and the auto-name system pulled from the wrong message.

**Fix**: May be a test artifact, but verify R37 message index for auto-name doesn't collide with the "F name" button label.

### BUG 9: Stale Textbox Content Between Phases

**Symptom**: 19-2 shows "enter a name..." when it should show "select gender.", 19-3 shows "select gender." when it should show "select a race.", etc.

**Root cause**: The top textbox appears to be one phase behind. The instruction text may be updating but the game renders the PREVIOUS phase's prompt due to an off-by-one in the phase/message selection logic. Alternatively, the screenshots were taken at transition moments.

**Status**: Likely a timing artifact in save state capture. Need in-game verification.

---

## Summary: What Still Shows Japanese in Chargen

### Category A: Bitmap/Texture Labels (require R1188 atlas edit or EXE UV patch)
- Tab labels: カナ, かな, 英数, 記号
- Buttons: 決定 (OK), 男名/女名 (M.Name/F.Name)
- Stat labels: 力, 知恵, 信仰心, 生命力, 敏捷度, 幸運度
- **Workaround available**: PCSX2 texture replacement PNGs already built

### Category B: EXE Composite Glyphs (require EXE patching)
- Title banner: 新規登録 (New Character)
- Sidebar labels: 性別, 種族, 属性, 職業

### Category C: Translation Data Bugs (fixable in JSON)
- Gender "lv.7" -> "male" (wrong msg_index)
- Alignment shifted by one (good/neutral/evil off by 1)
- Top textbox overflow from double word-wrapping

### Category D: Already Working
- Race names (human, elf, gnome, etc.)
- Class names (fighter, thief, mage, etc.)
- Personality traits
- Instruction prompts (partially -- overflow aside)
- Decorative headers (Name, Gender, Race, etc. -- original game)
- Description box text
- Keyboard grids (Latin alphabet)
- Character name pools
