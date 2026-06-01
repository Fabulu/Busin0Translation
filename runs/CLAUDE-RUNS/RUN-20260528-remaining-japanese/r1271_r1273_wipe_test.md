# R1271 + R1273 Nuclear Wipe Test

**Date:** 2026-05-28
**ISO:** `build/BUSIN0_EN_r1271_r1273_wipe.iso`

## What Was Done

Zeroed ALL pixel data in resources R1271 and R1273 simultaneously to determine
what these two textures render in-game.

### File Structure (both identical: 133,120 bytes each)

- Bytes 0..15: Sub-header (16 bytes) -- PRESERVED
  - `00000000 C0040200 10000000 00000000`
  - sub[1] = 0x204C0 = 132,288 = payload size
- Bytes 16..132303: Payload (132,288 bytes) -- ZEROED
  - GS register setup + pixel data (PSMT8 texture atlas)
- Bytes 132304..133119: Sector padding (816 bytes) -- already zeros

### Format Details

- Type: type01 (raw GS transfer)
- Pixel format: PSMT8 (8-bit indexed, 256-color palette)
- Both files had byte-identical headers, suggesting paired/mirrored atlases

### Build Process

1. Created zeroed R1271 + R1273 in `build/packdata_resources/`
2. Built full v9 ISO (all other patches applied: translations, R1188, EXE, etc.)
3. Copied to `build/BUSIN0_EN_r1271_r1273_wipe.iso`
4. Removed wiped resource files from `build/packdata_resources/`

## Expected Results

### If R1271/R1273 are font atlases:
- Text rendered from these atlases will DISAPPEAR
- Text from other atlases (R1188, R1272) will remain visible

### If R1271/R1273 are UI/menu texture atlases:
- Menu backgrounds, borders, or button graphics will vanish
- Text may still appear if sourced from separate font resources

### If R1271/R1273 are dungeon/battle textures:
- Specific visual elements in dungeon crawling or battle scenes will disappear

### If game crashes:
- The zeroed GS registers may cause a GIF transfer error
- If so, preserve the GS header portion in a follow-up test

## Test Instructions

1. Load `build/BUSIN0_EN_r1271_r1273_wipe.iso` in PCSX2
2. Start game, navigate through menus, enter dungeon, trigger battles
3. Check:
   - [ ] Which visual elements disappeared?
   - [ ] Does dialogue text still appear?
   - [ ] Do stat labels / menu labels still appear?
   - [ ] Are dungeon textures affected?
   - [ ] Are battle UI elements affected?
   - [ ] Does the game crash? (note when/where)
4. Take screenshots of affected screens
5. Compare with R1272 wipe test to determine which atlas handles what
