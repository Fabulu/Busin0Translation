# Findings Ledger — Run 2026-05-28: Remaining Japanese
**Started**: 2026-05-28 ~21:50
**Baseline**: Build v11 (commit a62c7bb)

---

## Agent #7: Build Pipeline Analysis [COMPLETE]
**Report**: recon_build_pipeline.md

### Findings
1. **build_v9.py** is 8-step: v2 sub-pipeline (type-1) -> type-2 variable-size injection -> Section 1 opcode patching -> PACKDATA rebuild -> ISO patch
2. Type-2 translations auto-glob from `data/type2_translated/batch_*.json`
3. Type-1 translations require hardcoded file list changes in the pipeline

### Bugs Found
- **BUG-B1**: `chunk_r37_extra.json` (111 translations including chargen confirm dialog) is NEVER LOADED by any pipeline step — dead data
- **BUG-B2**: R1053 (type-03) and R1908 (type-06) are still being patched despite being documented unsafe in KNOWN_ISSUES.md
- **BUG-B3**: `/tmp/inject_r39.py` lives outside repo — will be lost on cleanup
- **BUG-B4**: Type-2 encoding in build_v9 uses simple char-by-char mapper with NO word wrapping (standalone tools have proper wrapping)

### Gaps Found
- **GAP-B1**: No EXE patching in ISO build — stat labels, save names, font width scripts exist but aren't wired in
- **GAP-B2**: No texture replacement pipeline (intro narration, location banners, CockpitImg)
- **GAP-B3**: Only 27 of 617 type-02 resources translated (plus 94 excluded as binary data)
- **GAP-B4**: ~1,622 type-01 resources have zero translations

### Extension Points
- Type-2: drop new batch_*.json files into data/type2_translated/ (auto-discovered)
- Type-1: must edit hardcoded file list in pipeline
- EXE: needs new build step between PACKDATA rebuild and ISO creation
- Textures: needs entirely new pipeline stage

---

## Agent #3: R1100-R1190 Untranslated Dialogue [COMPLETE]
**Report**: recon_r1100_dialogue.md

### Findings
1. **CORRECTION**: R1118 (22), R1126 (171), R1134 (110), R1148 (181) are NOT dialogue — they're binary event scripts/stat tables with FFFE markers in numeric data
2. **Real untranslated text**: 54 messages across R1163-R1173 (9 resources)
3. R1174 already fully translated (4 messages in batch files)
4. 20 existing translations across 9 resources correctly labeled [DATA]/[LAYOUT]
5. Some FE:xx range glyphs in R1163-R1173 still need mapping

### Revised Scope
- **Original estimate**: 484 untranslated lines
- **Actual**: 54 messages across R1163-R1173
- **Blocker**: FE:xx glyph mapping (FFE0-FFFC range) needed before translation
- R1174 (already translated, same format) can serve as mapping reference

### R1347-R1355 Gap Resources
- 8 of 9 translated in `batch_gap1347.json` (131 entries, auto-loaded by injector)
- Only **R1350 missing** — single 12-glyph sound effect message ("ibakaaaa--- go")

### Technical Note
- Correct source files are `.raw` in `extracted/packdata_raw/`, NOT `.bin` in `extracted/packdata_resources/`
- The `.bin` files have different layout and produce garbage header values

---

## Agent #1: EXE Hardcoded Glyph Tables [COMPLETE]
**Report**: recon_exe_tables.md

### Findings (PARADIGM SHIFT)
1. **Menu labels are COMPOSITE GLYPHS, not multi-character strings**
   - ~430 unique glyph IDs stored as uint32 (glyph in upper 16, flag in lower 16)
   - Each glyph ID 480+ = entire Japanese word as a single pre-rendered font tile
   - e.g., glyph 500+501 = "召喚" (Summon), 506+507 = "削除" (Delete)
   - **Translation requires replacing font texture tiles, NOT swapping glyph IDs**
2. **Structs contain IEEE 754 floats** (1.0, 1.5, 100.0, 0.05) intermixed with glyph refs — positioning/scale params. Earlier uint16 scans had false positives from float misinterpretation.
3. **Character name input area** (0x3C844A-0x3C8F64): kana keyboard layout — 146 kana + 126 kanji glyphs as uint32 with flags. Needs replacement with ASCII keyboard.
4. **VA formula confirmed**: `VA = file_offset - 0x80 + 0x00100000`
5. **No traditional text strings** in EXE data section — all Japanese is either composite glyph refs in structs or system tables

