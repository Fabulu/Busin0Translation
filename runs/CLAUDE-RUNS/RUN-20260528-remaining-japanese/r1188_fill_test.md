# R1188 Fill Test

## Purpose
Determine whether R1188 is the source atlas for chargen stat labels and other kanji glyphs on the character creation screen.

## Method
- Preserved the 3072-byte header of R1188 (type01 resource, 528,384 bytes total)
- Filled ALL 525,312 pixel bytes with 0x88 (every 4bpp nibble = 8, mid-gray solid)
- Built a PACKDATA.DIG with ONLY R1188 modified (all other resources are original/unpatched)
- Injected into a clean ISO copy

## Files
- Fill script: `tools/r1188_fill_test.py`
- ISO build script: `tools/build_r1188_fill_test_iso.py`
- Intermediate PACKDATA: `build/PACKDATA_r1188_fill.DIG`
- Test ISO: `build/BUSIN0_EN_r1188_fill_test.iso`

## PACKDATA size
Original: 839,661,568 bytes
Modified: 839,661,568 bytes (diff: +0, exact match)

## Test Instructions
1. Load `build/BUSIN0_EN_r1188_fill_test.iso` in PCSX2
2. Navigate to character creation (chargen)
3. Observe stat labels, tab labels, and any kanji text

## Expected Results

### If R1188 IS the source:
- ALL glyphs sourced from R1188 will render as solid gray blocks
- Stat labels (STR, INT, PIE, etc.) will be solid blocks
- Tab labels will be solid blocks
- Any other text from this atlas will be solid blocks

### If R1188 is NOT the source:
- Stat labels and kanji will display normally (unchanged from original game)
- R1188 may be used for other screens or not loaded during chargen at all

## Result
_(to be filled after testing)_
