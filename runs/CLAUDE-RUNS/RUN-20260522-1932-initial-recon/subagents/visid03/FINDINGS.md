# Visual ID Sheet 3 (Glyphs 300-399) Findings

## Summary

Sheet 3 does NOT contain hiragana or katakana as initially expected. The glyphs break into two distinct regions:

### Region 1: Kanji (300-369)
- 70 complex CJK characters with high stroke density
- At 12x12 pixels, these are unmistakably kanji, not kana
- Kana at 12x12 px have simple, distinctive shapes (2-5 strokes); these glyphs have 8-15+ strokes
- All identifications in this region are marked `?` (low confidence) due to the extreme difficulty of distinguishing specific kanji at 12x12 pixel resolution
- The kanji appear to follow roughly JIS-by-radical or stroke-count ordering (based on adjacent characters having similar radical structures)
- Estimated accuracy: 20-30% for specific character IDs; the general class (kanji) is certain

### Region 2: Box-Drawing / UI Elements (370-399)
- 30 glyphs consisting of horizontal bars, line segments, and dots
- Pattern: thick double horizontal bars (370-375), bars with dots/marks (376-379), thinner bar pairs (380-389), thin bars and dots (390-399)
- These are tile/border fragments used for UI rendering (menus, dialog boxes)
- Glyphs 384-385 match the `─` (U+2500) horizontal line identified by template matching at 98.6% confidence
- Glyph 395 appears to be a solid/filled block

## Key Observations

1. **No kana transition here**: The game's glyph encoding does NOT follow JIS/SJIS order. Per prior analysis (GLYPH_MAPPING_PLAN.md), the mapping is custom/proprietary. Kana may be in the 100-200 range or scattered by frequency.

2. **Template matching vs. visual inspection discrepancy**: The template_match_v4 results (FINDINGS.md for impl14) claimed glyphs 200-383 were "entirely blank tiles." This is incorrect -- they clearly contain visible characters. The issue is the incomplete PSMT4 deswizzle: the template matcher compared against garbled atlas data, not the actual glyphs. The glyph_sheet PNGs (which this visual ID is based on) use correctly extracted individual glyph images.

3. **Overall atlas layout** (refined):
   - 0-99: ASCII, symbols, punctuation
   - 100-199: Common characters (kanji by frequency)
   - 200-369: More kanji (medium-to-low frequency), ordered roughly by radical/stroke count
   - 370-499: Box-drawing, tile fragments, UI borders
   - 500-699: More tile fragments
   - 700-858: Kanji (medium-high stroke count)

4. **Where are the kana?** The kana (hiragana + katakana) are likely encoded as glyph indices in the most-frequently-used range (roughly 0-200), interleaved with common kanji and particles. This matches the frequency data showing the highest-use glyphs are in 0x0000-0x00FF. A cross-reference approach (matching known Japanese terms against MSG glyph sequences) is needed to confirm kana positions.

## Confidence

- Region classification (kanji vs box-drawing): HIGH confidence
- Individual kanji identification: LOW confidence (20-30% estimated accuracy)
- Box-drawing element descriptions: MEDIUM confidence

## Output

- `data/visual_id_sheet3.json`: 100 entries, all prefixed with `?` or `?_`
