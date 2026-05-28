# Phase 3 - Font Atlas Analysis: FINDINGS

**Date:** 2026-05-22
**Status:** Font atlas FOUND and partially rendered

---

## Critical Discovery: Font Atlas is Resource 1272

**File:** `extracted/packdata_resources/1272_type01.bin`
**Size:** 65,792 bytes
**Format:** PS2 GS PSMT4 (4 bits per pixel, 16-color indexed)
**Texture Dimensions:** 256x512 pixels
**Structure:** 192-byte header + 64-byte palette (16 RGBA32 colors) + 65,536 bytes pixel data

### Verification
- **TEX0 register** at header offset 0x50 = `0x2000000661410000`:
  - PSM = 20 (PSMT4 = 4bpp indexed)
  - TW = 8 (2^8 = 256 pixels wide)
  - TH = 9 (2^9 = 512 pixels tall)
  - TBW = 4 (buffer width = 256 pixels)
  - CPSM = 0 (PSMCT32 palette format)
  - CSM = 0 (CSM1 palette lookup mode)
- **Unique in the dataset:** Only PSMT4 256x512 texture among 2,883 resources
- **Palette is all-white** (R=255,G=255,B=255,A=255 for all 16 entries) -- the font is rendered purely through alpha/intensity channel. Each 4bpp value represents opacity (0=transparent, 15=fully opaque), with color applied at render time by the game engine.
- **Size math:** 192 + 64 + (256*512/2) = 192 + 64 + 65536 = 65,792 bytes (exact match)

### Glyph Grid Analysis
For ~858 glyphs in a 256x512 atlas:
- **Best fit: 16x16 pixel cells** = 16 columns x 32 rows = 512 slots (too few)
- **Best fit: 14x14 pixel cells** = 18 columns x 36 rows = 648 slots (still low)
- **Most likely: 12x12 cells** = 21 columns x 42 rows = 882 slots (close to 858)
- **Also possible: mixed sizes** -- proportional width glyphs (variable-width font)

The exact cell size and grid arrangement need further investigation with a proper PSMT4 deswizzle. The raw renders at 128-pixel page width clearly show rows of Japanese characters (kanji, kana, punctuation) in the expected glyph order.

---

## Resource Format: PS2 GS Texture (Type 01)

All type 01 resources in PACKDATA.DIG follow this format:

```
Offset  Size    Description
0x00    192     Header (GIF tags + GS register setup)
  0x00    8     Version/count (01 00 00 00 02 00 00 00)
  0x10    16    GIF tag 1
  0x20    16    GIF tag 2
  0x30    16    GS TRXPOS/TRXREG register data
  0x50    8     TEX0 register (pixel format, dimensions, CLUT config)
  0x60    16    Alpha/blend settings
  0x70    8     Dimensions stored directly as (width_u16, height_u16, 0, 0)
  0x78-BF       Additional register setup / padding
0xC0    N       Palette data (RGBA32 entries: 64 bytes for 4bpp, 1024 bytes for 8bpp)
0xC0+N  M       Pixel data (PSMT4 or PSMT8 swizzled)
```

### Texture Size Distribution
| Format | Dimensions | Resource Count | Raw Size |
|--------|-----------|----------------|----------|
| PSMT4 128x128 | 128x128 | 500 | Various |
| PSMT8 256x512 | 256x512 | 232 | 132,288 |
| PSMT8 256x256 | 256x256 | 103 | ~66,000 |
| PSMT8 512x512 | 512x512 | 92 | 263,360 |
| PSMT8 128x128 | 128x128 | 58 | Various |
| **PSMT4 256x512** | **256x512** | **1** | **65,792** |

Resource 1272 is the ONLY PSMT4 256x512 texture -- confirming its unique role as the font atlas.

---

## PS2 GS Swizzle Issue

The pixel data is stored in PS2 GS hardware-native format with block/column swizzling:

### PSMT4 Storage Layout
- **Page:** 128x128 pixels (8,192 bytes at 4bpp)
- **Block:** 32x16 pixels (256 bytes at 4bpp)
- **Column:** 32x2 pixels (32 bytes at 4bpp)

For a 256x512 texture: 2 pages wide x 4 pages tall = 8 pages total

### Current Render Status
- **Raw at 128px width:** Characters clearly visible within each page (GS pages are 128px wide for PSMT4)
- **Paged 256x512:** Pages correctly arranged, characters visible but with intra-block swizzle artifacts
- **Column-unswizzled:** Partially improved, characters more recognizable
- **Full deswizzle:** Requires correct PSMT4 block table and column interleave order (in progress)

**Renders saved to:** `dumps/font_renders/`

Key files:
- `font_atlas_raw_128w.png` -- Best current render (128x1024, raw page-width)
- `font_atlas_paged_256x512.png` -- Correct page arrangement (256x512)
- `font_atlas_paged_inv.png` -- Inverted for readability
- `1272_col_unswiz_inv.png` -- Column-deswizzled, inverted
- `1272_zoom_kanji.png` -- Zoomed view of kanji region

