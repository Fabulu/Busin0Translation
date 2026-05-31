# v28 R1272 Font Atlas Verification

**Date:** 2026-05-28
**ISO:** `build/BUSIN0_EN_v28.iso` (1,274,544,128 bytes)

## 1. R1272 Presence in ISO

- **PACKDATA.DIG** found at ISO LBA 16029
- **R1272 TOC entry:** sector_offset=211364, sector_count=33, type_code=1
- **R1272 size in ISO:** 67,584 bytes (33 sectors x 2048)
- **Original R1272 size:** 67,584 bytes -- **SAME SIZE**
- **Patched R1272 size:** 67,584 bytes -- **SAME SIZE**

**Result:** ISO R1272 matches the patched version byte-for-byte.
The game should accept this resource since it is the exact same size as the original.

## 2. Byte-Level Comparison

| Comparison | Differences |
|---|---|
| ISO vs Patched (build/packdata_resources) | **0** (identical) |
| ISO vs Original (extracted/packdata_raw) | **19,390 bytes differ** in pixel data |

**Conclusion:** The v28 ISO definitively contains our English font atlas, not the original Japanese one.

## 3. Swizzle Fix Verification

Deswizzled the R1272 pixel data from the ISO using PSMT4 deswizzle.
The deswizzled image (`build/v28_r1272_deswizzled.png`) shows:

- **Top rows:** Clear English ASCII characters (A-Z, a-z, 0-9, punctuation)
- **Swizzle is correct:** Letters are readable and properly positioned in the grid

### Key Glyph Checks

| Slot | Character | Pixel Fill | Status |
|---|---|---|---|
| 33 | A | 15% (22/144) | HAS CONTENT |
| 34 | B | 19% (27/144) | HAS CONTENT |
| 58 | Z | 12% (17/144) | HAS CONTENT |
| 65 | a | 13% (19/144) | HAS CONTENT |
| 90 | z | 10% (15/144) | HAS CONTENT |
| 16 | 0 | 19% (27/144) | HAS CONTENT |
| 25 | 9 | 17% (24/144) | HAS CONTENT |
| 0 | (space) | 0% (0/144) | EMPTY (correct) |
| 1 | ! | 8% (12/144) | HAS CONTENT |

All English letter slots have rendered content. Space slot is correctly empty.

## 4. Menu Button Tiles (683-866)

- **143 / 184** menu tile slots have content
- The 41 empty slots are expected (not all menu labels use all slots)
- Sample checks:
  - Slot 683: HAS CONTENT (25% fill)
  - Slot 700: HAS CONTENT (19% fill)
  - Slot 866: HAS CONTENT (21% fill)

## 5. Visual Confirmation

The deswizzled preview image confirms:
- Row 0-4: Full English ASCII character set rendered in Consolas font
- Lower rows: Menu tile text fragments (guild, shop, quest, party, etc.)
- No Japanese glyphs visible in the English character range
- Glyph grid alignment is correct (12x12 cells, 21 columns)

## 6. Will the Game Load It?

**YES -- with high confidence.** Reasons:

1. R1272 is **exactly the same size** (67,584 bytes / 33 sectors) as the original
2. The 16-byte resource sub-header is preserved (`payload_size=65,792`)
3. The 192-byte GS/GIF header is preserved from the original
4. The 64-byte palette is preserved from the original
5. Only the pixel data (65,536 bytes) has been modified
6. The swizzle format matches what the game expects (PSMT4 via PSMCT32 upload)

The previous v27 builds that used an **extended** atlas (larger than original) were rejected.
v28 keeps the original 256x512 dimensions and original file size, which the game's
resource loader should accept without issue.
