# Visual Identification: Sheet 08 (Glyphs 800-849)

## Summary

Sheet 08 contains the final 50 glyphs (indices 800-849) from the Busin 0: Wizardry Alternative Neo font atlas. These are the last glyphs in the 858-slot atlas (range 0x0000-0x035A).

## Confidence Assessment

**Overall confidence: VERY LOW -- effectively UNIDENTIFIABLE by visual inspection**

All 50 glyphs are marked with descriptive placeholders rather than character guesses. At 12x12 pixel resolution, these end-of-atlas kanji are rendered with extreme sparsity (typically 3-8 white pixels per glyph), making individual character identification impossible through visual means alone.

## Key Observations

1. **Extreme pixel sparsity**: Each glyph contains only a handful of white pixels on a 12x12 black grid. This is characteristic of high-stroke-count kanji compressed into minimal pixel space -- the rendering simply cannot resolve the individual strokes.

2. **Usage frequency**: Per msg_frequency_analysis.txt:
   - Indices 0x0320-0x033F (800-831) fall in a block with 60 unique glyphs / 496 total occurrences
   - Indices 0x0340-0x0351 (832-849) fall in a block with only 25 unique / 226 total occurrences
   - Many slots in the 832-849 range may be unused padding

3. **Template matching failed**: The automated bitmap template matcher (glyph_map_template.json) returned garbage results for this range -- box-drawing characters, quotation marks, and arrows with scores of 0.69-0.82 (well below reliability threshold).

4. **Pattern consistency with earlier sheets**: Sheets 4 and 6 also contained "tile fragment" ranges where individual identification was impossible. Sheet 7 (700-799) produced all-uncertain kanji guesses. Sheet 8 continues this pattern of diminishing identifiability.

5. **Structural observation**: Rows within the sheet show the TOP row as the correct rendering and the BOTTOM row as an alternate/duplicate. The two renderings appear to differ slightly, suggesting sub-pixel alignment variation.

## What These Glyphs Likely Are

Based on atlas structure analysis:
- **Glyphs 0-93**: ASCII characters (confirmed by EXE glyph table)
- **Glyphs ~94-199**: Punctuation, symbols, hiragana, katakana
- **Glyphs ~200-383**: Blank padding tiles
- **Glyphs ~384-858**: Kanji and tile fragment components

Glyphs 800-849 are the rarest kanji used in the game text. They appear in very few messages (the 0x0340+ block averages under 10 occurrences per unique glyph). These would be uncommon characters used perhaps once or twice in the entire game script.

## Recommended Next Steps

Visual identification of these glyphs is a dead end. The path forward requires one of:

1. **Known-text cross-reference**: Decode MSG file contents using known game text (item names, spell names, dialogue from guides) to determine which character maps to each glyph index. This is the highest-confidence approach.

2. **Proper bitmap font matching**: Use a Japanese bitmap font designed for 12px (e.g., Shinonome shnmk12, Jiskan12) for pixel-perfect template matching. The Metrowerks CodeWarrior compiler likely used a standard JIS bitmap font.

3. **Runtime analysis**: If an emulator save state can be captured while displaying text containing these glyphs, screen OCR on the rendered output would work much better than atlas-level identification.

4. **SJIS ordering hypothesis**: If the kanji portion of the atlas follows JIS X 0208 order (Level 1 kanji in rows 16-47), then the mapping can be computed arithmetically once the base offset is determined.

## Output

- JSON file: `data/visual_id_sheet8.json`
- 50 entries, all marked with "?" prefix and descriptive shape annotations
- Format: `{"800": "?_kanji_description", ...}`
- **None of these identifications should be used as actual character mappings**
