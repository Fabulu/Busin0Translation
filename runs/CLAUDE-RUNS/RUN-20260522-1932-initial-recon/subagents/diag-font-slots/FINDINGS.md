# Diagnosis: Font Atlas Glyph Slot Mismatch

**Date:** 2026-05-22
**Status:** ROOT CAUSE IDENTIFIED -- Two different glyph ID systems are conflated

---

## Executive Summary

The english_glyph_table.json uses the **MSG resource glyph ID space**, but the font atlas positions are rendered by the game engine using the same `col = glyph % 21, row = glyph // 21` formula. The MSG encoder writes glyph IDs into MSG resources, and the game renders them by looking up pixel data at that atlas position. **The font atlas generator correctly places characters at the MSG glyph positions.** However, the EXE's ASCII glyph table (used for hardcoded EXE strings, NOT MSG resources) uses a DIFFERENT mapping. The bug report symptoms ("spaces render as !") suggest the problem is NOT in the MSG pipeline but rather in how EXE-originated strings are rendered, OR there is a mismatch between what the atlas generator drew and what the game expects at those positions.

---

## The Two Glyph ID Systems

### System 1: MSG Resource Glyphs (used by english_glyph_table.json)

This is the glyph ID space used in PACKDATA MSG resources. The encoder writes these IDs as BE uint16 values into MSG binary data.

Key mappings from `data/msg_glyph_map.json` (the ORIGINAL Japanese MSG system):
```
Glyph  0 = space (blank)
Glyph  1 = space (blank)        <-- BOTH 0 and 1 are space in the original
Glyph  8 = 「
Glyph  9 = 」
Glyph 13 = −
Glyph 16-25 = fullwidth digits ０-９
Glyph 33-58 = lowercase a-z
Glyph 62 = 、
Glyph 63 = 。
Glyph 112-157 = hiragana あ-ん
```

### System 2: EXE ASCII Glyph Table (at EXE offset 0x3C0870)

This is a separate 84-entry lookup table in the EXE. It maps ASCII codes 0x20-0x73 to glyph indices. It is used for hardcoded EXE text (menus, system messages, debug strings).

Key mappings:
```
ASCII 0x20 ' ' -> glyph  1     (space)
ASCII 0x21 '!' -> glyph  5
ASCII 0x22 '"' -> glyph  6
ASCII 0x2A '*' -> glyph 16     <-- CONFLICT: MSG has ０ here
ASCII 0x2B '+' -> glyph 17     <-- CONFLICT: MSG has １ here
ASCII 0x30 '0' -> glyph 22     <-- CONFLICT: MSG has ６ here
ASCII 0x41 'A' -> glyph 41     <-- CONFLICT: MSG has i here
ASCII 0x61 'a' -> glyph 73     <-- CONFLICT: MSG has nothing here
```

### System 3: english_glyph_table.json (our translation table)

```
' ' -> glyph  1     (matches BOTH systems for space)
'!' -> glyph  5     (matches EXE system)
'"' -> glyph  6     (matches EXE system)
'0'-'9' -> glyphs 16-25  (matches MSG system's fullwidth digit slots)
'a'-'z' -> glyphs 33-58  (matches MSG system's lowercase slots)
'A'-'Z' -> glyphs 112-137 (REPURPOSED from MSG hiragana slots)
```

---

## Check 1: Atlas Position for Each Character

The font atlas generator (`generate_font_atlas.py`) places characters at:
```
col = glyph_slot % 21
row = glyph_slot // 21
x_pixel = col * 12
y_pixel = row * 12
```

### Verification of Key Positions

| Char | Glyph | Col | Row | Pixel (x,y) | Atlas Content (from preview) |
|------|-------|-----|-----|-------------|------------------------------|
| ' '  | 1     | 1   | 0   | (12, 0)     | BLANK (correct - space has no pixels drawn) |
| '!'  | 5     | 5   | 0   | (60, 0)     | ! (correct) |
| '"'  | 6     | 6   | 0   | (72, 0)     | " (correct) |
| '0'  | 16    | 16  | 0   | (192, 0)    | 0 (correct) |
| 'a'  | 33    | 12  | 1   | (144, 12)   | a (correct) |
| 'A'  | 112   | 7   | 5   | (84, 60)    | A (correct) |

