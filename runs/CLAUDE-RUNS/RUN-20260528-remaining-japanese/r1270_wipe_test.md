# R1270 Wipe Test

**Date:** 2026-05-28
**ISO:** `build/BUSIN0_EN_r1270_wipe.iso`

## Purpose

Test whether R1270 provides kanji used in stat labels or other UI elements.
R1270 is one of the smaller kanji font pages (PSMT8, 133,120 bytes).

## R1270 Structure (parsed)

| Region      | Offset Range    | Size (bytes) | Contents                        |
|-------------|-----------------|-------------:|---------------------------------|
| Header      | 0x000 - 0x3FF   |        1,024 | Sub-header (16B) + GS registers (padded) |
| Pixel data  | 0x400 - 0x203FF |      131,072 | 256x512 PSMT8 glyph bitmaps    |
| Palette     | 0x20400 - 0x207FF |      1,024 | 256 RGBA entries                |

### GS Register Details
- **PSM:** 0x13 (PSMT8) -- 8-bit indexed color
- **Dimensions:** 256 x 512
- **TBP0:** 0, **TBW:** 4
- **TEX0:** 0x2000000661310000

## What Was Done

1. Zeroed ONLY the pixel data (0x400 - 0x203FF, 131,072 bytes)
2. Header and palette left intact (game can still load/reference the texture without crashing)
3. Built ISO with the wiped R1270 injected via `packdata_resources/`
4. Cleaned up after build (file auto-consumed by build script)

## What to Look For

Boot the ISO and check:
- **Stat labels** (STR, VIT, INT, PIE, etc.) -- do any kanji disappear?
- **Equipment screen** labels
- **Spell names** in menus
- **Item descriptions** with kanji
- **Battle UI** text
- Any blank squares or missing characters in the menus

If stat label kanji vanish, R1270 is confirmed as the source and we know exactly
which glyph indices to target for English replacement.

## Expected Outcome

If R1270 is a kanji font page used for stat labels, those labels will render as
blank/invisible where they previously showed kanji. Other text (from other font
pages) should be unaffected.
