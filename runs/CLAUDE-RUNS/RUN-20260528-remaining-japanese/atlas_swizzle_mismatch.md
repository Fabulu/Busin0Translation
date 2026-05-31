# Atlas Swizzle Mismatch: CONFIRMED AND FIXED

## Hypothesis
`generate_font_atlas.py` writes R1272 atlas data in LINEAR page layout, but the
game expects PSMT4-swizzled (PSMCT32 upload format) data. Glyph tiles at higher
positions (95+) land at WRONG byte offsets, explaining why stat labels at slots
346, 535, 717 show Japanese instead of English.

## Verdict: CONFIRMED

### Evidence

1. **Original R1272 IS swizzled.** Round-trip test (deswizzle then re-swizzle)
   produces an EXACT byte-for-byte match with the original 65,536 bytes of pixel
   data. This proves the on-disc format is PSMT4/PSMCT32 swizzled.

2. **Our generator WAS writing LINEAR data.** The old code used a "page layout"
   (128x128 pages tiled 2 columns wide) with linear byte ordering within each
   page. Comparing our output against `swizzle_psmt4(our_linear_data)` showed
   **10,840 bytes differing** out of 65,536.

3. **Page layout != simple linear.** For a 256-wide texture, the page layout puts
   pixel (128,0) at byte offset 8192 instead of 64. Out of 131,072 pixel
   positions, **130,048 are at different offsets** between page-layout and
   simple-linear ordering. Neither matches the swizzled format the game expects.

4. **Early slots appeared to work by accident.** Slots 0-94 (y=0..53) all fall
   within the first 128x128 page's first ~54 rows. Within a single page, the
   block/column swizzle moves pixels around, but for the first few rows the
   transparent background (all 0xFF bytes) masks the byte-ordering difference.
   Higher slots (y > ~96) cross block boundaries where the swizzle divergence
   becomes visible.

### Byte layout comparison

| Format | Pixel (0,0) byte offset | Pixel (128,0) byte offset | Pixel (0,128) byte offset |
|--------|------------------------|--------------------------|--------------------------|
| Simple linear | 0 | 64 | 16384 |
| Page layout (old generator) | 0 | 8192 | 16384 |
| PSMT4 swizzled (game expects) | via block+column tables | via block+column tables | via block+column tables |

## Fix Applied

**File:** `tools/generate_font_atlas.py`

**Change:** Replaced the linear page-layout 4bpp pixel packing (lines 114-150)
with:

1. Build a simple linear pixel array (1 byte per pixel, values 0-15) at
   page-aligned dimensions (256 x 640, rounded up from 256 x 540).
2. Call `swizzle_psmt4()` from `psmt4_deswizzle.py` to convert to PSMCT32
   upload format.
3. Write the swizzled bytes as the pixel data section of the .bin file.

Also moved the `from psmt4_deswizzle import swizzle_psmt4` import to the top of
the file to avoid `sys.stdout` wrapper conflicts.

### Verification

- **Round-trip test PASSES:** deswizzle(our_swizzled_output) then re-swizzle
  reproduces exact bytes.
- **Glyph content at high slots verified:** Slots 346, 535, 683, 700, 717 all
  show correct English glyph content when deswizzled.
- **Output size:** 82,176 bytes (192 header + 81,920 pixel data + 64 palette),
  same as before.

## Impact

This fix should resolve ALL remaining cases where glyph tiles at positions 95+
display as Japanese on the PS2 (or display garbage). Menu stat labels, item
descriptions, and any text using high glyph slots should now render correctly
with the English font atlas.
