# Visual ID Sheet 4 (Glyphs 400-499) -- FINDINGS

**Date:** 2026-05-22
**Status:** Attempted, very low confidence
**Output:** `data/visual_id_sheet4.json`

---

## Summary

Sheet 4 covers glyph indices 400-499. **No characters could be identified with confidence.** All 100 entries are marked with "?" and descriptive labels.

## Observations

### Glyphs 400-479: Tile Fragments (Deswizzle Artifacts)

These 80 glyphs display extremely sparse pixel patterns -- typically just 2-5 lit pixels per 12x12 tile. The patterns include:
- Isolated dots
- Short horizontal dashes (1-3 pixels wide)
- Small vertical bars
- Scattered single pixels

These are consistent with the **deswizzle problem** documented in `impl04-font/FINDINGS.md`. The PSMT4 font atlas uses PS2 GS hardware block/column swizzling, and the current deswizzle implementation is not fully correct. The result is that most glyphs in this range render as fragmented pixel noise rather than recognizable characters.

The same pattern was observed in `visual_id_sheet6.json` (glyphs 600-699), where similar sparse "tile fragments" were labeled the same way.

**These are NOT blank/unused glyphs.** Per the frequency analysis (`recon22-msg-freq/FINDINGS.md`), the 0x0180-0x01BF block (384-447) has 437 total uses across 59 unique indices, and 0x01C0-0x01FF (448-511) has 551 uses across 55 unique indices. These glyphs appear frequently in game text.

### Glyphs 460-474: Half-Kanji Fragments

A subset of glyphs in the 460-474 range show slightly more structure -- vertical bars, angled strokes, and triangular shapes. These may be partial renderings of kanji left/right components (radicals), suggesting the underlying characters are kanji but the deswizzle is only capturing part of each character's pixel data.

### Glyphs 480-499: Dense Complex Characters (Kanji)

The last 20 glyphs (480-499) show dramatically more pixel density. These are clearly full characters with complex internal structure, consistent with kanji. However, at 12x12 pixels even with 8x zoom, the individual kanji cannot be reliably identified due to:
1. Residual deswizzle artifacts creating noise
2. The inherent ambiguity of 12x12 pixel kanji (many kanji look similar at this resolution)
3. The game uses a custom character ordering, so positional inference is not possible

## Blocking Issue

**The deswizzle problem must be resolved before visual identification can succeed for this sheet.** The glyph sheet rendering pipeline produces correct-looking output only for very simple shapes (horizontal lines, basic blocks). Complex characters (kana and kanji) are corrupted by incorrect PSMT4 deswizzle.

## Recommendations

1. **Fix the PSMT4 deswizzle** -- this is the highest-priority blocker for all visual identification work
2. **Use cross-reference mapping** (approach C from GLYPH_MAPPING_PLAN.md) as an alternative to visual ID
3. **Try bitmap template matching** with a proper Japanese BDF font (e.g., Shinonome 12px) once deswizzle is fixed
4. Re-run visual identification on a corrected rendering of sheet 4
