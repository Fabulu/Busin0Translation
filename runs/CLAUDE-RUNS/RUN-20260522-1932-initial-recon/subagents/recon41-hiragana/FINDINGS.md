# Hiragana Name Entry Table -- Findings

## Location

The hiragana character mapping table is at **RAM 0x004C99B8**, immediately before the katakana table at 0x004C9AB0. It spans from 0x004C99B8 to 0x004C9AA4 (approximately 236 bytes with variable padding between entries).

## Structure

The table has **15 entries** (rows), each containing **6 uint16 glyph IDs** (12 bytes of data). Entries are separated by variable-length zero padding (not a uniform stride). The 6 glyph IDs per row follow a **stride-57 pattern**: `val[n] = base + n * 57`.

### Entry Addresses and Values

| Row | RAM Address  | Glyph IDs                     | Code Case |
|-----|-------------|-------------------------------|-----------|
| 0   | 0x004C99B8  | 86, 143, 200, 257, 314, 371  | $a1=0     |
| 1   | 0x004C99C8  | 87, 144, 201, 258, 315, 372  | $a1=1     |
| 2   | 0x004C99D8  | 88, 145, 202, 259, 316, 373  | $a1=2     |
| 3   | 0x004C99E8  | 89, 146, 203, 260, 317, 374  | $a1=3     |
| 4   | 0x004C99F8  | 90, 147, 204, 261, 318, 375  | $a1=4     |
| 5   | 0x004C9A08  | 91, 148, 205, 262, 319, 376  | $a1=5     |
| 6   | 0x004C9A18  | 92, 149, 206, 263, 320, 377  | $a1=6     |
| 7   | 0x004C9A30  | 93, 150, 207, 264, 321, 378  | $a1=7 (a) |
| 8   | 0x004C9A3C  | 94, 151, 208, 265, 322, 379  | $a1=7 (b) |
| 9   | 0x004C9A50  | 126, 183, 240, 297, 354, 411 | $a1=0xA (a) |
| 10  | 0x004C9A5C  | 127, 184, 241, 298, 355, 412 | $a1=0xA (b) |
| 11  | 0x004C9A68  | 128, 185, 242, 299, 356, 413 | $a1=0xA (c) |
| 12  | 0x004C9A78  | 129, 186, 243, 300, 357, 414 | extra     |
| 13  | 0x004C9A88  | 95, 152, 209, 266, 323, 380  | extra     |
| 14  | 0x004C9A98  | 96, 153, 210, 267, 324, 381  | extra     |

## Interpretation of the 6 Values Per Row

There are two competing interpretations:

### Interpretation A: 6 size variants of the SAME character (15 unique hiragana)
- katakana_mapping.json maps all 6 stride-57 values to the same character
  (e.g., 98/155/212/269/326/383 all map to "ア")
- This would mean only 15 unique hiragana characters, which seems too few
- Page-0 glyph IDs: 86-96, 126-129

### Interpretation B: 6 DIFFERENT characters per row (90 grid positions)
- The rendering code at 0x002F53F0 loops through all 6 values (s1=0..5) and
  calls a position function (0x001C1DC0) with different index each time
- The position function loads screen coordinates from a lookup table at 0x00542748
- This means each of the 6 values is rendered at a different screen position
- However, katakana_mapping.json explicitly says all 6 are the same character

### Resolution
The most likely explanation is that **Interpretation A is correct** -- the 6 values
are the same character at 6 different font sizes/resolutions, and the rendering code
draws the same character at multiple positions for different UI contexts (e.g.,
large selected, small in grid, preview in name field, etc.). The position function
returns coordinates for each rendering context, not grid cell positions.

This gives **15 unique hiragana page-0 glyph IDs**: 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 126, 127, 128, 129.

However, this seems like too few for a complete hiragana character set. The katakana table similarly has only 41 unique page-0 glyphs (98-135, 250-256), which is also fewer than the 46 basic katakana. Some characters may be absent from the name entry grid.

## Rendering Code

The hiragana rendering is dispatched through a switch statement at **0x002F5380** in the EE RAM. The switch variable is `$a1` (register), which selects different grid rows:

- `$a1=0` through `$a1=6`: individual hiragana rows 0-6
- `$a1=7`: two sub-rows (rows 7-8)
- `$a1=0xA`: three sub-rows (rows 9-11)
- `$a1=0xC`: appears to be another tab
- `$a1=0xD`: **katakana tab** (uses table at 0x004C9AB0)
- `$a1=0xE`: another tab

## Key Observations

1. The hiragana table (0x4C99B8) is **IDENTICAL** between both save states (katakana-tab-active and hiragana-tab-active). The table is static data, not dynamic.

2. No pointers to the table were found in RAM -- addresses are **hardcoded** as MIPS `lui`/`addiu` pairs in the executable code.

3. The hiragana page-0 glyph IDs (86-96, 126-129) are **non-overlapping** with katakana page-0 IDs (98-135, 250-256). They are adjacent ranges in the font atlas.

4. The gap between 96 and 126 (glyphs 97-125) contains the start of the katakana range (98-125). Glyphs 126-129 appear after the first katakana block, suggesting the font atlas interleaves some hiragana characters within the katakana range.

## Output Files

- `data/hiragana_glyph_map.json` -- complete grid data with all 90 glyph IDs and their grid positions
