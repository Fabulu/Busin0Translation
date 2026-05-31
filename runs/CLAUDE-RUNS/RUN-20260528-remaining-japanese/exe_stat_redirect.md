# Can We Apply the Banner Fix (Patch 4) to Stat Labels?

**Date**: 2026-05-28
**Analyst**: Claude Opus 4.6 (1M context)
**Question**: Can we replace stat label kanji glyph IDs with ASCII letter glyph IDs in EXE menu struct records, the same way Patch 4 replaced banner glyph IDs?

---

## Answer: NO -- Stat Labels Are NOT in Menu Struct Records

The banner fix (Patch 4 in `patch_exe.py`) works by scanning 56-byte menu struct records at EXE offsets 0x3C3000-0x3C5300 for kanji tile IDs and replacing them with ASCII tile IDs. **This approach cannot work for stat labels because stat labels are not stored in menu struct records.**

---

## Evidence: Exhaustive Search Results

### Menu struct region (0x3C3000-0x3C5300) search

| Stat Label | Glyph ID | As Tile in Menu Struct? | Details |
|-----------|----------|------------------------|---------|
| STR (force) | 346 | **NO** | Not found in any menu struct record |
| INT-1 (chi) | 535 | **NO** | Appears at 0x3C3D1A only as slot-25 field (R38 msg index), not as a tile ID |
| INT-2 (e/megumi) | 717 | Coincidental | 717 is a tile in record 0x3C33B8, but that record is for the "create char" button, not stat labels |
| FTH (shin) | 308 | **NO** | Not found |
| FTH (kou) | 354 | **NO** | Not found |
| FTH (kokoro) | 320 | **NO** | Not found |
| VIT (sei) | 718 | Coincidental | 718 is a tile in the "create char" button record |
| VIT (mei) | 696 | Coincidental | 696 is a tile in the "adventure" button record |
| AGI (bin) | 582 | **NO** | Not found |
| AGI (shou) | 719 | Coincidental | 719 is a tile in the banner record (Patch 4 already rewrites this) |
| LCK (kou) | 720 | Coincidental | Same -- already rewritten by Patch 4 |
| LCK (un) | 721 | Coincidental | Same -- already rewritten by Patch 4 |

The "coincidental" matches are tile IDs for completely unrelated menu buttons (create, adventure, banner). They happen to share numeric values with stat label glyph IDs because the game's glyph ID namespace is shared, but they serve different purposes.

### Full EXE search for stat label glyph ID sequences

Searched the entire 4.1MB EXE for consecutive stat label glyph ID sequences as both BE and LE uint16:

| Sequence | BE hex | LE hex | Found in EXE? |
|----------|--------|--------|---------------|
| INT: 535,717 | 021702cd | 1702cd02 | **NO** (only in R38 resource) |
| FTH: 308,354,320 | 013401620140 | 340162014001 | **NO** |
| VIT: 718,696,346 | 02ce02b8015a | ce02b8025a01 | **NO** |
| AGI: 582,719,590 | 024602cf024e | 4602cf024e02 | **NO** |
| LCK: 720,721,590 | 02d002d1024e | d002d1024e02 | **NO** |

The stat label glyph ID sequences exist only in the R38 MSG resource, not in the EXE binary.

---

## Where Stat Labels Actually Come From

### Rendering Pipeline (Confirmed by Multiple Analyses)

The chargen screen uses **two different rendering paths**:

1. **For attribute VALUES** (male, Elf, fighter, etc.): Reads from R38 MSG indices. These render correctly in English because R38 is patched.

2. **For stat/attribute LABELS** (STR, INT, gender, race, etc.): Renders individual kanji glyph IDs from **kanji font pages** (R1270, R1271, R1273-R1277), NOT from R1272 (our English font atlas).

### Font Page Architecture

The game has separate font page resources for kanji:

| Resource | Role | Replaced? |
|----------|------|-----------|
| R1272 | Base font (ASCII, glyphs 0-94) | YES (English) |
| R1303 | Kanji font page | NO |
| R1269 | Kanji font page | NO |
| R1270 | Kanji font page | NO |
| R1271 | Kanji font page | NO |
| R1273 | Kanji font page | NO |
| R1274-R1277 | Extended kanji pages | NO |
| R1302 | Kanji font page | NO |

Font page table location: EXE file offset 0x3CAA60 (11 resource IDs as u32).

**Glyph IDs 95+ are served by kanji font pages, not R1272.** So when the game renders glyph 346, it looks up the bitmap in one of R1270-R1277 where the original Japanese kanji is still present. Our English bitmaps at R1272 position 346 are never consulted.

### R38 IS Patched But Not Used for These Labels

R38 messages 1-6 contain correct English translations (str, int, fth, vit, agi, lck). However, the chargen stat screen does NOT read R38 for the stat labels. Evidence:
- R38 is loaded and working (attribute values like "male", "Human", "fighter" display correctly)
- The stat labels still show Japanese kanji despite R38 being fully English in RAM
- The rendered kanji match the original R38 glyph IDs (346, 535+717, etc.), not the patched English glyph IDs (83+84+82 for "str")

---

## Why the Banner Fix Worked But Stat Labels Won't

