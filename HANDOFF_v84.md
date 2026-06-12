# Busin 0: Wizardry Alternative Neo — English Fan Translation Handoff

## Project Overview

This is a Japanese-to-English fan translation of **Busin 0: Wizardry Alternative Neo** (SLPM-65378) for PS2. The translation modifies the actual ISO data (PACKDATA resources, EXE patches, font atlases) so it works on real PS2 hardware — NOT PCSX2 texture replacement.

The project has ~4,000 translated dialogue messages, translated menu/stat labels, a custom English font atlas, chargen screen patches, and EXE string patches. The build pipeline (`build/build_v9.py`) orchestrates 10+ steps to produce a playable ISO.

**Current state (v84)**: Chargen works fully in English. Town LOADS (no more VIF crash). But the intro scene dialogue, narration text, town hub buttons, and tavern menus have serious bugs. The game is currently unplayable past chargen due to scene script corruption.

## Architecture Quick Reference

- **PACKDATA.DIG**: ~840MB resource archive with 2883 resources. TOC at sector 0 (12 bytes/entry: sector_offset, sector_count, type_code as LE u32).
- **Type-01 resources**: Sub-header (16 bytes) + offset table + FFFF-delimited glyph streams. Used for item/spell/menu text (R34-R49).
- **Type-02 resources**: Header (0x20 bytes) + Section 0 (scene opcodes, BE u16) + Section 2 (text glyphs, BE u16 FFFF-delimited groups). Growing Section 2 requires remapping Section 1 opcode offsets.
- **R1272 (type-01)**: 256x512 PSMT4 font atlas. Glyph slots 0-94 = ASCII, 121-146 = uppercase duplicates for name entry, 683+ = menu tiles.
- **EXE (SLPM_653.78)**: Menu struct records at 0x3C3000-0x3C5300 reference glyph IDs. Patched SJIS strings. Patched at 0x3C9DA0 area.
- **Build pipeline**: `build/build_v9.py` — Steps 1-8.5. See CLAUDE.md for full details.

## PCSX2 Save States & Screenshots