The atlas preview image confirms: glyph 1 position (col 1, row 0) IS blank. The font atlas generator is placing characters correctly.

---

## Check 2: Glyph 1 = Space

**Atlas position (1, 0) at pixel (12, 0): CONFIRMED BLANK.**

The `generate_font_atlas.py` code iterates over `slot_to_char` (reversed glyph table). For space (' '), it calls `draw.text()` with the space character. The font renders nothing visible for space, so the cell remains black (= transparent in game). This is correct.

---

## Check 3: Glyph 5 = '!'

**Atlas position (5, 0) at pixel (60, 0): CONFIRMED has exclamation mark.**

Visible in the preview image at row 0, 6th cell from left (0-indexed col 5).

---

## Check 4: EXE ASCII Table Consistency with MSG Encoding

**The EXE ASCII table and our english_glyph_table.json are INCONSISTENT for most characters.**

| Character | EXE Table Glyph | english_glyph_table Glyph | Match? |
|-----------|-----------------|---------------------------|--------|
| ' ' (space) | 1  | 1  | YES |
| '!'       | 5  | 5  | YES |
| '"'       | 6  | 6  | YES |
| '#'       | 7  | 7  | YES |
| '$'       | 8  | 8  | YES |
| '%'       | 9  | 9  | YES |
| '&'       | 10 | 10 | YES |
| "'"       | 13 | 13 | YES |
| '('       | 14 | 14 | YES |
| ')'       | 15 | 15 | YES |
| '*'       | 16 | 70 | **NO** -- EXE=16, english=70 |
| '+'       | 17 | 27 | **NO** -- EXE=17, english=27 |
| ','       | 18 | 28 | **NO** -- EXE=18, english=28 |
| '-'       | 19 | 29 | **NO** -- EXE=19, english=29 |
| '.'       | 20 | 30 | **NO** -- EXE=20, english=30 |
| '/'       | 21 | 26 | **NO** -- EXE=21, english=26 |
| '0'       | 22 | 16 | **NO** -- EXE=22, english=16 |
| '1'       | 23 | 17 | **NO** -- EXE=23, english=17 |
| '9'       | 33 | 25 | **NO** -- EXE=33, english=25 |
| ':'       | 34 | 59 | **NO** -- EXE=34, english=59 |
| '?'       | 39 | 31 | **NO** -- EXE=39, english=31 |
| '@'       | 40 | 32 | **NO** -- EXE=40, english=32 |
| 'A'       | 41 | 112 | **NO** -- EXE=41, english=112 |
| 'a'       | 73 | 33 | **NO** -- EXE=73, english=33 |

**Only the first 10 punctuation characters (space through ')') match between the two systems.** Everything from '*' onward diverges.

---

## Root Cause Analysis: "YOUR!NEXT!VISIT>"

The symptom "spaces render as !" means something is emitting glyph 5 where glyph 1 should appear. Let me trace through scenarios:

### Scenario A: MSG resource text (our encoder)

Our encoder uses `english_glyph_table.json`:
- Space -> glyph 1 -> atlas pos (1,0) -> blank cell = CORRECT
- '!' -> glyph 5 -> atlas pos (5,0) -> exclamation = CORRECT

If MSG text shows "YOUR!NEXT!VISIT>", the encoder IS correctly writing glyph 1 for spaces. **The problem is NOT in the MSG encoder.**

### Scenario B: The text is coming from the EXE, not MSG

If the game is rendering a hardcoded EXE string using the EXE ASCII table:
- ASCII space (0x20) -> EXE table -> glyph 1 -> atlas blank = would be correct
- This would NOT produce the bug.

### Scenario C: The font atlas pixel data is wrong

The atlas PREVIEW shows correct placement. But the 4bpp binary conversion might be wrong. The generate_font_atlas.py uses a page-based layout:
```python
page_col = x // 128
page_row = y // 128
page_idx = page_row * 2 + page_col
```