| Feature | Banner (Patch 4) | Stat Labels |
|---------|-----------------|-------------|
| Data location | EXE menu struct records (0x3C33F0 etc.) | NOT in EXE menu structs |
| Glyph storage | Tile IDs in 56-byte struct records | Glyph IDs in R38 MSG streams |
| Font source | R1272 (our English atlas) | Kanji pages (R1270-R1277) |
| Rendering path | Menu struct tile renderer | Glyph text renderer via kanji pages |
| Fix approach | Replace tile IDs in struct records | Cannot use same approach |

The banner is rendered by the menu struct system which references R1272 tiles directly. Stat labels are rendered by the glyph text system which dispatches glyph IDs 95+ to kanji font pages.

---

## Viable Fix Approaches (Ordered by Feasibility)

### Option A: Replace Kanji Font Page Tiles (RECOMMENDED)

Replace the bitmap data at specific glyph positions in the kanji font page resources (R1270-R1277) with English letter bitmaps.

| Glyph ID | Kanji | Replace With | Font Page |
|----------|-------|-------------|-----------|
| 346 | force | (blank -- shared with VIT) | Determine by range |
| 535 | know | "in" | Determine by range |
| 717 | wisdom | "t" | Determine by range |
| 308 | faith | "f" | Determine by range |
| 354 | worship | "t" | Determine by range |
| 320 | heart | "h" | Determine by range |
| 718 | life | "vi" | Determine by range |
| 696 | destiny | "t" | Determine by range |
| 582 | agile | "ag" | Determine by range |
| 719 | quick | "i" | Determine by range |
| 590 | degree | (blank -- shared) | Determine by range |
| 720 | fortune | "lc" | Determine by range |
| 721 | luck | "k" | Determine by range |

**Prerequisite**: Determine which kanji font page (R1270-R1277) serves each glyph ID range. This requires either:
- Reverse-engineering the glyph-to-page dispatch function in the EXE
- Empirically testing by modifying each font page and checking which glyphs change

**Risk**: These kanji glyphs may appear in dialogue text elsewhere. Since the game is being fully translated, replacing them with English fragments would break any remaining Japanese text using those characters.

### Option B: Patch the Glyph-to-Page Dispatch

Modify the EXE's font dispatch code so that stat label glyph IDs (346, 535, etc.) are redirected to R1272 instead of the kanji font pages. This would let our existing English bitmaps at R1272 positions 346, 535, etc. actually get used.

**Challenge**: Requires finding and modifying the glyph dispatch function. The font page table at 0x3CAA60 and the glyph lookup table at 0x3C8B10 are involved but the exact dispatch logic is unknown.

### Option C: Patch R38 Glyph IDs to ASCII Range

Change the R38 stat label messages to use glyph IDs in the 0-94 range (ASCII, served by R1272) instead of the 300+ range (kanji, served by font pages). BUT: the chargen screen doesn't read R38 for stat labels, so this won't work either.

### Option D: Patch the EXE Rendering Code

Modify the chargen renderer to read stat labels from R38 (which is already English) instead of using the hardcoded glyph tile path. This is the most correct fix but requires complex MIPS disassembly work.

---

## Key Unknowns

1. **Which font page serves which glyph ID range?** The font page table at 0x3CAA60 lists 11 pages, but the glyph-to-page mapping function hasn't been reverse-engineered.

2. **Where does the chargen screen get stat label glyph IDs?** They're not in the EXE menu structs, not stored as consecutive sequences in the EXE data section. They might be computed by the rendering code (e.g., a function that takes stat_type=0 and returns glyph_ids=[346]) or stored in a compact lookup table that hasn't been located.

3. **The glyph table at 0x3C8B10-0x3C8D40** contains sequential (flag, glyph_id) pairs for glyph IDs 306-360+. Its purpose is unclear -- it may be a glyph-to-tile-coordinate mapping for the font atlas, not a rendering source.

---

## Summary

The Patch 4 (banner fix) approach of replacing glyph IDs in menu struct records **cannot** be applied to stat labels because:
1. Stat label glyph IDs are NOT stored in the 56-byte menu struct records
2. Stat labels are NOT rendered from R1272 -- they use kanji font pages (R1270-R1277)
3. No consecutive stat label glyph ID sequences were found anywhere in the EXE binary

The most promising fix is **Option A** (replacing specific glyph positions in the kanji font page resources) or **Option B** (redirecting the font page dispatch for those glyph IDs to R1272).

---

## Files Referenced

- `build/patch_exe.py` -- Patch 4 banner fix implementation
- `data/menu_labels.csv` -- Menu label definitions (stat entries have exe_offset=0x000000)
- `extracted/SLPM_653.78` -- Original EXE binary
- `extracted/packdata_resources/0038_type01.bin` -- Original R38 MSG resource
- `debug_22_5_stats.md` -- Save state analysis confirming stat labels use kanji font pages
- `debug_stats_still_japanese.md` -- Analysis of why patched R38 doesn't fix stat labels
- `exe_sidebar_glyphs.md` -- Menu struct record layout documentation
- `exe_stat_table_decode.md` -- Confirmed 0x3AB080 region does NOT contain stat glyph IDs
- Font page table: EXE offset 0x3CAA60 (R1303, R1269, R1270, R1271, R1273, R1274-R1277, R1302)
