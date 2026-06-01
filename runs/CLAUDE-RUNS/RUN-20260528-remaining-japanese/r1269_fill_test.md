# R1269 Fill Test -- Font Page Identification

## Purpose
Fill R1269's pixel data with solid 0x88 bytes to identify which in-game kanji glyphs are rendered from this font page resource.

## Resource Details
- **Resource**: R1269 (index 1269, type01)
- **Format**: PSMT8, 512x512 (8-bit indexed, 262144 pixel bytes)
- **File size**: 263,360 bytes (.bin) / 264,192 bytes (.raw with 16-byte sub-header)
- **Pixel data offset**: 0x4D0 from raw resource start (0x4C0 from TIM2 data start)
- **Pixel data size**: 262,144 bytes (512 * 512)
- **Fill value**: 0x88 (palette index 136)
- **Original non-zero coverage**: 46.2% of pixel data had glyph content

## Font Page Table (EXE offset 0x3CAA60)
Confirmed R1269 appears as entries [2] and [3] in the font page table:
```
[0] R1303  [1] R1303
[2] R1269  [3] R1269   <-- this test
[4] R1270  [5] R1270
[6] R1271  [7] R1271
[8] R1273  [9] R1273
...
```

## ISO Output
- **File**: `build/BUSIN0_EN_r1269_fill_test.iso`
- **Method**: Direct ISO binary patch (copy original, overwrite R1269 pixel region in-place)
- **Script**: `tools/r1269_fill_test.py`

## PACKDATA.DIG Location in ISO
- LBA: 16029
- R1269 sector offset: 0x33859
- R1269 absolute ISO offset: 0x1BB7B000

## Test Instructions
1. Boot `build/BUSIN0_EN_r1269_fill_test.iso` in PCSX2
2. Navigate to any screen with kanji text (town menus, item descriptions, dialogue)
3. **If kanji appear as solid blocks**: those glyphs are rendered from R1269
4. **If kanji appear normal**: those glyphs come from a different font page (R1270, R1271, etc.)
5. Take screenshots to document which characters are affected

## Expected Outcome
Some subset of kanji will turn into solid rectangles. This identifies the exact glyph range served by R1269, which is needed to:
- Map glyph indices to font page resources
- Know which resources to modify when replacing kanji with English glyphs
- Build a complete font page allocation map

## Date
2026-05-28
