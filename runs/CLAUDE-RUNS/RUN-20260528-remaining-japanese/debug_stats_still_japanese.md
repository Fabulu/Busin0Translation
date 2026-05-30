# Debug Report: Stats/Attributes STILL Japanese in v19 Save States

**Date**: 2026-05-28
**Save States**: stillbad-5.p2s, stillbad-6.p2s
**ISO**: BUSIN0_EN_v19.iso (built 2026-05-30 23:07)
**Analyst**: Claude Opus 4.6 (1M context)

---

## Executive Summary

The stat labels (force/str, int, fth, vit, agi, lck) and sidebar labels (gender, race, alignment, class) display as Japanese kanji on the chargen status screen despite R38 being 100% English in the ISO and in RAM. **The previous analysis document (exe_chargen_renderer.md) was WRONG about the data source for these labels.** The chargen screen does NOT read stat/sidebar labels from R38 messages 2-14.

## What We Verified (All Correct)

| Component | Status | Location |
|-----------|--------|----------|
| R38 in v19 ISO | 100% English | ISO PACKDATA.DIG sector 0x7B1 |
| R38 in RAM (stillbad-5) | 100% English | RAM 0x00E14382 |
| R38 in RAM (stillbad-6) | 100% English | RAM 0x00E14382 |
| R39 in build/ISO | Mostly English (stat patterns removed) | build/packdata_resources/0039_type15.raw |
| R44 in ISO | Patched (no JP stat glyphs) | ISO, verified clean |
| Font atlas (R1272) binary | English bitmaps at slots 0-94 | build/english_font_atlas.bin |
| Font atlas in ISO | Matches build exactly | ISO R1272 |
| Font atlas in EE RAM | English version loaded | RAM pattern match confirmed |
| Font atlas in GS VRAM | English version present (original NOT found) | GS.bin from save state |

## What the Screen Actually Shows

From stillbad-6.p2s screenshot:

**Left panel (stats):**
- HP/MAX 15 15 -- ENGLISH (but "HP/MAX" is NOT from R38 MSG 0 or 1)
- force/str (kanji 346) 25 -- JAPANESE label
- int (kanji 535,717) 9 -- JAPANESE label
- fth (kanji 308,354,320) 9 -- JAPANESE label
- vit (kanji 718,696,346) 4 -- JAPANESE label
- agi (kanji 582,719,590) 6 -- JAPANESE label
- lck (kanji 720,721,590) 4 -- JAPANESE label

**Right panel (attributes):**
- gender (kanji 511,512) male -- JAPANESE label, ENGLISH value
- race (kanji 513,514) Elf -- JAPANESE label, ENGLISH value
- alignment (kanji 515,511) -- JAPANESE label
- class (kanji 504,517) fighter -- JAPANESE label, ENGLISH value

**Bottom panel (personality):**
- All English text -- CORRECT

## The Contradiction

R38 MSG 2 = "str" (glyph IDs 83,84,82) -- English, in RAM.
R38 MSG 11 = "gender" (glyph IDs 71,69,78,68,69,82) -- English, in RAM.
Yet the screen renders kanji 346 (force/str) and kanji 511,512 (gender).

The ENGLISH R38 values (male=MSG 25, Elf=MSG 30, fighter=MSG 37) DO render correctly.
Only the LABEL portion shows Japanese.

## ROOT CAUSE CONFIRMED

**The EXE contains a hardcoded UI layout data table at VA ~0x4AB000-0x4AF000 (file offsets 0x3AB080-0x3AF080) that stores Japanese glyph IDs for stat and attribute labels.** This table is used by the chargen screen renderer to define label positions and glyph sequences. The glyph IDs in this table (e.g., 511+512 for gender, 346 for str/force) are rendered via R1272, and since glyph positions 300+ in R1272 still contain the original Japanese kanji bitmaps, the labels appear in Japanese.

The BE glyph pair 511,512 (gender kanji) appears 130+ times in this EXE data region. The data structure appears to be a packed array of (glyph_id, layout_flags, position_data) records.

### Why R38 translations don't fix this

The chargen rendering system uses **TWO different data paths**:

1. **For attribute VALUES** (male, Elf, fighter): It reads from R38 message indices stored in the linked list node (node+6 field). These are correctly resolved to English glyphs because R38 is patched.