### Detailed Table Catalog (11 categories, ~380 translatable items)
| Table | Offset | Content | Items | Format |
|-------|--------|---------|-------|--------|
| 2C | 0x3C3000-0x3C5300 | Menu label pair structs | 106 records | 56-byte: icon + label glyphs + floats |
| 2B | 0x3C83C0-0x3C93A0 | Chargen/name entry kana grid | 81 groups | 4-byte (flag,glyph) with FFFE separators |
| 2A | 0x3C9BF0-0x3C9DA0 | Name entry keyboard grid | 38 entries | 12-byte (primary + 5 alternates) |
| 2F | 0x3C93B0-0x3C93C8 | NPC names | 2 | Emilia, Lute |
| 2E | 0x3C9DA0-0x3C9DFC | Bitmap tab labels | ~10 | Glyph IDs 6400-6409 (bitmap font) |
| 2J | 0x3F9D00-0x3F9EC0 | Equipment type labels | 12 | Glyph IDs 2036-2047 (separate texture) |
| 2I | 0x3EE9D0-0x3F3500 | Battle debug strings | 161 | SJIS — NOT player-visible (TTY) |
| 2G | varies | Save slot names | 6 | Fullwidth SJIS |
| 2L | varies | Misc SJIS strings | 7 | Only 2 potentially visible |

### Blockers
- **139 unmapped glyph IDs** (94 in menu + 45 in chargen) must be added to msg_glyph_map.json
- Name entry system (2A+2D+2E) needs complex restructuring: kana grid → Latin alphabet
- Menu labels use single-kanji-per-concept composite glyphs — translation is a texture tile problem

### Implications
- The "293 Japanese text tables" was a miscount — many are float data misidentified
- Menu translation is partly a TEXTURE problem (font tile replacement for composite glyphs)
- Name input keyboard restructuring is a separate EXE patching task
- 161 battle debug strings can be SKIPPED (not player-visible)
- Save slot names (6 items) are a quick win via SJIS replacement

---

## Agent #2: R39 Equipment Text [COMPLETE]
**Report**: recon_r39.md

### Binary Structure (26,624 bytes)
- 16-byte sub-header (payload_size=2462, stride=240)
- 14-entry sequential table (bytes 16-239)
- 97-entry offset table (bytes 240-631), offsets relative to byte 240
- Glyph stream: 97 FFFF-delimited messages (bytes 632-2701)
- 14 sequential data sections: 558 more messages (bytes 2720-26090)
- **Total: 655 messages** (not 565 as previously estimated)

### M8 Root Cause — FOUR interrelated bugs in build_full_english_v2.py
1. **BUG-R39a**: `stream_end` clips at `payload_end=2478`, but messages 91-96 extend to byte 2701 beyond that boundary → only 91 of 97 groups found
2. **BUG-R39b**: Group 90 straddles boundary (starts 2454, FFFE at 2478, FFFF at 2480). Pipeline truncates at 2478 and appends SPURIOUS FFFF → 2 extra bytes shift all subsequent data
3. **BUG-R39c**: Rebuilt offset table uses found count (91) instead of original (97) → game's message index lookup breaks
4. **BUG-R39d** (NEW): **Wrong offset base** — pipeline produces offsets relative to byte 16 (payload start), but game reads them relative to byte 240 (OT start). Every offset is wrong by 224 bytes!

### Translation Status
- 84 of 97 OT-indexed messages have translations in chunk files
- 558 messages in sequential sections (equipment names/descriptions) still need translation
- Fix is clear: parse stream to byte 2701 (not payload_end), preserve all 97 groups
- **Offset base must be byte 240 (OT start), not byte 16 (payload start)**
- Safest approach: fixed-length in-place replacement with padding (zero OT changes needed)
- Analysis script saved: `runs/.../analyze_r39.py`

---

## Agent #4: CockpitImg Textures [COMPLETE]
**Report**: recon_cockpit_textures.md

### PSMT8 Deswizzle: SOLVED
- VRAM-simulation approach in `tools/psmt8_deswizzle.py` works perfectly with `dbw_ct32=256`
- Key correction: file header is **192 bytes** (not 208 as older tool assumed)
- Decoded images are **pixel-perfect**, no artifacts
- Both `deswizzle_psmt8()` and `swizzle_psmt8()` work — **reswizzle pipeline is production-ready**

