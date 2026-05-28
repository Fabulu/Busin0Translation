# Template Matching Findings

## Method
- Best configuration: bitmap-13 (MS Gothic at 13px, 1-bit rendering, centered)
- Tested 30+ configurations across multiple rendering strategies:
  - Bitmap (1-bit, no anti-aliasing) at sizes 8-16px
  - Grayscale with thresholds 64/96/128/160/192 at sizes 12-14px
  - Oversize-downscale (render at 24/36/48px, downscale to 12x12)
  - Multiple fonts: msgothic.ttc, msmincho.ttc, meiryo.ttc
- Rendered 6996 reference characters covering ASCII, full-width, hiragana, katakana, JIS X 0208 kanji
- Compared each of 882 game glyphs (48x48 PNG, downscaled to 12x12 binary) against all references
- Scoring: pixel-wise match percentage (144 pixels per glyph)
- Vectorized numpy matching, total time: 317s

## Results
- Total glyphs mapped: 882
- Average match score: 0.8995
- Median match score: 0.9236
- Perfect match (100%): 207 (mostly blank/space glyphs)
- Near-perfect (>=95%): 378
- High confidence (>=90%): 505
- Medium confidence (>=85%): 617
- Low confidence (<80%): 217

## Quality Assessment
The results have significant limitations:

1. **Blank glyphs dominate high scores**: 207 glyphs are completely blank (score=1.0 matching space). The glyph range 200-383 appears to be entirely blank tiles from the atlas.

2. **Simple characters match well**: Horizontal lines (glyph_0384-0439 area) match perfectly to box-drawing character U+2500.

3. **Complex characters match poorly**: Kanji and complex kana in the 400-881 range score 70-85%, meaning the matched character is likely wrong. The TTF font renders at a fundamentally different resolution/style than the game's bitmap font.

4. **Many false positives**: Characters like "_" (underscore) match many glyphs that contain only a few dark pixels in the lower portion.

## Font Size Comparison (all strategies performed similarly)
| Config | Avg Score | >=90% Count |
|--------|-----------|-------------|
| bitmap-13 | 0.8995 | 505/882 |
| gray-13-t64 | 0.8994 | 505/882 |
| bitmap-11 | 0.8992 | 535/882 |
| gray-12-t96 | 0.8981 | 521/882 |
| bitmap-14 | 0.8975 | 508/882 |
| bitmap-12 | 0.8971 | 512/882 |

## Output Files
- `data/glyph_map_template.json` - Simple index-to-character mapping
- `data/glyph_map_template_detailed.json` - Includes confidence scores per glyph

## Recommendations
1. **Use a proper BDF bitmap font**: The Shinonome 12px font (shinonome-0.9.11) would likely give pixel-perfect matches for most characters. The server was unreachable during this run.
2. **Try k12x10 or other Japanese bitmap fonts**: Any 12-pixel Japanese BDF font designed for terminals/games should work much better.
3. **Manual verification needed**: The current mapping is useful as a starting point but the kanji identifications (scores below 90%) are unreliable.
4. **The glyph atlas structure**: Glyphs 0-199 appear to be punctuation/symbols, 200-383 are blank, 384-881 contain the actual character set (lines, kana, kanji).
