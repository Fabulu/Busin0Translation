# FULL TRANSLATION PLAN: Busin 0 - Wizardry Alternative Neo

**Date:** 2026-05-22
**Supersedes:** REINSERTION_PLAN.md (original Phase A-F plan)
**ISO:** Busin 0 - Wizardry Alternative Neo (Japan) (v2.01)
**Target:** Complete English fan translation

---

## Current State of the Project

### What Is Done
| Component | Status | Details |
|-----------|--------|---------|
| PACKDATA.DIG TOC parsed | DONE | 2,882 entries, 12-byte LE triplets |
| Type-1 MSG resources decoded | DONE | 21 resources, 1,168 messages, glyph map (759 entries) |
| Type-1 translations | 96.7% DONE | 1,129 of 1,168 messages translated (chunk files) |
| Type-2 dialogue extracted | DONE | 12,886 runs from 112 resources, output in `data/type2_dialogue_full.json` |
| Type-2 resource format decoded | DONE | Section 2 at offset 0x18, size at offset 0x14, Format A/B distinguished |
| Scene map | DONE | R1196-R1213 mapped to story progression, chronological order established |
| Font atlas generator | DONE | 256x512, 4bpp, 21x42 grid, 12x12 cells |
| English glyph table | DONE | `data/english_glyph_table.json` -- A-Z, a-z, digits, punctuation |
| EXE analysis | DONE | Only 5 save-slot strings need translation; battle strings are debug-only |
| Video analysis | DONE | No subtitles or embedded text in BSN2_0.DSI |
| Type-2 glyph overrides | PARTIAL | 38 kanji overrides identified (type-2 uses different font page) |

### What Is Broken (5 Known Bugs in Pipeline)

| # | Bug | Severity | Location | Root Cause |
|---|-----|----------|----------|------------|
| B1 | Stream-start detection off by 2 bytes | CRITICAL | `build/full_patch_pipeline.py` `find_ss()` | Hits 0xFFFF in offset table flags, not glyph stream |
| B2 | Offset table not rebuilt after injection | CRITICAL | `build/full_patch_pipeline.py` | English messages change length but offset pointers stay at Japanese positions |
| B3 | Trailing ` / ` in all chunk translations | CRITICAL | `data/translate_chunks/chunk_*_translated.json` | Chunk separator treated as literal text; "Nothing unusual. / " rendered in-game |
| B4 | Multi-message entries not split | CRITICAL | Chunk translation files | "switch off / switch on" packed into single entry instead of two FFFF-delimited messages |
| B5 | `encode_all_translations.py` drops nested dicts | HIGH | `tools/encode_all_translations.py` | Cannot parse `translations_dungeon_story.json` or `translations_menus.json` |

### What Is Not Started
| Component | Scale | Notes |
|-----------|-------|-------|
| Type-2 dialogue translation | 12,886 messages (~2.6 MB text) | Bulk of the game's story |
| Type-2 dialogue injection | 112 resources, Format A/B handling | 98% overflow in-place, requires full rebuild |
| Image textures | ~50 menu button images | Japanese text burned into TMX textures |
| EXE save-slot string patching | 5 strings | Trivial once pipeline works |
| Remaining 275 MSG resources | Unknown unique content | May contain duplicates or additional text |

---

## Phase Dependency Graph

```
Phase 1 (Fix Pipeline)
    |
    +---> Phase 2 (Type-2 Extraction) ----+
    |                                      |
    |     Phase 7 (Image Textures)         +---> Phase 4 (Type-2 Injection)
    |     [independent, deferred]          |         |
    |                                      |         v
    +---> Phase 3 (Type-2 Translation) ---+    Phase 5 (Complete Rebuild)
                                                     |
                                                     v
                                               Phase 6 (ISO + Patch)
```

### Parallelism Summary

| Parallel Group | Phases | Notes |
|----------------|--------|-------|
| Group A | Phase 1 + Phase 7 (start) | Bug fixes and image research are independent |
| Group B | Phase 2 + Phase 3 (overlap) | Translation can begin on resources as they are extracted |
| Group C | Phase 4 + Phase 5 | Sequential: injection feeds into rebuild |
| Group D | Phase 6 | Sequential: requires completed rebuild |

Phases 2 and 3 have significant overlap potential: as soon as a batch of type-2 dialogue is extracted and verified, translation can begin on that batch while extraction continues on remaining resources.

Phase 7 (Image Textures) is fully independent and can proceed at any time. It is deferred because the game is playable with Japanese button images -- they are recognizable by icon/position.

---

## Phase 1: Fix Pipeline

**Goal:** Eliminate all 5 known bugs so that type-1 injection produces correct English text in-game.

**Estimated scope:** 1-2 days
**Dependencies:** None
**Blocks:** Everything else

### Bug Fixes Required

#### Fix B1: Stream-start detection (2-byte offset)

**File:** `build/full_patch_pipeline.py`

Replace the `find_ss()` heuristic with proper offset table parsing:
```
msg_count = struct.unpack_from(">H", raw, 0x10)[0]
table_size = (msg_count + 1) * 4   # entry[0] = count, entries[1..N] = offsets
ss = 16 + table_size               # glyph stream starts after table
```

13 of 21 modified resources are affected. Without this fix, every message pointer is wrong by 2 bytes.

#### Fix B2: Offset table rebuild after injection

