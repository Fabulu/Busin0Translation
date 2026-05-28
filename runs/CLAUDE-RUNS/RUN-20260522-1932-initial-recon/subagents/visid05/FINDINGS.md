# Visual ID Sheet 5 (Glyphs 500-599) -- FINDINGS

**Date:** 2026-05-22
**Status:** Attempted, very low confidence
**Output:** `data/visual_id_sheet5.json`

---

## Summary

Sheet 5 covers glyph indices 500-599. **No individual kanji characters could be identified with confidence.** All 100 entries are marked with `?_` descriptive labels. The structural category (kanji vs sparse fragment) is identified with moderate confidence.

## Observations

### Glyphs 500-589: Dense Kanji (90 characters)

These 90 glyphs are clearly complex CJK characters (kanji). They have high stroke density, left-right or top-bottom compositional structure, and are distinctly more complex than kana. However, at 12x12 pixel bitmap resolution, individual kanji identification is extremely unreliable:

- Most cells have 40-80% pixel fill in the top (correct) rendering
- Many kanji share nearly identical bitmap patterns at this resolution (e.g., 持/待, 技/扱, 語/話)
- The second rendering row (bottom) in each cell often shows a corrupted/different deswizzle variant

**Notable structural patterns observed:**
- Glyphs 500-505: Moderate density, several appear to have left-side radicals (hand radical, tree radical)
- Glyphs 510-519: Very dense kanji, among the most filled in the sheet. Likely high-stroke-count characters
- Glyphs 515-516, 519: Nearly fully filled bitmaps -- possibly characters like 議, 識, 鋼, 蔵
- Glyphs 540-541, 550-551: Clear left-right compositional structure
- Glyphs 575-576: Very dense wide characters, possibly 13+ stroke kanji
- Glyphs 580-584: Transition zone -- complexity decreasing

### Glyphs 585-589: Transitional Characters

These show a mix of moderate density and block-like patterns. They could be:
- Lower-stroke-count kanji
- Characters with large simple radicals (e.g., mouth radical 口, earth radical 土)

### Glyphs 590-599: Sparse/Simple Characters

The last 10 glyphs are dramatically sparser than the rest of the sheet:
- 590: Single dot or stroke in top-right area
- 591: Small mark
- 592: Short horizontal dash
- 593: Nearly blank, tiny mark
- 594: Small isolated mark
- 595-596: Small square/block shapes
- 597-599: Small block marks

These could be:
1. Simple kanji (一, 二, 十, 口, 日, etc.)
2. Special symbols or punctuation
3. The beginning of a different character category
4. Partially rendered characters due to deswizzle issues

## Comparison with Adjacent Sheets

| Sheet | Range | Content |
|-------|-------|---------|
| Sheet 3 (300-399) | 300-369: kanji (70), 370-399: box-drawing (30) |
| Sheet 4 (400-499) | 400-479: tile fragments (80), 480-499: dense kanji (20) |
| **Sheet 5 (500-599)** | **500-589: dense kanji (90), 590-599: sparse marks (10)** |
| Sheet 6 (600-699) | 600-649: tile fragments (50), 650-699: half-kanji fragments (50) |
| Sheet 7 (700-799) | 700-738: kanji (39), 739+: more kanji |

The atlas layout shows kanji scattered across multiple non-contiguous regions, with tile/box-drawing fragments interspersed. This is consistent with the PSMT4 deswizzle affecting different atlas regions differently -- some regions render correctly while others show fragments.

## Blocking Issues

1. **PSMT4 deswizzle quality**: The sheet_05 rendering appears better than sheets 4 and 6 (which show mostly fragments), but the kanji are still ambiguous at 12x12 pixels
2. **No positional ordering clue**: Unlike JIS-ordered fonts, this game uses a custom glyph ordering, so position within the atlas cannot be used to infer character identity
3. **Template matching failed**: The existing template match (impl14) scored all glyphs in this range at 0.80-0.93 against backtick/dash characters, which are clearly wrong

## Recommendations

1. **Cross-reference approach**: Match known Japanese game strings (spell names, menu text from the EXE debug strings in recon02) against MSG glyph sequences to decode the mapping
2. **BDF bitmap font matching**: Use a proper 12px Japanese bitmap font (Shinonome, k12x10) for template matching once available
3. **Screenshot comparison**: If game screenshots are available showing readable text, match the on-screen characters to their glyph indices via the MSG data
4. **Fix deswizzle for sheets 4, 6**: These adjacent sheets may contain the same characters but with corrupted rendering -- fixing deswizzle would reveal the full picture

## Confidence Assessment

- Character class (kanji vs sparse/simple): **HIGH** for 500-589, **MEDIUM** for 590-599
- Individual character identification: **NONE** -- no specific kanji could be identified with any confidence
- Estimated accuracy of specific IDs: ~0% (no IDs attempted)