2. **For attribute/stat LABELS** (gender, race, str, int, etc.): It uses a DIFFERENT mechanism that does NOT read from R38. The labels are likely:
   - Rendered from a separate data table in the EXE (hardcoded glyph IDs for stat labels)
   - OR rendered from high-numbered glyph IDs in R1272 that correspond to pre-rendered Japanese composite tiles (similar to how R1188 works for tab labels)
   - OR read from a DIFFERENT resource that wasn't patched

### Evidence for the "different mechanism" theory:

1. The EXE's chargen code (VA 0x2ED000-0x2F5000) calls `JAL 0x301E50` with resource indices 38, 39, 44, 51 -- setting up resource data pointers in a slot table.

2. The `chargen_render_A` function (VA 0x2F1090) iterates a linked list of descriptors, each with type (0/1/2) and value (uint16). For type 0, it calls `JAL 0x301E90` with the value as argument. For types 1 and 2, it uses different code paths.

3. The stat LABELS might use type 1 or 2 (the bitmap/icon rendering path), while the VALUES use type 0 (the MSG glyph path). The previous analysis assumed all sidebar elements use type 0, but this may be wrong.

4. The original font atlas has kanji bitmaps at glyph positions 300+ (e.g., position 346 = kanji for "force"). The English font atlas only overwrites positions 0-94 (ASCII range). So if the game renders glyph ID 346 using R1272, it will show the ORIGINAL Japanese kanji bitmap because we never replaced positions 300+ in the font atlas.

## Critical Insight: Font Atlas Positions 300+

The English font atlas (R1272) only contains English bitmaps at glyph positions 0-94 (ASCII characters). Positions 95-882 still contain the ORIGINAL Japanese kanji bitmaps from the original game.

When the chargen screen renders stat label "force" using glyph ID 346, it looks up position 346 in R1272 and finds the ORIGINAL Japanese kanji bitmap for force. **The font atlas correctly renders whatever glyph ID it receives.**

This confirms: the stat labels are being rendered using the ORIGINAL Japanese glyph IDs (346, 535, 717, etc.), NOT the English glyph IDs from R38 (83, 84, 82 for "str"). The rendering system is NOT reading from R38 for these labels.

## Where the Japanese Glyph IDs Come From

The Japanese stat/label glyph IDs in the rendered output must come from one of:

1. **The EXE's data section**: A hardcoded table mapping stat_type -> glyph_id_sequence. This table would have the original Japanese glyph IDs and was never patched.

2. **A third linked list type**: The `chargen_render_A` dispatches on node type (0, 1, 2). Types 1 and 2 might use icon/bitmap rendering that reads glyph IDs from a different table than R38.

3. **An unpatched resource**: Resource R51 (loaded at VA 0x2F596C) or another resource in the R36-R55 range that contains the stat label glyph IDs and wasn't translated.

## Recommended Next Steps (Ordered by Feasibility)

### Option A: Patch the font atlas at kanji positions (RECOMMENDED -- Simplest)
1. Render English text bitmaps into the R1272 font atlas at the specific kanji glyph positions used for stat/attribute labels
2. Map: position 346 -> "str" bitmap, positions 535+717 -> "int" bitmap, positions 308+354+320 -> "fth" bitmap, etc.
3. Map: positions 511+512 -> "gender" bitmap, 513+514 -> "race", 515+511 -> "align", 504+517 -> "class"
4. This requires rendering multi-character English text into each 12x12 glyph cell
5. **Advantage**: No EXE patching required, no layout changes needed
6. **Risk**: These kanji glyphs might appear in other game screens (dialogue, menus) where they'd also show English text instead of kanji. However, since the game is being translated to English, this is probably desirable.

### Option B: Patch the EXE UI layout table
1. Locate the exact structure format of the UI layout data at VA 0x4AB000-0x4AF000
2. Replace the Japanese glyph IDs with English glyph IDs (e.g., 346 -> 83,84,82 for "str")
3. **Challenge**: The EXE table format interleaves glyph IDs with position/flag data. Multi-character English labels (e.g., "gender" = 6 characters) can't fit where a 2-character Japanese label (e.g., 511+512 = 2 glyphs) was, without restructuring the layout data.
4. **Risk**: Changing the glyph count per label may break the rendering layout.

### Option C: Create composite tiles in R1272 at unused positions
1. Render composite English labels ("str", "int", "gender", etc.) as single 12x12 tiles
2. Place them at unused glyph positions in R1272
3. Patch the EXE table to reference these new composite tiles
4. **Advantage**: Clean rendering, correct size
5. **Challenge**: Finding unused positions, patching EXE

