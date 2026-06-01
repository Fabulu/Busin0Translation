# R39 Sidebar Label Patch: Inline Data Area

**Date**: 2026-05-28
**Analyst**: Claude Opus 4.6

---

## Summary

Searched R39 (`0039_type15.raw`, 26,624 bytes) for all four sidebar label kanji
pairs. Only one label -- alignment (515,511) -- exists in R39's inline data area.
The other three sidebar labels (gender, race, class) are NOT in R39; they are
rendered through the R38 MSG system (already translated).

---

## Search Results

| Sidebar Label | Glyph IDs | Found in R39 inline data? | Found in R39 text messages? |
|---------------|-----------|---------------------------|----------------------------|
| Gender (sei-betsu) | 511,512 | NO | NO (512 appears 5x but never after 511) |
| Race (shu-zoku) | 513,514 | NO | NO (513 not found at all) |
| Alignment (zoku-sei) | 515,511 | YES -- 3 locations | YES -- 13 locations in text |
| Class (shoku-gyou) | 504,517 | NO | NO (504 found 1x, not followed by 517) |

### Alignment locations in inline data (stat label area)

These are in the same structural block pattern as the already-patched stat labels
(HP, STR, etc.) at 0x56D6-0x57B6. Each block has the wrapper sequence
`[679, 839, 287, 136]` followed by glyph IDs.

| Offset | Original (BE) | Patched (BE) | English |
|--------|---------------|--------------|---------|
| 0x5816 | 515 (zoku), 511 (sei) | 41 (A), 52 (L) | AL |
| 0x5846 | 515 (zoku), 511 (sei) | 41 (A), 52 (L) | AL |
| 0x5878 | 515 (zoku), 511 (sei) | 41 (A), 52 (L) | AL |

### Alignment locations in text messages (NOT patched)

13 occurrences at offsets 0x0F38-0x161A. These are embedded in type-2 message text
(surrounded by other kanji glyphs like ya, ka, yo, so). They should be handled by
the text translation/injection system, not individual binary patches.

---

## Glyph ID Mapping Used

| Letter | Glyph ID | Source |
|--------|----------|--------|
| A | 41 | glyph_map_partial.json |
| L | 52 | glyph_map_partial.json |

---

## Why Other Sidebar Labels Are Missing from R39

The chargen sidebar rendering path was confirmed by EXE disassembly (VA 0x2F1090):
the sidebar function loads R38 MSG indices and renders them through the generic text
system. The R38 resource already contains correct English translations:

- R38 MSG 11: RACE
- R38 MSG 12: GENDER
- R38 MSG 13: ALIGNMENT
- R38 MSG 14: CLASS

If the sidebar still shows Japanese for gender/race/class, the issue is in R38
injection into the ISO, NOT in R39 data.

The alignment label (515,511) appears in R39's inline data because it is ALSO
used in the character stat sheet display (same area as HP/STR/INT labels), which
is a separate rendering path from the sidebar.

---

## File Modified

`C:/Programmieren/wizardrytranslation/build/packdata_resources/0039_type15.raw`

6 bytes changed (3 pairs of BE uint16 values).
