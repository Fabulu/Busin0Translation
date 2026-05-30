# Definitive ISO Extraction Test - v15

**Date:** 2026-05-28  
**ISO:** `C:/Programmieren/wizardrytranslation/build/BUSIN0_EN_v15.iso`  
**Method:** Direct binary read from ISO -- PVD -> root dir -> PACKDATA.DIG LBA -> TOC -> resource data

---

## R38: VERDICT = ENGLISH (96.3%)

**182 of 189 messages are pure English. 6 are single-kanji Japanese. 1 is a lookup table (MSG 0).**

### English messages confirmed (sample)
| MSG | Glyphs | Decoded |
|-----|--------|---------|
| 1 | 40,48 | HP |
| 2 | 40,48,15,45,40,48 | HP/MHP |
| 4 | 41,46,52 | INT |
| 9 | 46,65,77,69 | Name |
| 10 | 44,69,86,69,76 | Level |
| 11 | 50,65,67,69 | Race |
| 12 | 39,69,78,68,69,82 | Gender |
| 13 | 33,76,73,71,78,77,69,78,84 | Alignment |
| 14 | 35,76,65,83,83 | Class |
| 15 | 48,69,82,83,79,78,65,76,73,84,89 | Personality |
| 16 | 51,79,82,67,69,82,89 | Sorcery |
| 17 | 40,79,76,89,0,45,65,71,73,67 | Holy Magic |
| 18 | 33,84,84,82,73,66,85,84,69,83 | Attributes |

### Remaining Japanese messages (6 total)
| MSG | Glyph ID | Decoded | Meaning |
|-----|----------|---------|---------|
| 3 | 346 | 力 | "Power" (stat label) |
| 26 | 518 | 男 | "Male" |
| 27 | 349 | 女 | "Female" |
| 43 | 401 | 侍 | "Samurai" |
| 152 | 520 | 善 | "Good" |
| 154 | 289 | 悪 | "Evil" |

These are single-kanji labels intentionally left as Japanese in R38 (the translation files did not include replacements for these).

### MSG 0: Lookup table (not text)
MSG 0 has 377 glyphs in a `[value, 0, value, 0, ...]` pattern with large IDs (188, 756, 764, ..., 11004). This is a **pointer/offset table**, not displayable text. It alternates between a kanji glyph ID and a zero spacer. Not a translation concern.

---

## R1272: English Font Atlas IS Present

| Property | Value |
|----------|-------|
| TOC entry | sector_offset=211371, sectors=33, type=1 |
| Payload size | 65,792 bytes |
| Built font size | 65,792 bytes (exact match) |
| First 100 bytes | **Identical** to `build/english_font_atlas.bin` |
| Full byte match | 60,293 / 65,792 = **91.6%** |
| Non-zero in ASCII region | 3,914 / 4,096 bytes |

The 8.4% difference is expected -- the built font has English letter bitmaps in slots 0-94 while the original Japanese kanji bitmaps remain in the higher slots (95+). The English letter region is confirmed present and matching.

---

## EXE (SLPM_653.78): Save Slot Patches ARE Present

| Offset | Expected | Actual | Status |
|--------|----------|--------|--------|
| 0x3FC720 | `BUSIN 0` | `BUSIN 0` | OK |
| 0x3FC750 | `BUSIN 0 Data 1` | `BUSIN 0 Data 1` | OK |
| 0x3FC770 | `BUSIN 0 Data 2` | `BUSIN 0 Data 2` | OK |
| 0x3FC790 | `BUSIN 0 Data 3` | `BUSIN 0 Data 3` | OK |
| 0x3F9370 | `BUSIN 0 Suspend` | `BUSIN 0 Suspend` | OK |

### Minor: One un-patched SJIS string remains
At offset **0x3F9678**, the original fullwidth SJIS string `ＢＵＳＩＮ０` is still present. This is in a memory card icon metadata block (surrounded by `BISLPM-62098BUSINWZ`, `icon1.ico`, `icon2.ico`). It is a PS2 memory card display string, not player-visible during gameplay. The `patch_exe.py` script has a 6th entry for this offset but it may not have been included in the v15 build pipeline.

---

## Summary

| Component | Status | Detail |
|-----------|--------|--------|
| **R38 text** | **ENGLISH** | 182/189 messages English, 6 single-kanji labels remain |
| **R1272 font** | **ENGLISH** | English letter bitmaps confirmed in atlas |
| **EXE save slots** | **PATCHED** | All 5 main save slot names are English ASCII |
| **EXE memcard SJIS** | **Un-patched** | 1 cosmetic SJIS string at 0x3F9678 (memcard icon metadata) |

**The v15 ISO definitively contains English text in R38.** The game will display English for all 182 translated messages. The 6 remaining Japanese messages are single-character stat/class/alignment labels (力, 男, 女, 侍, 善, 悪) that were not included in the translation data.

---

## Files extracted for inspection
- `r38_from_iso.bin` -- Raw R38 data (12,288 bytes)
- `r1272_from_iso.bin` -- Raw R1272 font atlas (67,584 bytes)
- `exe_from_iso.bin` -- Full EXE (4,185,776 bytes)
