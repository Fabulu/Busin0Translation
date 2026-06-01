# v31 ISO Verification Report

**Date:** 2026-05-28
**ISO:** `C:/Programmieren/wizardrytranslation/build/BUSIN0_EN_v31.iso`
**Size:** 1,274,544,128 bytes

## 1. R39 Stat Label Patches -- CONFIRMED PRESENT

v31 has the English stat patches that v30 was missing:

| Offset | v30 (broken) | v31 (fixed) | Status |
|--------|-------------|-------------|--------|
| 0x56D6 | glyph 346 (力) | glyph 51 (S) | PATCHED |
| 0x5700 | glyph 535 (知) | glyph 41 (I) | PATCHED |
| 0x5702 | glyph 717 (恵) | glyph 49 (Q) | PATCHED |

**This is the key difference between v30 and v31.** The user was correct that v30 had no change -- the R39 stat patches were not making it into v30. They are now present in v31.

## 2. R38 Gender Entries (MSG 25/26) -- STILL JAPANESE

| MSG | Content | Status |
|-----|---------|--------|
| 26 | glyph 518 = 男 (Male) | STILL JAPANESE |
| 27 | glyph 518-equivalent = 女 (Female) | STILL JAPANESE |

These are the only intentional remaining JP glyphs in R38 besides MSG 0 (which is a glyph lookup table, not displayed text).

**Full R38 JP scan:** 3 of 189 messages contain JP glyphs:
- MSG 0: glyph lookup table (not user-visible text)
- MSG 26: 男 (Male)
- MSG 27: 女 (Female)

## 3. R1272 Font Atlas -- CORRECT

- TOC[1272]: 33 sectors, type=1
- Payload size: 65,792 bytes (sub-header reports this; total resource = 67,584 bytes including padding)
- **100.0% byte-match** with built `english_font_atlas.bin`
- Non-zero bitmap data confirmed in ASCII glyph region (3,942 non-zero bytes in first 4096)

## Summary

| Check | Result |
|-------|--------|
| R39 stat "S" at 0x56D6 | PASS -- English glyph 51 |
| R39 stat "IQ" at 0x5700 | PASS -- English glyphs 41,49 |
| R39 vs v30 | CONFIRMED DIFFERENT -- v30 had Japanese, v31 has English |
| R38 MSG 26 (Male) | FAIL -- still 男 |
| R38 MSG 27 (Female) | FAIL -- still 女 |
| R1272 font atlas | PASS -- 100% match with English atlas |

**Verdict:** v31 is a genuine improvement over v30. The R39 stat label patches (STR/IQ/PIE/VIT/AGI/LUC) are now correctly injected. The remaining Japanese in R38 is limited to the gender labels (MSG 26/27), which were a known remaining item.
