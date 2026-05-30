# REMAINING WORK -- Busin 0 Fan Translation Final Push

**Created**: 2026-05-28
**Baseline**: Wave 7 (commit 9906b96)
**Build**: v12 pipeline (build/build_v9.py)

---

## MUST DO (blocks release -- visible Japanese remains)

### M1. 62 Additional Menu Font Tiles (Gap Entries 106-159)
**What**: The EXE menu button table extends to entry 159, but `menu_labels.csv` only covers entries 0-105. Entries 106-159 contain 33 unique button pairs referencing 62 additional glyph IDs (867-931) that still display Japanese kanji in-game. These are buttons for: assist, co-op, sell, church, temple, floor, level up, cure, rank, like/dislike, accept, trade, train, sorry, display, status, relics, ruins, ancient, loyal, reward, build, take.
**Files**:
- `data/menu_labels.csv` -- add entries 106-159
- `tools/generate_font_atlas.py` -- extend to write 45+ rows (currently only 42)
- `data/R1272_psmt4_deswizzled.png` -- expand to 256x540+
- `extracted/packdata_raw/1272_type01.raw` -- rebuilt atlas output
**Approach**:
1. Add 62 entries to menu_labels.csv with English translations
2. Update generate_font_atlas.py to render 924+ cells (21x44 grid minimum)
3. Handle 8 overflow glyph IDs (924-931) that exceed 924-cell atlas -- either expand texture to 45 rows or remap to unused cells
4. Rebuild R1272 and inject into PACKDATA
**Effort**: 2-4 hours
**Dependencies**: None -- extends existing pipeline

### M2. R38 Alignment Label Shift Bug (9 Wrong Translations)
**What**: Alignment labels in `chunk_r38_fix.json` are systematically shifted by one position. Groups 149-156 each have the WRONG English text. Also MSG 25 (male gender label) is mapped to a duplicate "lv7" instead of "male". Result: selecting "Neutral" shows "Good", selecting "Evil" shows "Neutral" on the chargen screen.
**Files**:
- `data/translate_chunks/chunk_r38_fix.json` -- fix 9 entries
**Approach**: Replace entries for messages 25, 149-156 with correct translations:
- MSG 25: "male" (currently "lv.7")
- MSG 149: "neutral \"n\"" (currently "good \"g\"")
- MSG 150: "evil \"e\"" (currently "neutral \"n\"")
- MSG 151-156: fix the remaining shift
**Effort**: 15 minutes
**Dependencies**: None

### M3. R1188 Name Entry Screen Texture
**What**: The name entry screen has Japanese tab/button labels (katakana/hiragana/alphanumeric/symbol mode tabs, confirm button, male/female name tabs). R1188 is a 1024x1024 PSMT4 UI texture atlas containing these labels as pre-rendered bitmaps. These are the most prominent remaining Japanese text visible to players.
**Files**:
- `extracted/packdata_raw/1188_type01.raw` -- source PSMT4 texture
- `tools/psmt4_deswizzle.py` -- deswizzle tool (working, round-trip verified)
- New: image editor output for English replacement labels
**Approach**:
1. Deswizzle R1188 to get editable bitmap (1024x1024, 4bpp with 0xC00 header)
2. Locate tab labels in the atlas (likely at known grid positions)
3. Replace Japanese text with English: "Kana" -> "ABC", "Symbol" -> "Sym", "Confirm" -> "OK", "Male Names" -> "M.Names", "Female Names" -> "F.Names"
4. Reswizzle and inject back into PACKDATA
**Effort**: 4-8 hours (PSMT4 format is solved, but atlas layout needs manual mapping)
**Dependencies**: PSMT4 deswizzle (done), PCSX2 texture dump for reference (recommended)

### M4. Untranslated Dialogue Resources (~7,600 Lines)
**What**: 166 type-02 text resources remain untranslated. The largest gaps:
- 46 MSG-format resources (R680-R911): dungeon events, ~30-40 lines each
- 101 ICS-format scenario scripts (R1911-R2026): small, 2-8 groups each (~314 groups total)
- R1067/R1095/R1103: large system text resources
- 34 resources with 50+ lines = ~3,950 highest-value lines
**Files**:
- `data/type2_translated/batch_*.json` -- new batch files (auto-discovered by pipeline)
- `data/msg_glyph_map.json` -- may need ~100 additional low-frequency kanji mappings
**Approach**:
1. Extract and decode each resource using existing tooling
2. Map any unmapped glyph IDs (cross-reference with guide_full_text.txt)
3. Translate using guide as primary reference, with context from surrounding dialogue
4. Create batch_dungeon_b.json, batch_ics_*.json etc. -- pipeline auto-discovers
**Effort**: 20-40 hours (largest single work item)
**Dependencies**: Glyph mapping for low-frequency kanji

