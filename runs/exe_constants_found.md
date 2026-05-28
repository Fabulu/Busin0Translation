# EXE Constant Search Results (2026-05-28)

## Constants in Text Renderer Area (file 0x200000-0x210000)

### li reg, 42 (atlas column count)
- 0x3061A8: addiu r2, r0, 42 (in func_3060B0 glyph renderer)
- 0x306F08: addiu r2, r0, 42 (in another renderer function)
- 0x30F070: addiu r7, r0, 42 (late renderer area)

### div-by-21 magic (0x30C30C31)
- 0x3061C0: lui r2, 0x30C3 (in func_3060B0, paired with ori 0x0C31)
- 0x306F20: lui r2, 0x30C3 (second instance)

### FFFE/FFFD/FFFF Control Code Handling (in func_302DB0)
- 0x302F70: ori r3, r0, 0xFFFE (page break)
- 0x302F78: ori r3, r0, 0xFFFD (line break)
- 0x302F88: ori r3, r0, 0xFFFD (duplicate)
- 0x302EF8: ori r3, r0, 0xFFFF (message end)

### FontDispSetCnt Max Check
- 0x305908: slt r2, r5, r6 (compare current count vs max)
- 0x30590C: bne r2, r0, 4 (if under max, skip error)
- 0x305910: lui r4, 0x004F (load "FontDispSetCnt Max Over" string)
- Max value comes from struct+0x20 (lw r5, 0x20($s5)) — RUNTIME, not hardcoded!

### slti Checks in func_302DB0
- 0x302EA8: slti r3, r6, 32 (character-related limit check)
- 0x302FD8: slti r3, r3, 32 (another 32-value check)
- NOTE: No slti with 21 or 42 found in this function!

### Buffer Size
- 0x305B2C: addiu r5, r0, 168 (buffer init, 168 bytes = 14 entries * 12 bytes)
- 0x305B60: addiu r5, r0, 168 (second init)

### X-Advance (ALREADY PATCHED in v10)
- 0x207A5C: addiu v0, v0, 24 → patched to 14 (FontDisp render 1)
- 0x208D30: addiu v0, v0, 24 → patched to 14 (FontDisp render 2)
- 0x209824: addiu v0, v0, 24 → patched to 14 (FontDisp render 3)

### Text Box Width Parameters (ALREADY PATCHED)
- 0x1F3524: addiu t1, zero, 100 → patched to 220 (small box)
- 0x1F3608: addiu t1, zero, 140 → patched to 255 (narration box)

## Key Architecture Understanding

1. Glyph Display Buffer: 14 slots × 12 bytes = 168 bytes
2. FontDispSetCnt max comes from struct+0x20 (runtime value, set during init)
3. The 42/21 constants are for ATLAS UV lookup, not display limits
4. The 14-slot buffer is the ANIMATION buffer (glyphs fade in one at a time)
5. slti 32 checks are for glyph ID range, not display count
6. The actual per-message glyph limit comes from the DISPLAY_TEXT opcode GLYPH_COUNT
7. Visual truncation at "deathly s" = ~22 chars despite smaller font = pixel width clipping

## Next Steps
- Find where struct+0x20 (FontDisp max count) is initialized
- Find the actual pixel-width clipping code (not the 100/140 text box params)
- The narration text box 140→255 patch may not affect the right rendering path
- Consider: the 14-slot animation buffer means only 14 glyphs visible at once?
  If glyphs fade in sequentially and the buffer recycles, total visible depends
  on animation timing, not buffer size
