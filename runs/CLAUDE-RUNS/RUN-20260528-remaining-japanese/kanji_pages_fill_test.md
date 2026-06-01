# Kanji Font Page Fill Test

**Date:** 2026-05-28  
**ISO:** `build/BUSIN0_EN_all_kanji_fill.iso`  
**Script:** `build/kanji_fill_test.py`

## Purpose

Identify which PACKDATA resources provide the kanji glyphs used on the chargen
stat label screen (and elsewhere). All suspected kanji font page resources are
filled with solid 0xFF blocks simultaneously. If every kanji on-screen becomes
a solid block, these resources are confirmed as the font source.

## Resources Filled

| Resource | File                  | Size (bytes) | Notes                    |
|----------|-----------------------|-------------|--------------------------|
| R1269    | 1269_type01.raw       | 264,192     | Kanji page (large)       |
| R1270    | 1270_type01.raw       | 133,120     | Kanji page (small)       |
| R1271    | 1271_type01.raw       | 133,120     | Kanji page (small)       |
| R1273    | 1273_type01.raw       | 133,120     | Kanji page (small)       |
| R1274    | 1274_type01.raw       | 264,192     | Kanji page (large)       |
| R1275    | 1275_type01.raw       | 264,192     | Kanji page (large)       |
| R1276    | 1276_type01.raw       | 264,192     | Kanji page (large)       |
| R1303    | 1303_type01.raw       | 264,192     | Kanji page (large)       |

**Not included:** R1272 (this is the halfwidth/ASCII font atlas, already patched
with English glyphs in normal builds).

**R1188** was also NOT filled -- it is the name-entry keyboard atlas, not a
general kanji font page.

## Fill Method

Each resource was filled entirely with 0xFF bytes (every pixel = white/solid).
No header preservation was attempted since type01 resources are raw pixel data
without sub-headers.

## How to Interpret Results

1. **Boot the ISO** in PCSX2 and navigate to character creation (chargen).
2. Look at the stat labels (STR, INT, PIE, VIT, AGI, LCK area -- the original
   Japanese labels like 力, 信仰, etc.)
3. Check ALL kanji visible on screen.

### Outcome A: ALL kanji are solid blocks
- Confirmed: R1269-R1276 + R1303 are the complete kanji font source.
- Next step: identify WHICH specific resource contains the chargen stat kanji
  by filling one at a time.

### Outcome B: Some kanji remain normal
- There are additional font sources beyond these 8 resources.
- The kanji that remain normal come from a different resource.
- Investigate: R1188, R1272, or other resources.

### Outcome C: Game crashes or glitches
- The 0xFF fill may have corrupted expected structure.
- The PACKDATA grew by +165,888 bytes vs original (due to rounding differences).
  This could cause issues if the ISO extent is size-limited.

## Build Details

- PACKDATA size: 839,827,456 bytes (original: 839,661,568, diff: +165,888)
- ISO size: 1,274,544,128 bytes
- 58 total resources patched (8 kanji fills + 50 existing translation patches)
- Cleanup: all kanji fills removed from `build/packdata_resources/` after ISO
  was built, so normal builds are unaffected.
