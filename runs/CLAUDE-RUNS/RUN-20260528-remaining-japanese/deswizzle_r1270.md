# Deswizzle R1270 Results

**Date**: 2026-05-28

---

## Result: R1270 is NOT a kanji font page

R1270 (133,120 bytes, PSMT8 256x512) is an **environment/character portrait texture**, NOT a kanji font page. Deswizzling with multiple `dbw_ct32` values (64, 128, 256) all produce portrait-like images showing two humanoid figures (possibly NPC portraits).

### Evidence

1. **Visual**: All deswizzle attempts show organic shapes (torso, head, clothing), not a grid of kanji bitmaps
2. **Palette**: Full-color RGBA palette (earthy skin tones: R=214/G=172/B=163, etc.), NOT a monochrome font palette
3. **Pixel distribution**: 47.3% non-zero in body -- consistent with a portrait (fonts have much higher zero ratios)
4. **First non-zero pixel**: Offset 19,859 (0x4D93) -- first ~18KB are blank (portrait with transparent background on top)
5. **Confirmed by font_pages_analysis.md**: "R1304-R1311 are NOT kanji font pages" and the table at 0x3CA968 is "a general texture resource loading list unrelated to fonts"

### Images Generated

| File | Description |
|------|-------------|
| `R1270_raw_no_deswizzle.png` | Raw bytes as pixels, no deswizzle |
| `R1270_raw_grayscale.png` | Raw as grayscale |
| `R1270_deswizzle_dbw64.png` | Deswizzled, dbw=64 |
| `R1270_deswizzle_dbw64_gray.png` | Deswizzled, dbw=64, grayscale |
| `R1270_deswizzle_dbw128.png` | Deswizzled, dbw=128 (best portrait) |
| `R1270_deswizzle_dbw128_gray.png` | Deswizzled, dbw=128, grayscale |
| `R1270_deswizzle_dbw256.png` | Deswizzled, dbw=256 |
| `R1270_deswizzle_dbw256_gray.png` | Deswizzled, dbw=256, grayscale |

### GS Register Analysis

R1270's header contains register writes for texture rendering setup (TEX0, TEX1, CLAMP, FRAME, MIPTBP), but NO image transfer registers (BITBLTBUF/TRXREG/TRXDIR). The game uploads pixel data programmatically.

| Register | Value | Decoded |
|----------|-------|---------|
| TEX0_1 (0x06) | 0x2000000661310000 | TBP0=0, TBW=4, PSM=19(PSMT8), TW=8(256), TH=9(512) |
| TEX1_1 (0x14) | 0x0000000000000000 | Default |
| CLAMP_1 (0x08) | 0x0000000000000005 | Clamp mode |
| FRAME_1 (0x4C) | 0x0000000002000100 | FBP=256, FBW=0, PSM=2 |
| MIPTBP1_1 (0x34) | 0x0040000400008000 | Mipmap config |

---

## The Actual Kanji Font System

Per `font_pages_analysis.md`, the game uses exactly TWO font atlas resources:

| Resource | Format | Dimensions | Role |
|----------|--------|------------|------|
| **R1188** | PSMT4 | 1024x1024 | All kanji, kana, symbols, stat labels, UI labels |
| **R1272** | PSMT4 | 256x512 | ASCII/Latin characters (our English replacement) |

Stat labels (STR, INT, etc.) are rendered as glyph tiles from **R1188**, not R1270. To replace kanji with English letters, **edit R1188 directly** -- the deswizzle/reswizzle toolchain already exists (`psmt4_deswizzle.py`), and the atlas has been successfully exported as `R1188_CORRECT_dbw512.png`.

### Corrected Table Entry

The earlier `glyph_range_dispatch.md` incorrectly listed R1270 as page 92 in the font tile system. The table at EXE offset 0x3CA968 is a general texture resource loading list, NOT a font page table. The actual font page system uses the page table at 0x3DB180 with cell data pointing into R1188's VRAM space.

---

## Conclusion

R1270 cannot be used for kanji editing because it is not a font resource. To edit specific kanji for the translation, edit **R1188** (the 1024x1024 PSMT4 kanji atlas) using the existing `psmt4_deswizzle.py` toolchain.
