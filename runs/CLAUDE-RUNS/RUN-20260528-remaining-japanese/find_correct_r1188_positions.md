# Finding Correct R1188 Stat Label Positions: Investigation Results

**Date**: 2026-05-28
**Investigator**: Claude Opus 4.6 (1M context)

---

## Executive Summary

**The R1188 stat patcher (`patch_r1188_stats.py`) was editing the WRONG RESOURCE.** Stat labels (STR, INT, PIE, VIT, AGI, LCK) are NOT rendered from R1188. They are rendered from **R1272** (the font atlas) using direct glyph ID -> atlas position mapping.

The R1188 atlas edits never showed in-game because the game never reads stat label data from R1188. R1188 contains the name-entry keyboard grid glyphs and tab labels/sidebar labels (which ARE rendered from R1188 via bitmap sprites).

---

## Evidence Chain

### 1. R1188 kana edits DO work

Edits to the kana/ASCII rows (y=0-143) in R1188's deswizzled 1024x1024 PSMT4 atlas are visible in-game. The deswizzle (bw_psmt4=1024, dbw_ct32=512) and reswizzle round-trip is correct (0 mismatches verified).

### 2. R1188 stat edits DON'T work

The stat patcher wrote English letter pixels at positions like atlas(1,508) for STR, atlas(768,3) for INT-1, etc. These positions ARE mathematically correct for the VRAM nibble address mapping:

```
R1188_base = 0xA140
vram_nibble = (vram_blk - R1188_base) * 512 + _psmt4_nibble_addr(U, V, 256)
atlas(x,y) = reverse_lookup[vram_nibble]
```

The round-trip verifies, pixels are written correctly. But they never appear on screen.

### 3. Stat labels come from R1272, not R1188

From `stat_render_trace.md` analysis of chargen disassembly:

The chargen screen has TWO rendering paths:
- **Path A**: R38 MSG text (for VALUES like "Human", "thief", "female")
- **Path B**: Font atlas direct tile (for LABELS like STR, INT, FTH)

Path B uses the **original Japanese glyph IDs** (346, 535, 717, etc.) directly as R1272 atlas positions. It renders 12x12 bitmap tiles from R1272, not from R1188.

Evidence:
- R38 in RAM is 100% English, but stat labels show Japanese
- The Japanese glyph IDs (346, 535, 717...) map to R1272 atlas positions that still contain original JP kanji bitmaps
- The `generate_font_atlas.py` + `render_menu_tiles.py` system DOES render English tiles at these positions, but the user may not have rebuilt the font atlas after stat label CSV entries were added

### 4. The R1188 "CORRECT" deswizzle image was misleading

`R1188_CORRECT_dbw512.png` was created with a DIFFERENT deswizzle algorithm/parameters than what the actual patchers use. 740,348 out of 1,048,576 pixels differ between it and the standard `deswizzle_psmt4()` output. This caused confusion when trying to visually locate kanji in the atlas.

---

## Stat Label Glyph Mapping (R1272)

| Stat | Japanese | Glyph IDs | R1272 Position | Current Tile |
|------|----------|-----------|----------------|--------------|
| STR | 力 | 346 | row 16, col 10 (x=120, y=192) | "str" |
| INT | 知恵 | 535, 717 | (120,300), (24,408) | "in", "t" |
| FTH | 信仰心 | 308, 354, 320 | (168,168), (312,192), (180,180) | "f", "t", "h" |
| VIT | 生命力 | 718, 696, 346 | (36,408), (72,396), (120,192) | reuse STR | 
| AGI | 敏捷度 | 582, 719, 590 | (192,324), (48,408), (120,336) | "ag", "i", "deg" |
| LCK | 幸運度 | 720, 721, 590 | (60,408), (72,408), (120,336) | "lc", "k", reuse AGI |

Note: Glyph 346 (力) is shared between STR and VIT-3. Glyph 590 (度) is shared between AGI-3 and LCK-3.

---

## What Was Actually Found in R1188

R1188 kanji positions were identified by visual inspection of the correctly-rendered deswizzled atlas. The stat kanji ARE present in R1188's visual grid, but R1188 is used for the name-entry keyboard display, not for stat labels:

| Character | Row | Col | Deswizzled Position | Purpose in R1188 |
|-----------|-----|-----|--------------------| ----------------|
| 力 | 10 | 8 | (185, ~242) | Keyboard grid glyph |
| 信 | 8 | 6 | (137, ~194) | Keyboard grid glyph |
| 心 | 15 | 11 | (257, ~362) | Keyboard grid glyph |
| 生 | 10 | 4 | (89, ~242) | Keyboard grid glyph |
| 命 | 10 | 1 | (17, ~242) | Keyboard grid glyph |
| 仰 | 37 | 11 | (257, ~890) | Keyboard grid glyph |
| 敏 | 36 | 20 | (473, ~866) | Keyboard grid glyph |
| 知 | 8 | 15 | (353, ~194) | Keyboard grid glyph |

These positions are in the "CORRECT" deswizzle view. In the standard deswizzle used by patchers, the positions are completely different (scrambled layout).

---

## Recommendations

### 1. Remove `patch_r1188_stats.py` from the build pipeline

It edits R1188 at positions that are never read by the stat label renderer. The edits are harmless (they write to valid but unused VRAM regions) but waste build time and add confusion.

### 2. Ensure `generate_font_atlas.py` is run BEFORE `build_full_english_v2.py`

The build script reads `build/english_font_atlas.bin` but does not regenerate it. The user must run:
```
python tools/generate_font_atlas.py
python build/build_full_english_v2.py
```

### 3. Verify R1272 stat tiles in-game

The `menu_labels.csv` entries for stat label glyph IDs (346, 535, 717, etc.) produce valid English tiles ("str", "in", "t", "f", etc.). If these still show Japanese in-game after a full rebuild, the issue is likely:
- Font atlas not regenerated (run `generate_font_atlas.py`)
- Build using stale `english_font_atlas.bin`
- Game caching texture from a different source

### 4. Consider improving stat label readability

Current abbreviations ("str", "in"+"t", "f"+"t"+"h") are functional but could be improved. Each 12x12 tile has very limited space for text. Consider:
- Single-character abbreviations: S, I, F, V, A, L (matching Western Wizardry conventions)
- Using the shared glyph system more carefully to avoid conflicts

---

## Key Files

- **R1188 atlas**: `extracted/packdata_raw/1188_type01.raw` (name-entry keyboard grid)
- **R1272 font atlas**: `build/english_font_atlas.bin` (glyph rendering atlas)
- **Stat tile definitions**: `data/menu_labels.csv` (lines 102-114)
- **Tile renderer**: `tools/render_menu_tiles.py`
- **Atlas generator**: `tools/generate_font_atlas.py`
- **Broken stat patcher**: `tools/patch_r1188_stats.py` (edits wrong resource)
- **Render trace analysis**: `runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/stat_render_trace.md`
