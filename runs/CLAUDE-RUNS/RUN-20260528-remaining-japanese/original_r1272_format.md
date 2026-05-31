# R1272 Font Atlas Byte Format Analysis

## Definitive Answer

**The original R1272 pixel data is in PSMCT32 upload format** -- swizzled for
host-to-GS transfer using PSMCT32 IMAGE mode, to be stored in VRAM and read
back as PSMT4 texture data by the GPU.

It is NOT linear, and NOT in PSMT4 VRAM layout directly.

## Evidence

### 1. Deswizzle produces clean glyph grid

Applying `deswizzle_psmt4()` (PSMCT32 write + PSMT4 read simulation) with
`dbw_ct32=256` produces a clean, organized Japanese glyph grid.
Roundtrip (deswizzle then re-swizzle) passes with **exact byte match**.

### 2. Linear interpretation produces garbage

Reading the original pixel data as simple linear 4bpp (256 pixels wide, no
swizzle) produces a garbled, scrambled image with no recognizable glyphs.

### 3. GIF header confirms upload path

The `.bin` header at offset `0x50` contains TEX0_1:
- TBP0=0, TBW=4, PSM=20 (PSMT4), TW=8 (256px), TH=9 (512px)

TRXDIR at offset `0x90` = 1 (host->GS upload), confirming this is a
PSMCT32 IMAGE transfer to VRAM.

### 4. Gradient test: deswizzle is NOT identity

A synthetic gradient pattern deswizzled with the same parameters shows only
6.2% of pixels match -- the swizzle transformation is highly non-trivial.

## File Structure

### Original R1272 `.raw` (67,584 bytes)
```
Offset  Size    Content
0x000   16      Sub-header (h0=0, payload_size=65792, h2=0x10, h3=0)
0x010   192     GIF packet header (TEX0, CLAMP, TEX1, MIPTBP1, BITBLTBUF, TRXREG, TRXDIR)
0x0C0   65,536  Pixel data (PSMCT32 upload format, 4bpp, 256x512)
0x100C0 64      CLUT/palette (16 RGBA colors, grayscale ramp)
--- file ends at 0x10800 (67,584) ---
Note: 1,776 bytes of trailing data exist beyond declared payload_size
```

### Original R1272 `.bin` (65,792 bytes = raw payload without 16-byte sub-header)
```
Offset  Size    Content
0x000   192     GIF packet header
0x0C0   65,536  Pixel data (PSMCT32 upload format)
0x100C0 64      CLUT/palette
```

### English font atlas `.bin` (82,176 bytes)
```
Offset  Size    Content
0x000   192     GIF header (copied from original, TH patched 9->10)
0x0C0   81,920  Pixel data (LINEAR 128x128 page layout - NOT PSMCT32!)
0x140C0 64      "Palette" (all 0xFF - copied from wrong offset in original)
```

## Format Mismatch Bug

**`generate_font_atlas.py` writes pixel data in LINEAR 128x128 page layout, but
the game expects PSMCT32 upload format.**

The code at line 114 states:
```
# The atlas is stored as pages of 128x128 at 128px width (linear, no swizzle)
```

The pixel placement logic (lines 134-150) arranges pixels linearly within
128x128 pages:
```python
pixel_offset = page_idx * 128 * 128 + local_y * 128 + local_x
```

This does NOT match the PSMCT32 swizzle pattern that the original data uses.

### Why it partially works

When the game uploads the linear atlas data via PSMCT32 IMAGE transfer and
reads it back as PSMT4 texture, the deswizzle transformation still produces
recognizable English glyphs because:

1. The page-level organization (128x128) happens to match the PSMT4 page size
2. Within each page, the block-level swizzle DOES reorder pixels, but since the
   glyphs are small (12x12 cells), some glyphs fall within single blocks and
   remain intact
3. Large areas of the atlas are transparent (0xFF), which is invariant under
   any permutation

However, glyphs that span block boundaries (32x16 in PSMT4, 8x8 in PSMCT32)
will have **pixel-level corruption** at block edges.

### Additional bug: palette read from wrong offset

`generate_font_atlas.py` line 19 reads:
```python
palette = orig[192:256]  # This is the first 64 bytes of PIXEL DATA, not palette!
```
The actual palette (grayscale ramp RGBA) is at `orig[-64:]` (last 64 bytes).
The "palette" saved in the atlas is all 0xFF (transparent pixel data), so the
injected font atlas has NO valid palette. This may or may not matter depending
on whether the game uses the embedded CLUT or a separately-uploaded palette.

## Byte-by-byte Comparison

- Original pixel data: 65,536 bytes (22.7% non-transparent)
- English atlas pixel data: first 65,536 bytes of 81,920 (9.8% non-transparent)
- Matching bytes: 46,622 / 65,536 (71.1%)
- Matching bytes that are 0xFF: 46,616
- **Matching non-0xFF bytes: 6** (effectively zero meaningful overlap)

## Correct Fix

To properly inject the English font atlas, `generate_font_atlas.py` should:

1. Render glyphs to a linear pixel buffer (as it does now)
2. Call `swizzle_psmt4()` to convert linear pixels to PSMCT32 upload format
3. Write: `header (192 bytes) + swizzled_pixel_data + real_palette (64 bytes)`

This would produce pixel data in the same PSMCT32 upload format as the original.

## Parameters for swizzle/deswizzle

| Parameter  | Value |
|------------|-------|
| tex_w      | 256   |
| tex_h      | 512   |
| bw_psmt4   | 256   |
| dbw_ct32   | 256   |
| header_size| 192 (.bin) or 1024 (.raw) |

## Injected R1272 `.raw` (83,968 bytes)
```
Offset  Size    Content
0x000   16      Sub-header (payload_size=82176)
0x010   82,176  english_font_atlas.bin (verbatim)
0x010+  padding Zero-padded to sector boundary
```
Confirmed: `injected[16:] == english_font_atlas.bin` (exact match).
