# R1188 Atlas Grid Analysis

**Date**: 2026-05-28
**Atlas**: `build/textures_to_edit/R1188_CORRECT_dbw512.png` (1024x1024, grayscale L mode)

---

## 1. Summary

**R1188 does NOT use a fixed-width cell grid.** Glyphs are proportionally spaced with
variable widths (7-24px). The game stores per-glyph UV coordinates in an EXE BSS table,
not in the atlas header. There is no simple `pixel_x = (index % cols) * cell_w` formula.

---

## 2. Row Height: 24px (fixed)

Row height is consistently 24 pixels across the entire atlas. Content rows begin at:

| Row | Y start | Content |
|-----|---------|---------|
| 0   | 0       | ASCII digits/punctuation: `5 6 7 8 9 : ; < = > ? A B C D E F G H I` |
| 1   | 24      | ASCII: `(C) a b c d e f g h i j k l m n o p q r s` |
| 2   | 48      | Kana + symbols: `X O X <- -> ...` + hiragana |
| 3   | 72      | Hiragana continued |
| 4   | 96      | Katakana: a-i-u-e-o line through wa-wo-n |
| 5   | 120     | Katakana continued |
| 6-41 | 144-984 | Kanji (36 rows) |

Gap rows exist as single empty scan lines between some rows (e.g., y=0, y=24, y=48, y=72
are gaps). In the kanji region (y=144+), there are 8 single-pixel gap rows at:
y=192, 216, 264, 336, 408, 528, 576, 840.

A 24px grid from y=0 covers all content rows with at most 1-2px offset.

---

## 3. Column Width: VARIABLE (proportional)

### Width Distribution (left half, 590 detected blobs)

| Width (px) | Count | Note |
|------------|-------|------|
| 7-10       | rare  | Narrow punctuation (period, comma, I) |
| 11-14      | 35    | Narrow Latin chars, small kana |
| 15-17      | 41    | Medium-width Latin/kana |
| 18-20      | 52    | Wide Latin/kana |
| 21-23      | 260   | **Most kanji** (mode = 23px, 22px) |
| 24         | 34    | Widest kanji |

Individual kanji are typically 21-23px wide, but many blobs appear wider because
adjacent kanji touch (no empty column between them):

| Blob width | Actual | Count |
|------------|--------|-------|
| 45-48 px   | 2 merged kanji | 78 |
| 70-72 px   | 3 merged kanji | 34 |
| 95 px      | 4 merged kanji | 8 |
| 120 px     | 5 merged kanji | 4 |

### Row 0 glyph start positions (demonstrating irregular spacing)

```
x=0, 21, 47, 69, 93, 120, 144, 161, 186, 210, 238, 282, 308, 332, 354, 379, 403, 427, 450, 478
Diffs: 21, 26, 22, 24, 27, 24, 17, 25, 24, 28, 44, 26, 24, 22, 25, 24, 24, 23, 28
```

No tested cell width (12, 16, 20, 22, 23, 24, 25, 26) produces aligned residuals.

---

## 4. Glyphs Per Row

| Section | Rows | Chars/row | Total |
|---------|------|-----------|-------|
| ASCII+kana (rows 0-5) | 6 | 20-21 | 125 |
| Kanji (rows 6-41) | 36 | 21 | 756 |
| **Total left half** | 42 | - | **881** |

Every kanji row contains exactly 21 characters (verified against the character-by-character
transcription in `r1188_label_coordinates.md`).

---

## 5. Left Half vs Right Half

### Left half (x=0 to ~495): Main glyph region
- 881 glyphs arranged in 42 rows of 20-21 chars
- Full-size rendering (~18-24px wide, 24px tall)
- Clean, well-formed proportional characters

### Right half (x=512 to 1023): Secondary/smaller font
- Rows 0-6 (y=0-166): Scattered small ASCII/symbol characters with ~22px row height
  but significant deswizzle artifacts and irregularity
- Rows 7+ (y=167-1007): Densely packed content (kanji at smaller size)
  - Virtually NO empty columns between characters
  - Each 24px row strip is one continuous blob of pixels
  - Pixel density is high (~8000-9000 non-zero pixels per 24px row)
- **Not usable as a regular grid** -- characters blend into each other

---

## 6. Grid Formula Attempts

### Fixed cell_w x cell_h = FAILED

| Tested (cols x cell) | Result |
|---------------------|--------|
| 21 x 24 (match R1272) | 21*24=504 > 496px left half width; residuals don't align |
| 20 x 24 | Residuals don't align |
| 24 x 24 | Residuals don't align |
| 16 x 24 | Residuals don't align |

**No fixed-column grid formula maps glyph indices to pixel positions.**

### Group+Index encoding (glyph IDs 6400+)

Per the EXE analysis in `r1188_sprite_metadata.md`:

```c
uint8 group = glyph_id >> 8;     // e.g., 0x19 = 25
uint8 index = glyph_id & 0xFF;   // e.g., 0x00-0x0C

// BSS table at 0x4EB100: stride 8 per group
uint32 texpage = *(uint32*)(0x4EB100 + group*8);
uint32 uv_base = *(uint32*)(0x4EB104 + group*8);

// Per-glyph UV: 8 bytes per glyph
uint8 U = uv_base[index*8 + 0];  // U coordinate (0-255)
uint8 V = uv_base[index*8 + 1];  // V coordinate (0-255)
```

This confirms there is **no grid formula**. Each glyph has an explicit (U, V) pair stored
in the EXE's runtime BSS memory (populated at load time, not in the atlas file).

The UV coordinates address a 256x256 sub-atlas window (since U and V are single bytes).

---

## 7. Per-Glyph Metadata in R1188 Header

The R1188 header contains 416 bytes of metadata at offset 0xA60-0xBFF labeled as
"per-glyph rendering metadata" in `r1188_sprite_metadata.md`. However, this data is:
- Mostly structured as 4-byte values
- Contains color/palette setup data (CLUT-related), not UV coordinates
- NOT a per-glyph UV table (too small: 416 bytes / 8 bytes per glyph = only 52 entries,
  but the atlas contains 881+ glyphs)

The actual UV mapping is stored in the EXE BSS and populated at runtime.

---

## 8. Actionable Conclusions

1. **R1188 CANNOT be edited by simple cell replacement.** Unlike R1272 (which has a clean
   12x12 fixed grid), R1188's proportional layout requires either:
   - Rewriting the UV table in the EXE BSS (complex, requires runtime patching)
   - PCSX2 texture hash replacement (already implemented in `patch_r1188_direct.py`)
   - Full atlas re-rendering with matching proportional layout

2. **For English translation**, the most practical approach remains:
   - Use `patch_r1188_direct.py` for PCSX2 texture replacement
   - Or patch the EXE to redirect glyph lookups to R1272 (which already has English)

3. **The 24px row height is reliable** -- any atlas editing should preserve this.

4. **21 glyphs per row is reliable** for kanji rows (6-41), but the column positions
   within each row are not regular.
