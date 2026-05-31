# Atlas Position Comparison: Why ASCII Works but Slot 346 (STR) Didn't

## Summary

The root cause was that `generate_font_atlas.py` had TWO critical bugs that have
since been fixed (current version on disk is correct):

1. **Wrong pixel format**: The old code wrote pixels in "page-linear" layout
   (128x128 pages, linear within each page). The game expects **PSMT4-swizzled**
   data organized for PSMCT32 DMA upload. The current code correctly calls
   `swizzle_psmt4()` to produce the right format.

2. **Wrong palette source**: The old code used `orig[192:256]` (64 bytes of 0xFF
   padding) as the palette. The real palette is at `orig[-64:]` (a proper
   grayscale RGBA ramp from R=172 down to R=0).

## File Structure

### Original R1272 (.bin = 65792 bytes)
```
[0:192]       GIF packet header (DMA tag + GIF A+D register writes: TEX0, CLAMP, etc.)
[192:65728]   65536 bytes of PSMT4 pixel data (PSMCT32 upload format, swizzled)
[65728:65792] 64 bytes = RGBA palette (16 colors x 4 bytes)
```

### English Atlas (current, 82176 bytes)
```
[0:192]       GIF header (copied from original, TEX0 TH patched: 9->10 for 1024px height)
[192:82112]   81920 bytes of PSMT4 pixel data (PSMCT32 upload format, swizzled)
[82112:82176] 64 bytes = RGBA palette (copied from orig[-64:])
```

## PSMT4 Swizzle Explained

The PS2 GS stores PSMT4 textures with a complex block/column swizzle pattern:
- **Pages**: 128x128 pixels each (8192 bytes = 16384 nibbles)
- **Blocks**: 32x16 pixels each (256 bytes = 512 nibbles), arranged per `BLOCK_TABLE_4`
- **Column table**: 16x32 nibble index lookup within each block (`COLUMN_TABLE_4`)

The game uploads pixel data to GS VRAM using PSMCT32 transfers (32-bit word swizzle
with 64x32 pages, 8x8 blocks). The on-disc format must match the PSMCT32 upload
layout so the data lands correctly in VRAM for PSMT4 readback.

The `swizzle_psmt4()` function:
1. Writes linear pixel values to a simulated VRAM using PSMT4 block/column addressing
2. Reads them back using PSMCT32 block/column addressing
3. Produces the byte stream the game's DMA engine expects

## Byte-Level Comparison at Position 33 (A)

- **Grid position**: col=12, row=1, pixel origin (144, 12)
- **Page**: page_col=1, page_row=0, page_idx=1 (second page, top row)
- After `swizzle_psmt4()`, the A glyph data scatters across multiple PSMCT32 blocks
  within the byte stream. The exact byte positions depend on the block/column tables.
- **Deswizzle verification** (current atlas): Shows clean 'A' glyph with proper antialiasing

## Byte-Level Comparison at Position 346 (str stat label)

- **Grid position**: col=10, row=16, pixel origin (120, 192)
- **Page**: page_col=0, page_row=1, page_idx=2 (first column, second page row)
- The "str" text (rendered by `render_menu_tiles.py`) occupies 41 foreground pixels
- **Deswizzle verification** (current atlas): Shows clean "str" label

## Why ASCII Used to "Work"

ASCII characters at positions 0-94 appeared to work even with the old buggy
page-linear format because:
- The first ~95 glyphs occupy the top portion of the texture (rows 0-54 of
  a 12px grid = y=0..53, entirely within page rows 0)
- In the first 128 rows, page-linear and PSMT4 block addressing partially
  overlap for certain column ranges, causing some glyphs to appear (though
  likely with artifacts or partial corruption)
- Antialiased edges may have masked subtle corruption in single-pixel details

Slot 346 at y=192 crosses into page_row=1, where page-linear and PSMT4
addressing diverge completely, producing invisible/garbage glyphs.

## GIF Packet Header Details

The 192-byte header contains:
- Offset 0x00: DMA tag (16 bytes)
- Offset 0x10: GIF tag (PACKED mode, NLOOP=4, NREG=1, REG=A+D)
- Offset 0x20: A+D writes for CLAMP_1, MIPTBP1_1, TEX2_1, TEX0_1
- Offset 0x50: TEX0_1 data: TBP0=0, TBW=4, PSM=0x14(PSMT4), TW=8(256px), TH=9->10(512->1024px)
- Offset 0x60: GIF tag (DISABLE), followed by additional transfer setup

## Palette Details

Original palette (16 RGBA entries at file end):
```
Index  0: R=172 G=172 B=172 A=128  (lightest gray, maps to 4bpp value 0 = most opaque)
Index  1: R=155 G=155 B=155 A=128
...
Index 14: R=  8 G=  8 B=  8 A=128
Index 15: R=  0 G=  0 B=  0 A=  0  (transparent, maps to 4bpp value 15 = background)
```

The old buggy atlas had all-0xFF palette (every color = white, alpha=255), which
would render all glyph values as white-on-white (invisible for some blend modes).

## Current Status

The current `generate_font_atlas.py` (last modified May 31) correctly:
1. Uses `swizzle_psmt4()` for proper PSMCT32 upload format
2. Sources palette from `orig[-64:]` (real grayscale ramp)
3. Patches TEX0 TH for extended height (540px -> round to 1024)
4. Injects menu tiles via `render_menu_tiles.py`

The atlas binary needs to be re-injected into PACKDATA.DIG via
`full_patch_pipeline.py` after any regeneration.
