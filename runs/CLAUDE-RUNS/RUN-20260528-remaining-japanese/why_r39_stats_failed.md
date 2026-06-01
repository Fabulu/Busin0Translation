# Why R39 Stat Label Patches Don't Fix Chargen

**Date**: 2026-05-28
**Savestate Analyzed**: `RAMdumps/32-1.p2s` (chargen screen)
**Analyst**: Claude Opus 4.6 (1M context)

---

## Short Answer

The R39 stat labels at offsets 0x56D6-0x57B6 ARE patched to English, ARE loaded into RAM, and ARE correct. The chargen screen simply does NOT read stat labels from R39. It reads them from R38 -- but not via the glyph-stream text path. The chargen renders stat labels using the **font atlas tile path**, which fetches bitmaps directly from kanji font pages (R1270-R1277) using the original Japanese glyph IDs. Since those font pages were never replaced, Japanese kanji still appear.

---

## RAM Evidence from 32-1.p2s

### R39 Patches: Present in RAM

R39 loads at RAM `0x00E29900`. The glyph stream (bytes 0x278-0xA8E) matches the patched file 100% (1035/1035 uint16 values identical).

The sequential data section stat labels are ALSO patched in RAM:

| R39 Offset | Original (JP) | File (patched) | RAM Value | Decoded |
|------------|---------------|----------------|-----------|---------|
| 0x56D6     | 0x015A (force-kanji) | 0x0033 | 0x0033 | S |
| 0x5700     | 0x0217 (know-kanji)  | 0x0029 | 0x0029 | I |
| 0x5702     | 0x02CD (wisdom-kanji)| 0x0031 | 0x0031 | Q |
| 0x572C     | 0x0134 (faith-kanji) | 0x0026 | 0x0026 | F |
| 0x572E     | 0x0162 (worship-kanji)| 0x0034| 0x0034 | T |
| 0x575A     | 0x02CE (body-kanji)  | 0x0036 | 0x0036 | V |
| 0x575C     | 0x02B8 (life-kanji)  | 0x0029 | 0x0029 | I |
| 0x575E     | 0x015A (force-kanji) | 0x0034 | 0x0034 | T |
| 0x5788     | 0x0246 (agile-kanji) | 0x0021 | 0x0021 | A |
| 0x578A     | 0x02CF (quick-kanji) | 0x0027 | 0x0027 | G |
| 0x578C     | 0x024E (degree-kanji)| 0x0029 | 0x0029 | I |
| 0x57B6     | 0x02D0 (fortune-kanji)|0x002C | 0x002C | L |
| 0x57B8     | 0x02D1 (luck-kanji)  | 0x0023 | 0x0023 | C |
| 0x57BA     | 0x024E (degree-kanji)| 0x002B | 0x002B | K |

All patched values match RAM exactly. The patches loaded successfully.

### R38 Patches: Also Present in RAM

R38 loads at RAM `0x00E14382` with English stat labels:

| R38 Msg | RAM Glyphs | Decoded |
|---------|-----------|---------|
| 0       | (empty)   |         |
| 1       | 0028 0030 | HP      |
| 2       | 0028 0030 000F 002D 0028 0030 | HP/MHP |
| 3       | 0033 0034 0032 | STR |
| 4       | 0029 002E 0034 | INT |
| 5       | 0026 0034 0028 | FTH |
| 6       | 0036 0029 0034 | VIT |
| 7       | 0021 0027 0029 | AGI |
| 8       | 002C 0023 002B | LCK |
| 9       | 002E 0041 004D 0045 | Name |
| 10      | 002C 0045 0056 0045 004C | Level |
| 11      | 0032 0041 0043 0045 | Race |
| 12      | 0027 0045 004E 0044 0045 0052 | Gender |
| 13      | 0021 004C 0049 0047 004E | Align |

### EXP at R39 0x58D6: English

Glyph IDs 0x0025 0x0038 0x0030 = "EXP". This is in the same sequential data region. It was English in the original R39 too -- it was never Japanese. The fact that EXP is English does NOT prove our patches work for chargen; EXP appears in a different context (possibly item/spell descriptions read by a different code path).

### Original Japanese Glyph 0x015A: NOT Found as Standalone Label

The original Japanese glyph sequence for stat labels (e.g., `FFFF 015A FFFE FFFF 0217 02CD`) has zero hits in RAM. Only the patched English versions exist. This confirms the ISO patches loaded correctly.

---

## Root Cause: Two Different Rendering Paths

The chargen screen uses two independent rendering systems:

### Path A: R38 MSG Text (works -- renders English)

```
R38 message index -> offset table lookup -> FFFF-delimited glyph stream
  -> glyph IDs in 0-94 range (ASCII)
  -> text engine: atlas_position = glyph_id
  -> looks up 12x12 bitmap in R1272 (our English font atlas)
  -> draws on screen
```

**Used for**: Race values (Human, Elf), class values (thief, fighter), gender values (male, female), personality text.
**Status**: WORKING. These display in English.

### Path B: Font Atlas Direct Tile (broken -- renders Japanese kanji)

