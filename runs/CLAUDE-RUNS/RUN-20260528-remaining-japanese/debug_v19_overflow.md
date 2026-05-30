# Debug: v19 Chargen Text Overflow

## Root Cause

The v2 pipeline (`build/build_full_english_v2.py`) has a `clean_and_encode()` function
that processes translation text in two stages:

1. Splits on ` / ` to find explicit FFFE line breaks (placed by the translator)
2. Passes each segment to `encode_text(part, max_chars_per_line=18)` for glyph encoding

**The bug:** `encode_text()` applies word wrapping at 18 chars per line, but R38 chargen
descriptions were written to fit 20-char-wide textboxes. Segments like
`"anxious in dungeons."` (20 chars) get re-wrapped to 2 lines, creating overflow.

This is the **same class of bug** as the v19 double-wrapping fix for type-2 messages,
but in the type-1 (v2) pipeline.

## Impact

- **48 messages** in R38 had extra FFFE line breaks from word wrapping
- **16 messages** had >3 visible lines (real overflow beyond the 3-line chargen box)
- Affected chargen screens: race descriptions (118-122), alignment descriptions
  (123-125), class descriptions (126-141), stat descriptions (142-147),
  personality descriptions (87-116), gender description (117)

## Fix Applied

**File:** `build/build_full_english_v2.py` line 133

```python
# BEFORE (buggy):
line_glyphs = encode_text(part, max_chars_per_line=18, max_lines_per_page=3)

# AFTER (fixed):
line_glyphs = encode_text(part, max_chars_per_line=20, max_lines_per_page=3)
```

## Why 20 is safe

- All translation segments across all chunks are <=20 chars (verified: 0 segments >20)
- Only 2 entries in the entire dataset lack explicit ` / ` breaks and exceed 18 chars
  (R40 m21 "removing from party." and R40 m38 "sort alphabetically.", both exactly 20)
- The chargen textbox is 20 chars wide

## R37 Status

R37 chargen prompts are fine. The only "overflows" are keyboard layout messages
(msgs 18-21) which are intentionally multi-line. All prompt messages (msgs 2-17)
fit within their textboxes.

## Overflow Messages (OLD code)

These 16 messages had >3 visible lines before the fix:

| Msg | Category        | Text (input)                                           |
|-----|-----------------|--------------------------------------------------------|
|  89 | Personality     | lives to hoard gold. / angry if loot is / low.        |
|  99 | Personality     | obsessed with traps. / crushed by success.             |
| 103 | Personality     | believes women have / no place in battle.              |
| 104 | Personality     | won't forgive those / who slay tame foes.              |
| 113 | Personality     | thrives in hardship. / hates being helped.             |
| 119 | Race desc       | Elf: High INT & VIT / but frail. Best / at magic.     |
| 130 | Class desc      | Great EXP gain. Can / instant-kill foes. / Sorc Lv2.  |
| 131 | Class desc      | Knight gear usable. / Learns Sorcery / up to Lv5.     |
| 132 | Class desc      | Restores HP. Dispel / vs undead. Sorc & / Holy Lv6.   |
| 135 | Class desc      | Longbow user. Lowers / traps, steals items / Lv3.     |
| 137 | Class desc      | Holy aura heals HP. / Can learn Dispel. / Lv6.        |
| 138 | Class desc      | Removes curses from / equipped items. / Sorc Lv6.     |
| 140 | Class desc      | Dual wields same / weapon type. Learns / Sorc Lv6.    |
| 141 | Class desc      | Longbow. Best trap / skill. Steals items / Lv4.       |
| 145 | Stat desc       | affects max hp, / status resistance, / revival success.|
| 147 | Stat desc       | affects breath / resist and critical / hit chance.     |

After fix: **0 overflows**.
