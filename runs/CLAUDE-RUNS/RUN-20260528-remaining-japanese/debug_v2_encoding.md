# V2 Pipeline Encoding Analysis

## Question: Does build_full_english_v2.py conflict with build_v9.py's wrapping/page-break logic?

## V2 Pipeline (build_full_english_v2.py) - Type-01 Resources

### How it encodes English translations

The v2 pipeline's `clean_and_encode()` function (line 93-136):

1. Splits the translation text on ` / ` to find FFFE boundaries
2. For EACH segment between ` / ` separators, calls `encode_text()` from `tools/encode_english_text.py`
3. Inserts 0xFFFE between segments
4. The `encode_text()` call is: `encode_text(part, max_chars_per_line=18, max_lines_per_page=3)`

### Does it have word_wrap?

**YES** - via `encode_text()` in `tools/encode_english_text.py`.

`encode_text()` does full word wrapping:
- Tracks `line_chars` per line, breaks at word boundaries when exceeding `max_chars_per_line=18`
- Inserts 0xFFFE for line breaks
- Inserts 0xFFD2 page breaks every `max_lines_per_page=3` lines

### Does it insert FFD2 page breaks?

**YES** - `encode_text()` inserts `0xFFFE` then `0xFFD2` when `lines_on_page > max_lines_per_page` (line 25-28 of encode_english_text.py).

### How does it handle ` / `?

Splits on ` / `, treats each part as a separate segment. Inserts 0xFFFE between them. Each segment is INDEPENDENTLY word-wrapped by `encode_text()`.

---

## Build_v9.py - Type-02 Resources (Step 4)

### How it encodes (lines 200-217):

1. Calls `word_wrap(en_text)` - custom function that splits on ` / `, wraps long segments at word boundaries (max 18 chars), then re-joins with ` / `
2. Splits the wrapped result on ` / `
3. Inserts 0xFFFE between parts
4. Inserts 0xFFD2 (page break) every 3 lines instead of 0xFFFE
5. Encodes characters via simple `enc(ch)` lookup

### Does it have word_wrap?

**YES** - its own `word_wrap()` function (lines 59-77), plus manual FFD2 insertion every 3 lines.

---

## Comparison: V2 vs V9

| Feature | V2 (type-01) | V9 Step 4 (type-02) |
|---------|-------------|---------------------|
| Word wrap | YES (encode_text) | YES (word_wrap + manual) |
| Max chars/line | 18 | 18 |
| Page breaks (FFD2) | YES (every 3 lines) | YES (every 3 lines) |
| Line breaks (FFFE) | YES | YES |
| ` / ` handling | Split -> per-segment wrap | Pre-wrap all -> split |

### Key Difference

The v2 pipeline wraps EACH ` / ` segment independently through `encode_text()`, which has its own internal line counter. So each segment starts with a fresh `lines_on_page = 1` counter.

The v9 pipeline wraps first (via `word_wrap()`), then processes ALL parts with a SHARED `line_count` counter across the entire message, inserting FFD2 every 3 cumulative lines.

**This means:**
- V2: A 6-line message (two 3-line segments separated by ` / `) would get page breaks within each 3-line segment independently, but the FFFE between segments does NOT reset the game's line counter.
- V9: A 6-line message gets FFD2 after every 3rd cumulative line, regardless of ` / ` boundaries.

---

## Impact on R38 Descriptions (Type-01, handled by V2)

### Double-wrapping risk?

**YES, there IS a double-wrapping risk in the V2 pipeline.**

If the translation text already contains ` / ` for manual line breaks (i.e., the translator pre-wrapped to 18 chars), then `clean_and_encode()` splits on ` / ` and passes each segment to `encode_text()`. Since each segment is already <= 18 chars, `encode_text()` will NOT add extra wraps. **No double-wrap in this case.**

However, if a segment is longer than 18 chars, `encode_text()` WILL wrap it, adding additional FFFE + potentially FFD2 tokens. If the translator also put ` / ` in the translation assuming those would be the only line breaks, you get EXTRA lines from the encoder's wrapping.

### Overflow scenario for R38:

The translations were shortened to 3 lines max (i.e., 2 ` / ` separators = 3 segments). Each segment should be <= 18 chars. So:
- `clean_and_encode()` splits into 3 segments
- Each segment <= 18 chars -> `encode_text()` adds no extra wraps
- Result: exactly 3 lines separated by FFFE
- **No FFD2 page breaks are inserted** (because each segment is only 1 line, never exceeding `max_lines_per_page=3`)
- **No overflow** - the 3-line limit is respected

### Conclusion

**The v2 pipeline's encoding is SAFE for R38 descriptions** as long as:
1. Each line segment (between ` / `) is <= 18 characters
2. There are at most 3 segments

If both conditions hold, `encode_text()` passes through each segment without adding wraps or page breaks. The only FFFE tokens come from the ` / ` split in `clean_and_encode()`.

**No conflict between v2 and v9** because they handle different resource types:
- V2 handles type-01 (R34, R36-R49, etc.)
- V9 Step 4 handles type-02 (dialogue resources)
- V9 Step 2 handles only R35, R2654 (flat-format resources, with its own word_wrap)

The pipelines do not double-process the same resources.
