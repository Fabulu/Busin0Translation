# Visual Identification: Sheet 01 (Glyphs 100-199)

**Date:** 2026-05-22
**Status:** INCOMPLETE -- resolution too low for reliable character identification

---

## Summary

Glyphs 100-199 from `sheet_01_glyphs_0100-0199.png` were examined visually. At 12x12 pixel original resolution (8x zoom on the sheet), individual Japanese character identification is not reliable. The characters render as abstract horizontal bar patterns that do not contain enough distinguishing detail for confident identification.

## Findings by Range

### Glyphs 100-157: BLANK
- All 58 cells are completely black (no visible pixels)
- Cross-reference with `glyph_cells_16x16_top8rows.png` confirms cells 100-111 are blank
- The automated template matcher (`glyph_map_template_detailed.json`) scored these as space (1.0 confidence) or underscore (0.87-0.95 confidence)
- **However**, glyph frequency data shows many of these indices are heavily used in-game:
  - Glyph 113: rank 5 (675 uses, 0.60%)
  - Glyph 136: rank 6 (665 uses, 0.60%)
  - Glyph 152: rank 8 (491 uses, 0.44%)
  - Glyph 130: rank 10 (480 uses, 0.43%)
  - Glyph 123: rank 11 (451 uses, 0.40%)
  - Glyph 132: rank 12 (444 uses, 0.40%)
- **Hypothesis:** These glyphs exist in the font atlas but the PS2 PSMT4 deswizzle used to generate the glyph sheets was incomplete. The glyph cells image and sheet images may be showing incorrectly deswizzled (blank) data for these atlas positions. The actual character data is present in the font texture but mapped to different pixel coordinates by the PS2 GS swizzle pattern.

### Glyphs 157-159: NEAR-BLANK
- 157: Single white pixel at top-right border area
- 158: Single white pixel at mid-right area (glyph 158 is rank 7 at 493 uses -- definitely a real character)
- 159: Tiny artifact at bottom-right edge
- These single pixels are likely edge artifacts from an adjacent glyph in the atlas, not the actual character content

### Glyphs 160-199: VISIBLE BUT UNIDENTIFIABLE
- All 40 cells have visible white-on-black content
- Each cell shows TWO rows (page artifact from PSMT4 deswizzle); TOP row is the correct glyph
- At 12x12 pixels, characters appear as horizontal bar patterns:
  - 160-169: Pairs of horizontal bars with varying width/gaps
  - 170-175: Very thick horizontal bars (nearly full-width)
  - 176-179: Medium bars with gaps and dot fragments
  - 180-185: Bars with additional dot elements alongside
  - 186-189: Shorter bar segments
  - 190-194: Short bars plus small dot patterns
  - 195-199: Complex multi-element patterns (bars + scattered dots)

**These patterns are consistent with Japanese characters** (hiragana, katakana, or SJIS symbols) rendered at 12px, but the individual character shapes cannot be distinguished at this resolution.

## Why Identification Failed

1. **12x12 pixels is below the minimum for CJK OCR** -- research (documented in `recon36-font-id-methods/FINDINGS.md`) shows OCR accuracy drops sharply below 150 PPI, and 12x12 is well below that threshold.

2. **PSMT4 deswizzle artifacts** -- the "two rows" effect means the rendering pipeline did not perfectly reconstruct the atlas layout. Some glyph data may be displaced or duplicated.

3. **No contrast between similar characters** -- at 12px, many hiragana/katakana pairs are visually identical (e.g., は/ぱ, ウ/ク/ケ, シ/ツ/ソ/ン).

4. **Blank-but-used glyphs** -- the most damaging issue is that glyphs 100-157 appear blank despite being heavily used in the game text. This suggests a systematic rendering problem in the sheet generation, not individual character issues.

## Recommendations

1. **Fix the PSMT4 deswizzle** -- the blank range 100-157 contains heavily-used characters. The current deswizzle implementation is likely mapping these glyphs to wrong atlas positions. A correct deswizzle would reveal the actual characters.

2. **Use cross-reference mapping instead** -- the `GLYPH_MAPPING_PLAN.md` Approach C (known-text cross-reference) has a 90% likelihood of success without requiring visual identification. Match known Japanese terms (class/race/spell names) against MSG glyph sequences to build a constraint-based mapping.

3. **Template matching with Shinonome 12px font** -- if a correct deswizzle is achieved, compare each 12x12 glyph against the Shinonome bitmap font (which is available at exactly 12px for all JIS X 0208 characters).

4. **Higher-resolution rendering** -- if the original 4bpp font texture has anti-aliasing (16 levels per pixel), rendering at 2x or 4x with proper interpolation would significantly improve character visibility.

## Files

- **JSON output:** `data/visual_id_sheet1.json` (metadata only, no character identifications)
- **Sheet image:** `dumps/glyph_sheets/sheet_01_glyphs_0100-0199.png`
- **Cell reference:** `dumps/font_renders/pages/glyph_cells_16x16_top8rows.png` (covers glyphs 0-127)
- **Frequency data:** `dumps/glyph_frequency.json`
