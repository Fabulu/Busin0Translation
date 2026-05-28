# Recon 42: All Character Input Tab Tables

**Date:** 2026-05-22
**EXE:** `C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78`
**Output:** `C:/Programmieren/wizardrytranslation/data/all_tab_mappings.json`

---

## Overview

The name entry screen has 4 tabs. All table data resides in the EXE at virtual addresses 0x4C9670-0x4CA900. The data is organized as:

1. Tab label glyph definitions (0x4C9670-0x4C9920)
2. Pointer table to label glyphs (0x4C9930-0x4C9990)
3. Header entry with glyph 0x04A8 (0x4C99A0-0x4C99B7)
4. Hiragana main grid cells (0x4C99B8-0x4C9AA7)
5. Katakana main grid cells (0x4C9AB0-0x4C9CCF)
6. Special character grid cells (0x4C9CE0-0x4CA607)
7. European/alphanumeric grid indices (0x4CA608-0x4CA6EF)
8. Control/navigation entries (0x4CA6F0-0x4CA70F)
9. Glyph pair table (0x4CA710-0x4CA8CF)
10. Additional glyph pair tables (0x4CA8D0+)

---

## Table Formats

### 6-Variant Cell Format (Hiragana + Katakana grids)

Each cell stores 6 uint16 glyph IDs representing the same character at 6 different font sizes/styles. The 6 variants are spaced by 57 (0x39) in glyph ID space. Only the **base glyph** (first value) is needed to identify the character.

- Hiragana: 16-byte stride (6 uint16 + 4 bytes padding) for individually coded cells
- Katakana: 12-byte stride (6 uint16, no padding) in 8-column rows of 96 bytes

### Pair Cell Format (Special characters)

Each cell is 4 bytes: `(uint16 glyph_id, uint16 zero)` or `(0xFFFF, 0xFFFF)` for empty.

### Grid Index Format (European)

Simple array of uint16 glyph indices. `0x3C` = blank/space cell, `0xFFFF` = disabled.

---

## Tab 0: Katakana (confirmed)

**Main grid start:** `0x4C9AB0`
**Format:** 7 rows of 8 cells, 12-byte stride (6 uint16 per cell)

| Row | Cols | Base Glyphs | Notes |
|-----|------|-------------|-------|
| 0 | 8 (col7 empty) | 0x62-0x68 | ア行 (a-ki) |
| 1 | 8 (col7 empty) | 0x69-0x6F | ク行 (ku-chi?) |
| 2 | 8 (col7 empty) | 0x70-0x76 | ... |
| 3 | 8 (col7 empty) | 0x77-0x7D | ... |
| 4 | 7 (col6 empty) | 0x82-0x87, 0xFA | Extended row |
| 5 | 7 (col7 empty) | 0x88-0x8E | Extended row (dakuten) |
| 6 (dakuten) | 8 | 0x88-0x8E, 0x86 | Variant with dakuten |

**Special characters section start:** `0x4C9CE0`
- 200 pair-format cells covering glyph ranges:
  - 0x0019-0x0024: Small kana / special marks
  - 0x0072: Additional mark
  - 0x1900-0x190C: Katakana dakuten/combo group 1
  - 0x1A00-0x1A0C: Group 2
  - 0x1B00-0x1B0C: Group 3
  - 0x1C00-0x1C0C: Group 4
  - 0x1D00-0x1D0C: Group 5
  - 0x1E00-0x1E0F: Group 6
  - 0x1F00-0x1F0C: Group 7
  - 0x2000-0x200C: Group 8
  - 0x2100-0x210C: Group 9
  - 0x2200-0x220C: Group 10
  - 0x2300-0x230C: Group 11
  - 0x2400-0x240C: Group 12
- 66 non-empty cells total

---

## Tab 1: Hiragana

**Start:** `0x4C99B8`
**Format:** 15 individually addressed 6-variant cells

| Index | Address | Base Glyph | Decimal |
|-------|---------|-----------|---------|
| 0 | 0x4C99B8 | 0x56 | 86 |
| 1 | 0x4C99C8 | 0x57 | 87 |
| 2 | 0x4C99D8 | 0x58 | 88 |
| 3 | 0x4C99E8 | 0x59 | 89 |
| 4 | 0x4C99F8 | 0x5A | 90 |
| 5 | 0x4C9A08 | 0x5B | 91 |
| 6 | 0x4C9A18 | 0x5C | 92 |
| 7 | 0x4C9A30 | 0x5D | 93 |
| 8 | 0x4C9A3C | 0x5E | 94 |
| 9 | 0x4C9A50 | 0x7E | 126 |
| 10 | 0x4C9A5C | 0x7F | 127 |
| 11 | 0x4C9A68 | 0x80 | 128 |
| 12 | 0x4C9A78 | 0x81 | 129 |
| 13 | 0x4C9A88 | 0x5F | 95 |
| 14 | 0x4C9A98 | 0x60 | 96 |

Base glyph range: 0x56-0x60 (11 glyphs) and 0x7E-0x81 (4 glyphs) = 15 total.

