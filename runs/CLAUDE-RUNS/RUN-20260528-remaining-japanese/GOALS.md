# RUN: Complete All Remaining Japanese Text
**Date**: 2026-05-28
**Build**: v11 (BUSIN0_EN_v11.iso) — WORKING, full English dialogue displays correctly

## Mission
Translate and patch ALL remaining Japanese text in the game. The core dialogue system works perfectly. Now we need to catch everything else: stat labels, menu buttons, UI textures, EXE-hardcoded text, location banners, and any other Japanese that appears anywhere in the game.

## What's Still Japanese (from screenshot analysis)

### On the chargen Status screen visible in the screenshot:
1. **新規登録** (top-left banner) = "New Registration" — CockpitImg texture R2121
2. **○ボタンか×ボタンをおすと最終確認へ移ります。** (top-right) = "Press O/X to confirm" — R37 msg 124 (NOW TRANSLATED in chunk_r37_extra.json, needs rebuild)
3. **力, 知恵, 信仰心, 生命力, 敏捷度, 幸運度** (stat labels left side) = STR, INT, FTH, VIT, AGI, LCK — These ARE in R38 but chargen reads from EXE table at 0x3C844A-0x3C8F64
4. **性別 男** = Gender Male — EXE hardcoded at 0x3C844A area
5. **種族** = Race — EXE hardcoded
6. **属性** = Alignment — EXE hardcoded
7. **職業** = Class — EXE hardcoded (but "Fighter" shows in English!)
8. **Personality description overflows** — needs 2-line max (FIXED in chunk_r38_fix.json)

### Other known remaining Japanese:
9. **Name entry tabs**: カナ, かな, 英数, 記号, 決定, 男名, 女名 — bitmap font glyphs (IDs 6400+) from font resources R0x04A4/R0x04A5
10. **Location banners**: 酒場 (Tavern) etc. — CockpitImg textures R2118-R2124
11. **Intro narration slideshow**: Pre-rendered TextEventImage textures in R1192, R2361
12. **Menu buttons**: Tavern request board, guild options — CockpitImg textures
13. **R39 equipment menus**: 481/565 messages still Japanese
14. **R1100-R1190 dialogue**: R1126 (171 lines), R1134 (110), R1148 (181), R1118 (22)
15. **Various gap resources**: R1347-R1355 (translated, needs rebuild integration)
16. **EXE save slot names**: Patched but not in ISO yet

## Categories of Work

### A. Already translated, just needs rebuild
- R37 extra translations (111 messages including confirm dialog)
- R38 STR label fix
- R38 personality descriptions shortened
- R1347-R1355 gap translations (131 messages)
- EXE save slot names

### B. Needs EXE patching (LE uint16 glyph ID tables)
- Chargen stat labels at 0x3C844A-0x3C8F64
- Menu label pair structs at 0x3C3026-0x3C5174
- Name entry grid labels
- Various other EXE tables (293 Japanese text tables found)

### C. Needs texture replacement (PSMT8 deswizzle/reswizzle)
- R2118-R2124: CockpitImg textures (tavern/guild backgrounds + buttons)
- R1192: Intro narration TextEventImage
- R2361: Ending narration TextEventImage
- 411 ground truth PNGs available in build/pcsx2_dumps/
- Deswizzle lookup table generated (1,282 data points)

### D. Needs new translations
- R1100-R1190 range (R1126, R1134, R1148, R1118)
- R39 remaining equipment text (481 messages)
- Any other resources discovered during testing

### E. Video text (if any)
- BSN2_0.DSI confirmed NO subtitles/text
- TextEvent overlays during video handled by MSG system (already translated)
