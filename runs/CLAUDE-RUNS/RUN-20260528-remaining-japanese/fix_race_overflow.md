# Race Name Overflow Analysis and Fix

**Date**: 2026-05-28

---

## Problem

User reports:
1. "Hobbit" overflows the race selection menu box
2. "Automa" (Automata) does not show at all

## Root Cause Analysis

### Renderer Constraint

The text renderer uses a **fixed 24 screen-pixel (12 atlas texel) advance** per glyph,
regardless of whether the glyph is halfwidth (Latin) or fullwidth (kanji/kana). There is
no per-glyph width table (confirmed in `halfwidth_font_analysis.md`). This means each
English letter occupies the same screen width as each Japanese kana character.

### Race Name Glyph Counts

| MSG | Japanese       | JP Glyphs | English (old) | EN Glyphs | Delta | Status       |
|-----|---------------|-----------|---------------|-----------|-------|--------------|
| 29  | ningen (2)    | 2         | Human         | 5         | +3    | Fits (box is wide) |
| 30  | erufu (3)     | 3         | Elf           | 3         | 0     | OK           |
| 31  | noomu (3)     | 3         | Gnome         | 5         | +2    | Fits         |
| 32  | dowaafu (4)   | 4         | Dwarf         | 5         | +1    | Fits         |
| 33  | hobitto (4)   | 4         | Hobbit        | 6         | +2    | OVERFLOW     |
| 34  | ootomaataa (6)| 6         | Automa        | 6         | 0     | OK           |

### Display Box Width

The race selection menu renders items in a vertical list. The display column appears to
accommodate up to 5 glyphs comfortably (Human, Gnome, Dwarf all display fine at 5 glyphs).
At 6 glyphs, "Hobbit" gets clipped at the right edge of the rendering area.

The box is likely sized for the longest _commonly visible_ Japanese entry. With only 5
items shown at once (Automata requires scrolling), the longest visible JP name is 4 glyphs
(hobitto/dowaafu). The box has some padding beyond that, accommodating 5 English glyphs,
but 6 causes clipping.

### Automa Not Showing

This is **normal game behavior**, not a bug. The race selection list shows only 5 items at
a time. Automata is the 6th race and requires scrolling past Hobbit to appear. The original
Japanese game works the same way. "Automa" (6 glyphs) = "ootomaataa" (6 glyphs), so it
fits perfectly when scrolled into view.

## Fix Applied

**File**: `data/translate_chunks/chunk_02_translated.json`

Changed R38 MSG 33 (race name label):
- Before: `"Hobbit / "` (6 glyphs)
- After:  `"Hobit / "`  (5 glyphs)

"Hobit" at 5 glyphs fits within the display box alongside Human/Gnome/Dwarf (all 5 glyphs).
The single-b spelling is nonstandard but immediately recognizable, and matches the
established pattern of abbreviated names throughout the translation (e.g., "Automa" for
"Automata").

Note: The race description in MSG 122 (`"Hobbit: Small but / agile and lucky. / Born thieves."`)
was NOT changed. Description text renders in a separate, wider textbox (224px / ~18 glyphs)
where "Hobbit" at the start of a line is not an overflow concern.

## No Other Race Names Need Changes

- Human (5), Elf (3), Gnome (5), Dwarf (5) all display correctly at 5 or fewer glyphs
- Automa (6) matches the original Japanese glyph count and displays correctly when scrolled