**Note:** The hiragana section likely shares the same special character grid as katakana (dakuten variants, small kana). The 15 base cells represent the "clean" hiragana characters. The full hiragana tab on screen has many more characters including dakuten/handakuten rows which are generated from the special character grid section.

---

## Tab 2: European/Alphanumeric

**Full grid:** `0x4CA610` (6 rows x 10 columns)
**Reduced grid:** `0x4CA680` (6 rows x 10 columns)

### Full Grid (56 characters + 4 blanks)

Grid indices 0x00-0x37 arranged in 6 rows of 10:

```
Row 0: 00 01 02 03 04 05 06 07 08 09
Row 1: 0A 0B 0C 0D 0E 0F 10 11 12 13
Row 2: 14 15 16 17 18 19 1A 1B 1C 1D
Row 3: 1E 1F 20 21 22 23 24 25 26 27
Row 4: 28 29 2A 2B 2C 2D 2E 2F 30 31
Row 5: 32 33 34 35 36 37 __ __ __ __
```

Expected character mapping (indices 0-55):
- 0x00-0x05: First 6 characters (possibly space + punctuation?)
- 0x06-0x1F: A-Z (26 uppercase letters, indices 6-31)
- 0x20-0x23: a-d? or more uppercase?
- 0x2D-0x37: 0-9 or digits (11 values)
- 0x3C: Blank/space cell marker

### Reduced Grid (uppercase + digits only)

```
Row 0: __ __ __ __ __ __ 06 07 08 09   (A B C D)
Row 1: 0A 0B 0C 0D 0E 0F 10 11 12 13   (E-N)
Row 2: 14 15 16 17 18 19 1A 1B 1C 1D   (O-X)
Row 3: 1E 1F 20 21 22 23 __ __ __ __   (Y Z + 4 more)
Row 4: __ __ __ __ __ 2D 2E 2F 30 31   (digits 0-4)
Row 5: 32 33 34 35 36 37 00 02 01 FF   (digits 5-9 + controls)
```

The reduced grid starts at index 0x06 (likely 'A') and includes indices through 0x23 (30 values for A-Z + some extras), then digits 0x2D-0x37 (11 values for 0-9 + something).

---

## Tab 3: Symbols

The symbols tab (記号) appears to share the special character grid with the katakana tab, using glyph ranges 0x1900-0x2400. These 66 non-empty cells in the pair-format section at 0x4C9CE0 are organized into 13 groups (0x19xx through 0x24xx), each with up to 13 glyphs (0x00-0x0C suffix).

The symbols likely include:
- Japanese punctuation (。、「」etc.)
- Mathematical symbols
- Special marks (★、♪、♂♀ etc.)
- Brackets and other symbols

---

## Tab Label Glyphs

22 label glyph entries at 0x4C9670-0x4C9910, each 32 bytes:
- Glyphs 0x04A9-0x04BE (22 entries)
- Each has the structure: `{glyph_id, 0, glyph_id, 0, glyph_id+1, 0, 0, 0, ...}`
- Pointer table at 0x4C9930 references these in a specific order

The label glyphs correspond to the visual labels shown on the character selection grid (row/column headers like ア, カ, サ, etc.).

---

## Glyph Pair Table

At `0x4CA714`: 109 entries of `(0x0000, glyph_id)` where glyph_id ranges from 0x04BF to 0x04F4. Each glyph appears twice in the table (likely normal + highlighted state). These are related to the character input UI elements.

---

## Key Findings

1. **The 4 tabs share some data structures.** The hiragana and katakana tabs use the 6-variant cell format (3 or 6 font size variants per character). The special characters / dakuten / symbols section at 0x4C9CE0 is shared between tabs.

2. **Katakana main grid is at 0x4C9AB0** (confirmed) with 7 rows of 8 cells. Each cell has 6 font-size variant glyph IDs spaced by 57.

3. **Hiragana cells start at 0x4C99B8** with 15 individually-addressed cells (16-byte stride for the first group, then variable).

4. **European grids use simple glyph index arrays.** Full grid at 0x4CA610 (56 chars in 6x10), reduced grid at 0x4CA680 (uppercase + digits only).

5. **The symbols tab reuses the special character grid** from 0x4C9CE0 with 66 non-empty cells covering glyph ranges 0x1900-0x2400.

6. **Font variant spacing is always 57 (0x39)** for the hiragana/katakana grids. This means the font atlas has 6 copies of each kana at different sizes, spaced 57 glyphs apart.

7. **The European grid index-to-character mapping needs to be determined** from the actual font atlas or save state analysis. The indices 0x06-0x1F likely map to A-Z, and 0x2D-0x37 likely map to 0-9.

---

## Files

- **JSON output:** `C:/Programmieren/wizardrytranslation/data/all_tab_mappings.json`
- **EXE file:** `C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78`
- **Key addresses:**
  - Tab label glyphs: 0x4C9670
  - Pointer table: 0x4C9930
  - Table header: 0x4C99A0
  - Hiragana cells: 0x4C99B8
  - Katakana grid: 0x4C9AB0
  - Special/symbols grid: 0x4C9CE0
  - European full grid: 0x4CA610
  - European reduced grid: 0x4CA680
  - Glyph pair table: 0x4CA714