**If the game's page layout differs from the generator's page layout, glyphs will appear at wrong positions.** For example, if glyph 1 (col 1, row 0, pixel 12,0) is in page 0 and the game reads page 0 correctly, it would be fine. But if pages are swizzled differently, the pixel data at the game's expected position for glyph 1 might actually contain the pixels the generator placed at a different location.

### Scenario D: The atlas binary was not actually injected

If the original Japanese atlas is still being used:
- Glyph 1 in the original Japanese atlas = space (blank) per msg_glyph_map.json
- This would render correctly as space, NOT as !

So this scenario also doesn't explain the bug.

### Scenario E (MOST LIKELY): Mixed glyph ID system confusion

The `glyph_map_partial.json` file shows a THIRD mapping that appears to be the name-entry screen system:
```
Glyph 1 = space
Glyph 5 = !
...
Glyph 73 = a
Glyph 86 = あ
```

This matches the EXE ASCII table exactly. If any code path is using the EXE ASCII table to convert text, then rendering with our atlas (which has MSG-system glyphs) would produce garbage, because:
- EXE says 'a' = glyph 73 -> our atlas has NOTHING at glyph 73 (col 10, row 3)
- EXE says '0' = glyph 22 -> our atlas has '6' at glyph 22

**BUT** this doesn't explain spaces-as-! either, since both systems agree that glyph 1 = space and glyph 5 = !.

---

## Possible Bug: Japanese Text Leaking ("のO<")

The screenshot mentions "のO<!:!CARE!FO" with Japanese の visible. This is glyph 136 in the MSG system (の = hiragana). In our english_glyph_table, glyph 136 = 'Y'. If the original Japanese MSG data was NOT fully replaced, a Japanese の (glyph 136) would render as 'Y' on our atlas, NOT as の.

**The fact that の is visible means the ORIGINAL Japanese atlas pixels are being rendered.** This strongly suggests:
1. The font atlas replacement did not take effect, OR
2. There are multiple font atlas textures and only one was replaced, OR
3. The game loads the atlas at runtime and our replacement is being overwritten

---

## Conclusions

1. **The english_glyph_table.json glyph assignments are internally consistent** -- the MSG encoder and font atlas generator agree on which character goes at which glyph slot.

2. **The EXE ASCII table uses a DIFFERENT glyph mapping** from our english_glyph_table.json. Characters '*' through 'z' and beyond are at different glyph slots. The EXE ASCII table must be patched to match english_glyph_table.json, OR our table must be changed to match the EXE. Since the EXE table is used for hardcoded strings and the MSG system uses our table, they MUST be reconciled.

3. **The "spaces as !" symptom is NOT explained by glyph ID mismatch** between the two tables, since both agree glyph 1 = space and glyph 5 = !. The symptom suggests either:
   - The font atlas binary was not correctly injected into the game
   - The 4bpp page layout in generate_font_atlas.py is wrong (pages are in wrong order or swizzled differently than the game expects)
   - The original Japanese atlas is still being used (evidenced by の appearing)

4. **The presence of Japanese の in the output is the strongest clue.** It means the original Japanese font pixels are being rendered. Our replacement atlas is either not being loaded or is being loaded into the wrong location.

---

## Recommended Next Steps

1. **Verify atlas injection:** Confirm that `build/english_font_atlas.bin` is actually being inserted into PACKDATA.DIG at the correct resource slot (resource 1272, type 01).

2. **Check for multiple font atlases:** The game has 12 font descriptors pointing to different texture pages. There may be multiple atlas resources that all need replacing.

3. **Validate 4bpp page layout:** Extract the pixel data from the game's VRAM during rendering (via PCSX2 GS dump) and compare against what generate_font_atlas.py produces. The page layout (128x128 pages, 2 columns x 4 rows) may not match the game's GS texture format.

4. **Reconcile EXE and MSG glyph tables:** Patch the EXE ASCII table at 0x3C0870 so that its glyph IDs match english_glyph_table.json. This is needed for any hardcoded EXE strings to render correctly.

5. **Quick test:** Hex-dump the first 12 bytes at atlas position (1,0) in the built binary. If they are all 0x0F (transparent), space is correctly blank. If they contain non-0x0F values, the atlas generator has a bug.