---

## EXE Font Configuration (SLPM_653.78)

### Font Descriptor Structs at EXE 0x3C0700
13 font descriptor structures (28 bytes each), separated by 0x80808080 + 0x01000100 markers:

```
Idx  Type    Count  CellW  CellH  TexW  TexH
 0  0x0002    0x22    16     16    256   256
 1  0x0002    0x21    80     16    256   256
 2  0x0002    0x24    96     16    256   256
 3  0x0002    0x2b    56     32    256   256
 4  0x0002    0x21    80     32    256   256
 5  0x0002    0x2c    96     32    256   256
 6  0x0002    0x20    56     48    256   256
 7  0x0002    0x21    80     48    256   256
 8  0x0002    0x23    96     48    256   256
 9  0x0002    0x2a    56     64    256   256
10  0x0002    0x21    80     64    256   256
11  0x0002    0x25    96     64    256   256
12  0xffff (terminator)
```

These appear to define different font rendering configurations (sizes 16/32/48/64 pixels) for different UI contexts (battle, event, menu, etc.).

### Glyph Index Array at EXE 0x3C0870
77 entries: `[1, 5, 6, 7, 8, 9, 10, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 33(!), 34("), 35(#), 36($), 37(%), 38(&), 39('), 40((), 41()), 42(*), 43(+), 44(,), 45(-), 46(.), 47(/), 48(0)...86(V), 89(Y), 90(Z), 91([), 92(\), 93(])]`

This maps ASCII characters `!` through `]` (with W and X skipped) to glyph indices in the font atlas. The first 30 entries (1-30) appear to be control characters or special symbols.

### FCD Resource References in EXE
- `FCD_battle_font` at 0x3F03C1 -- Battle system font resource
- `FCD_event_font` at 0x3F34C8 -- Event/dialogue font resource
- `FCD_battle_common_effect` at 0x3EE3B9
- `FCD_event_frame` at 0x3F34F8

These are debug strings logged during font resource loading/unloading.

---

## No Other Font Candidates Found

### Eliminated Candidates
- **Entry 34 (type 20):** 972-byte container TOC with 19 sub-entries pointing into PACKDATA.DIG -- not font data itself
- **132,288-byte type01 files:** PSMT8 256x512 textures -- confirmed as 3D model/character textures via palette analysis (varied RGBA colors, not font-like)
- **Entries 36-38 (type01):** Offset/index tables (3-7KB) with incrementing 32-bit values -- possibly script/text offset tables, not font data
- **MOJI.TMZ files:** Battle effect sprites (damage numbers), not the main game font
- **TMX/TMX0 files:** UI textures (BAR_00.TMX, GUILD_00.TMX), not fonts
- **EXE embedded data:** Width table candidates at 0x3DDC48 are actually log2 lookup tables from the C runtime

### Font Metadata Still Needed
- **Width table:** Not yet located. For variable-width rendering, there should be ~858 byte values (4-16 range) specifying each glyph's advance width. Likely stored near the font texture in PACKDATA or in one of the small type01 resources.
- **SJIS mapping table:** Not found in EXE or resources. The game likely computes glyph positions algorithmically from SJIS codepoints rather than using a lookup table.

---

## Recommended Next Steps

1. **Complete PSMT4 deswizzle** -- Implement the exact PS2 GS PSMT4 block/column pixel reordering to get a clean render of all 858+ glyphs
2. **Determine glyph cell size** -- Once properly deswizzled, measure exact cell dimensions (likely 12x12 or variable)
3. **Find width table** -- Scan small type01 resources for sequences of ~858 bytes in range 4-16
4. **Map SJIS codes to glyph indices** -- Analyze the text rendering code path in the EXE to understand glyph lookup
5. **Design replacement strategy** -- Either:
   a. Replace individual glyphs with Latin characters (if cell size allows)
   b. Create a new font atlas with Latin + remaining Japanese characters
   c. Modify the rendering code to support variable-width Latin text

---

## Files Produced

### Renders (in `dumps/font_renders/`)
- `font_atlas_raw_128w.png` -- Raw font data at GS page width
- `font_atlas_paged_256x512.png` -- Page-arranged 256x512
- `font_atlas_paged_inv.png` -- Inverted for readability
- `1272_col_unswiz_inv.png` -- Column-deswizzled inverted
- `1272_zoom_kanji.png` -- Zoomed kanji section
- `1272_zoom_top.png` -- Zoomed top (ASCII/punctuation) section
- Plus ~80 additional diagnostic renders at various settings

### Scripts
- `tools/analyze_font_entry.py` -- Font atlas analysis and rendering script

### This Document
- `runs/CLAUDE-RUNS/RUN-20260522-1932-initial-recon/subagents/impl04-font/FINDINGS.md`
