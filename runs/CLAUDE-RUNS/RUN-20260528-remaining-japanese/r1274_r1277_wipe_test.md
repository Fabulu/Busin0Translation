# R1274-R1277 Pixel Wipe Test

**Date:** 2026-05-28
**ISO:** `build/BUSIN0_EN_r1274_r1277_wipe.iso`

## What was done

Wiped pixel data in resources R1274, R1275, R1276, R1277 to identify what they render in-game.

- All four files: 264,192 bytes each, type-01 (PSMT8 texture)
- Structure: 2,048-byte GS header (0x000-0x7FF) + 262,144-byte pixel region (0x800-end)
- Header preserved intact; pixel data zeroed from offset 0x800 onwards
- Built into ISO via `build_v9.py`

## Testing checklist

- [ ] Boot ISO in PCSX2
- [ ] Check title screen / menus for missing textures
- [ ] Check dungeon exploration for missing textures
- [ ] Check battle scenes for missing textures
- [ ] Note which visual element(s) disappear -- that identifies what R1274-R1277 contain

## Files

| Resource | Source | Size | Action |
|----------|--------|------|--------|
| R1274 | `extracted/packdata_raw/1274_type01.raw` | 264,192 | pixels zeroed |
| R1275 | `extracted/packdata_raw/1275_type01.raw` | 264,192 | pixels zeroed |
| R1276 | `extracted/packdata_raw/1276_type01.raw` | 264,192 | pixels zeroed |
| R1277 | `extracted/packdata_raw/1277_type01.raw` | 264,192 | pixels zeroed |

## Cleanup

Temporary wiped `.raw` files removed from `build/packdata_resources/` after ISO build.
