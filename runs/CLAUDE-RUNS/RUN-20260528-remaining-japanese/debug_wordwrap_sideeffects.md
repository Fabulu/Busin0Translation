# word_wrap Side-Effect Analysis

## Summary

The `word_wrap()` function in `build_v9.py` has a **double-wrapping bug** that affects
**2,394 of 13,387 type-2 translations** (17.9%). Short labels (R38 stat names) are
NOT affected because R38 is type-1 and goes through the v2 pipeline instead.

## Pipelines and What They Use

| Pipeline | Resources | Wrapping | FFD2 Logic |
|---|---|---|---|
| v2 (`build_full_english_v2.py`) | Type-1 (R38, R43, etc.) | `encode_text()` (word-based) | Inside `encode_text()` |
| build_v9 Step 2 | R35 (type-02), R2654 (type-44) | `word_wrap()` | **None** (FFFE only) |
| build_v9 Step 4 | All other type-02 resources | `word_wrap()` | Every 3 lines -> FFD2 |

## Bug #1: Double-Wrapping in Step 4

Translations already contain intentional ` / ` line breaks (placed by translators
at ~18 char boundaries). `word_wrap()` splits on ` / `, then re-wraps any segment
over 18 chars, creating ADDITIONAL segments.

### Example

```
Input:  "The medal earned from / defeating the floor / master was offered."
         (3 parts, intended as 3 lines)

After word_wrap:
         "The medal earned / from / defeating the / floor / master was / offered."
         (6 parts -- doubled!)
```

The original 3-line text becomes 6 lines. With FFD2 every 3 lines, this creates
an unintended **page break** in the middle of a single thought:

```
--- Page 1 ---
  The medal earned
  from
  defeating the
--- [WAIT FOR INPUT, CLEAR] ---
--- Page 2 ---
  floor
  master was
  offered.
```

### Impact

- **2,394 translations** have at least one segment > 18 chars that gets re-split
- FFD2 page breaks fire at wrong positions (after word_wrap creates extra segments)
- Text that was meant to flow as 2-3 lines gets split across pages

## Bug #2: Trailing Empty Segment (Minor)

Translations ending with ` / ` (standard format) produce a trailing empty segment
after `split(' / ')`. This creates a trailing FFFE in the glyph stream.

```
"str / " -> split -> ['str', ''] -> glyphs: [s, t, r, FFFE]
```

This is actually **correct behavior** -- the v2 pipeline explicitly documents this
as matching the original binary format (every FFFF group ends with FFFE before FFFF).
However, in Step 4's FFD2 logic, the empty trailing segment increments `line_count`,
which can cause an off-by-one in where the next FFD2 fires.

## Bug #3: FFD2 Counter Interaction with Empty Segments

In Step 4, the empty trailing segment counts toward `line_count`:

```python
for pi, part in enumerate(parts):
    if pi > 0:
        line_count += 1          # <-- empty trailing part increments this
        if line_count >= 3:
            glyphs.append(0xFFD2)  # <-- could fire on empty part
```

For a translation like `"HP / MP / str / "` (3 parts + 1 empty = 4 segments after split),
the FFD2 fires at the boundary between "str" and the empty segment -- inserting a
page break right before the trailing FFFE.

## R38 Short Labels: NOT AFFECTED

R38 is type-1 (not type-2), so it goes through `build_full_english_v2.py` which uses
`clean_and_encode()` -> `encode_text()`. This pipeline:
- Does NOT call `word_wrap()`
- Handles trailing empty segments correctly (just appends FFFE, documented as intentional)
- Has its own FFD2 logic inside `encode_text()` that only fires on actual content words

**R38 short labels like "str / ", "male / " are encoded correctly.**

## Proposed Fix

### Option A: Strip trailing empty segments before FFD2 logic (minimal fix)

```python
# In Step 4 encoding (line ~202 of build_v9.py):
en_text = word_wrap(en_text)
parts = en_text.split(' / ')

# Strip trailing empty segments before counting lines for FFD2
while parts and parts[-1].strip() == '':
    parts.pop()

# Add trailing FFFE back after encoding (to match original binary format)
# ... encode parts with FFD2 logic ...
glyphs.append(0xFFFE)  # restore trailing FFFE
```

### Option B: Remove word_wrap from Step 4 entirely (recommended)

The translations already have ` / ` line breaks at appropriate positions. The v2
pipeline's `encode_text()` handles word-wrapping internally. `word_wrap()` in Step 4
is redundant and destructive (double-wrapping).

```python
# REMOVE this line from Step 4:
# en_text = word_wrap(en_text)

# Keep the rest of the encoding logic as-is
parts = en_text.split(' / ')
# ... but also strip trailing empty parts for FFD2 counting
```

### Option C: Make word_wrap only wrap segments that don't have existing breaks (safe compromise)

```python
def word_wrap(text, max_chars=18):
    segments = text.split(' / ')
    # If text already has line breaks, trust them -- don't re-wrap
    if len(segments) > 1:
        return text
    # Only wrap single-segment (no existing breaks) text
    wrapped = []
    seg = segments[0]
    while len(seg) > max_chars:
        brk = seg.rfind(' ', 0, max_chars + 1)
        if brk <= 0:
            brk = max_chars
        wrapped.append(seg[:brk])
        seg = seg[brk:].lstrip(' ')
    wrapped.append(seg)
    return ' / '.join(wrapped)
```

## Recommendation

**Option B** is the safest. The type-2 translations were written with ` / ` breaks
already placed. Removing `word_wrap()` from Step 4 eliminates the 2,394 double-wrapped
messages while preserving the existing line structure. The only risk is translations
with single long lines (no ` / ` breaks) that exceed 18 chars -- but these are rare
in the type-2 corpus since the translation process adds breaks.

If safety margin is needed, use **Option C** which only wraps lines that have zero
existing breaks.

## Files Involved

- `C:/Programmieren/wizardrytranslation/build/build_v9.py` -- lines 59-76 (word_wrap), line 109 (Step 2 call), line 202 (Step 4 call), lines 203-217 (FFD2 logic)
- `C:/Programmieren/wizardrytranslation/build/build_full_english_v2.py` -- lines 93-136 (clean_and_encode, no word_wrap)
- `C:/Programmieren/wizardrytranslation/tools/encode_english_text.py` -- lines 7-46 (encode_text with proper word-based wrapping)