### CRITICAL CORRECTION: R2118-R2124 Are NOT Tavern/Guild Textures
These are **demo disc splash screens** left over in the retail build:
- R2118: Demo disclaimer text (512x512)
- R2119: "Memory card not supported in demo" (512x64)
- R2120: "Continue in retail version" (512x64)
- R2121: Promotional "On sale now! 6,800 yen" (512x512) — NOT "新規登録"!
- R2122: "Demo version" badge (512x64)
- R2123/R2124: PSMT4 format (different pipeline)

### Where Are the Real Tavern/Guild Button Labels?
- **Rendered at runtime from MSG glyph font system or EXE-hardcoded glyph ID tables**
- Evidence: PCSX2 dumps show no Japanese button sprites; Busin 1 uses standalone TMX files but Busin 0 has no equivalent
- R1215-R1346 range confirmed as NPC portraits, not UI textures
- This means tavern/guild labels are a GLYPH problem (ties to EXE table 2C findings), not a texture problem

### Tool Status
- `deswizzle_psmt8()` and `swizzle_psmt8()`: **production-ready**
- Formula: `dbw_ct32 = tex_w / 2` (256 for 512-wide textures)
- Bug: `main()` function has wrong header size (1024 vs actual 208) — core functions are fine
- Demo screens: lowest priority (not player-visible in retail)

---