**File:** `build/full_patch_pipeline.py`

After encoding all messages into the new glyph stream, rebuild the offset table:
```
1. Encode each message separately, recording its byte length
2. Compute cumulative offsets: offset[i] = table_size + sum(lengths[0..i-1]) + (2 * i)
3. Write new table: [msg_count, 0x0000] + [offset_i, flags_i] for each message
4. flags = 0xFFFF for last entry, 0x0000 for all others
```

This is the same algorithm needed for type-2 Format A resources (Phase 4), so implement it as a shared function.

#### Fix B3: Strip trailing ` / ` from chunk translations

**File:** New cleanup script or integrated into encoder

Before encoding, strip the chunk separator artifact:
```python
text = text.rstrip()
if text.endswith(' /'):
    text = text[:-2].rstrip()
```

Apply to all 10 chunk files (chunk_00 through chunk_09).

#### Fix B4: Split multi-message chunk entries

**File:** New preprocessing script

Chunk entries containing ` / ` that correspond to multiple FFFF-delimited game messages must be split:
```
Input:  {"resource": 49, "message": 3, "english": "The switch is off. / Turned the switch on. / "}
Output: {"resource": 49, "message": 3, "english": "The switch is off."}
        {"resource": 49, "message": 4, "english": "Turned the switch on."}
```

Cross-reference against `data/full_decoded_text.json` to determine the correct message count per resource.

#### Fix B5: Unified translation loader

**File:** Rewrite `tools/encode_all_translations.py`

Create a single loader that reads from:
1. Chunk files (primary source, after B3/B4 cleanup)
2. `translations_dungeon_story.json` (nested `messages.{id}.english` structure)
3. `translations_menus.json` (uses `"en"` key instead of `"english"`)

Output: unified `data/all_translations_clean.json` with flat `{resource_id: {message_index: english_text}}` structure.

### Scripts

| Script | Purpose | New/Modify |
|--------|---------|------------|
| `tools/clean_chunk_translations.py` | Fix B3 + B4: strip separators, split multi-messages | NEW |
| `tools/unified_translation_loader.py` | Fix B5: merge all translation sources | NEW |
| `build/full_patch_pipeline.py` | Fix B1 + B2: correct stream-start, rebuild offset tables | MODIFY |

### Validation

After fixes:
1. Rebuild type-1 resources for R42 (inn), R43 (shop), R49 (dungeon)
2. Rebuild PACKDATA.DIG with type-1 patches only
3. Build ISO and boot in PCSX2
4. Visit the Inn -- confirm "Welcome to the Inn." displays correctly (no trailing slash, no garbled text)
5. Visit a dungeon door -- confirm "Nothing unusual." displays correctly
6. Check resource 49 message 3/4 -- confirm switch messages are separate

### Risks

| Risk | Mitigation |
|------|------------|
| Offset table format varies between resources | Parse entry[0] as msg_count; validate table_size < payload_size |
| Some Format B resources have no offset table | Detect by checking if first 2 bytes at offset 0x10 form a valid count (< 1000) |
| Cleaning ` / ` may break intentional slash usage | Only strip trailing ` / ` pattern (space-slash-space at end of string) |

---

## Phase 2: Type-2 Dialogue Extraction

**Goal:** Produce clean, translatable Japanese text for all 12,886 dialogue messages from 112 type-2 resources, with correct kanji decoding.

**Estimated scope:** 2-3 days
**Dependencies:** Phase 1 (shared offset table code)
**Can overlap with:** Phase 3 (translation can start as extraction completes)

### Current State

Extraction is already done (`data/type2_dialogue_full.json`, 3.5 MB). However:
1. **Kanji decoding is wrong for type-2 resources** -- the type-1 glyph map produces incorrect kanji because type-2 uses a different font page. 38 override mappings have been identified but ~500+ kanji remain unmapped.
2. **Coverage is 91.6%** -- 8.4% of glyphs decode as `[??]` placeholders.
3. **Format A vs Format B sub-classification** within Section 2 is known (~84 Format A, ~116 Format B) but not integrated into extraction.

### Tasks

#### Task 2.1: Complete type-2 glyph map

Extend `data/type2_glyph_overrides.json` (currently 38 entries) to cover all kanji that differ between type-1 and type-2 font pages.

**Method:**
1. Extract raw glyph ID sequences from R1203 binary (1,580 messages)
2. For each unknown glyph ID, look up its pixel rendering in the font atlas
3. Cross-reference against the English fan guide (`dumps/guide_full.txt`) to identify the correct kanji
4. Build a complete type-2 glyph map: start with the 759-entry type-1 map, overlay the overrides

**Alternative faster method:**
- Since we are translating to English (not preserving Japanese), we do not need 100% kanji accuracy
- We need enough accuracy to understand the meaning for translation
- The existing 91.6% coverage + 38 overrides + guide cross-reference may be sufficient
- Translate using partial decoding + guide context, flagging uncertain passages

#### Task 2.2: Re-extract with corrected map

Re-run `tools/extract_type2_dialogue.txt` with the override map applied, producing:
- `data/type2_dialogue_corrected.json` -- all 12,886 messages with corrected kanji
- `data/type2_dialogue_for_translation.json` -- filtered to dialogue-only resources (exclude data tables)

#### Task 2.3: Build translation input files

