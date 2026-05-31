# Stat Label Render Trace: Definitive Analysis

**Date**: 2026-05-28
**Savestate**: `RAMdumps/22-5.p2s` (chargen screen, patched ISO)
**Analyst**: Claude Opus 4.6 (1M context)

---

## Executive Summary

**The chargen stat labels (STR, INT, FTH, VIT, AGI, LCK) and attribute labels (Gender, Race, Alignment) ARE read from R38 glyph streams -- but the Japanese kanji on screen come from the FONT ATLAS FALLBACK PATH, not from R38 itself.**

The rendering system has TWO overlapping paths:
1. **R38 MSG text path**: Reads R38 MSG 1-13, gets English glyph IDs, renders via the composable text engine.
2. **Font atlas tile path**: Uses the ORIGINAL Japanese glyph IDs (346, 535, 717, etc.) as R1272 atlas positions to render pre-baked bitmap tiles.

The font atlas path takes priority for stat/attribute labels on the chargen screen. Since R1272 positions 95-882 still contain original Japanese kanji bitmaps, the Japanese appears despite R38 being fully English.

---

## Evidence Chain

### 1. R38 IS 100% English in RAM

R38 loads at RAM `0x00E14382` with offset table at `0x00E14300`.

| RAM MSG | Address | Glyph IDs (remapped +0x20) | Decoded |
|---------|---------|---------------------------|---------|
| 0 | 0xE14382 | 72,80,15,77,72,80 | HP/MHP |
| 1 | 0xE14392 | 83,84,82 | STR |
| 2 | 0xE1439C | 73,78,84 | INT |
| 3 | 0xE143A6 | 70,84,72 | FTH |
| 4 | 0xE143B0 | 86,73,84 | VIT |
| 5 | 0xE143BA | 65,71,73 | AGI |
| 6 | 0xE143C4 | 76,67,75 | LCK |
| 7 | 0xE143CE | 78,65,77,69 | NAME |
| 8 | 0xE143DA | 76,69,86,69,76 | LEVEL |
| 9 | 0xE143E8 | 82,65,67,69 | RACE |
| 10 | 0xE143F4 | 71,69,78,68,69,82 | GENDER |
| 11 | 0xE14404 | 65,76,73,71,78,77,69,78,84 | ALIGNMENT |
| 12 | 0xE14428 | 67,76,65,83,83 | CLASS |

No second (Japanese) copy of R38 exists anywhere in the 32MB EE RAM. Confirmed by exhaustive search for:
- Original JP stat pattern `FFFF 015A FFFE FFFF 0217 02CD` -- **zero hits**
- Raw (un-remapped) file-format `FFFF 0028 0030` -- **zero hits**

### 2. Screen Shows Japanese Kanji for Labels

From the 22-5.p2s screenshot (chargen screen):
- **Japanese labels**: force-kanji (STR), know+wisdom-kanji (INT), faith+worship+heart-kanji (FTH), etc.
- **English values**: "thief", "female", "Human" -- these DO come from R38 (MSG 37, MSG 25, MSG 29)
- **English UI text**: "select a class.", "Class&Parameter", "Bonus Point"

### 3. If R38 Were Read for Labels, They'd Be English

The glyph-to-atlas mapping is: `atlas_position = glyph_id - 32`

If R38 MSG 1 (STR) were rendered:
- RAM glyph IDs: 83, 84, 82
- Atlas positions: 51, 52, 50
- R1272 at positions 51,52,50: English letters S, T, R (our replacement)
- Screen would show: "STR"

But screen shows force-kanji. Therefore **R38 is NOT the data source for these labels**.

### 4. The Original Japanese Glyph IDs ARE the R1272 Atlas Positions

The Japanese kanji visible on screen correspond to R1272 font atlas positions that were NEVER replaced:

