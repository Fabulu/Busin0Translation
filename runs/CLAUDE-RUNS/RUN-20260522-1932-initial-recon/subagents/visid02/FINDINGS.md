# Visual Identification: Sheet 02 (Glyphs 200-299)

**Date:** 2026-05-22
**Status:** Complete (low individual confidence)
**Input:** `dumps/glyph_sheets/sheet_02_glyphs_0200-0299.png`
**Output:** `data/visual_id_sheet2.json`

---

## Key Finding: Glyphs 200-299 are KANJI, NOT hiragana

Despite the initial hypothesis that this range should contain hiragana, cross-referencing with other visual identification results (especially visid03/sheet 3) conclusively shows that glyphs 200-299 are kanji characters, not hiragana.

### Evidence Against Hiragana

1. **Frequency mismatch:** If hiragana started at glyph 200, then glyph 245 would be the particle `no` -- the most common non-space character in Japanese, expected at 4-5% frequency. But glyph 245 has only 94 uses (0.084%), rank 92. The actual most-frequent glyphs (1, 3, 62, 63, 93, 113, 136) are all in the 0-200 range, where the real kana must reside.

2. **Glyph 255 (0xFF) is rank 3 with 1075 uses.** If this were hiragana position 55 = `he`, that frequency is implausible. `he` is a relatively uncommon hiragana. This glyph is likely a very common kanji.

3. **Visual complexity in rows 7-9:** Glyphs 270-299 show extremely dense stroke patterns with 10+ strokes -- far too complex for hiragana characters like `ra`, `ri`, `ru`, `re`, `ro`, `wa`, `wo`, `n`, which have 1-4 strokes at most.

4. **Confirmed by visid03 analysis:** The sheet 3 findings (glyphs 300-369) explicitly state: "The game's glyph encoding does NOT follow JIS/SJIS order" and provide a refined atlas layout where 200-369 = "kanji (medium-to-low frequency), ordered roughly by radical/stroke count."

### Revised Atlas Layout (from visid03)

| Range | Content |
|-------|---------|
| 0-99 | ASCII, symbols, punctuation |
| 100-199 | Common characters (kanji by frequency?) |
| 200-369 | More kanji (medium-to-low frequency) |
| 370-499 | Box-drawing, tile fragments, UI borders |
| 500-699 | Tile fragments (composed kanji parts) |
| 700-858 | Kanji (high stroke count) |

### Where Are the Kana?

The hiragana and katakana characters are most likely encoded in the high-frequency glyph range (roughly indices 0-200), interleaved with common kanji and particles. Key evidence:
- The top 20 most-frequent glyphs (indices 1, 3, 62, 63, 93, 113, etc.) should include hiragana particles like `no`, `ha`, `ni`, `wo`, `te`, `ga`
- A cross-reference approach (matching known Japanese game terms against MSG glyph sequences) is needed to locate specific kana positions

### Individual Kanji Identification

All 100 glyphs are marked with `?_kanji_` prefix and structural descriptions. At 12x12 pixel resolution, individual kanji identification is unreliable. Observations:

- **Glyphs 200-249 (rows 0-4):** Simpler kanji with 3-8 visible strokes. Dominant patterns include horizontal bars, simple enclosures, and angular strokes.
- **Glyphs 250-269 (rows 5-6):** Medium complexity kanji with diagonal elements and cross patterns.
- **Glyphs 270-299 (rows 7-9):** Very dense kanji with 10+ strokes. These have heavy fill patterns occupying most of the 12x12 cell.

### Template Matching Discrepancy

The template_match_v4 results (impl14) claimed glyphs 200-383 were "entirely blank tiles" (207 blank matches at score=1.0). This is incorrect -- the glyph sheet clearly shows visible character content. The discrepancy is due to the incomplete PSMT4 deswizzle used by the template matcher: the template matcher compared against garbled/swizzled atlas data, while the glyph sheet PNGs use correctly extracted individual glyph images.

## Confidence

- **Region classification (kanji):** HIGH confidence
- **Individual kanji identification:** VERY LOW confidence (5-15% estimated accuracy)
- **All entries prefixed with `?_kanji_`** indicating they need cross-reference confirmation

## Recommendations for Resolution

1. **Cross-reference mapping** (highest priority): Match known Japanese game terms (class names, item names, etc.) against MSG glyph sequences to identify individual characters through context.
2. **Template matching with correct deswizzle:** Re-run template matching using the correctly extracted glyph images (not the garbled atlas data).
3. **Frequency analysis:** Map glyph usage frequency against expected Japanese character frequency to narrow candidates.
