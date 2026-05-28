# RUN: VWF Implementation + Texture Deswizzle
**Date**: 2026-05-28
**Build**: v10 (BUSIN0_EN_v10.iso)

## Primary Goals
1. Fix text truncation by finding and patching the character-per-line/display limit
2. Complete PSMT8 texture deswizzle for ISO-based texture replacement
3. Integrate pending translations (R1347-R1355, overflow fixes)

## Current State
- X-advance patched 24→14 (text is smaller, CONFIRMED working)
- BUT truncation persists at same character count (~22 chars)
- Truncation is NOT pixel-based (smaller font still truncates same)
- Truncation is NOT from DISPLAY_TEXT GLYPH_COUNT (verified correct)
- FontDisp max comes from struct+0x20 (runtime value, not constant)
- Display buffer is 14 entries × 12 bytes = 168 bytes
- slti 32 checks exist in func_302DB0
- No li+sw pattern found setting struct+0x20 to a small value

## Key Files
- runs/exe_constants_found.md — all EXE constants catalogued
- runs/exe_reverse_engineering.md — full reverse engineering notes
- build/BUSIN0_EN_v10.iso — current test build
- tools/patch_section1_offsets.py — Section 1 opcode patcher
- build/pcsx2_dumps/ — 411 ground truth texture PNGs