### M5. R39 Equipment Text Completeness
**What**: R39 has 655 total messages. 545 are translated (sections 1-14 equipment text), but the injector (build/inject_r39_v2.py) uses fixed-size in-place replacement, and 72/82 OT-indexed messages truncate because English is longer than Japanese kanji. The 4 original bugs (stream boundary, offset base, group count) are fixed, but truncation remains.
**Files**:
- `build/inject_r39_v2.py` -- current injector (in-place, no OT changes)
- `data/type2_translated/batch_r39_equip_a.json`, `batch_r39_equip_b.json`
**Approach**: Either:
- (A) Accept truncation for now (items still display, just cut short) -- RELEASE OK
- (B) Implement variable-size R39 injection with OT recalculation -- fixes truncation but risks regression
**Effort**: Option A = 0 hours (accept as-is). Option B = 4-8 hours.
**Dependencies**: None

### M6. 932 Cross-File Duplicate Keys
**What**: 932 (resource, message) pairs appear in multiple translation files. The build pipeline uses "later entries win" deduplication, which works but means which translation actually appears depends on file load order. Most are type-1 chunk overlaps (chunk_00 vs chunk_r36, etc.) that are intentional upgrades.
**Files**:
- Various `data/translate_chunks/chunk_*.json` files
- `data/type2_translated/batch_dungeon_a.json` vs `chunk_00_translated.json`
**Approach**: Audit duplicates, remove the older/inferior copy from each pair. The 932 count is inflated -- most are R35/R36 entries where dedicated chunk files supersede the original chunk_00.
**Effort**: 1-2 hours
**Dependencies**: None

---

## SHOULD DO (quality improvements)

### S1. QA: Long Line Truncation (859 Lines > 28 Chars)
**What**: 859 translated lines exceed the 28-character display limit (18 chars at 12px, or 28 at ~8px estimated). Breakdown: 481 lines 51+ chars (critical), 124 lines 41-50 chars, 108 lines 33-40 chars, 146 lines 29-32 chars. Most critical lines are in batch_r39_equip_a.json (quest/skill descriptions) which may use a different renderer with wider boxes.
**Files**:
- `data/type2_translated/batch_r39_equip_a.json` -- most offenders
- `data/type2_translated/batch_06.json` -- dialogue lines
- Various batch/chunk files
**Approach**:
1. Test R39 quest descriptions in-game to determine actual display width
2. For dialogue (batch_01 through batch_09): re-wrap using " / " line break markers at 18 char boundaries
3. For R39 descriptions: may need abbreviation or accept scrolling if renderer supports it
**Effort**: 4-8 hours
**Dependencies**: Half-width font patch (S4) would double available width and resolve most issues

### S2. Equipment Type Icon Sprites (Glyph IDs 2036-2047+)
**What**: Equipment category icons (sword, axe, staff, armor, etc.) are pre-rendered Japanese text sprites in a separate texture atlas. 52 icons total (not just 12), each with 4 animation states. These show as small Japanese labels next to equipment in menus.
**Files**:
- Unknown PACKDATA resource (icon sprite sheet not yet identified)
- EXE tables at 0x3F9CF0-0x3FA030 (icon animation table) and 0x3B38EA-0x3B39EE (item glyph base table)
**Approach**:
1. Locate the PACKDATA resource containing the icon sprite sheet (scan for glyph IDs 1604-2348 range)
2. Deswizzle the texture (likely PSMT4 or PSMT8 -- tools exist for both)
3. Replace Japanese type labels with English (Sword, Axe, Staff, etc.)
4. Reswizzle and inject
**Effort**: 4-8 hours (finding the resource is the main unknown)
**Dependencies**: PSMT4/PSMT8 deswizzle (both done)

