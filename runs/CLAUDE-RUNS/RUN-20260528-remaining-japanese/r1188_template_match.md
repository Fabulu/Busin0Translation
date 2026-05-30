# R1188 Atlas Template Matching Results

**Date**: 2026-05-28

## Objective

Find the exact pixel coordinates where each PCSX2-dumped tab/stat label appears in the deswizzled R1188 atlas (`build/textures_to_edit/R1188_CORRECT_dbw512.png`).

## Method

- Atlas: `R1188_CORRECT_dbw512.png` (1024x1024, grayscale, 16 levels: 0,17,34,...,255)
- Dumps: 16 PNG files with CLUT `3cb39bf7659ef15f` from `build/pcsx2_dumps/`
- Template data is in the **alpha channel** (RGB=255,255,255), alpha range 0-128 with 16 levels
- Both 4bpp index space and atlas grayscale space were tested
- Matching methods: Normalized Cross-Correlation (NCC) and Sum of Squared Differences (SSD)

## Result: NO MATCHES FOUND

Template matching failed for all 16 dumps. The best NCC score was 0.577 (needs >0.95 for a real match). The best SSD average pixel difference was 4.2 out of 15 levels.

### What Was Tried

1. **Full atlas NCC** -- all 16 scores below 0.58 (POOR)
2. **Full atlas SSD** in 4bpp index space -- best avg pixel diff = 4.2/15
3. **256x256 sub-region matching** (16 quadrants of the 1024x1024 atlas) -- no improvement
4. **Proper CLUT mapping** (dump alpha levels [0,11,19,...,128] mapped to atlas gray [0,17,34,...,255] via shared 4bpp index) -- same poor results
5. **Raw R1188 byte stream search** for distinctive 8-pixel subsequences -- 0 matches found
6. **Cross-atlas search** against R1272, R1189, R1192, R1215, R1216, R1900, R2118 -- no matches in any texture

## Root Cause

The deswizzled R1188 atlas does NOT correctly represent the VRAM region from which the game reads these labels. From the existing analysis (`find_tab_label_atlas.md`):

> "R1188 has NOT been successfully deswizzled. All attempts with the VRAM simulation deswizzler using dbw_ct32 values of 64, 128, 256, 512, and 1024 produced garbled output."

The R1188_CORRECT_dbw512.png **does** contain valid-looking Japanese glyphs (variable-width characters in rows), but they are in the wrong arrangement. The game uses 17 different TEX0 configurations to read sub-regions of R1188's VRAM at runtime, and our deswizzle does not reconstruct the correct pixel layout for the 256x256 PSMT4 sub-region at page 0x2214.

## NCC Scores (for reference)

| # | Dump Hash | Size | Best (x,y) | NCC Score |
|---|-----------|------|-----------|-----------|
| 1 | `16625baf9feaeafb` | 48x20 | (335, 800) | 0.411 |
| 2 | `19a39fbc8a08d7ec` | 48x20 | (159, 30) | 0.388 |
| 3 | `1f839869fab251d` | 48x20 | (462, 27) | 0.393 |
| 4 | `280ea82c1c476a98` | 64x16 | (471, 1) | 0.577 |
| 5 | `4841ef9a2dc4981` | 64x16 | (457, 5) | 0.362 |
| 6 | `5d0c6327e20384e7` | 64x16 | (453, 265) | 0.326 |
| 7 | `6f1fb24fad5cd1a` | 48x20 | (159, 30) | 0.439 |
| 8 | `88ff8b577084a2a8` | 48x20 | (309, 8) | 0.423 |
| 9 | `9677cb23da53ff88` | 48x20 | (159, 28) | 0.448 |
| 10 | `9bec87b4031a7172` | 48x20 | (356, 30) | 0.443 |
| 11 | `aa43f966ad69195e` | 64x16 | (457, 5) | 0.315 |
| 12 | `bb20512b10c3128b` | 64x16 | (448, 168) | 0.303 |
| 13 | `c89b469f7a152a6` | 48x20 | (46, 31) | 0.424 |
| 14 | `d09a04bdfaf715bc` | 40x24 | (42, 74) | 0.439 |
| 15 | `d455234204274c43` | 64x16 | (459, 3) | 0.425 |
| 16 | `f2013a64642252e3` | 64x16 | (452, 770) | 0.385 |

## PCSX2 Dump Content (ASCII Art)

### Tab Labels (48x20)

All have Japanese kanji/kana in the alpha channel. These are character creation and status screen UI labels like: カナ, かな, 英数, 記号, 性別, 種族, 職業, 幸運度, 敏捷度, etc.

### Stat Labels (64x16)

Six contain Japanese text, one (`f2013a64642252e3`) contains **Latin text** -- appears to be something like "ATTRIBUTE" rendered in a proportional font.

### Other (40x24)

One dump (`d09a04bdfaf715bc`) contains 2 large kanji.

## Recommendations

Since template matching against the current deswizzled atlas cannot work, the viable paths forward are:

1. **PCSX2 texture replacement** -- Inject English labels directly using PCSX2's texture replacement feature, keyed by CLUT hash `3cb39bf7659ef15f` and TEX0 hash per dump. This bypasses atlas coordinates entirely and works immediately.

2. **Fix the R1188 deswizzle** -- Reverse-engineer the EXE's DMA upload code for R1188 to find the correct BITBLTBUF/TRXREG parameters, then re-deswizzle the raw data.

3. **VRAM dump approach** -- Use PCSX2's GS debugger to capture the actual 256x256 texture page at address 0x2214 from VRAM at runtime, producing a correctly-arranged atlas to match against.

## Key Files

- Deswizzled atlas: `build/textures_to_edit/R1188_CORRECT_dbw512.png`
- PCSX2 dumps: `build/pcsx2_dumps/*3cb39bf7659ef15f*`
- Prior analysis: `runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/find_tab_label_atlas.md`
- R1188 raw: `extracted/packdata_raw/1188_type01.raw`