For each tier of resources (see Scene Map), produce translation-ready files:
```json
{
  "resource": 1196,
  "scene": "Town Hub / Vigger Shop Intro",
  "messages": [
    {"index": 0, "japanese": "...", "context": "Orc shopkeeper greeting"},
    {"index": 1, "japanese": "...", "context": "First shop dialogue"}
  ]
}
```

Group by translation priority tier:
- **Tier 1 (Intro/Core):** R1196, R1197, R1198, R1199, R1200, R1201 (6 resources, ~3,400 messages)
- **Tier 2 (Town Events):** R1202, R1203, R1204, R1205, R1206 (5 resources, ~5,300 messages)
- **Tier 3 (Mid Dungeon):** R1207-R1210, R1354, R1355 (6 resources, ~3,900 messages)
- **Tier 4 (Late/Endgame):** R1211-R1213, R1353 (4 resources, ~2,100 messages)
- **Tier 5 (Peripheral):** Remaining 91 resources (~186 messages total, mostly short or structural)

### Scripts

| Script | Purpose | New/Modify |
|--------|---------|------------|
| `tools/build_type2_glyph_map.py` | Merge base map + overrides into complete type-2 map | NEW |
| `tools/extract_type2_dialogue_v2.py` | Re-extract with corrected map, classify Format A/B | NEW |
| `tools/prepare_translation_input.py` | Generate per-tier translation input files | NEW |

### Risks

| Risk | Mitigation |
|------|------------|
| Incomplete kanji map causes mistranslation | Cross-reference every passage against the English guide; flag uncertain kanji with `[?]` |
| Some "dialogue" is actually data tables | Filter by line_count > 0; resources with only high msg_count but zero line_count are data |
| Multiple font pages for different resource ranges | Test overrides on R1196 (earliest story) and R2659 (latest); if they differ, build per-range maps |

---

## Phase 3: Type-2 Dialogue Translation

**Goal:** Translate all 12,886 dialogue messages from Japanese to English.

**Estimated scope:** 5-10 days (the largest single phase)
**Dependencies:** Phase 2 (corrected Japanese text)
**Can overlap with:** Phase 2 (translate completed tiers while extraction continues)

### Translation Resources

1. **`dumps/guide_full.txt`** -- English fan translation guide for the game. Contains story summaries, NPC dialogue references, item/location names. Primary reference for terminology and plot accuracy.

2. **NPC name mappings** (from Scene Map findings):

| Japanese | English | Role |
|----------|---------|------|
| ヴェーラ | Vera Almohad | Tavern owner, main NPC |
| コンデ | Konde | Sorcerer at the inn |
| ウェブスター | Webster | Lord of ancient city |
| ギヨーム | Guillaume | Historical figure |
| オルトルード | Ortrud | The Holy King |
| シムゾン | Simson | Key NPC |
| ベルタン | Bertrand | B3F NPC |
| ルーシー | Lucy | Shop part-timer |
| レプラコーン | Leprechaun | B2F NPC |
| ヨッペン | Yoppen | B6F/B9F NPC |
| エレンシカ | Elenshika | Guild NPC |
| オダ | Oda | Orc shopkeeper |
| ドゥーハン | Duhan | Kingdom name |
| ディアラント | Diralanto | Ancient city |
| セポイ | Sepoy | King reference |

3. **Standard Wizardry terminology:** Use the Busin 1 (English release) translations as reference for class names, spell names, skill names, and RPG mechanics terminology.

### Translation Method

Each message will be translated with:
1. **Decoded Japanese text** (from Phase 2 output with corrected glyph map)
2. **Guide cross-reference** (matching by NPC name, scene context, or keyword)
3. **Context from surrounding messages** (dialogue flows are sequential within each resource)
4. **Control code preservation** -- keep the same number of FFFE (line breaks) and FFD2-FFD4 (page breaks) as the original. English text is word-wrapped within existing page boundaries.

### Translation Output Format

```json
{
  "resource": 1196,
  "translations": {
    "0": "Welcome to Vigger's Shop!",
    "1": "What'll it be? Buying or\nselling?",
    "2": "Heh, you adventurers sure\ndo find some strange stuff\nin the dungeon."
  }
}
```

Line breaks (`\n`) in translations map to FFFE control codes. Page breaks are inserted automatically every 3 lines by the encoder.

### Parallelism Within Phase 3

Translation can be parallelized by tier. Each tier is independent (different resources, different scenes):

| Batch | Resources | Messages | Can Start When |
|-------|-----------|----------|----------------|
| Batch 1: Intro | R1196-R1201 | ~3,400 | Phase 2, Tier 1 extraction complete |
| Batch 2: Town | R1202-R1206 | ~5,300 | Phase 2, Tier 2 extraction complete |
| Batch 3: Mid Dungeon | R1207-R1210, R1354-R1355 | ~3,900 | Phase 2, Tier 3 extraction complete |
| Batch 4: Endgame | R1211-R1213, R1353 | ~2,100 | Phase 2, Tier 4 extraction complete |
| Batch 5: Peripheral | 91 remaining resources | ~186 | Phase 2, Tier 5 extraction complete |

### Text Fitting Constraints