### S3. Compass HUD Directions
**What**: The dungeon compass/minimap may display Japanese direction labels (N/S/E/W equivalents). Not yet investigated in detail.
**Files**: Unknown -- could be texture or MSG resource
**Approach**: PCSX2 screenshot during dungeon exploration to identify source. May be in R38 system labels or a texture resource.
**Effort**: 1-2 hours investigation + 1-2 hours fix
**Dependencies**: None

### S4. Half-Width Font Patch (12px -> 6px Glyph Advance)
**What**: The text renderer uses a fixed 12px advance per glyph with a 224px display box, giving 18 chars/line max. English needs ~36 chars/line. Patching the advance from 12 to 6 at 3 EXE sites would double capacity.
**Files**:
- `extracted/SLPM_653.78` -- EXE binary
- `build/patch_exe.py` -- existing EXE patcher
- Patch sites: VA 0x303E70, 0x303EF4, 0x305BF8 (advance values), X-clamp 128->256
**Approach**:
1. Add 3 new patches to patch_exe.py for the advance value
2. Patch the X position clamp from 128 to 256
3. Update font atlas tiles to half-width (6px per character instead of 12px)
4. Test extensively -- may affect ALL text rendering including menus
**Effort**: 4-8 hours (high risk of side effects on non-dialogue text)
**Dependencies**: Font atlas tile rework if half-width tiles needed

### S5. Name Consistency Fixes
**What**: QA found two canonical name issues:
- "Vera el-Muwahhid" should be "Vera Almohad" (per Busin 1 US canonical name)
- "DUHAN BAR LUNA" should be "DUHAN BAR LUNA LIGHT" (missing word)
**Files**:
- `data/type2_translated/batch_01.json` -- both entries
**Approach**: Find and replace the two entries.
**Effort**: 15 minutes
**Dependencies**: None

### S6. 25 Empty English Translation Entries
**What**: 25 entries have empty english fields. Most are placeholder/separator entries (R1163-R1173 layout templates, R39 section headers, R36 spacers) with no translatable content.
**Files**:
- `data/type2_translated/batch_r1163_1167.json`, `batch_r1168_1173.json` -- layout templates (confirmed non-text, can remove)
- `data/type2_translated/batch_r39_equip_a.json`, `batch_r39_equip_b.json` -- section separators
- `data/translate_chunks/chunk_r36_translated.json` -- spacer entries
**Approach**: Remove or add placeholder text. Non-functional but keeps QA clean.
**Effort**: 30 minutes
**Dependencies**: None

---

## NICE TO HAVE (polish)

### N1. Proportional Width Font
**What**: Instead of fixed half-width (S4), implement per-glyph width tables for true proportional rendering. Would give the most natural English text appearance.
**Files**:
- `extracted/SLPM_653.78` -- needs code injection (new function)
- Width table data (new resource or EXE data section)
**Approach**: MIPS code injection: replace fixed advance with table lookup. Requires free EXE space for the width table and new code.
**Effort**: 16-24 hours (complex EXE RE + code injection)
**Dependencies**: Deep understanding of text renderer (partially done)

### N2. Name Entry Default to ABC Mode
**What**: The name entry screen defaults to hiragana mode. For an English translation, it should default to alphanumeric (ABC) mode. Requires EXE patch to change the initial tab index.
**Files**:
- `extracted/SLPM_653.78` -- EXE binary
- EXE table 2E at 0x3C9DA0 (tab label glyph IDs)
- MIPS code at VA 0x494050 (tab resolver)
**Approach**: Find the initial tab index variable and patch its default value from 0 (kana) to 2 (alphanumeric).
**Effort**: 1-2 hours (once the variable is located)
**Dependencies**: M3 (R1188 texture edit should happen first so tabs make visual sense)

### N3. Demo Disc Splash Screens (R2118-R2124)
**What**: Leftover demo disc screens in the retail build. Not visible during normal gameplay. R2118 = demo disclaimer, R2119 = "no memory card in demo", R2121 = "on sale now! 6,800 yen" promotional splash.
**Files**:
- `extracted/packdata_raw/2118-2124_type01.raw`
- `tools/psmt8_deswizzle.py` (PSMT8 format, production-ready)
**Approach**: Deswizzle, edit text in image editor, reswizzle, inject. Or simply skip (not player-visible).
**Effort**: 2-4 hours if desired
**Dependencies**: PSMT8 deswizzle (done)

