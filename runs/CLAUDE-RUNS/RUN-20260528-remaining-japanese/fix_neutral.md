# Fix: Alignment Label Overflow (Good/Neutral/Evil)

## Problem
The alignment selection list in character creation (R38) overflows because
English labels are much wider than their Japanese originals.

## Entries Fixed (chunk_03_translated.json)

| MSG | Japanese (glyphs) | Old English | New English | Ratio |
|-----|-------------------|-------------|-------------|-------|
| M148 | 善「g」 (4 fw) | Good "G" (8 hw) | G "G" (5 hw) | 4fw~56px vs 5hw~40px OK |
| M149 | 中立「n」 (5 fw) | Neutral "N" (11 hw) | Neut "N" (8 hw) | 5fw~70px vs 8hw~64px OK |
| M150 | 悪「e」 (4 fw) | Evil "E" (8 hw) | E "E" (5 hw) | 4fw~56px vs 5hw~40px OK |
| M152 | 中立 (2 fw) | Neutral (7 hw) | Neut (4 hw) | 2fw~28px vs 4hw~32px OK |

fw = full-width (~14px), hw = half-width (~8px)

## Rationale
- "Neutral" (7 chars) was the worst offender vs 中立 (2 glyphs) -- 3.5x glyph count
- Shortened to "Neut" (4 chars) to fit within pixel budget
- "Good" and "Evil" also shortened to "G" and "E" for consistency with
  the single-kanji originals (善, 悪)
- The keyboard shortcut hints ("G", "N", "E") are preserved unchanged