| Context | Max chars/line (fixed-width 12px) | Max chars/line (VWF ~7px avg) |
|---------|----------------------------------|-------------------------------|
| Standard NPC dialogue | 12-13 | ~22-25 |
| Bulletin board (R46) | 18-19 | ~32-35 |
| Dungeon examination | 16-18 | ~28-32 |
| Lines per page | 3 | 3 |

Without VWF (which requires EXE patching), English text is limited to ~13 characters per line. This is extremely tight. Translation strategy:
- Use abbreviations where possible ("can't" not "cannot", "don't" not "do not")
- Prefer short synonyms ("big" over "enormous", "get" over "acquire")
- Accept more page breaks (English will use 2-3x more pages than Japanese)
- If VWF is implemented later, translations can be expanded without re-translation

### Scripts

| Script | Purpose | New/Modify |
|--------|---------|------------|
| `tools/translate_type2_batch.py` | Translate a batch of resources using guide + glyph map | NEW |
| `tools/validate_translations.py` | Check all translations fit within line/page constraints | NEW |
| `data/type2_translations/tier1.json` | Tier 1 translations output | NEW (data) |
| `data/type2_translations/tier2.json` | Tier 2 translations output | NEW (data) |
| `data/type2_translations/tier3.json` | Tier 3 translations output | NEW (data) |
| `data/type2_translations/tier4.json` | Tier 4 translations output | NEW (data) |

### Risks

| Risk | Mitigation |
|------|------------|
| Incomplete kanji decoding causes translation errors | Flag uncertain passages; cross-reference with guide for every scene |
| 13-char line limit makes English unreadable | Prioritize VWF implementation; design translations for both fixed and variable width |
| Control code count must match original | Validate that translated messages have same number of page breaks as originals |
| Some messages are speaker tags or system text, not dialogue | Identify by FF01 (speaker) and FFE0/FFE1 (format) codes; handle specially |

---

## Phase 4: Type-2 Dialogue Injection

**Goal:** Re-encode all translated dialogue as BE uint16 glyph streams, inject into Section 2 of each type-2 resource, update size headers.

**Estimated scope:** 3-5 days
**Dependencies:** Phase 1 (offset table rebuild code), Phase 3 (translations)
**Sequential with:** Phase 5 (rebuild)

### Injection Process (per resource)

This is the byte-level process documented in `recon-type2-injection/FINDINGS.md`:

```
STEP 1: Read original raw resource from extracted/packdata_raw/{id}_type02.raw
STEP 2: Preserve bytes 0x00 through section2_offset (Section 1 + header)
STEP 3: Determine Format A (offset table) vs Format B (flat stream)
STEP 4: Build new Section 2 glyph stream from translations
STEP 5: Update section2_total_size at offset 0x14 (LE uint32)
STEP 6: Assemble: preserved_header + new_section2
STEP 7: Pad to 2048-byte sector boundary
STEP 8: Write to build/packdata_resources/{id}_type02.raw
```

### Format A vs Format B Handling

**Format A (~84 resources):** Section 2 has an offset table before the glyph stream.
- Parse offset table to locate each message
- Encode each message separately
- Rebuild offset table with new byte offsets
- Same algorithm as type-1 Format A (shared code from Phase 1 Bug Fix B2)

**Format B (~116 resources):** Section 2 is a flat glyph stream with FFFF separators.
- Simpler: just replace the glyph stream directly
- No offset table to rebuild
- Still must update section2_total_size at 0x14

### Header Fields

| Field | Offset | Action |
|-------|--------|--------|
| zero | 0x00 | DO NOT CHANGE |
| payload_size | 0x04 | DO NOT CHANGE (describes Section 1, which is unchanged) |
| stride | 0x08 | DO NOT CHANGE (always 0x20 for type-2) |
| flags0 | 0x0C | PRESERVE (0, 1, or 64) |
| section_count | 0x10 | DO NOT CHANGE (always 1) |
| section2_total_size | 0x14 | **MUST UPDATE** to new Section 2 byte count |
| section2_offset | 0x18 | DO NOT CHANGE (Section 1 is unchanged, so offset stays) |
| flags1 | 0x1C | PRESERVE (0 or 2) |
| Section 1 data | 0x20..s2o | DO NOT TOUCH (3D models, scripts, textures) |

### Space Analysis

98% of resources will overflow their original sector allocation with 2x English expansion. This is handled by the PACKDATA rebuild in Phase 5 (new sector allocations for all resources).

Total estimated expansion: ~144 MB additional across all type-2 resources. Final PACKDATA.DIG will grow from ~839 MB to ~983 MB. This is within PS2 DVD capacity (4.7 GB single-layer).

### Control Code Handling

| Code | Meaning | Rule |
|------|---------|------|
| FFFF | Message end | Keep same count (one per message) |
| FFFE | Line break | Re-generate from word-wrap (new positions) |
| FFD2/FFD3/FFD4 | Page break | **Preserve same count as original** (game scripts may expect specific page counts) |
| FFF9 | Wait + line break | Preserve if original had it |
| FF01...0148 | Speaker name tag | Copy verbatim from original |
| FFE0/FFE1 | Format off/on | Preserve if original had it |

### Scripts

| Script | Purpose | New/Modify |
|--------|---------|------------|
| `tools/encode_type2_resources.py` | Encode translations for all type-2 resources | NEW |
| `tools/inject_type2_section2.py` | Replace Section 2 in each resource binary | NEW |
| `tools/verify_type2_injection.py` | Validate: s2 size matches header, Section 1 unchanged, offsets consistent | NEW |