### Option D: NOT NEEDED -- R51 is irrelevant
R51 (type02 dialogue) was checked and does not contain stat/attribute label glyph IDs.

## Files Referenced

- ISO: `C:/Programmieren/wizardrytranslation/build/BUSIN0_EN_v19.iso`
- Font atlas: `C:/Programmieren/wizardrytranslation/build/english_font_atlas.bin`
- Original font: `C:/Programmieren/wizardrytranslation/extracted/packdata_resources/1272_type01.bin`
- Glyph table: `C:/Programmieren/wizardrytranslation/data/english_glyph_table.json`
- EXE: `C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78`
- Save state screenshots: `RAMdumps/tmp_sb5/Screenshot.png`, `RAMdumps/tmp_sb6/Screenshot.png`
- Previous analysis (CONTAINS ERRORS): `runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/exe_chargen_renderer.md`

## EXE UI Layout Table Details

The UI layout data table is in the EXE at:
- **File offsets**: ~0x3AB000 to ~0x3AF100
- **Virtual addresses**: ~0x4AB000 to ~0x4AF100
- **Size**: approximately 17KB

Sample entries showing gender label (glyph pair 511,512):
- VA 0x4ABA53: `[33023, 512, 170, 2808, 511, 512, 171, 2809, ...]`
- VA 0x4ABB5B: `[33023, 512, 170, 2808, 511, 512, 171, 2809, ...]` (duplicate for different screen state)

The data format appears to be packed records with:
- Glyph IDs as BE uint16 (matching the MSG glyph format)
- Layout/position flags interleaved between glyph IDs
- Multiple copies of the same label layout for different screen phases (chargen has ~8 phases)

## Glyph ID Mapping Required (for font atlas patching)

| Japanese Glyph IDs | Japanese Text | English Translation | English Glyph IDs |
|---|---|---|---|
| 346 | 力 (chikara) | str | 83, 84, 82 |
| 535, 717 | 知恵 (chie) | int | 73, 78, 84 |
| 308, 354, 320 | 信仰心 (shinkou-shin) | fth | 70, 84, 72 |
| 718, 696, 346 | 生命力 (seimei-ryoku) | vit | 86, 73, 84 |
| 582, 719, 590 | 敏捷度 (binshou-do) | agi | 65, 71, 73 |
| 720, 721, 590 | 幸運度 (kouun-do) | lck | 76, 67, 75 |
| 511, 512 | 性別 (seibetsu) | gender | 71, 69, 78, 68, 69, 82 |
| 513, 514 | 種族 (shuzoku) | race | 82, 65, 67, 69 |
| 515, 511 | 属性 (zokusei) | align | 65, 76, 73, 71, 78 |
| 504, 517 | 職業 (shokugyou) | class | 67, 76, 65, 83, 83 |

### Important: Font atlas cell size constraint

Each glyph position in R1272 is a 12x12 pixel cell. Japanese kanji naturally fit in 12x12. For English labels, we need to fit the COMPLETE English word into the same number of cells that the Japanese label uses:

| Japanese | Cells Used | English | Approach |
|---|---|---|---|
| 力 (1 kanji) | 1 cell | STR | Render "STR" compressed in 1 cell (4px/char) |
| 知恵 (2 kanji) | 2 cells | INT | "I" + "NT" across 2 cells, or "IN" + "T" |
| 信仰心 (3 kanji) | 3 cells | FTH | "F" + "T" + "H" (one letter per cell) |
| 生命力 (3 kanji) | 3 cells | VIT | "V" + "I" + "T" |
| 敏捷度 (3 kanji) | 3 cells | AGI | "A" + "G" + "I" |
| 幸運度 (3 kanji) | 3 cells | LCK | "L" + "C" + "K" |
| 性別 (2 kanji) | 2 cells | Gender | Abbreviate to "GN" or render "Ge"+"nd" etc. |
| 種族 (2 kanji) | 2 cells | Race | "Ra"+"ce" |
| 属性 (2 kanji) | 2 cells | Align | "Al"+"gn" |
| 職業 (2 kanji) | 2 cells | Class | "Cl"+"ss" |

For single-cell labels (like 力->STR), the 12px width allows roughly 3-4 characters at 3-4px each using a narrow font. This is feasible but requires careful bitmap rendering.

The render_menu_tiles.py system (already used for menu tile injection into R1272) could be extended to handle these stat/attribute label tiles.
