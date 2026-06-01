# R1188 Kanji Wipe Test

**Date:** 2026-05-28
**ISO:** `build/BUSIN0_EN_r1188_kanji_wipe.iso`
**Script:** `tools/build_r1188_kanji_wipe_iso.py`

## Purpose

Since the previous R1188 nuclear wipe showed that kana edits ARE visible,
this test isolates ONLY the kanji rows. If chargen stat labels disappear,
they definitely come from R1188's kanji region and we need correct cell positions.

## What Was Done

R1188 (1188_type01.raw, 528,384 bytes) is a 1024x1024 PSMT4 font/glyph atlas.
The atlas is organized in a grid with 24px-tall rows:

| Grid rows | Y range   | Content        | Action     |
|-----------|-----------|----------------|------------|
| 0-5       | 0-143     | ASCII + kana   | PRESERVED  |
| 6-41      | 144-1007  | Kanji glyphs   | ZEROED     |

### Byte Layout
- **Header:** bytes 0-3071 (3,072 bytes) -- preserved
- **Pixel data:** bytes 3072-527359 (524,288 bytes total, 512 bytes/row)
  - Kana region: pixel bytes 0-73727 (y=0-143) -- **PRESERVED**
  - Kanji region: pixel bytes 73728-442367 (y=144-1007) -- **ZEROED** (442,368 bytes)
  - Bottom row: pixel bytes 442368-524287 (y=1008-1023) -- preserved
- **Trailing data:** bytes 527360-528383 (1,024 bytes) -- preserved

### Verification
- Kana rows confirmed identical to original (73,728 bytes match)
- Kanji rows confirmed all-zero
- PACKDATA size matches original exactly (839,661,568 bytes, diff: +0)
- ISO size: 1,274,544,128 bytes

## How to Test

1. Load `build/BUSIN0_EN_r1188_kanji_wipe.iso` in PCSX2
2. Navigate to character creation (chargen)
3. Observe stat labels (STR, INT, PIE, VIT, AGI, LCK) and other kanji text
4. Kana (hiragana/katakana) in the name-entry grid should STILL be visible

## Interpreting Results

### If stat labels DISAPPEAR (invisible/blank):
- **R1188 kanji rows (6-41) ARE the source** of stat labels
- This confirms we need correct cell coordinates within those rows
- The comprehensive R1188 patcher should target these specific rows

### If stat labels REMAIN visible:
- Stat labels come from **somewhere else** (not R1188 kanji rows)
- They might come from:
  - R1188 kana rows (0-5) -- unlikely for kanji
  - A completely different resource
  - The EXE or VRAM upload from another source
- Further investigation needed

### If kana grid ALSO disappears:
- Something went wrong with row preservation
- Rebuild needed

## Previous Tests
- R1188 fill test (all pixels = 0x88): confirmed R1188 IS used on chargen screen
- R1188 nuclear wipe (all pixels = 0x00): confirmed kana glyphs vanish
- This test: isolates kanji rows only to pinpoint stat label source