```
Original Japanese glyph ID (346, 535, 718, etc.)
  -> glyph ID >= 95, dispatched to kanji font page
  -> looks up 12x12 bitmap in R1270-R1277 (ORIGINAL Japanese kanji pages)
  -> draws on screen
```

**Used for**: Stat labels (STR, INT, FTH, VIT, AGI, LCK), attribute labels (Gender, Race, Alignment, Class).
**Status**: SHOWS JAPANESE. The kanji font pages were never replaced.

### Why Path B Ignores R38

The chargen code at VA `0x2F1090` iterates a linked list of UI descriptor nodes. For stat/attribute LABELS, it uses a tile-based rendering path that references the original Japanese glyph IDs as font atlas positions. These glyph IDs (346, 535, 717, etc.) map to positions in the kanji font pages (R1270-R1277), NOT to R1272.

Even though R38 messages 3-8 contain the English translations "STR", "INT", etc., the chargen label renderer does not read those messages for the label display. It only uses R38 for the attribute VALUES.

### Why R39 Patches Are Irrelevant

R39 is a type15 resource containing item/spell/equipment descriptions. The stat labels in R39's sequential data section (0x56CE+) are full sentences like "[prefix glyphs] STR [suffix glyphs] / SP [more glyphs]" -- these are descriptive text about how stats affect equipment, NOT the standalone labels shown on the chargen screen.

---

## The Font Page Architecture

| Resource | Role | Replaced? |
|----------|------|-----------|
| R1272    | Base font (ASCII, glyphs 0-94) | YES (English bitmaps) |
| R1269    | Kanji font page | NO |
| R1270    | Kanji font page | NO |
| R1271    | Kanji font page | NO |
| R1273    | Kanji font page | NO |
| R1274-R1277 | Extended kanji pages | NO |
| R1302    | Kanji font page | NO |
| R1303    | Kanji font page | NO |

Font page table in EXE: file offset `0x3CAA60` (11 resource IDs as uint32).

Glyph IDs 0-94 are served by R1272 (English). Glyph IDs 95+ are dispatched to kanji font pages. Our English font atlas only covers positions 0-94.

---

## What the EXE Contains

### NOT in the EXE
- Glyph ID 346 (0x015A) is NOT loaded via any MIPS `li` instruction
- No consecutive stat glyph ID sequences (346, 535+717, 308+354+320, etc.) found anywhere in the EXE as BE or LE uint16
- Stat labels are NOT stored in the 56-byte menu struct records at 0x3C3000-0x3C5300

### IS in the EXE
- Glyph ID 511 (0x01FF, gender-kanji) loaded at 8 locations via `addiu $reg, $zero, 0x01FF`
- R38 message index table at VA `0x004C1F40`: `[1,2,3,4,5,6,7,8,9,10,11,21]`
- Font page table at file offset `0x3CAA60`

The stat label glyph IDs are likely stored in the chargen screen's UI bytecode/script data within a resource (not the EXE binary itself) or computed at runtime from a compact lookup.

---

## Fix Options (from prior analysis, ordered by feasibility)

### Option A: Replace Kanji Font Page Bitmaps (RECOMMENDED)

Replace the bitmaps at specific glyph positions in the kanji font page resources (R1270-R1277) with English letter fragments:

| Glyph ID | Current Kanji | Replace With |
|----------|--------------|-------------|
| 346      | force        | "S" (shared with VIT pos 3) |
| 535      | know         | "I" or "In" |
| 717      | wisdom       | "t" or "NT" |
| 308      | faith        | "F" |
| 354      | worship      | "T" |
| 320      | heart        | "H" |
| 718      | life         | "V" or "Vi" |
| 696      | destiny      | "t" or "IT" |
| 582      | agile        | "A" or "Ag" |
| 719      | quick        | "I" |
| 590      | degree       | (shared -- used by AGI and LCK) |
| 720      | fortune      | "L" or "Lc" |
| 721      | luck         | "K" |

**Prerequisite**: Determine which kanji font page serves each glyph ID range.
**Risk**: These kanji appear in dialogue text too. Since the game is being fully translated, this is acceptable.

### Option B: Redirect Font Page Dispatch in EXE

Patch the EXE's glyph dispatch code so glyph IDs 346, 535, etc. are redirected to R1272 instead of kanji font pages. Then our existing English bitmaps at those R1272 positions would be used.

### Option C: Patch EXE Chargen Code

Modify the chargen renderer to read stat labels from R38 glyph streams (which are already English) instead of using the font atlas tile path. Most correct but most complex.

---

## Key File Paths

- Patched R39: `build/packdata_resources/0039_type15.raw`
- Patched R38: `build/packdata_resources/0038_type01.raw`
- Original R39: `extracted/packdata_raw/0039_type15.raw`
- EXE: `extracted/SLPM_653.78`
- Font atlas: `build/english_font_atlas.bin`
- Savestate: `RAMdumps/32-1.p2s`
- Prior analysis: `runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/stat_render_trace.md`
- Prior analysis: `runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/exe_stat_redirect.md`
- Prior analysis: `runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/debug_stats_still_japanese.md`