### Test Resources (start with these)

| Resource | Size | Format | Messages | Why Test This |
|----------|------|--------|----------|---------------|
| R35 | 4 KB | A | 37 | Small Format A, easy to verify |
| R675 | 806 KB | B | 22 | Large Format B, few messages |
| R1196 | large | B | 923 | First story resource, player sees immediately |
| R1203 | 166 KB | B | 1,580 | Most-analyzed resource (Vigger Shop/Lucy) |
| R2659 | 100 KB | A/B? | 6,276 | Highest message count, stress test |

### Risks

| Risk | Mitigation |
|------|------------|
| Section 2 contains non-dialogue data interleaved with text | Only inject into resources with confirmed dialogue (line_count > 0); skip 86 data-only resources |
| Control code count mismatch breaks game scripts | Preserve exact FFD2/D3/D4 count; only re-generate FFFE positions |
| payload_size field semantics unclear | Keep unchanged (refers to Section 1 only); if dialogue fails to display, try updating |
| Format A offset table flags vary | Preserve original flag pattern (0x0000 for all except last = 0xFFFF) |

---

## Phase 5: Complete Rebuild

**Goal:** Rebuild PACKDATA.DIG from all patched resources (type-1 + type-2 + font atlas) with updated TOC.

**Estimated scope:** 2-3 days
**Dependencies:** Phase 1 (type-1 patches), Phase 4 (type-2 patches), font atlas
**Sequential with:** Phase 6

### Rebuild Algorithm

```
SECTOR = 2048
TOC_ENTRIES = 2883
HEADER_SECTORS = 125

For each entry 0..2882:
  1. Load resource from build/packdata_resources/ if modified,
     else from extracted/packdata_raw/ (original)
  2. Compute needed_sectors = ceil(resource_size / SECTOR)
  3. Assign sector_offset = running_sector; running_sector += needed_sectors
  4. Write TOC entry: (sector_offset, needed_sectors, type_code) as 3x LE uint32

Write TOC (34,596 bytes) + padding to sector 125 (256,000 bytes)
Write each resource sequentially, padded to sector boundary
```

### Resources To Patch

| Category | Count | Source |
|----------|-------|--------|
| Type-1 MSG (menus, items) | ~21 | Phase 1 output |
| Type-2 dialogue | ~112 | Phase 4 output |
| Font atlas (R1272) | 1 | Font atlas generator output |
| EXE strings (SLPM_653.78) | 1 | Phase 5 EXE patching (5 strings) |
| **Total modified** | **~135** | Out of 2,882 total |
| Unmodified (pass-through) | ~2,747 | Copied byte-for-byte from original |

### Edge Cases

1. **Outlier entries 1370, 2100:** Preserve original TOC bytes exactly (they encode header region layout, not actual resources)
2. **Sub-header zero2 field:** Entries 2880+ have value 64 instead of 0. Preserve original values.
3. **Contiguity:** Original PACKDATA has no gaps between resources. Rebuild must maintain this.
4. **Multiple font atlases:** If battle/event/menu use different font resources (FCD_event_font, FCD_battle_font references in EXE), all must be patched. Currently only R1272 is known.

### EXE Patching (included in Phase 5)

Patch 5 save-slot display strings in SLPM_653.78:

| Offset | Original (SJIS) | Replacement (ASCII) |
|--------|-----------------|---------------------|
| 0x3FC750 | BUSIN0 Data 1 (fullwidth) | BUSIN 0 Data 1 |
| 0x3FC770 | BUSIN0 Data 2 (fullwidth) | BUSIN 0 Data 2 |
| 0x3FC790 | BUSIN0 Data 3 (fullwidth) | BUSIN 0 Data 3 |
| 0x3F9370 | BUSIN0 Suspend Data (fullwidth) | BUSIN 0 Suspend Data |
| 0x3FC720 | BUSIN0 (fullwidth) | BUSIN 0 |

Constraint: ASCII replacement must be <= original SJIS byte length (2 bytes per fullwidth char = plenty of room).

### Scripts

| Script | Purpose | New/Modify |
|--------|---------|------------|
| `tools/rebuild_packdata.py` | Full sequential rebuild with new TOC | MODIFY (add type-2 support) |
| `tools/verify_packdata.py` | Validate rebuilt PACKDATA | NEW |
| `tools/patch_exe_strings.py` | Patch 5 save-slot strings in EXE | NEW |
| `tools/find_all_font_resources.py` | Identify all font atlas resources (battle/event/menu) | NEW |

### Validation Checklist

- [ ] TOC is parseable; all entries have valid sector_offset and sector_count
- [ ] Resources are contiguous (no gaps, no overlaps)
- [ ] Each resource's sub-header payload_size matches actual data
- [ ] Non-modified resources are byte-identical to originals (spot-check 50 random)
- [ ] Modified type-1 resources decode back to expected English text
- [ ] Modified type-2 resources have correct section2_total_size at 0x14
- [ ] Font atlas resource renders correct English glyphs
- [ ] Total file size is reasonable (~983 MB, within DVD capacity)

### Risks

