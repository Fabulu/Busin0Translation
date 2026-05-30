# Font Atlas Verification Report (v18 Build)

Date: 2026-05-28

## Summary

**ALL CHECKS PASSED.** The 184 English menu font tiles in R1272 are correctly
built and injected into the v18 ISO.

---

## 1. Atlas Binary Structure

File: `build/english_font_atlas.bin` (65,792 bytes)

| Component     | Size (bytes) | Status  |
|---------------|-------------|---------|
| Header        | 192         | MATCH - preserved from original R1272 |
| 4bpp pixel data | 65,536    | OK - 256x512 atlas, 8 pages of 128x128 |
| Palette       | 64          | MATCH - preserved from original R1272 |

The header and palette are byte-identical to the original
`extracted/packdata_resources/1272_type01.bin`.

## 2. Glyph Rendering Verification

### Uppercase A-Z (slots 33-58)
- **26/26** characters have visible foreground pixels.
- Visually confirmed in `build/english_font_atlas_preview.png`: clean Consolas
  10pt bitmaps, properly centered in 12x12 cells.

### Lowercase a-z (slots 65-90)
- **26/26** characters have visible foreground pixels.
- Visually confirmed in preview PNG.

### Digits, punctuation, symbols
- Rows 1-5 of the preview show `! " # $ % & ' ( ) * + , - . / 0 1 2 3 4`
  through `t u v w x y z { | } ~` -- all rendering correctly.

### Menu tiles (slots 683-866)
- **184 total tile slots** defined in `data/menu_labels.csv` (92 active label
  pairs, each using 2 glyph slots).
- **155 tiles** have visible foreground pixels.
- **29 tiles** are intentionally empty (tile_2 of abbreviated short words like
  "HP", "MP", "ATK" where the full label fits in tile_1).
- Visually confirmed in preview PNG bottom section: menu labels like "town",
  "guild", "shop", "inn", "quest", "party", etc. are visible.

## 3. ISO Injection Verification

### R1272 in v18 ISO
- PACKDATA.DIG extent: sector 16029
- R1272 TOC entry: sector_offset=211369, sector_count=33, type_code=1
- Sub-header: zero1=0, payload_size=65792, stride=16, zero2=0

### Binary comparison
- **ISO R1272 == build/packdata_resources/1272_type01.raw**: BYTE-IDENTICAL
- **Atlas payload in ISO == build/english_font_atlas.bin**: BYTE-IDENTICAL

The font atlas is correctly embedded at byte offset 16 within R1272, exactly
where the game engine expects to find it.

## 4. Pipeline Code Review

### `tools/generate_font_atlas.py`
- Renders ASCII glyphs using Consolas 10pt into a 256x512 grayscale image.
- Calls `render_menu_tiles.load_menu_tiles()` to inject 184 menu tile bitmaps
  into slots 683-866.
- Converts to 4bpp game format: 0=opaque text, 15=transparent background.
- Assembles: original_header(192) + pixel_data(65536) + original_palette(64).
- Asserts output is exactly 65,792 bytes.

### `build/build_full_english_v2.py` (Step 3)
- Reads `build/english_font_atlas.bin` (65,792 bytes).
- Reads original `extracted/packdata_raw/1272_type01.raw` (67,584 bytes).
- Preserves original sub-header fields (zero1, stride, zero2).
- Sets payload_size = 65,792 (len of atlas bin).
- Assembles: sub_header(16) + atlas(65792) = 65,808, padded to 67,584 (33 sectors).
- Writes to `build/packdata_resources/1272_type01.raw`.

### Header preservation
- The sub-header (16 bytes: zero1, payload_size, stride, zero2) comes from the
  original raw file, with only payload_size updated.
- The atlas internal header (192 bytes) and palette (64 bytes) come from the
  original extracted resource -- they are NOT regenerated.
- This means TIM2/CLUT metadata is faithfully preserved.

## 5. Conclusion

The font atlas pipeline is working correctly end-to-end:

1. `generate_font_atlas.py` produces correct 4bpp pixel data with preserved
   header/palette from the original game resource.
2. `build_full_english_v2.py` correctly wraps the atlas in the resource
   sub-header format and injects it into the PACKDATA.DIG rebuild.
3. The v18 ISO contains byte-identical R1272 data.
4. All 26+26 ASCII letter glyphs and all 155 non-blank menu tiles render
   with visible foreground pixels.
5. The 29 empty menu tile slots are intentional (second tile of short labels).

**No issues found.**