| Stat | Japanese | Original Glyph IDs | R1272 Atlas Position | Content |
|------|----------|--------------------|--------------------|---------|
| STR | force | 346 | 346 | Original JP kanji bitmap |
| INT | know+wisdom | 535, 717 | 535, 717 | Original JP kanji bitmaps |
| FTH | faith+worship+heart | 308, 354, 320 | 308, 354, 320 | Original JP kanji bitmaps |
| VIT | life+destiny+force | 718, 696, 346 | 718, 696, 346 | Original JP kanji bitmaps |
| AGI | agile+quick+degree | 582, 719, 590 | 582, 719, 590 | Original JP kanji bitmaps |
| LCK | fortune+luck+degree | 720, 721, 590 | 720, 721, 590 | Original JP kanji bitmaps |
| Gender | nature+distinction | 511, 512 | 511, 512 | Original JP kanji bitmaps |
| Race | seed+tribe | 513, 514 | 513, 514 | Original JP kanji bitmaps |
| Alignment | belong+nature | 515, 511 | 515, 511 | Original JP kanji bitmaps |

Our English font atlas (R1272) only replaced positions 0-94 (ASCII characters). Positions 95-882 retain original Japanese bitmaps.

### 5. Japanese Glyph IDs 346, 535, 717 etc. NOT Found in EXE Data Section

Exhaustive search of EXE data section `0x3AB080-0x3AF080` found **zero matches** for the primary stat glyph IDs (346, 535, 717, 308, 354, etc.) as either BE or LE uint16. The glyph IDs are NOT hardcoded in the EXE layout tables.

### 6. The Menu Struct Font Atlas System IS the Rendering Path

The `fix_shared_glyphs.md` document confirms that the font atlas stat label approach (via `menu_labels.csv` -> `render_menu_tiles.py` -> `generate_font_atlas.py`) replaces kanji bitmaps at the ORIGINAL glyph positions in R1272.

The menu struct system (56-byte entries at EXE file offset `0x3C2F58-0x3C5338`, VA `0x4C2F80-0x4C5338`) references R1272 tile IDs in the 475-921 range. Some of these tile IDs overlap with the kanji glyph IDs used for stat labels.

---

## The TWO Rendering Paths (Definitive)

### Path A: R38 MSG Text (for VALUES)

```
R38 MSG index -> offset table lookup -> FFFF-delimited glyph stream
  -> glyph IDs (remapped +0x20 in RAM)
  -> text engine renders each glyph via atlas_position = glyph_id - 32
  -> looks up 12x12 bitmap at atlas position in R1272
  -> draws on screen
```

**Used for**: Race values (Human, Elf), class values (thief, fighter), gender values (male, female), personality names, spell level labels (Lv1-Lv7), combat stats (OFE, ACC, DEF, EVA).

**Status**: Working correctly. English text renders because R38 is patched and atlas positions 0-94 have English bitmaps.

### Path B: Font Atlas Direct Tile (for LABELS)

```
Original Japanese glyph ID (346, 535, etc.)
  -> used directly as R1272 atlas position
  -> looks up 12x12 bitmap at that atlas position
  -> draws on screen
```

**Used for**: Stat labels (STR/force, INT/know+wisdom, etc.), attribute labels (Gender, Race, Alignment).

**Status**: Shows Japanese because atlas positions 95-882 retain original kanji bitmaps. The `menu_labels.csv` system is designed to replace these specific positions with English text bitmaps, but the replacements may not be fully applied or may have rendering conflicts (see `fix_shared_glyphs.md`).

---

## How the Chargen Renderer Works

### Function at VA 0x2F1090 (chargen_render_A)

```
$s2 = descriptor struct pointer
$s1 = linked list head at $s2+4

FIRST LOOP (stat/attribute labels):
  For each node in linked list:
    type = lh 4($s1)        ; 0, 1, or 2
    msg_index = lhu 6($s1)   ; R38 message index
    update_flag = lh 8($s1)
    
    Call 0x301E90(slot=type, msg_index)
    ; This is a DIRTY-BIT CHECKER, not a data lookup!
    ; Returns 1 if the message's display needs updating.
    
    If update needed:
      Re-render the label (via Path B, font atlas tiles)
    
    next = lw 0($s1)

SECOND LOOP (values/icons):
  For each node in second linked list at $s2+8:
    Call 0x180FD0(tile_id from node)
    ; Tile-based rendering for attribute values
    
    next = lw 0($s1)
```

