# R1272 Fill Test -- Solid Block Verification

## Purpose

Determine if R1272 is the source for chargen stat labels and/or menu buttons
by filling ALL pixel data with 0x88 (solid blocks). If those UI elements
become solid blocks in-game, R1272 IS their source.

## What Was Done

1. Read original R1272 (`extracted/packdata_raw/1272_type01.raw`, 67,584 bytes)
2. Preserved all non-pixel data:
   - Sub-header: bytes 0x000-0x00F (16 bytes)
   - GIF packet header: bytes 0x010-0x0BF (192 bytes)
   - CLUT/palette: bytes 0x100C0-end (1,856 bytes)
3. Filled pixel data (bytes 0x0C0-0x100BF, 65,536 bytes) with 0x88
4. Patched into a copy of `build/PACKDATA.DIG` at sector offset 211367 (33 sectors)
5. Injected patched PACKDATA into source ISO

## Output

- **ISO**: `build/BUSIN0_EN_r1272_fill_test.iso` (1,274,544,128 bytes)
- Based on the latest `build/PACKDATA.DIG` (which has all current translations injected)
- Only R1272 was modified; all other resources are from the latest build

## Verification

- Header bytes unchanged (confirmed match with original)
- All 65,536 pixel bytes confirmed as 0x88 in final ISO
- Palette bytes unchanged (confirmed match with original)

## How to Test

Boot the ISO in PCSX2 and check:

1. **Chargen stat labels** (STR, INT, PIE, VIT, AGI, LUK) -- if solid blocks, R1272 is the source
2. **Menu buttons** (equip, status, etc.) -- if solid blocks, R1272 is the source
3. **Message text** -- should also be solid blocks (R1272 is the known font atlas for MSG text)
4. **Name entry grid** -- check if affected

## Expected Results

- If R1272 is the ONLY font source: ALL text and labels become solid blocks
- If stat labels / menu buttons remain readable: they use a DIFFERENT resource (likely R1188 or baked EXE textures)
- Partial corruption = R1272 supplies some but not all UI text

## Notes

- 0x88 in PSMT4 4bpp format = nibbles 0x8,0x8 = palette index 8 for both pixels
- Palette index 8 in the original grayscale ramp is a mid-gray value
- Result: visible solid gray rectangles where glyphs normally appear
