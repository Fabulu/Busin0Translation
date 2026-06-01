# Kanji Font Pages Wipe Test (R1269-R1277, R1302-R1303)

## Date: 2026-05-28

## Purpose
Determine if chargen stat labels come from the 10 kanji font page resources
referenced in the EXE font page table at 0x3CAA60.

Previous test: R1188 kanji wipe had NO effect on stat labels, ruling it out.
This test wipes ALL 10 remaining kanji font pages.

## Resources Wiped

| Resource | Size | Pixel Bytes Zeroed | Type |
|----------|------|--------------------|------|
| R1269 | 264,192 | 262,144 | PSMT8 512x512 |
| R1270 | 133,120 | 131,072 | PSMT8 512x256 |
| R1271 | 133,120 | 131,072 | PSMT8 512x256 |
| R1273 | 133,120 | 131,072 | PSMT8 512x256 |
| R1274 | 264,192 | 262,144 | PSMT8 512x512 |
| R1275 | 264,192 | 262,144 | PSMT8 512x512 |
| R1276 | 264,192 | 262,144 | PSMT8 512x512 |
| R1277 | 264,192 | 262,144 | PSMT8 512x512 |
| R1302 | 264,192 | 262,144 | PSMT8 512x512 |
| R1303 | 264,192 | 262,144 | PSMT8 512x512 |

## PSMT8 File Structure
- Header: 1024 bytes (GIF tags, GS registers) -- PRESERVED
- Pixel data: 131,072 or 262,144 bytes -- ZEROED
- Palette: 1024 bytes (256 RGBA entries) -- PRESERVED

## Method
1. Built normal v9 ISO via `generate_font_atlas.py` + `build_v9.py`
2. Directly patched the ISO in-place: for each resource, located it via
   PACKDATA TOC and zeroed the pixel data region while preserving header
   and palette
3. All 10 resources verified: pixels=ZEROED, palette=PRESERVED

## Test ISO
`build/BUSIN0_EN_kanji_pages_wipe.iso` (1,274,544,128 bytes)

## Cleanup
No zeroed files remain in `build/packdata_resources/` -- normal builds unaffected.

## Test Instructions
1. Load `build/BUSIN0_EN_kanji_pages_wipe.iso` in PCSX2
2. Go to character creation (chargen)
3. Look at stat labels (STR, INT, PIE, VIT, AGI, LCK) and any kanji text

## Expected Outcomes
- **If stat labels DISAPPEAR**: These kanji font pages are the source.
  Next step: identify which specific resource(s) and render English labels.
- **If stat labels REMAIN**: The source is something else entirely
  (possibly hardcoded rendering, or a different resource not in this set).
- **If other kanji text disappears but stat labels remain**: The font pages
  serve different kanji, and stat labels use a separate mechanism.
