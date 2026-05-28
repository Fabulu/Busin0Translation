# Garbled English Text - Root Cause Analysis

## Summary

There are **two independent bugs** causing the garbled output. Both are in
`tools/generate_font_atlas.py`.

---

## Bug 1: Missing PSMT4 Swizzle (causes ALL glyphs to display wrong)

### The Problem

The font atlas generator writes pixel data using a simple page-based linear
layout (line 75 comment: "linear, no swizzle"). However, the PS2 Graphics
Synthesizer reads PSMT4 (4-bit indexed) textures using a **hardware block
swizzle** pattern.

The original atlas (`extracted/packdata_resources/1272_type01.bin`) stores its
65536 bytes of pixel data in PS2 PSMT4 swizzled order. When deswizzled (as
confirmed by `tools/psmt4_deswizzle_v2.py` and the correct deswizzled PNG in
`dumps/font_renders/font_atlas_deswizzled_correct.png`), the glyphs appear in
a clean 21-column grid.

But `generate_font_atlas.py` renders glyphs into a PIL Image at the correct
(col, row) positions and then writes the pixels out in a linear page layout
(lines 92-108). It does **not** apply the PSMT4 block swizzle that the PS2
hardware expects. As a result, every single glyph pixel ends up at the wrong
memory offset, and the GPU reads garbage from wrong positions.

### Evidence

- `generate_font_atlas.py` line 75: explicitly says "linear, no swizzle"
- `psmt4_deswizzle_v2.py` exists and correctly deswizzles the original, proving
  the original data IS swizzled
- The preview PNG (`build/english_font_atlas_preview.png`) shows a clean grid -
  but this is the pre-swizzle image, not what the PS2 sees
- The deswizzled original (`dumps/font_renders/font_atlas_deswizzled_correct.png`)
  shows the scrambled block pattern of a PSMT4 texture

### Fix Required

The generator must apply PSMT4 swizzle when converting the atlas image to the
binary format. The inverse of the deswizzle in `psmt4_deswizzle_v2.py` must be
applied: given a desired pixel at (x, y) in the logical atlas, compute the
byte offset where that pixel must be written in the PSMT4-swizzled binary data.

---

## Bug 2: Glyph Slot Collision (uppercase A-Z overwrites hiragana)

### The Problem

`data/english_glyph_table.json` assigns uppercase letters to slots 112-137:

    "A": 112, "B": 113, "C": 114, ... "Z": 137

But according to `data/msg_glyph_map.json`, the game's **original** glyph
slots 112-137 contain **hiragana**:

    112: "a" (hiragana a)
    113: "i" (hiragana i)
    114: "u" (hiragana u)
    ...
    137: "ha" (hiragana ha)

This means:

1. **The encoder** correctly emits glyph 112 when it sees 'A' in English text.
2. **The font atlas generator** draws the English 'A' at atlas position for
   slot 112 (column 112%21=7, row 112//21=5).
3. **But** if the swizzle were correct, this would work -- the problem is that
   without swizzle, the 'A' glyph pixels land somewhere else entirely, and the
   GPU reads the old hiragana pixels (or random data) from where it expects
   slot 112 to be.

So Bug 2 is actually a consequence of Bug 1. If the swizzle is fixed, the
uppercase mapping to slots 112-137 would work correctly because the font atlas
binary would have English letters at those swizzled positions.

However, there is a **secondary concern**: the font atlas generator replaces
the ENTIRE pixel data (all 65536 bytes), meaning any slot NOT in the english
glyph table will have blank/transparent pixels. This means Japanese characters
that the game may still reference (e.g., for untranslated strings) will show
as blank. This is a separate issue from the garbled text.

---

## Bug 3: Space Renders as ! (glyph 1 vs glyph 5)

### The Problem

The encoder maps space -> glyph 1 (`english_glyph_table.json` line 2).
The original `msg_glyph_map.json` confirms glyph 1 = space, so this mapping
is correct at the data level.

However, in the garbled output, spaces display as `!`. Looking at the glyph
table: `"!" -> glyph 5`. The font atlas generator places the space character
at slot 1 (column 1%21=1, row 1//21=0) and `!` at slot 5 (column 5, row 0).

Because of the missing swizzle (Bug 1), the pixels intended for slot 1 end up
at a different memory location. What the GPU reads from the slot 1 position is
whatever data happens to be at that swizzled offset -- which could be the `!`
glyph or just happen to look like `!`.

**This is another consequence of Bug 1.** Fix the swizzle and spaces should
render correctly.

---

## Bug 4: Punctuation Garbled (> < = : render wrong)

Same root cause as Bug 1. The encoder mappings for punctuation are:

    ":": 59, ";": 60, "<": 61, "=": 62, ">": 63

These are all correct glyph IDs, but without proper PSMT4 swizzle, the
rendered pixels for these characters end up at wrong memory offsets.

---

## Trace: "aUTO-FILLa!:" -> should be "Auto-fill"

- 'A' -> encoder emits glyph 112 -> GPU reads slot 112 from swizzled memory
  -> finds hiragana "a" pixels because data is not swizzled correctly
- 'u' -> glyph 53 -> some wrong character due to swizzle
- 't' -> glyph 52 -> garbled
- 'o' -> glyph 47 -> garbled
- (etc.)

The fact that some lowercase letters appear correct-ish while uppercase shows
hiragana suggests that the lower glyph slots (0-70ish) happen to be in a
region where the linear and swizzled layouts partially overlap (they coincide
for the first portion of page 0), while higher slots (112+) are in regions
where the swizzle divergence is total.

---

## Files Involved

| File | Role | Issue |
|------|------|-------|
| `tools/generate_font_atlas.py` | Creates font atlas binary | **Missing PSMT4 swizzle** (primary bug) |
| `data/english_glyph_table.json` | char -> glyph slot mapping | Correct |
| `tools/encode_english_text.py` | Text encoder | Correct |
| `data/msg_glyph_map.json` | Original game's glyph map | Reference only |
| `tools/psmt4_deswizzle_v2.py` | Deswizzle for reading | Has correct deswizzle logic to invert |
| `build/full_patch_pipeline.py` | Assembles patched DIG | Correct (just copies atlas binary) |

---

## Recommended Fix

1. In `tools/generate_font_atlas.py`, after rendering the atlas to the PIL
   Image, apply the **PSMT4 swizzle** when writing pixels to `pixel_data`.
   The swizzle is the inverse of the deswizzle in `psmt4_deswizzle_v2.py`:
   instead of "given byte offset, compute (x,y)", do "given (x,y), compute
   byte offset".

2. The deswizzle function in `psmt4_deswizzle_v2.py` uses a simple
   page-linear layout (128px wide pages). However, the deswizzled output
   image (`font_atlas_deswizzled_correct.png`) visually shows the correct
   glyphs, so this deswizzle IS correct for this game. The swizzle (inverse)
   should use the exact same page/offset math but in reverse direction.

3. **However** -- the deswizzler in `psmt4_deswizzle_v2.py` uses
   `HEADER_SIZE = 256`, while the generator uses 192. The original file is
   65792 bytes. If header=192, pixel_data=65536, palette=64: 192+65536+64=65792.
   If header=256, pixel_data=65536: 256+65536=65792 with no palette. This
   discrepancy needs investigation -- the correct header size determines where
   pixel data starts and whether there is a separate palette block.

4. Verify whether the "simple page-linear" deswizzle in `psmt4_deswizzle_v2.py`
   is truly correct, or if the real PS2 PSMT4 requires block-level swizzling
   (32x16 blocks within pages). The `debug_swizzle.py` file attempted multiple
   deswizzle methods (32x16 blocks, 32x32 blocks, linear), suggesting
   uncertainty. The correct method should be validated against known glyph
   positions from `msg_glyph_map.json`.