All at: `C:\Users\Fabian Trunz\OneDrive - Berner Fachhochschule\Dokumente\PCSX2\snaps\`

Each save state has a `.png` (screenshot) and `.gs.zst` (GS dump with full VRAM state). View PNGs with the Read tool. GS dumps can be analyzed for texture/VRAM data.

### v84 Test Session (2026-06-12) — Current Build

| Timestamp | Screenshot | GS Dump | Description |
|-----------|-----------|---------|-------------|
| 20260612061701 | YES | YES | Narration: "curse and left." — `r` glyph artifact NOT fixed |
| 20260612061730 | YES | YES | Narration: "Soon after, plague struck" — `r` artifact persists |
| 20260612061801 | YES | YES | Wrong dialogue: "Belgraano: We must find her" — name misspelled, wrong scene text, `r` artifact |
| 20260612061856 | YES | YES | Wrong dialogue: "Join the force? Yes No" — choice rendered as plain text, game stuck in infinite loop |

### v83 Test Session (2026-06-11) — Previous Build

| Timestamp | Screenshot | GS Dump | Description |
|-----------|-----------|---------|-------------|
| 20260611200937 | YES | NO | Narration: "A heavy fog had settled over the deserted streets" — `r` artifacts on r, y |
| 20260611201059 | YES | NO | Narration: "The city was deathly still" — `y` artifact |
| 20260611201141 | YES | NO | Narration: "Jewel of Venoa" — `V` overbar, `r` artifacts |
| 20260611201255 | YES | YES | Dialogue: "face twitching / Hey friend" — missing portrait, garbled name "ge y" |
| 20260611201630 | YES | YES | Dialogue: Sister scene — garbled name "rc:", missing portrait |
| 20260611201746 | YES | YES | Town hub: Japanese buttons (酒場 LUNALIGHT), menu tiles not rendering |
| 20260611201958 | YES | YES | Tavern menu: Japanese sub-buttons (依頼, 王国掲示板, etc.), English "Gonna take on a job?" in dialogue box |
| 20260611202031 | YES | YES | Tavern alt view |
| 20260611202129 | YES | YES | Quest description: REQUEST LIST — entirely Japanese text |
| 20260611202227 | YES | YES | Bulletin board: "old times" post — English but first char missing ("ill" not "I'll") |
| 20260611202335 | YES | YES | Bulletin board: "board is open" post — text overflows left boundary, lines jumbled |
| 20260611202546 | YES | YES | Narration replays on tavern exit — same intro text re-triggers |
| 20260611202804 | YES | YES | Garbled scene: scattered 「ム!♪ characters — should be dialogue |
| 20260611203408 | YES | YES | REFERENCE (original Japanese ISO): Simzon portrait + 『シムゾンさん！』— shows what the scene SHOULD look like with full-screen character portrait |

### Older Reference

| Timestamp | Description |
|-----------|-------------|
| 20260606101326 | Chargen stat labels (v42 era) |
| 20260606101329 | Chargen stat labels (v42 era) |
| 20260606112454 | Chargen keyboard |
| 20260606120504 | Chargen |
| 20260611060849 | VIF crash on town entry (v80 era, now fixed) |

## Bug List — Priority Order

### P0: GAME-BREAKING — Scene Script Corruption

**BUG-1: Section 1 opcode patcher corrupts non-text opcodes (FALSE POSITIVES)**

The patcher at `tools/patch_section1_offsets.py` scans Section 1 for DISPLAY_TEXT (`0004 0000 GOFF 0000 GCNT`) and SET_NAME_REF (`000C`/`000D`) patterns using substring matching. But multi-word opcodes (0x0006=7 words, 0x0016=6 words, 0x0017=5 words) can have parameters that accidentally match these patterns. The patcher then remaps those parameters as if they were Section 2 offsets, corrupting scene flow commands.

**Impact**: Portraits don't display (0x0006 scene init corrupted), wrong dialogue plays (0x0016/0x0017 branch conditions corrupted), choices render as plain text (flow control broken), narration replays on tavern exit, game gets stuck in infinite dialogue loops.

**Confirmed in**: R1196 (11 false positives), R1197 (10 false positives), likely ALL type-02 resources with translated text.

**v84 attempted fix**: Added `body_positions` set to exclude matches inside known multi-word opcodes. **DID NOT WORK** — v84 testing shows same or worse corruption. The fix approach may be incomplete (missing opcode types in the exclusion list, or the sequential scan to build body_positions itself fails due to data regions in Section 1).

**Root cause analysis**: Section 1 is NOT purely sequential opcodes — it contains interleaved data regions (zero padding, embedded tables, 0xFFFF markers) that make sequential walking unreliable. The current pattern-matching approach with exclusions is fundamentally fragile.

**Recommended approach**: The safest fix may be to NOT remap Section 1 at all. Instead, keep Section 2 the SAME SIZE as the original by padding English translations with null glyphs (0x0000) to match the original group sizes. This eliminates the need for any offset remapping. English text that's shorter than Japanese would be null-padded; English text that's longer would need to be truncated or abbreviated. This trades some translation quality for guaranteed correctness.

**Alternative**: Do a proper full disassembly of Section 1 using the game's actual opcode table (needs reverse-engineering from the EXE). Only remap offsets at positions definitively identified as DISPLAY_TEXT or SET_NAME_REF opcodes. This is more work but preserves variable-size translations.

**Files**: `tools/patch_section1_offsets.py` (the `patch_section1()` function, lines 270-370)

**BUG-2: Translation injection destroys embedded name data**

SET_NAME_REF opcodes (0x000C) point to specific glyph positions WITHIN Section 2 message groups where character names are embedded alongside dialogue text. The injector (`inject_and_patch()` in `tools/patch_section1_offsets.py`) replaces ALL non-control glyphs in each group with English translation, destroying the embedded names.

**Impact**: Character name labels show random English text fragments ("ge y", "rc:") instead of character names.

**Fix**: Before injecting, parse Section 1 to collect all SET_NAME_REF glyph indices. During injection, preserve those glyph sequences or replace them with English name equivalents. Or, if using the fixed-size approach from BUG-1, this becomes moot since glyph positions don't move.

### P1: RENDERING — Glyph Artifacts

**BUG-3: Lowercase `r`, `y` and uppercase `V` have stray pixel artifacts**

These characters render with small marks (subscript dots on r/y, overbar on V) in the dialogue font.

**v84 attempted fix**: Moved duplicate A-Z block from atlas slots 95-120 to 121-146 to avoid column overlap. **DID NOT WORK** — artifacts persist in v84 testing.

**The column-overlap theory is WRONG**. The artifacts exist on `r` (slot 82), `y` (slot 89), and `V` (slot 54) which are in the STANDARD ASCII range (0-94), not the duplicate block. The issue is likely:
- Consolas 10pt rendering in 12x12 cells: descenders on r/y extend below the cell boundary, or
- The original Japanese glyph data at those positions wasn't fully cleared (the atlas starts from a clean black image at line 57, but the PSMT4 nibble packing or swizzle may leave residual data), or
- The PS2 GS reads beyond the 12x12 cell boundary (4-row overread) and picks up data from cells in the row below

**Diagnostic**: Compare the actual pixel data in `build/english_font_atlas.bin` at the byte positions for slots 82 (r), 89 (y), 54 (V) against the atlas preview PNG. Check if the stray pixels are in the atlas binary or only appear on PS2.

**Files**: `tools/generate_font_atlas.py`

### P2: MISSING FEATURES — Town Hub & Menus

**BUG-4: Town hub buttons show Japanese kanji (酒場, ギルド, etc.)**

Menu tile glyph IDs 683+ are in the R1272 atlas, and the EXE menu structs reference them. v84 attempted to fix the atlas format (linear nibble packing instead of swizzle). But v84 testing didn't explicitly confirm if buttons changed — the scene corruption prevents reaching the town hub reliably.

**v84 attempted fix**: Replaced `swizzle_psmt4()` with direct nibble packing in `generate_font_atlas.py`.

**Status**: NEEDS TESTING. If the atlas format fix worked, buttons should show English. If not, the tile rendering system may read from a different VRAM location than where R1272 is uploaded.

**Files**: `tools/generate_font_atlas.py`, `data/menu_labels.csv`, `tools/render_menu_tiles.py`

**BUG-5: Tavern sub-menu buttons Japanese (依頼, 王国掲示板, etc.)**

These are the same menu tile system as BUG-4. Will be fixed if BUG-4 is fixed.

**BUG-6: Bottom bar Japanese (キャンプ, システム, ライブラリー)**

Controller hint text at the bottom of screens. May be hardcoded SJIS in the EXE or from a different resource. Needs investigation.

**BUG-7: Quest descriptions untranslated on REQUEST LIST screen**

v84 added `build/inject_r39_quest.py` to translate R39 groups 412-476 (quest titles + UI labels). **NEEDS TESTING** — may already be fixed in v84.

### P3: TEXT LAYOUT

**BUG-8: Bulletin board text overflows left boundary**

The bulletin board renderer positions text using full-width Japanese character metrics. Half-width English characters shift leftward, causing the first 1-2 chars to be clipped outside the board frame.

**Fix options**: (a) EXE patch to bulletin board renderer for half-width metrics, (b) Pad English lines with leading spaces, (c) Use wider characters. Needs investigation of the board renderer in the EXE.

**BUG-9: Bulletin board "ill" should be "I'll"**

Translation typo in `build/inject_r46_r47.py` line for message slot 21. Simple text fix.

### P4: INTRO NARRATION

**BUG-10: Intro narration still shows Japanese**

R1193's Section 2 contains both FFFF-delimited groups (translated) and trailing data (234 glyphs, the ACTUAL displayed text). The trailing data uses the SAME glyph table as standard dialogue. We encoded English text into it, but it still shows Japanese.

**Theory**: The intro narration rendering path may use a DIFFERENT font resource than R1272, or the glyph IDs in the trailing data need to be in a different range. The original Japanese glyphs (0x70+ range) are standard glyph IDs that map through R1272. Our English glyphs (0-94) should also map through R1272. If the intro font atlas has English at 0-94, the text should render.

**Diagnostic needed**: Use the GS dump from `20260612061701` to check what texture is being used to render the narration text. Compare against R1272's VRAM location.

## Key Files

| File | Purpose |
|------|---------|
| `build/build_v9.py` | Master build pipeline (Steps 1-8.5) |
| `build/build_full_english_v2.py` | Step 1: Type-01 resource injection |
| `tools/patch_section1_offsets.py` | Section 1 opcode remapping + `inject_and_patch()` |
| `tools/generate_font_atlas.py` | R1272 font atlas generation |
| `tools/render_menu_tiles.py` | Menu tile rendering into atlas |
| `build/patch_exe.py` | EXE binary patches |
| `build/rebuild_packdata.py` | PACKDATA assembly from individual resources |
| `build/inject_r46_r47.py` | Bulletin board injection |
| `build/inject_r39_v2.py` | Equipment text injection |
| `build/inject_r39_quest.py` | Quest label injection (v84, new) |
| `tools/patch_r2138.py` | Stat/UI label atlas patcher |
| `tools/patch_r2100.py` | Chargen font atlas patcher |
| `data/english_glyph_table.json` | ASCII char → glyph slot mapping |
| `data/msg_glyph_map.json` | Original game's char → glyph mapping |
| `data/menu_labels.csv` | Menu tile definitions |
| `data/translate_chunks/chunk_*_translated.json` | Type-01 translations |
| `data/type2_translated/batch_*.json` | Type-02 translations |
| `CLAUDE.md` | Project instructions and architecture docs |
| `BUGS_v83.md` | Previous bug report (partially outdated) |

## Build & Test Instructions

```bash
cd C:\Programmieren\wizardrytranslation
python tools/generate_font_atlas.py && python build/build_v9.py && cp build/BUSIN0_EN_v9.iso build/BUSIN0_EN_vNN.iso
```

**CRITICAL**: Always boot FRESH from title screen in PCSX2. NEVER load save states from older ISO builds — they contain stale RAM data. Use File → Boot ISO.

**Test sequence**: Title → New Game → skip intro video → chargen (create character) → confirm → enter town → tavern → bulletin board → exit tavern. Check for: glyph artifacts, correct dialogue, portraits showing, buttons in English, narration not replaying.

## What Needs To Be Done (Priority Order)

1. **Fix Section 1 opcode remapping** (BUG-1) — This is the #1 blocker. Either implement proper opcode-aware remapping, or switch to fixed-size Section 2 injection (pad translations to match original group sizes). The current pattern-matching approach with body_positions exclusions has been attempted twice and failed both times.

2. **Fix embedded name references** (BUG-2) — Once BUG-1 is fixed (especially if using fixed-size approach), verify names display correctly. May need explicit name glyph preservation.

3. **Fix glyph artifacts on r/y/V** (BUG-3) — Investigate whether the artifacts are in the atlas binary or caused by PS2 GS cell overread. May need to adjust font rendering (smaller font, more cell padding) or clear surrounding cells.

4. **Verify menu tiles work** (BUG-4/5) — The atlas format fix (linear vs swizzle) was applied in v84 but not tested due to scene corruption. Once BUG-1 is fixed and the game is playable, check if town buttons show English.

5. **Fix bulletin board layout** (BUG-8/9) — Text clipping and the "ill" typo.

6. **Investigate intro narration** (BUG-10) — Why the translated text doesn't display.

7. **Bottom bar text** (BUG-6) — Low priority, needs investigation.
