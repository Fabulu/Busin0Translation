# R1272 Nuclear Wipe Test

**Date:** 2026-05-28
**ISO:** `build/BUSIN0_EN_r1272_wipe.iso`

## What Was Done

Zeroed ALL pixel data in resource R1272 (index 1272, type01) to determine
whether R1272 exclusively handles dialogue font rendering vs stat labels.

### R1272 Structure (67,584 bytes = 33 sectors)
- Bytes 0..15: Sub-header (16 bytes) -- PRESERVED
  - `00000000 00010100 10000000 00000000`
  - sub[1] = 65,792 = payload size
- Bytes 16..65807: Payload (65,792 bytes) -- ZEROED
  - Originally: ~160 bytes GS register setup + 65,536 bytes pixel data (256x256 8bpp font atlas)
  - Now: all zeros (no GS transfer, no texture)
- Bytes 65808..67583: Sector padding (1,776 bytes) -- already zeros

### Build Process
1. Created zeroed R1272 in `build/packdata_resources/1272_type01.raw`
2. Rebuilt `build/PACKDATA_r1272_wipe.DIG` using ONLY the zeroed R1272 (no other mods)
3. Injected into copy of original ISO at LBA 16029
4. No EXE patches applied (vanilla EXE, only PACKDATA modified)

## Expected Results

### If R1272 is the ONLY dialogue font atlas:
- **Dialogue text:** DISAPPEARS completely (no glyphs to render)
- **Stat labels (HP, MP, STR, etc.):** STILL VISIBLE (sourced from R1188 or other resource)
- **Menu labels:** Depends on source -- may or may not be affected

### If R1272 is used for ALL text (dialogue + stats):
- **All text disappears** -- stats, menus, dialogue, everything

### If game crashes:
- The zeroed GS registers may cause a GIF transfer error
- If so, the GS header should be preserved in a follow-up test

## Test Instructions

1. Load `build/BUSIN0_EN_r1272_wipe.iso` in PCSX2
2. Start game, enter a save with characters (to see stat screens)
3. Check:
   - [ ] Does dialogue text appear? (expect: NO)
   - [ ] Do stat labels appear? (expect: YES if R1188 handles them)
   - [ ] Do menu labels appear? (note which ones)
   - [ ] Does the game crash? (note when/where)
4. Take screenshots of key screens

## Results

*(Fill in after testing)*

- Game boots: 
- Title screen text: 
- Menu text visible: 
- Stat labels visible: 
- Dialogue text visible: 
- Crashes: 
- Conclusion: 
