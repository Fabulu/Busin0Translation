# Visual Identification: Sheet 06 (Glyphs 600-699)

**Date:** 2026-05-22
**Status:** Complete (with caveats)
**Input:** `dumps/glyph_sheets/sheet_06_glyphs_0600-0699.png`
**Output:** `data/visual_id_sheet6.json`

---

## Key Finding: ALL glyphs 600-699 are tile fragments, NOT complete kanji

### Evidence

1. **Glyphs 600-649 (rows 0-4):** Extremely sparse -- each cell contains only 1-4 lit pixels (dots, tiny dashes). These are clearly top or corner fragments of larger composed characters. The existing `glyph_map_template.json` maps these as backticks (`` ` ``), underscores, or single-pixel marks.

2. **Glyphs 650-699 (rows 5-9):** Denser patterns showing vertical strokes, hooks, and partial enclosures. These are left or right halves (or quarters) of full kanji. Each shows roughly half a character's structure -- vertical strokes with horizontal attachments, partial radicals, etc.

3. **Tile composition context:** The font atlas uses a 21-column x 42-row grid of 12x12 pixel cells (882 total slots). The game's text rendering system composes full kanji from multiple tile indices. Glyphs in this range represent individual tiles that get assembled into complete characters at render time.

### Confidence Assessment

- **0/100 complete kanji identified** -- None of these glyphs are standalone readable kanji.
- All 100 entries marked with `?_tile_fragment_` or `?_half_kanji_` prefix describing visible stroke patterns.
- Proper identification requires either:
  - (a) The tile composition table that maps tile groups to full characters, or
  - (b) Adjacent sheet analysis to manually reconstruct full kanji from neighboring tiles.

### Pattern Observations

- Glyphs 600-649: Progressively denser from top-left corner fragments (600) toward bottom-edge fragments (649). Likely represent the sparse top portions of kanji whose main body appears in tiles below (higher glyph indices).
- Glyphs 650-699: Show substantial left/right half-character structures. The vertical strokes and hooks are consistent with common radicals (e.g., ninben, tehen, gonben patterns).
- The duplication pattern visible in rows 6-7 (660-669 vs 670-679) where top and bottom renderings look similar suggests the rendering algorithm repeats for verification.

### Recommendation

These tile fragments cannot be individually identified as kanji. To decode them:
1. Find the tile composition table in the EXE or runtime data that maps glyph ID sequences to Unicode characters.
2. Alternatively, use the message frequency analysis (`recon22-msg-freq`) cross-referenced with known game text to reverse-engineer which tile combinations produce which kanji.