| Risk | Mitigation |
|------|------------|
| PACKDATA grows beyond 4.7 GB DVD capacity | Extremely unlikely (current 839 MB + ~144 MB expansion = ~983 MB) |
| Multiple font atlases missed | Search for all type-03/type-04 resources with 256x512 4bpp structure matching R1272 |
| Sub-header field semantics wrong for some resources | Test incrementally: rebuild with 5 modified resources first, then 20, then all |

---

## Phase 6: ISO + Patch

**Goal:** Build a playable English ISO and generate an xdelta patch for distribution.

**Estimated scope:** 1 day
**Dependencies:** Phase 5 (rebuilt PACKDATA.DIG + patched EXE)
**Sequential: final phase**

### ISO Rebuild

```python
import pycdlib
from io import BytesIO

iso = pycdlib.PyCdlib()
iso.open("Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso")

# Replace PACKDATA.DIG
with open("build/PACKDATA.DIG", "rb") as f:
    data = f.read()
iso.modify_file_in_place(BytesIO(data), len(data), iso_path="/PACKDATA.DIG;1")

# Replace EXE (if patched)
with open("build/SLPM_653.78", "rb") as f:
    data = f.read()
iso.modify_file_in_place(BytesIO(data), len(data), iso_path="/SLPM_653.78;1")

iso.write("build/BUSIN0_EN.iso")
iso.close()
```

If PACKDATA.DIG changed size (it will), `modify_file_in_place()` may fail. Fallback: use `rm_file()` + `add_fp()` to replace with a different-sized file.

Second fallback: Use PS2 ISO tools (cdvd2iml/iml2iso or custom sector-level tool).

### xdelta Patch Generation

```bash
xdelta3 -e -f -s "original.iso" "build/BUSIN0_EN.iso" "release/busin0_english_v1.0.xdelta"
```

Prerequisite: xdelta3 binary. Download from https://github.com/jmacd/xdelta-gpl/releases if not installed.

### PCSX2 Testing Checklist

- [ ] Game boots to title screen
- [ ] Title menu options work (New Game, Continue, Options)
- [ ] Character creation screen functions
- [ ] Town hub shows English NPC dialogue (R1196)
- [ ] Inn greeting shows English text (R42, type-1)
- [ ] Shop dialogue shows English text (R43, type-1)
- [ ] Dungeon text shows English labels (R49, type-1)
- [ ] Story dialogue in Bar Luna Light (R1197, type-2)
- [ ] Save/load screen shows English labels (EXE strings)
- [ ] Battle system functions (combat text from type-1 resources)
- [ ] No crashes during scene transitions
- [ ] Font rendering clean (no garbled glyphs, no misaligned text)

### Scripts

| Script | Purpose | New/Modify |
|--------|---------|------------|
| `tools/rebuild_iso.py` | Replace files in ISO via pycdlib | NEW |
| `tools/create_patch.py` | Generate xdelta patch | NEW |

### Risks

| Risk | Mitigation |
|------|------------|
| pycdlib cannot handle PS2 UDF quirks | Fallback to manual LBA patching or Ps2IsoTools |
| ISO size exceeds original (impacts xdelta) | xdelta handles different sizes; patch will be larger but functional |
| PCSX2 version compatibility | Test on PCSX2 1.7+ (Nightly) which has best PS2 compatibility |

---

## Phase 7: Image Textures (Deferred)

**Goal:** Replace ~50 Japanese menu button images with English versions.

**Estimated scope:** 5-10 days (art/design work + technical encoding)
**Dependencies:** None (fully independent)
**Priority:** LOW -- game is playable without this; buttons are recognizable by icon/position

### Scope

226 type-03 texture resources in PACKDATA.DIG. Subset containing Japanese text:

| Category | Estimated Count | Examples |
|----------|----------------|---------|
| Main menu buttons | 5-8 | New Game, Continue, Options, etc. |
| In-game menu buttons | 8-12 | Items, Magic, Equipment, Status, etc. |
| Location header banners | 10-15 | Town area names, dungeon floor titles |
| Battle UI overlays | 5-8 | VICTORY, DEFEAT, LEVEL UP |
| Shop/Inn/Church UI frames | 5-10 | Price labels, service names |
| Name entry screen | 1 | Replace hiragana/katakana grid with Latin alphabet |

### Process

```
1. Extract all type-03 resources as TMX/TIM2 images
2. Convert to PNG for inspection (TMX -> PNG converter)
3. Identify which contain Japanese text (manual review)
4. Create English replacement images (same dimensions, same palette)
5. Convert back to TMX format (PNG -> TMX converter)
6. Inject into PACKDATA resources
7. Include in Phase 5 rebuild
```

### Technical Details

- Format: PS2 TMX/TIM2, 4-bit or 8-bit indexed color
- Must preserve CLUT (color lookup table) exactly
- Must preserve image dimensions exactly
- Must preserve PS2 GS swizzle pattern if present
- Text rendering: use anti-aliased font on transparent background, match original style

### Name Entry Screen

Special case: the character name entry screen has a hiragana/katakana grid. For English, this needs replacement with a Latin alphabet grid (A-Z, space, backspace). This may require EXE patching in addition to texture replacement, since the grid layout and input mapping are likely hardcoded.

**Decision:** Defer name entry until after main translation is complete. Players can use default character names.

### Scripts