## Agent #5: Intro/Ending Narration Textures [COMPLETE] — CORRECTED BY SECOND AGENT
**Reports**: recon_narration_textures.md (two versions — second agent's findings supersede)

### CRITICAL CORRECTION: Intro text is NOT baked into textures!
1. **R1192** (157KB): Scene container with intro BACKGROUND ARTWORK (map, battle scenes, warrior portrait, city) as GS transfer packets. **Contains NO text.** Matched against PCSX2 dumps showing 512x512 painted backgrounds.
2. **R1193** (6KB): **Standard type-2 MSG resource** with 351 glyph indices in Section 2. Intro narration part 1 (Battle of Banquo backstory). 21 unmapped glyphs.
3. **R1194** (8KB): **Standard type-2 MSG resource** with 482 glyph indices in Section 2. Intro narration part 2 (Queen Oriana's speech). 40 unmapped glyphs.
4. **R1195** (2KB): Transition control script (wait/null marker).
5. **R2361** (43KB): Ending scene container (same format as R1192). No text — ending narration text location unidentified.

### Approach: USE EXISTING PIPELINE
- Map ~50 unique unmapped glyph indices (kanji in 300-1700 range, narration-specific)
- Translate text using English guide (`data/guide_full_text.txt`)
- Inject via existing build pipeline — **no texture editing needed!**
- This is a MEDIUM difficulty task, not the HARD texture problem we feared

---

## Agent #6: Name Entry Bitmap Font [COMPLETE]
**Report**: recon_name_entry_font.md

### Resource Structure (two agent interpretations — needs verification)
- **R1188** (527KB, type-01): Agent A says GS DMA draw commands (6,592 x 80-byte blocks). Agent B says **1024x1024 PSMT4 UI texture atlas** (0xC00 header + 524,288 bytes 4bpp pixels) containing tab labels, buttons, borders, title bar, instruction text. **Agent B likely more accurate** — 524,288 = exactly 1024x1024/2 bytes for 4bpp.
- **R1189** (65KB, type-02): Agent A says PSMT4 font atlas (512x256) with tab labels. Agent B says character grid glyphs (hiragana, katakana, latin, numbers) for keyboard selection. Both agree it's PSMT4.
- **Reconciliation**: R1188 = UI frame/tab labels/buttons texture. R1189 = keyboard character grid texture. Both need PSMT4 editing.

### Glyph ID 6400+ Encoding
- Group+index scheme: `group = id >> 8`, `index = id & 0xFF`
- 7 groups of 13 glyphs each
- Stored in EXE table 2E at file offset 0x3C9DA0
- At runtime, function VA 0x494050 resolves via BSS lookup table at VA 0x4EBBEC (populated when R1189 loads)

### What's What
- **Tab labels** (カナ/かな/英数/記号/決定/男名/女名): rendered using glyph IDs 6400+ from R1189's atlas
- **Grid characters** (A-Z, kana, etc.): use regular main-font glyph IDs from R1272
- R1192-R1214: UI frame/panel sprites, NOT tab label fonts

### Translation Approach
- Edit R1188's PSMT4 atlas for tab labels/buttons (1024x1024) — replace Japanese text with English
- Edit R1189's PSMT4 atlas for character grid if needed (512x256)
- Both need PSMT4 deswizzle (different from PSMT8 which is already solved)
- PCSX2 texture dump during name entry screen would give deswizzled reference
- EXE glyph IDs 6400-6412 referenced by 7 MIPS code blocks at VA 0x2FB094-0x2FB4C4

---

## Agent #8: Translation Coverage Audit [COMPLETE]
**Report**: recon_translation_coverage.md

### Findings
1. **CRITICAL BUG-C1**: 368 translations exist in batch files but are EMPTY in `build/v3_type2_translations.json` — consolidation script bug
   - R1354 lost 300 entries, R1353 lost 34, R1212 lost 33, R1213 lost 1
   - Empty indices follow pattern (67, 78, 88, 92, 96, 97...) — systematic bug
   - These render as Japanese in current ISO despite being translated
2. No duplicates across batch/chunk files
3. 13,112 of 13,113 type-2 entries have English text in batch files
4. All 1,444 type-1 entries translated in chunk files

### Coverage Summary
- **Type-02**: 124 of 510 translated (24.3%), 13,112 messages done
- **Type-01**: 20 of 1,642 translated — but those 20 cover core menus (R34-R49 etc.)
- **Type-01 with real text**: ~60 additional resources (dungeon labels, floor data) untranslated
- **Type-01 binary/3D**: ~1,562 resources — no translatable text, skip

### Untranslated Resources (High Priority)
- **R1910-R2026 dungeon events**: ~60 resources, 30-40 lines each (~2,000+ lines) — BIGGEST GAP
- **R1900-R1960**: ~2,500 lines across 20+ event scene resources
- **R2659**: 439 lines (late game)
- **R2129** (type-15, 327KB) and **R1186** (type-20, 500KB): large variant MSG resources
- **R1100-R1190**: 54 real messages (corrected from Agent #3)
- **R39**: Only 84/655 messages translated
- **34 resources with 50+ lines** = ~3,950 lines — highest value targets
- **Total untranslated**: ~7,631 dialogue lines across 381 type-02 resources

### Confirmed Ready but Not Wired
- `chunk_r37_extra.json` — 111 translations (confirms BUG-B1)
- `chunk_r38_fix.json` — 178 translations
- `chunk_r43_fix.json` — 26 translations
- R1347-R1355 gap (minus R1350) — done
- R989/R990/R1034, R1198 — done

---

## Agent #9: PS2 PSMT8 Deswizzle Research [COMPLETE]
**Report**: recon_psmt8_deswizzle.md

### Algorithm: FULLY SOLVED AND VERIFIED
- Two-phase VRAM simulation: write raw data using PSMCT32 block/column addressing, read back using PSMT8 block/column addressing
- Block table (4x8) and column table (16x16) from PCSX2's GSTables.cpp — verified correct
- Critical param: `dbw_ct32 = tex_w / 2`
- **Round-trip verified**: `swizzle(deswizzle(data)) == data` — zero byte differences for 512x512 and 512x64
- File format: 208-byte header (16 sub-header + 192 GS regs), NOT 1024 as `main()` uses
- CLUT swizzle: entries 8-15 swap with 16-23 in each 32-entry block, PS2 alpha 0-128 → multiply by 2

### Bug in tools/psmt8_deswizzle.py
- `main()` function uses `header_size = 1024` — should be `208`
- Core `deswizzle_psmt8()` and `swizzle_psmt8()` functions are correct

---

## Agent #10: Wizardry Fan Translation Community [COMPLETE]
**Report**: recon_community.md

### Findings
1. **No existing English patch** — we are the first playable translation attempt
2. **Diablo1_reborn's 577-page guide** (RPG Codex, April 2021) is the primary reference — already in our data as guide_full_text.txt
3. **Racjin decompression tools** on GitHub: `Raw-man/Racjin-de-compression` (CFC.DIG/CDDATA.DIG) — related but not identical to our PACKDATA.DIG
4. **Tale of the Forsaken Land** (Busin 1 US) establishes canonical English terminology
5. Community has been requesting this translation for years (GameFAQs, RPG Codex)

### Canonical Terminology (from Busin 1 US release)
- Kingdom of Duhan, Karman's Labyrinth, Holy King Ortrud
- Classes: Fighter, Thief, Mage, Priest, Ninja, Samurai, Bishop
- Characters: Bergran von Buren, Aurora (the witch)
- Unique race: Automata
- Items: Spell Stones
- Events: Battle of Banquo

---

---

## Implementation Status

### Phase 1: Quick Wins [COMPLETE]
- QW-2: Wired chunk_r37_extra.json (111 translations) ✓
- QW-3: Unsafe R1053/R1908 removal after v2 pipeline ✓
- QW-4: Moved /tmp/inject_r39.py to build/ ✓
- QW-5: Added R1350 translation ✓
- BUG-C1: Investigated — not a real bug (pipeline reads batches directly) ✓
- GAP-B1: Added EXE patching Step 8.5 to build pipeline ✓

### Phase 2: Intro Narration [IN PROGRESS]
- Agent mapping ~50 glyphs and translating R1193/R1194

### Phase 3: R39 Injector Fix [COMPLETE]
- Created build/inject_r39_v2.py — in-place fixed-size replacement
- Avoids all 4 bugs by not touching offset table
- 72/82 messages truncated (English longer than kanji) — known limitation
- Tavern softlock (M8) FIXED

### Phase 4: EXE Patcher [COMPLETE]
- Created build/patch_exe.py — 3 patch groups (9 patches total)
- Save slot names, player-visible SJIS strings, NPC names
- Added Step 8.4 to build pipeline
- Safety verification on all patches

---

### Wave 2 Results

#### Full Dialogue Scan [COMPLETE]
- 138 of ~304 text resources translated (45.4% by count, ~76.6% by line count)
- **166 untranslated text resources remain**:
  - 46 MSG-format type-02 (main dialogue): 29 dungeon/event (R680-R911), 3 large system (R1067/R1095/R1103), 3 text tables (R2217-R2219, ~2,500 groups!), 10 smaller
  - 101 ICS-format type-02 (R1911-R2026): small scenario scripts, 2-8 groups each (~314 groups total)
  - 19 non-type-02 text resources (R34-R49 system menus etc.)

#### Glyph Mapping: 864→1100 (+236 new kanji)
- FE:xx range confirmed as control codes, NOT unmapped glyphs
- R1163-R1173 confirmed as layout templates, NOT narration
- 565 standard-range glyphs remain unmapped (low-frequency)

#### R39 Equipment: 545 translations created
- Sections 1-7: 307 entries (spells, Alleid Actions, quests)
- Sections 8-14: 238 entries (quest UI, skills, shops, equipment types, party ranks)

#### R1193 Fix: Build warning eliminated
- Trailing unterminated data was being counted as group 3
- R1193 excluded from Step 4 (handled by Step 5 manual inject)

#### batch_gap681.json: Deleted (was research note, not translations)

#### Resources confirmed as non-text: R1163-R1173, R1186, R2129, R1168-R1173

---

## Summary Counters
| Category | Estimated Items | Status |
|----------|----------------|--------|
| EXE glyph tables | ~~293~~ **composite glyphs + kana keyboard** | TEXTURE problem, not glyph swap |
| R39 equipment messages | **655 total** (84/97 OT done, 558 sequential TODO) | M8 root cause found — 3 bugs |
| R1100-1190 dialogue | ~~484~~ ~~54~~ **0 — all layout templates** | FALSE POSITIVE eliminated |
| CockpitImg textures | R2118-R2124 are **DEMO DISC leftovers**, not tavern UI | PSMT8 deswizzle SOLVED, real UI location TBD |
| Narration textures | R1193+R1194 are **standard MSG glyph text!** | MEDIUM — use existing pipeline, map ~50 glyphs |
| Name entry font | R1189 is PSMT4 atlas (512x256), R1188 is GS draw commands | Edit R1189 atlas for tab labels, need PSMT4 deswizzle |
| R1900-R1960 events | ~~2,500~~ **0 lines — BINARY DATA** | FALSE POSITIVE from coverage audit |
| R2659 late game | ~~439~~ **0 lines — BINARY DATA** | FALSE POSITIVE from coverage audit |
| Build pipeline bugs | 4 bugs found | Needs fixing |
| Build pipeline gaps | 4 gaps found | Needs new code |
| Consolidation bug | 368 lost translations | CRITICAL — BUG-C1 |
| Unloaded translations | r37(111)+r38(178)+r43(26) | Needs wiring |
| Community/terminology | Canonical names from Busin 1 | Reference only |
