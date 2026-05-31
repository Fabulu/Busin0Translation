# v20 Overflow Audit -- Final Report

Date: 2026-05-28
ISO: `build/BUSIN0_EN_v20.iso`
Source: `build/PACKDATA.DIG` (extracted R34, R37, R38)

## Summary

**NO OVERFLOWS FOUND.** The `max_chars_per_line=20` fix in `build_full_english_v2.py`
has successfully eliminated all line-width overflows. All messages in R34, R37, and R38
are within safe limits.

## R38 -- Chargen Descriptions (MSG 87-148)

- Total messages in R38: 190
- Messages 87-148 checked: 62

### FFFE (line break) counts

| FFFE count | v20 msgs | Original JP msgs | Notes |
|------------|----------|-------------------|-------|
| 0          | 1        | 1                 | OK    |
| 1          | 0        | 7                 | English uses more lines (1->2) but within limit |
| 2          | 31       | 38                | OK    |
| 3          | 30       | 17                | Some went 2->3 via word-wrap, still within box limit |

- **Max FFFE in original JP**: 3 (17 messages, e.g., race/class/alignment descs)
- **Max FFFE in v20 EN**: 3 (30 messages)
- **Box capacity**: 3 FFFE breaks (3 content lines + trailing empty) confirmed safe
- **Max glyphs per line**: 20 (none exceed limit)
- **Page breaks (FFD2)**: 0 (none needed)

### Messages that gained FFFE breaks vs original (18 total)

These went from fewer breaks to more due to English word-wrapping, but all stay within
the 3-FFFE maximum that the original JP data proves the engine supports:

| MSG | Original FFFE | v20 FFFE | Status |
|-----|---------------|----------|--------|
| 90  | 2             | 3        | OK (within box limit) |
| 99  | 1             | 2        | OK |
| 104 | 1             | 2        | OK |
| 108 | 2             | 3        | OK (within box limit) |
| 118 | 2             | 3        | OK (within box limit) |
| 125 | 2             | 3        | OK (within box limit) |
| 126 | 2             | 3        | OK (within box limit) |
| 127 | 2             | 3        | OK (within box limit) |
| 129 | 2             | 3        | OK (within box limit) |
| 131 | 2             | 3        | OK (within box limit) |
| 132 | 2             | 3        | OK (within box limit) |
| 135 | 2             | 3        | OK (within box limit) |
| 143 | 1             | 2        | OK |
| 144 | 1             | 3        | OK (within box limit) |
| 145 | 1             | 3        | OK (within box limit) |
| 146 | 2             | 3        | OK (within box limit) |
| 147 | 1             | 2        | OK |
| 148 | 2             | 3        | OK (within box limit) |

## R37 -- Chargen Prompts

- Total messages: 129
- Messages 19-22 are keyboard layouts (intentionally multi-line, excluded from check)
- **Max glyphs per line**: <= 20 for all non-keyboard messages
- **Max FFFE**: <= 3 for all non-keyboard messages
- **Overflows found**: 0

## R34 -- Translated Messages

- Total messages: 32
- **Max glyphs per line**: <= 20
- **Max FFFE**: <= 3
- **Overflows found**: 0

## Conclusion

The `encode_text(max_chars_per_line=20)` change in `build_full_english_v2.py` line 134
correctly constrains all word-wrapped text to 20 glyphs per line. The word-wrapper
sometimes produces 3 content lines (3 FFFE) where the original JP had only 2, but this
is proven safe because 17 original JP messages in the same range already used 3 FFFE.

No fixes needed. v20 build is clean for R34, R37, and R38 text overflow.