| Script | Purpose | New/Modify |
|--------|---------|------------|
| `tools/extract_tmx_textures.py` | Extract and convert type-03 resources to PNG | NEW |
| `tools/catalog_text_textures.py` | Identify textures containing Japanese text | NEW |
| `tools/create_english_textures.py` | Render English text onto texture templates | NEW |
| `tools/encode_tmx.py` | Convert PNG back to TMX format | NEW |

### Risks

| Risk | Mitigation |
|------|------------|
| TMX format has undocumented variants | Compare multiple extracted textures; build format parser incrementally |
| PS2 GS swizzle makes pixel layout non-trivial | Deswizzle code already exists (`tools/psmt4_deswizzle.py`); extend for 8bpp |
| Art style mismatch (English text looks out of place) | Match original font style, weight, and anti-aliasing level |
| Name entry grid requires EXE patching | Defer to enhancement phase; document the grid layout for future work |

---

## "Proof of Life" Milestone

**Objective:** See English story dialogue in the game's intro scene, validating the complete pipeline end-to-end.

**Target scene:** Bar Luna Light (R1197) -- the second scene the player encounters, with Vera's dialogue.

### Minimum Viable Path

| Step | Time | What |
|------|------|------|
| 1 | 2 hrs | Fix Bugs B1+B2 in `full_patch_pipeline.py` (offset table) |
| 2 | 1 hr | Fix Bug B3 (strip ` / ` from chunk translations) |
| 3 | 2 hrs | Translate 10 messages from R1196 or R1197 (intro dialogue) |
| 4 | 2 hrs | Build type-2 injection for one resource (R1196 or R1197) |
| 5 | 1 hr | Rebuild PACKDATA.DIG with: type-1 patches + one type-2 patch + font atlas |
| 6 | 1 hr | Build ISO, boot in PCSX2, walk to the Vigger Shop or Bar Luna Light |
| 7 | -- | **See English story dialogue on screen** |
| **Total** | **~9 hrs** | |

### What This Validates

- Font atlas renders English glyphs correctly (uppercase, lowercase, punctuation)
- Type-1 MSG encoding and injection works (menu text)
- Type-2 Section 2 injection works (story dialogue)
- Section 2 size header update is correct (game reads the right amount of data)
- PACKDATA rebuild produces a bootable game
- ISO replacement works
- The full pipeline from Japanese -> English -> glyphs -> binary -> PACKDATA -> ISO is viable

### What This Does NOT Validate

- VWF (still fixed-width 12px -- text will be cramped but readable)
- All 12,886 dialogue messages (only ~10 tested)
- Format A offset table rebuild (test resource should be Format B)
- EXE patching
- Image textures
- Edge cases (empty messages, control-code-only messages, very long messages)

### Success Criteria

The milestone is achieved when:
1. The game boots without crashing
2. Menu text (Inn, Shop, Dungeon) displays in English
3. At least one story dialogue scene (R1196 or R1197) displays English text
4. No garbled characters, no missing text, no visual artifacts in the font

---

## Complete Script Inventory

### Phase 1: Fix Pipeline
| Script | Priority | Status |
|--------|----------|--------|
| `tools/clean_chunk_translations.py` | P0 | NEW |
| `tools/unified_translation_loader.py` | P0 | NEW |
| `build/full_patch_pipeline.py` | P0 | MODIFY (fix B1+B2) |

### Phase 2: Type-2 Extraction
| Script | Priority | Status |
|--------|----------|--------|
| `tools/build_type2_glyph_map.py` | P0 | NEW |
| `tools/extract_type2_dialogue_v2.py` | P0 | NEW |
| `tools/prepare_translation_input.py` | P1 | NEW |

### Phase 3: Type-2 Translation
| Script | Priority | Status |
|--------|----------|--------|
| `tools/translate_type2_batch.py` | P0 | NEW |
| `tools/validate_translations.py` | P1 | NEW |

### Phase 4: Type-2 Injection
| Script | Priority | Status |
|--------|----------|--------|
| `tools/encode_type2_resources.py` | P0 | NEW |
| `tools/inject_type2_section2.py` | P0 | NEW |
| `tools/verify_type2_injection.py` | P1 | NEW |

### Phase 5: Complete Rebuild
| Script | Priority | Status |
|--------|----------|--------|
| `tools/rebuild_packdata.py` | P0 | MODIFY |
| `tools/verify_packdata.py` | P1 | NEW |
| `tools/patch_exe_strings.py` | P2 | NEW |
| `tools/find_all_font_resources.py` | P1 | NEW |

### Phase 6: ISO + Patch
| Script | Priority | Status |
|--------|----------|--------|
| `tools/rebuild_iso.py` | P0 | NEW |
| `tools/create_patch.py` | P0 | NEW |

### Phase 7: Image Textures (Deferred)
| Script | Priority | Status |
|--------|----------|--------|
| `tools/extract_tmx_textures.py` | P3 | NEW |
| `tools/catalog_text_textures.py` | P3 | NEW |
| `tools/create_english_textures.py` | P3 | NEW |
| `tools/encode_tmx.py` | P3 | NEW |

**Priority key:** P0 = required for proof-of-life, P1 = required for full translation, P2 = enhancement, P3 = deferred

---

## Estimated Timeline

