# PSMT4 Deswizzle v2: FINDINGS

**Date:** 2026-05-22
**Status:** COMPLETE - Font atlas correctly deswizzled

---

## Key Discovery: Linear Page Rendering

The PSMT4 font atlas data is stored **linearly within each 128x128 page**. No block or column table rearrangement is needed for extraction. Each page of 8192 bytes represents 128x128 pixels at 4bpp in simple row-major order (64 bytes per row, lo nibble first).

For the 256x512 texture:
- 2 page columns x 4 page rows = 8 pages
- Pages arranged row-major: page 0 = top-left, page 1 = top-right, etc.
- Each page rendered at 128px width, placed side by side

### Why the PCSX2 Column Table Does NOT Apply Here

The PCSX2 `columnTable4[16][32]` and `blockTable4[8][4]` tables define how the GS hardware maps texture pixel coordinates `(x, y)` to VRAM byte addresses. This mapping is used at **texture read time** by the GS rasterizer.

However, the font atlas file data is NOT a raw VRAM dump. It is the **GIF IMAGE transfer source data** that gets uploaded to VRAM. The GIF IMAGE transfer writes this linear source data into VRAM, applying the PSMT4 swizzle during the upload. The result in VRAM is swizzled, but the file data itself is linear.

When extracting the texture from the file, we read the source data directly -- no deswizzle needed beyond simple page arrangement.

### Evidence

1. **128px-wide linear render shows perfect characters:** Rendering the raw data at 128 pixels per row (one PSMT4 page width) produces clearly readable Japanese characters in a regular grid.

2. **Block table makes things worse:** Applying the PSMT4 block table to rearrange 32x16 blocks introduced skewing artifacts on odd-page-indexed columns.

3. **Column table makes things much worse:** Applying the full PSMT4 column table spread characters horizontally and introduced heavy checkerboard patterns, because it separated lo/hi nibbles within each byte into positions 16 pixels apart.

4. **Raw byte analysis confirms linear storage:** Within each 256-byte segment, pixel data flows continuously -- adjacent bytes encode adjacent pixel pairs, and rows follow sequentially at 64-byte stride (128 pixels at 4bpp).

---

## Output Files

- `tools/psmt4_deswizzle_v2.py` - The deswizzle script
- `dumps/font_renders/font_atlas_deswizzled_correct.png` - 256x512 inverted grayscale
- `dumps/font_renders/font_atlas_deswizzled_correct_2x.png` - 512x1024 zoomed version

## File Format Summary

```
Offset  Size    Description
0x000   192     Header (GIF tags + GS register setup)
0x050   8       TEX0: PSM=0x14(PSMT4), TW=8(256px), TH=9(512px), TBW=4
0x0C0   64      Palette: 16 RGBA32 entries (all white - grayscale font)
0x100   65536   Pixel data: 8 pages of 8192 bytes each, linear 4bpp
```

## Algorithm

```python
for each page (py=0..3, px=0..1):
    page_idx = py * 2 + px
    page_offset = page_idx * 8192
    for each pixel in 128x128 page:
        byte_idx = page_offset + (local_y * 128 + local_x) // 2
        nibble_pos = (local_y * 128 + local_x) & 1
        pixel_value = lo_nibble if nibble_pos==0 else hi_nibble
        output[py*128+local_y][px*128+local_x] = pixel_value
```

## Character Grid

The font atlas contains approximately 858 Japanese glyphs (katakana, hiragana, kanji, numbers, punctuation, Latin letters). Characters appear to be approximately 12x12 pixels in a regular grid, yielding roughly 10-11 characters per 128-pixel page row.

## Implications for Translation

For font replacement/translation:
1. Read the file, skip 256-byte header
2. Modify pixel data as linear 4bpp at 128px page width
3. Write back with the same header
4. No swizzle/re-swizzle needed -- the GIF IMAGE transfer handles VRAM layout