### N4. Ending Narration Text
**What**: R2361 is the ending scene container (same format as R1192 intro backgrounds). The ending narration text location is unidentified -- may be in a nearby type-02 MSG resource or rendered differently.
**Files**: Unknown -- needs investigation near R2361
**Approach**: Scan resources near R2361 for MSG-format text. If found, translate via existing pipeline.
**Effort**: 2-4 hours investigation + translation time
**Dependencies**: None

### N5. Uppercase Letter Font Tiles
**What**: The font atlas only has lowercase a-z (glyph IDs 33-58). All 14,915 entries with uppercase are auto-lowered by the encoder. Adding A-Z would allow proper case display.
**Files**:
- `data/R1272_psmt4_deswizzled.png` -- font atlas
- `tools/generate_font_atlas.py` -- tile renderer
- `data/msg_glyph_map.json` -- needs 26 new uppercase mappings
- Build pipeline encoder -- needs case-sensitive mode
**Approach**: Find 26 unused glyph ID slots, render uppercase tiles, update glyph map, update encoder to preserve case.
**Effort**: 4-6 hours
**Dependencies**: M1 (font atlas expansion should happen first)

### N6. Data Hygiene: Pre-Lowercase Translation Sources
**What**: 14,915 of 15,898 entries (93%) contain uppercase that gets auto-lowered. Source files should ideally match what renders.
**Approach**: Batch script to lowercase all english fields. Low priority since functional behavior is correct.
**Effort**: 30 minutes
**Dependencies**: N5 (skip this if uppercase support is added)

---

## CONFIRMED NOT NEEDED (false positives eliminated)

| Item | Reason |
|------|--------|
| R1900-R1960 events | Binary data, not text |
| R2659 late game | Binary data, not text |
| R1163-R1173 dialogue | Layout templates, not text |
| R1186, R2129 | 3D model/mesh data |
| R2217-R2219 | 3D waypoint/coordinate data |
| EXE chargen keyboard grid | Kana grid for name input -- stays Japanese |
| 161 EXE battle debug strings | TTY output, not player-visible |
| CockpitImg tavern/guild textures | These are demo disc leftovers, not tavern UI |
| "293 Japanese text tables" in EXE | Miscount -- many were IEEE 754 floats |

---

## PRIORITY ORDER FOR FINAL PUSH

| Step | Item | Effort | Impact |
|------|------|--------|--------|
| 1 | M2: Fix R38 alignment shift bug | 15 min | Fixes broken chargen screen |
| 2 | S5: Name consistency fixes | 15 min | Fixes 2 wrong canonical names |
| 3 | M1: 62 gap font tiles | 2-4 hr | Translates all remaining menu buttons |
| 4 | M4: Untranslated dialogue (batch by priority) | 20-40 hr | Translates remaining ~7,600 lines |
| 5 | M3: R1188 name entry texture | 4-8 hr | Removes most visible Japanese UI |
| 6 | S1: QA long line fixes | 4-8 hr | Prevents text truncation |
| 7 | S4: Half-width font patch | 4-8 hr | Doubles text capacity system-wide |
| 8 | M6: Duplicate key cleanup | 1-2 hr | Ensures correct translations win |
| 9 | S2: Equipment type icons | 4-8 hr | Translates item category labels |
| 10 | N2: Name entry default ABC | 1-2 hr | QoL for English players |

**Total estimated effort**: 40-80 hours for MUST DO + SHOULD DO items.
**Minimum viable release**: Steps 1-4 (M2 + S5 + M1 + M4) = core text coverage.

---

## BUILD PIPELINE STATUS

### Working Steps (build/build_v9.py)
1. v2 sub-pipeline (type-1 resources)
2. Unsafe resource removal (R1053/R1908)
3. R39 in-place injection
4. Type-2 variable-size injection + Section 1 opcode patching
5. Merge all translations
6. PACKDATA.DIG rebuild
7. ISO patch
8. EXE patch (10 patches: save names, SJIS, NPC names, cleanup)
9. EXE insertion into ISO

### Pipeline Gaps Still Open
- **GAP-B2**: No texture replacement pipeline (R1188, equipment icons, etc.) -- manual PACKDATA injection needed
- **GAP-B4**: Type-2 word wrapping not in build pipeline (standalone tools have it)
- Font atlas rebuild step not automated (generate_font_atlas.py is standalone)
