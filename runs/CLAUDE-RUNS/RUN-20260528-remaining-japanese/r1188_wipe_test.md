# R1188 Nuclear Wipe Test

**Date:** 2026-05-28
**ISO:** `build/BUSIN0_EN_r1188_wipe.iso`

## What Was Done

R1188 (1188_type01.raw, 528,384 bytes) contains a 1024x1024 PSMT4 font/glyph atlas
used for the character creation (chargen) screen.

This test **zeroes ALL pixel data** in R1188 to make every glyph from this resource
completely invisible. If any chargen text disappears when running this ISO, that text
is sourced from R1188.

### File Structure
- **Header:** bytes 0-3071 (3,072 bytes) -- PRESERVED unchanged
- **Pixel data:** bytes 3072-527359 (524,288 bytes) -- ALL ZEROED
- **Trailing data:** bytes 527360-528383 (1,024 bytes) -- PRESERVED unchanged

### Build Process
1. Full build_v9.py pipeline executed (all translations, EXE patches, etc.)
2. R1188 in `build/packdata_resources/` replaced with zeroed version AFTER step 3.6
3. PACKDATA.DIG rebuilt with zeroed R1188
4. ISO assembled with updated PACKDATA + patched EXE

## How to Test

1. Load `build/BUSIN0_EN_r1188_wipe.iso` in PCSX2
2. Navigate to the character creation screen
3. Observe which text elements disappear vs remain visible

## Expected Results

### If chargen stat labels DISAPPEAR (invisible/blank):
- **R1188 IS the source** of those glyphs
- The stat labels (STR, INT, PIE, VIT, AGI, LCK), sidebar text, tab labels,
  kana grid, and any other chargen-screen text that vanishes all come from R1188
- This confirms the comprehensive R1188 patcher is targeting the correct resource

### If stat labels REMAIN VISIBLE:
- They come from a different resource (possibly the EXE, VRAM, or another texture)
- R1188 may only contain a subset of chargen glyphs
- Further investigation needed to identify the actual source

### Mixed results (some disappear, some stay):
- R1188 contains SOME chargen glyphs but not all
- Document which specific labels/text disappeared vs stayed visible
- The remaining visible text comes from another source

## Notes
- Zeros = invisible (transparent) because pixel value 0 maps to palette index 0,
  which is typically fully transparent in PS2 CLUT-based rendering
- This is more definitive than filling with solid color blocks because disappearance
  is unmistakable