| Phase | Effort | Cumulative | Blocks |
|-------|--------|------------|--------|
| Phase 1: Fix Pipeline | 1-2 days | 1-2 days | Everything |
| Phase 2: Type-2 Extraction | 2-3 days | 3-5 days | Phase 3, 4 |
| Phase 3: Type-2 Translation | 5-10 days | 8-15 days | Phase 4 (partial overlap with Phase 2) |
| Phase 4: Type-2 Injection | 3-5 days | 11-20 days | Phase 5 |
| Phase 5: Complete Rebuild | 2-3 days | 13-23 days | Phase 6 |
| Phase 6: ISO + Patch | 1 day | 14-24 days | Release |
| Phase 7: Image Textures | 5-10 days | (parallel/deferred) | Nothing |
| **Proof of Life** | **~9 hours** | **Day 2-3** | -- |
| **Total to v1.0 release** | **14-24 days** | | |

---

## Consolidated Risk Matrix

| # | Risk | Phase | Severity | Likelihood | Mitigation |
|---|------|-------|----------|------------|------------|
| 1 | Offset table rebuild breaks message pointers | 1, 4 | CRITICAL | CERTAIN (must fix) | Proper offset table parsing + rebuild algorithm |
| 2 | Type-2 font page uses different kanji mappings | 2 | HIGH | CONFIRMED | 38 overrides identified; extend to full coverage or translate from partial decoding + guide |
| 3 | Fixed-width 12px makes English barely readable | 3 | HIGH | CERTAIN | Design translations for 13-char lines; plan VWF as enhancement |
| 4 | PACKDATA grows too large for ISO | 5 | LOW | VERY LOW | ~983 MB << 4.7 GB DVD capacity |
| 5 | pycdlib cannot handle PS2 UDF | 6 | MEDIUM | LOW | Fallback: manual sector patching |
| 6 | Multiple font atlases need patching | 5 | MEDIUM | HIGH | Search all type-03/04 resources for atlas structure |
| 7 | Name entry screen unusable without EXE mod | 7 | HIGH | CERTAIN | Defer; players can use default names |
| 8 | Control code count mismatch breaks event scripts | 4 | MEDIUM | MEDIUM | Preserve FFD2-D4 count; only change FFFE positions |
| 9 | Section 2 contains non-dialogue binary data | 4 | MEDIUM | LOW-MEDIUM | Only inject into confirmed dialogue resources (line_count > 0) |
| 10 | Translation quality from partial kanji decoding | 3 | MEDIUM | MEDIUM | Cross-reference every passage against English guide |

---

## Appendix: Key File Paths

| File | Purpose |
|------|---------|
| `data/msg_glyph_map.json` | 759-entry type-1 glyph map |
| `data/type2_glyph_overrides.json` | 38 kanji overrides for type-2 resources |
| `data/english_glyph_table.json` | English char -> glyph slot mapping |
| `data/full_decoded_text.json` | All decoded type-1 MSG text |
| `data/type2_dialogue_full.json` | All extracted type-2 dialogue (12,886 messages) |
| `data/type2_dialogue_full.txt` | Human-readable type-2 dialogue dump (2.6 MB) |
| `data/translate_chunks/chunk_*_translated.json` | Type-1 translations (need B3/B4 cleanup) |
| `data/translations_dungeon_story.json` | Curated type-1 translations (different JSON structure) |
| `data/dialogue_resource_map.json` | Type-2 resource metadata (msg counts, sizes, offsets) |
| `extracted/packdata_raw/` | Original extracted resources |
| `build/packdata_resources/` | Patched resources for rebuild |
| `build/english_font_atlas_preview.png` | Font atlas visual preview |
| `build/PACKDATA.DIG` | Current (buggy) rebuilt PACKDATA |
| `dumps/guide_full.txt` | English fan translation guide |

## Appendix: MSG Control Code Reference

```
0xFFFF  Message separator (end of message)
0xFFFE  Line break (game does NOT auto-wrap; all breaks must be explicit)
0xFFF9  Wait for input + line break
0xFFD2  Page break variant 1
0xFFD3  Page break variant 2
0xFFD4  Page break variant 3
0xFFE0  Format off (disable text formatting)
0xFFE1  Format on (enable text formatting)
0xFF01  Speaker tag start marker
0x0148  Text begin marker (after speaker name)
0x0149  Text end marker
0x0145  Continuation marker 1
0x0146  Continuation marker 2
0x0147  Continuation marker 3
```

## Appendix: Type-2 Resource Header Quick Reference

```
TYPE-2 RESOURCE RAW LAYOUT

Bytes 0x00-0x0F: Sub-header (LE uint32 x 4)
  0x00: zero (always 0)
  0x04: payload_size (Section 1 data size) -- DO NOT CHANGE
  0x08: stride (always 0x20 for type-2) -- DO NOT CHANGE
  0x0C: flags0 (0, 1, or 64) -- PRESERVE

Bytes 0x10-0x1F: Section 2 descriptor (LE uint32 x 4)
  0x10: section_count (always 1) -- DO NOT CHANGE
  0x14: section2_total_size -- MUST UPDATE when S2 changes size
  0x18: section2_offset -- DO NOT CHANGE
  0x1C: flags1 (0 or 2) -- PRESERVE

Bytes 0x20 to (s2o-1): Section 1 data -- DO NOT TOUCH
Bytes s2o to (s2o + s2t - 1): Section 2 data -- REPLACE WITH ENGLISH
Bytes after S2: sector padding -- RECALCULATE
```
