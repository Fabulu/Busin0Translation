# Font Atlas Format Mismatch -- Definitive Analysis

**Date:** 2026-05-28
**Files compared:**
- Original: `extracted/packdata_raw/1272_type01.raw` (67,584 bytes)
- Atlas:    `build/english_font_atlas.bin` (82,176 bytes)

## File Structure

| Component   | Original (R1272)          | Our Atlas                 |
|-------------|---------------------------|---------------------------|
| Wrapper     | 16-byte raw header        | (none)                    |
| GS Header   | 192 bytes                 | 192 bytes (copied from original) |
| Pixel data  | 65,536 bytes (256x512 4bpp) | 81,920 bytes (256x640 4bpp) |
| Palette     | 64 bytes                  | 64 bytes (copied from original) |
| Extra       | 1,776 bytes               | (none)                    |

## THE BUG: Pixel Layout Mismatch

### Original R1272: LINEAR layout
```
byte_offset = (y * 256 + x) / 2     (width = 256, simple raster order)
```

### Our Atlas: PAGE-BASED layout  
```
page_idx    = (y / 128) * 2 + (x / 128)
pixel_offset = page_idx * 16384 + (y % 128) * 128 + (x % 128)
byte_offset  = pixel_offset / 2
```

These are **completely different mappings.** For pixel (5, 5):
- Linear byte offset:  642
- Page byte offset:    322

They **never agree** for y > 0.

## Proof: Glyph 346 (col=10, row=16, pixel origin 120,192)

Reading original pixels with LINEAR layout (correct):
```
y 0: f f f f c e 6 9 f f f f    <-- coherent Japanese character
y 1: e f c e a c 7 a f d d b
y 4: f f e f c d 5 9 f f f f
y 5: f f c e a c 8 a e d d b
y 8: f f f e d b 9 2 f f f f
y 9: f f e e c c a a d e a b
```

Reading original pixels with PAGE layout (wrong -- what our code assumes):
```
y 0: f f f f f f f f c a 9 5    <-- scrambled, pixels shifted
y 3: f f f f f f c e 9 8 7 8
y 4: e c f f f f f f f f f f    <-- cell straddles x=128 page boundary
y 7: f f f f 9 2 d b f f f f
```

The page layout scrambles the glyph because the 12-pixel-wide cell at x=120..131
straddles the 128-pixel page boundary, splitting it across two different pages.

## Why Some English Glyphs Appear to Work

They don't work correctly either. When the game reads the texture, it reads from
LINEAR byte positions, but our 'A' (glyph 33) was written to PAGE byte positions.
The game reads transparent pixels (0xF) where 'A' should be, and reads displaced
garbage where it expects other glyphs.

Any English text appearing on screen either:
1. Comes from a different mechanism (not this atlas)
2. Is coincidentally landing near the right spot for very small y values
3. Is being read through the GS hardware's own address mapping which may partially compensate

## Page Boundary Crossing Glyphs

33 glyphs fall in column 10 (x=120..131) and straddle the 128-pixel page boundary.
These are completely broken in the page layout because the left 8 pixels map to
page N and the right 4 pixels map to page N+1.

Affected glyph IDs: 10, 31, 52, 73, 94, 115, 136, 157, 178, 199, 220, 241, 262,
283, 304, 325, **346**, 367, 388, 409, 430, 451, 472, 493, 514, 535, 556, 577,
598, 619, 640, 661, 682.

## The Fix

In `tools/generate_font_atlas.py`, replace the page-based pixel packing (lines 117-150)
with simple linear packing:

```python
# Linear layout, width=256, 4bpp
pixel_data_size = ATLAS_W * ATLAS_H // 2
pixel_data = bytearray(b'\xff' * pixel_data_size)  # all transparent

for y in range(ATLAS_H):
    for x in range(ATLAS_W):
        val = atlas_pixels[y * ATLAS_W + x]
        game_val = 15 - min(val * 15 // 255, 15)
        pixel_offset = y * ATLAS_W + x
        byte_offset = pixel_offset // 2
        if pixel_offset % 2 == 0:
            pixel_data[byte_offset] = (pixel_data[byte_offset] & 0xF0) | (game_val & 0x0F)
        else:
            pixel_data[byte_offset] = (pixel_data[byte_offset] & 0x0F) | ((game_val & 0x0F) << 4)
```

This produces pixel data in the same linear format as the original R1272,
which is what the game engine expects.

## Byte-Level XOR Summary

Comparing first 65,536 bytes of pixel data (original vs atlas):
- 45,933 bytes match (70.1%)
- 19,603 bytes differ (29.9%)
- Match rate decreases from ~90% at low addresses to ~55% at high addresses,
  consistent with increasing displacement between linear and page layouts.