### Function 0x301E90 (dirty-bit bitmap checker)

This function does NOT return glyph data. It checks a BITMAP at `0x00565110` (slot 0), `0x005650D0` (slot 1), or `0x00565090` (slot 2) to determine if a message's on-screen representation needs re-rendering.

```
Input: $a0 = slot (0-12), $a1 = msg_index (0-511)
Output: $v0 = 1 if bit set (needs update), 0 if clear

bit_pos = msg_index & 0x1F
word_idx = msg_index >> 5
bitmap_word = *(table_base + word_idx * 4)
return (bitmap_word >> bit_pos) & 1
```

### Resource Slot Table

- GP = 0x00504FF0 (from ELF `.reginfo` section)
- Slot table pointer at GP-26868 = 0x004FE6FC
- Slot table base = 0x00DC3740 (all zeros in this savestate -- resources released after initial rendering)

---

## Answer to the Original Question

**Does the chargen screen read R38 message glyph streams for stat labels?**

**NO.** The chargen screen uses R38 glyph streams for attribute VALUES (race name, class name, gender, etc.) via Path A. But for stat/attribute LABELS, it uses the font atlas direct tile system (Path B), which renders bitmaps from R1272 atlas positions corresponding to the original Japanese kanji glyph IDs.

The function 0x301E90 called for each label node is only a dirty-bit checker, not a glyph data reader. The actual label rendering uses pre-determined atlas positions (the original Japanese glyph IDs) to draw tiles from R1272.

**The fix**: Replace the R1272 font atlas bitmaps at the specific Japanese kanji positions (346, 535, 717, etc.) with English text bitmaps. This is already implemented via `menu_labels.csv` -> `render_menu_tiles.py` -> `generate_font_atlas.py`, with shared-glyph conflicts resolved in `fix_shared_glyphs.md`.

---

## Key RAM Addresses (22-5.p2s)

| Address | Content |
|---------|---------|
| 0x00E14300 | R38 offset table (32-bit entries) |
| 0x00E14382 | R38 glyph data start (FFFF-delimited, English) |
| 0x00E160F2 | R38 last message (MSG 188) |
| 0x00E16A7E | Post-R38 data (R34 content starts) |
| 0x004C2F80 | Menu struct table base (VA, 161 entries x 56 bytes) |
| 0x004D46C8 | Stat msg index table: [2,3,4,5,6,7] = STR,INT,FTH,VIT,AGI,LCK |
| 0x00504FF0 | GP register value |
| 0x004FE6FC | Resource slot table pointer (GP-26868) |
| 0x00DC3740 | Resource slot table base (empty in this savestate) |
| 0x00565110 | Dirty-bit bitmap table (slot 0) |
| 0x005650D0 | Dirty-bit bitmap table (slot 1) |
| 0x00542470 | Text render state struct (zeroed = idle) |

## Files Referenced

- Savestate: `RAMdumps/22-5.p2s`
- EXE: `extracted/SLPM_653.78` (GP=0x504FF0, entry=0x100008)
- Patched R38: `build/packdata_resources/0038_type01.raw`
- Original R38: `extracted/packdata_resources/0038_type01.bin`
- Font atlas: `build/english_font_atlas.bin` (82,176 bytes)
- Glyph table: `data/english_glyph_table.json` (97 entries, atlas_pos = ASCII - 32)
- Menu labels: `data/menu_labels.csv`
- Prior analysis: `fix_shared_glyphs.md` (shared glyph conflict resolution)
- Prior analysis: `debug_stats_still_japanese.md` (initial discovery of the problem)
- Prior analysis: `exe_stat_table_decode.md` (EXE region 0x3AB080 is NOT stat glyph data)
