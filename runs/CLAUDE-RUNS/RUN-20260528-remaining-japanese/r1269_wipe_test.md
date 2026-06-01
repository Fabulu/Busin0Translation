# R1269 Wipe Test

**Date:** 2026-05-28
**ISO:** `build/BUSIN0_EN_r1269_wipe.iso`

## What was done

R1269 (264,192 bytes, PSMT8 512x512) pixel data was zeroed out to test whether
this font page provides the stat label kanji still visible in-game.

- **Header + palette preserved:** bytes 0x000-0x4BF (1,216 bytes)
- **Pixel data zeroed:** bytes 0x4C0-0x404BF (262,144 bytes = 512x512 @ 8bpp)
- **Trailing data preserved:** bytes 0x404C0-0x4083F (832 bytes)

## Build details

- Built via `build/build_v9.py` with wiped `1269_type01.raw` in `packdata_resources/`
- 60 resource overrides total (59 existing + 1 R1269 wipe)
- Wiped resource removed from `packdata_resources/` after build (cleanup)

## Test instructions

1. Boot `build/BUSIN0_EN_r1269_wipe.iso` in PCSX2
2. Check stat screens, equipment menus, spell lists -- anywhere kanji labels remain
3. If kanji disappear (become blank/invisible), they live on R1269
4. If kanji remain unchanged, they come from a different font page (R1270, R1271, etc.)

## Expected outcome

If R1269 is the source of remaining stat-label kanji, those characters will
render as blank (index 0 = transparent in palette). All English text and other
font pages should be unaffected.
