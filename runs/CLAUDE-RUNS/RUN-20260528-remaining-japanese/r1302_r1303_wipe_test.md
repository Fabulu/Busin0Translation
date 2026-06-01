# R1302 + R1303 Wipe Test

**Date:** 2026-05-28
**ISO:** `build/BUSIN0_EN_r1302_r1303_wipe.iso`

## Purpose

Determine what visual elements R1302 and R1303 provide by wiping their pixel
data. Both are PSMT8 textures (8-bit indexed color, 264,192 bytes each).

## What Was Done

Both R1302 (`1302_type01.raw`) and R1303 (`1303_type01.raw`) had their pixel
data zeroed while preserving the GS/TIM header.

### Byte Layout (each file)

| Region       | Offset        | Size          | Action     |
|--------------|---------------|---------------|------------|
| Header       | 0 - 2047      | 2,048 bytes   | PRESERVED  |
| Pixel data   | 2048 - 264191 | 262,144 bytes | ZEROED     |

- Format: PSMT8 (8bpp indexed), likely 512x512
- Total file size: 264,192 bytes (unchanged)

### Build Details

- Resources placed in `build/packdata_resources/` as `1302_type01.raw` and
  `1303_type01.raw` with zeroed pixel data
- Built via `python build/build_v9.py`
- Both wiped resources included among 54 total resource files in PACKDATA
- PACKDATA size: 839,849,984 bytes (same as standard v9 build)
- ISO size: 1,020,264,448 bytes
- Wiped resource files cleaned up after build

## How to Test

1. Load `build/BUSIN0_EN_r1302_r1303_wipe.iso` in PCSX2
2. Play through various screens: title, menus, dungeon, battle, shops
3. Note any missing textures, blank areas, or visual artifacts
4. Compare against the standard v9 ISO to identify differences

## Interpreting Results

### If something disappears:
- That visual element comes from R1302 or R1303
- To distinguish which, repeat the test wiping only one at a time

### If nothing changes:
- R1302 and R1303 may not be loaded in the tested areas
- Try additional game areas (different dungeons, cutscenes, etc.)
