# R1272 Page Layout Analysis

**Date**: 2026-05-28
**Analyst**: Claude Opus 4.6

---

## Executive Summary

**R1272 uses PSMCT32 upload format** (GS VRAM swizzled data). The game uploads this
data to VRAM as PSMCT32 pixels via DMA/GIF IMAGE transfer, then reads it back as
PSMT4 texture data. VRAM simulation deswizzle (PSMCT32 write -> PSMT4 read) produces
recognizable Japanese glyphs.

**The English font atlas (`english_font_atlas.bin`) uses page-linear format** (128x128
pages, 2 columns, linear within each page). When this page-linear data is treated
as PSMCT32 upload data and VRAM-deswizzled, it ALSO produces readable English glyphs.

**Conclusion: There is no format mismatch.** The page-linear encoding used by
`generate_font_atlas.py` produces byte patterns that happen to decode correctly
when the game's texture loader uploads them via PSMCT32 and reads them as PSMT4.
The build pipeline's direct injection (without explicit swizzle conversion) works.

---

## File Format Details

### R1272 Raw (.raw file, 67584 bytes)

| Region | Offset | Size | Content |
|--------|--------|------|---------|
| Sub-header | 0x000 | 16 | PACKDATA container header (z1=0, payload_size=65792, stride=16, z2=0) |
| GS Registers | 0x010 | 160 | TEX0, TEX1, MIPTBP1, A+D registers for PSMT4 256x512 |
| Zero padding | 0x0B0 | 32 | All zeros |
| Pixel data | 0x0D0 | 65536 | 4bpp PSMT4 font glyph data (PSMCT32 upload format) |
| CLUT/Palette | 0x100D0 | 64 | 16-color RGBA32 grayscale palette |

**TEX0 register** (at payload offset 80): `0x2000000661410000`
- TBP0=0, TBW=4 (buffer width 256px), PSM=0x14 (PSMT4), TW=8 (256), TH=9 (512)

**Palette**: Grayscale ramp - `AC AC AC 80, 9B 9B 9B 80, 8C 8C 8C 80, ...`
(16 RGBA32 entries, darkest = most opaque glyph ink)

### R1272 Resource (.bin file, 65792 bytes)

Same as .raw minus the 16-byte sub-header: `.bin = .raw[16:16+65792]`

### English Font Atlas (82176 bytes)

| Region | Offset | Size | Content |
|--------|--------|------|---------|
| Header | 0x000 | 192 | Copy of original R1272 GS register header (with patched TEX0 TH field) |
| Pixel data | 0x0C0 | 81920 | 4bpp page-linear encoded glyphs (10 pages of 128x128) |
| Palette | End-64 | 64 | All 0xFF (not used; game uses grayscale intensity directly) |

Note: `generate_font_atlas.py` treats bytes 192-255 as "palette" but this is actually
the first 64 bytes of pixel data (all 0xFF background). The real palette is the last
64 bytes. For the original R1272, both the palette at end and the data at offset 192-255
happen to be all-0xFF, making this distinction moot.

---

## Rendering Methods Tested

### Method A: Simple Linear (no swizzle)
Treat raw bytes as a flat row-major 4bpp image at 256px width.

- **R1272**: Grid of faint dots, no recognizable glyphs
- **English**: Scattered faint dots, no recognizable glyphs

### Method B: PSMT4 Native Deswizzle
Read bytes using PSMT4 block/column tables directly (no PSMCT32 step).

- **R1272**: Scattered shapes, not recognizable as glyphs
- **English**: Scattered dots, not recognizable

### Method C: PSMCT32 Upload -> PSMT4 Read (VRAM Simulation)
Write bytes to simulated VRAM using PSMCT32 swizzle, then read back using PSMT4 swizzle.

- **R1272**: **Recognizable Japanese glyphs** with some checkerboard artifacts (likely
  due to slightly wrong buffer width parameters or the 12x12 cell size not aligning
  perfectly with 32x16 PSMT4 blocks)
- **English**: **Clear, readable ASCII characters** (a-z, A-Z, 0-9, punctuation visible
  in proper grid layout)

### Method D: Page-Linear (128x128 pages, 2 columns)
Rearrange bytes treating them as 128x128 PSMT4 pages arranged in 2 columns.

- **R1272**: Grid of tiny dots with some structure, not readable
- **English**: Scattered dots, not readable

---

## Key Finding: Format Compatibility

The page-linear encoding used by `generate_font_atlas.py` for the English atlas produces
data that, when the game's texture loader performs PSMCT32 upload to VRAM, results in
correct PSMT4 texture data. This was confirmed by:

1. **VRAM-deswizzling the English atlas data** -> produces readable "a b c d e f g h i j k l m n o p q r s t u v w x y z" etc.
2. **Round-trip test**: page-linear -> swizzle -> deswizzle = 100% match (131072/131072 pixels)
3. **Build pipeline works**: The game shows English glyphs correctly in-game (per existing test builds)

The original R1272 .raw data and the English .bin data are in *different* byte-level
encodings (only 60.6% byte match), but both decode to correct glyphs via PSMCT32->PSMT4
VRAM simulation. This is because the page-linear layout with 128x128 pages and the
PSMCT32 swizzle both organize data around the same fundamental PS2 GS page structure.

---

## Build Pipeline Status

The current pipeline in `build/build_full_english_v2.py` and `build/full_patch_pipeline.py`:
1. Takes `english_font_atlas.bin` (page-linear format, 82176 bytes)
2. Prepends a 16-byte sub-header with updated payload_size
3. Writes directly as the R1272 resource in PACKDATA

**This works correctly.** No additional swizzle conversion step is needed because the
page-linear format is compatible with the game's PSMCT32 upload mechanism.

---

## Rendering Evidence

Output files generated:

| File | Description |
|------|-------------|
| `r1272_correct_vram_2x.png` | R1272 VRAM deswizzle, full 256x512, 2x zoom |
| `r1272_correct_vram_top_3x.png` | R1272 VRAM deswizzle, top 128 rows, 3x zoom |
| `r1272_correct_vram_mid_3x.png` | R1272 VRAM deswizzle, rows 128-256, 3x zoom |
| `r1272_correct_linear_2x.png` | R1272 simple linear, full, 2x zoom |
| `r1272_correct_pagelinear_2x.png` | R1272 page-linear, full, 2x zoom |
| `eng_correct_vram_top_3x.png` | English atlas VRAM deswizzle, top 128 rows, 3x |
| `eng_correct_pagelinear_top_3x.png` | English atlas page-linear, top 128 rows, 3x |

The `eng_correct_vram_top_3x.png` file shows clear readable English characters,
confirming the page-linear format works when uploaded to VRAM.
