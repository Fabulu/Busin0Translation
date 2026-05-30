# encode_english_text.py -- Full Behavior Documentation

Date: 2026-05-28

## File Location

`tools/encode_english_text.py`

---

## What It Does

Encodes an English string into a list of BE uint16 glyph indices, with automatic
word wrapping and page-break insertion.

### Parameters

- `max_chars_per_line` = **18** (default)
- `max_lines_per_page` = **3** (default)

### Word Wrap Algorithm

1. Flattens all `\n` in the input to spaces, then splits on whitespace into words.
2. For each word:
   - If the word does NOT fit on the current line (`line_chars + 1 + word_len > 18`),
     emit `0xFFFE` (line break) and increment `lines_on_page`.
   - If `lines_on_page > 3`, ALSO emit `0xFFD2` (page break) and reset counter to 1.
3. If the current line already has content, emit a space glyph before the word.
4. Encode each character via the glyph table (case-insensitive fallback, then `?`).

### Key Behaviors

| Feature                | Value / Behavior                             |
|------------------------|----------------------------------------------|
| Max line length        | **18 characters**                            |
| Line break marker      | **0xFFFE** -- yes, inserted automatically    |
| Page break marker      | **0xFFD2** -- yes, inserted after 3 lines    |
| Page break ordering    | FFFE emitted first, THEN FFD2 appended       |
| Handling of " / "      | **NOT handled at all** -- treated as literal  |
| Trailing FFFE/markers  | **No** -- nothing appended after last word    |
| FFFF terminator        | **Not added** by this function                |

### Critical Detail: " / " is IGNORED

`encode_english_text.py` does NOT split on `" / "`. It treats the slash and
surrounding spaces as ordinary characters. If a translation contains
`"Hello / World"`, it encodes `H e l l o   /   W o r l d` as 13 characters
on one line -- the slash is a literal glyph, not a line break.

This means: **encode_english_text.py is NOT used by the v2 pipeline (build_v9.py
Step 4).** It appears to be a standalone utility / early prototype.

---

## build_v9.py Step 4 Encoding (the ACTUAL v2 pipeline)

Location: `build/build_v9.py`, lines 199-217.

### Algorithm

1. Split the English text on `' / '` into `parts`.
2. For each part (after the first):
   - Increment `line_count`.
   - If `line_count >= 3`: emit `0xFFD2` (page break), reset `line_count = 0`.
   - Else: emit `0xFFFE` (line break).
3. Encode each character in the part via `enc()`.

### Key Behaviors

| Feature                | Value / Behavior                                |
|------------------------|-------------------------------------------------|
| Max line length        | **None** -- no word wrapping at all             |
| Line break marker      | **0xFFFE** -- yes, from " / " splits            |
| Page break marker      | **0xFFD2** -- yes, every 3rd line break          |
| Page break ordering    | FFD2 INSTEAD of FFFE (not both)                 |
| Handling of " / "      | **Primary mechanism** -- splits text on it       |
| Auto word wrap         | **DISABLED** (comment: "word_wrap removed")      |
| Trailing FFFE/markers  | **No** -- nothing appended after last part       |
| FFFF terminator        | Added by `inject_and_patch()`, not here          |

---

## Comparison: encode_english_text.py vs build_v9.py Step 4

| Aspect                   | encode_english_text.py       | build_v9.py Step 4           |
|--------------------------|------------------------------|------------------------------|
| Word wrapping            | YES, auto at 18 chars        | NO, relies on pre-wrapped    |
| Line break source        | Auto-calculated              | From " / " in translation    |
| " / " handling           | Ignored (literal chars)      | Split point for FFFE         |
| Page break trigger       | After 3 lines (>3)           | Every 3rd separator (>=3)    |
| Page break emit pattern  | FFFE then FFD2               | FFD2 only (no FFFE)          |
| Used in production?      | NO                           | YES                          |

### Could encode_english_text.py Create More Lines Than Expected?

**YES, absolutely.** With max_chars_per_line=18 and automatic word wrapping:

- A translation like `"The shopkeeper looks at you carefully"` (38 chars) would be
  wrapped into 3 lines automatically:
  - Line 1: `The shopkeeper` (14 chars)
  - Line 2: `looks at you` (12 chars)  
  - Line 3: `carefully` (9 chars)

- If the same text were used with build_v9.py Step 4 (no " / " markers), it would
  be encoded as a SINGLE line of 38 glyphs -- which would overflow the text box
  horizontally but not vertically.

**The two encoders produce fundamentally different output for the same input.**

### Page Break Ordering Difference

This is subtle but important:

- `encode_english_text.py`: Emits `FFFE` first, then `FFD2`.
  Sequence: `...word FFFE FFD2 word...`
- `build_v9.py Step 4`: Emits `FFD2` ONLY (no FFFE before it).
  Sequence: `...word FFD2 word...`

The game engine may behave differently depending on whether FFFE precedes FFD2
or not. The build_v9.py approach (FFD2 alone) appears to be the correct one
based on observed behavior in working translations.

---

## Conclusion

`encode_english_text.py` is a **standalone prototype** that is NOT used in the
actual build pipeline. The production encoder in `build_v9.py` Step 4:

1. Does NO automatic word wrapping (relies on translators inserting " / ").
2. Splits on " / " to create FFFE line breaks.
3. Inserts FFD2 page breaks every 3 lines (instead of FFFE).

If `encode_english_text.py` were accidentally used instead, it would:
- Create many more line breaks (auto-wrapping at 18 chars).
- Treat " / " as literal characters instead of break markers.
- Emit FFFE+FFD2 pairs instead of FFD2-only for page breaks.
