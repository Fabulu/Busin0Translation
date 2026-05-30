# Half-Width Word Wrap Analysis

## Current State (12px advance)

| Parameter | Value | Source |
|-----------|-------|--------|
| Glyph advance | 12px | Font atlas cell size |
| Display box width | 224px | EXE at VA 0x305980 |
| Max chars/line | 18 | 224 / 12 = 18.67, truncated to 18 |
| Lines per page | 3 | FFD2 page break every 3 lines |
| word_wrap() default | max_chars=18 | build_v9.py line 59 |

## Proposed State (6px advance)

| Parameter | Value | Notes |
|-----------|-------|-------|
| Glyph advance | 6px | Half-width ASCII glyphs |
| Display box width | 224px | Unchanged (same text box) |
| Pixel-theoretical max | 37 | 224 / 6 = 37.33 |
| 32-slot hard limit | 32 | EXE at VA 0x302F58: `slti $v1, $v1, 32` |
| **Effective max chars/line** | **32** | min(37, 32) = 32 |
| Lines per page | 3 | Unchanged |

The 32-slot glyph array is the binding constraint, not the pixel width. Each line's display array holds at most 32 halfword entries (VA 0x302F58). At 6px advance, 32 chars = 192px, well within the 224px box.

## build_v9.py Changes Required

### Location 1: word_wrap() function definition (line 59)

```python
# BEFORE:
def word_wrap(text, max_chars=18):

# AFTER:
def word_wrap(text, max_chars=32):
```

### Location 2: Call site in type-01/20/44 injection loop (line 109)

```python
en = word_wrap(en)
```

No change needed -- uses the default parameter.

### Location 3: Call site in type-2 injection loop (line 201)

```python
en_text = word_wrap(en_text)
```

No change needed -- uses the default parameter.

### Location 4: Page break logic (lines 204-213)

```python
line_count += 1
if line_count >= 3:
    glyphs.append(0xFFD2)  # page break
    line_count = 0
```

No change needed -- 3 lines per page stays the same.

### Summary of code changes

Only ONE line needs to change in build_v9.py:

```
Line 59: max_chars=18  -->  max_chars=32
```

Everything else (call sites, page break logic) works unchanged.

## inject_r46_r47.py -- Separate Concern

The R46/R47 inject script (`build/inject_r46_r47.py`) has its own hardcoded translations with manual line breaks (` / `) already baked in. These were hand-optimized for 18-char caps. At 32 chars/line, many of those manual breaks could be removed for better readability, but they will still display correctly as-is (shorter lines just look less cramped).

## fix_overflow.py -- Impact Assessment

### Current state
- **40 hand-rewritten translations** in `tools/fix_overflow.py`
- Threshold: >150 chars total triggers overflow (line 102)
- Line-level check: >18 chars per line for R1193/R1194 (line 107)
- These rewrites aggressively compressed text to fit 18 chars/line

### With 32 chars/line: most rewrites become unnecessary

At 18 chars/line x 3 lines/page = 54 chars visible per page.
At 32 chars/line x 3 lines/page = 96 chars visible per page.

That is a 78% increase in text capacity per page. The 150-char overflow threshold was based on the assumption that long messages need many page breaks at 18 chars/line. At 32 chars/line, a 150-char message only needs ~2 pages (5 lines) instead of ~3 pages (9 lines).

**Recommendation**: After the half-width EXE patch is confirmed working:

1. Revert the 40 fix_overflow.py rewrites back to the original (uncompressed) translations
2. Raise or remove the 150-char overflow threshold
3. Change the line-length check from 18 to 32
4. Re-run the overflow audit -- most messages will fit naturally

## overflow_patches.json -- Impact Assessment

### Current state
- **302 rewritten translations** in `overflow_patches.json`
- These were optimized for ~20 chars/line (slightly more generous than 18 due to earlier testing)

### With 32 chars/line: the vast majority are unnecessary

The original translations that prompted these 302 rewrites were typically 20-40 chars/line. At 32 chars/line, most original translations fit without any rewriting. Only messages with individual lines exceeding 32 characters would still need intervention, and English words rarely exceed 32 chars per line in natural text.

**Recommendation**: Discard overflow_patches.json entirely once half-width rendering is confirmed. Use the original machine/human translations as-is, with word_wrap(max_chars=32) handling line breaks automatically.

## Sequence of Operations

1. Apply EXE patches (glyph advance 12->6, X-clamp 128->256)
2. Rebuild font atlas with half-width (6px) ASCII glyphs
3. Change build_v9.py line 59: `max_chars=18` -> `max_chars=32`
4. Test with current translations (they will rewrap automatically)
5. If confirmed working: revert overflow rewrites, remove overflow_patches.json
6. Update fix_overflow.py thresholds (18->32 for line check, reconsider 150 total)

## Risk: 32-Slot Limit Could Be Raised

If 32 chars/line proves insufficient (unlikely for English dialogue), the 32-slot limit at VA 0x302F58 could be patched to 37 or 40. However, this would also require expanding the glyph slot array allocation, which is riskier. 32 chars/line is generous for a PS2 RPG dialogue box and should be sufficient.
