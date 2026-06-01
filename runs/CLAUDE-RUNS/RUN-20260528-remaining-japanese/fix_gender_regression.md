# Gender Regression Fix

## Problem
R38 messages 25/26 (gender selection values) showed Japanese kanji instead of English text.
The user reported that "Male"/"Female" used to work but regressed.

## Root Cause
`chunk_r38_fix.json` contained Unicode symbols for gender:
- M25: `♂` (U+2642) -> glyph ID 518
- M26: `♀` (U+2640) -> glyph ID 349

These glyph IDs are in the extended range (>256) requiring font tiles in R1272.
If the extended atlas doesn't render in-game, these show as blank/garbage/kanji fallback.

The build pipeline (`build_full_english_v2.py`) loads chunk_r38_fix.json as an OVERRIDE
after the main chunks, so these entries take priority.

Note: `chunk_r37_extra.json` has R37 M125/126 with "Male"/"Female" -- but those are
R37 entries (different resource), not the same as R38 M25/26.

## Fix Applied
In `data/translate_chunks/chunk_r38_fix.json`:
- M25: changed `♂` -> `Male` (encodes to glyph IDs [45, 65, 76, 69] -- standard ASCII)
- M26: changed `♀` -> `Female` (encodes to glyph IDs [38, 69, 77, 65, 76, 69] -- standard ASCII)

## Verification
Standard ASCII glyphs (A-Z, a-z) are in the base font atlas and always render correctly.
Rebuild required to take effect.
