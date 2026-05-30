# R1188 PSMT4 Swizzle: Cracked via Empirical PCSX2 Comparison

## Result

**DBW_CT32 = 512** is the correct PSMCT32 upload buffer width for R1188.

- 21 out of 31 PCSX2 texture dumps matched pixel-perfectly
- Roundtrip test (deswizzle then re-swizzle) produces EXACT byte match
- The existing deswizzle code was using DBW=1024 (wrong); the correct value is 512

## File Layout

```
1188_type01.bin (527,360 bytes):
  [0x000..0xBFF]  3,072 bytes  GIF/DMA header (GS register setup packets)
  [0xC00..0x80BFF] 524,288 bytes  PSMT4 pixel data (1024x1024 @ 4bpp)
  No CLUT at end of file (CLUT stored in separate VRAM region)

1188_type01.raw (528,384 bytes):
  [0x000..0x00F]  16 bytes  Outer container header
  [0x010..end]    527,360 bytes  = 1188_type01.bin content
  +1,008 bytes padding at EOF
```

## GS Registers (from TEX0)

```
TEX0 = 0x20100006A9440000
  TBP0 = 0       (texture base pointer)
  TBW  = 16      (buffer width in 64-pixel units = 1024 PSMCT32 pixels)
  PSM  = 20      (PSMT4 - 4-bit palettized)
  TW   = 10      (width = 2^10 = 1024)
  TH   = 10      (height = 2^10 = 1024)
  CBP  = 0       (CLUT base pointer)
  CPSM = 2       (PSMCT16 CLUT format)
```

## Why DBW=512 and Not 1024?

TBW=16 means the PSMT4 readback buffer width is 1024 pixels. But the PSMCT32
upload transfer uses a DIFFERENT buffer width. The game uploads the texture data
as PSMCT32 pixels with DBW=8 (in 64-pixel units = 512 pixels wide).

This means the upload writes 512 PSMCT32 pixels per row. Since each PSMCT32 pixel
is 4 bytes = 8 PSMT4 nibbles, the upload effectively writes 4096 nibbles per row
into VRAM. The PSMT4 readback then interprets those same VRAM words using its own
page/block/column swizzle at TBW=16 (1024 PSMT4 pixels wide).

The mismatch between upload width (512 PSMCT32) and readback width (1024 PSMT4)
is what makes R1188 different from R1272, where both use matching widths.

## CLUT (Color Lookup Table)

The 16-entry CLUT maps indices to grayscale RGBA values:

```
Index  R    G    B    A
  0    0    0    0    0   (transparent)
  1    24   24   24   128
  2    32   32   32   128
  3    40   40   40   128
  4    64   64   64   128
  5    80   80   80   128
  6    96   96   96   128
  7    104  104  104  128
  8    120  120  120  128
  9    136  136  136  128
 10    160  160  160  128
 11    168  168  168  128
 12    184  184  184  128
 13    192  192  192  128
 14    216  216  216  128
 15    240  240  240  128
```

## Deswizzle/Reswizzle Usage

```python
from psmt4_deswizzle import deswizzle_psmt4, swizzle_psmt4

# Read pixel data
bin_data = open('1188_type01.bin', 'rb').read()
pixel_data = bin_data[0xC00:]  # skip 3072-byte header

# Deswizzle: raw -> linear 1024x1024 indices (0-15)
linear = deswizzle_psmt4(pixel_data, 1024, 1024, bw_psmt4=1024, dbw_ct32=512)

# Modify linear pixels...

# Re-swizzle: linear -> raw format
raw_out = swizzle_psmt4(linear, 1024, 1024, bw_psmt4=1024, dbw_ct32=512)
```

## Verification Method

1. Collected 35 PCSX2 texture dumps matching bitfield `00002a94` (PSMT4 1024x1024)
2. Converted each 24x24 RGBA dump back to palette indices using the CLUT
3. For each candidate DBW value (64, 128, 256, 512, 1024):
   - Deswizzled the full R1188 pixel data
   - Searched for each PCSX2 glyph pattern in the deswizzled atlas
4. Only DBW=512 produced matches (21/31 dumps found at expected glyph positions)
5. Roundtrip verification confirmed exact byte-level reconstruction

## Files Updated

- `tools/psmt4_deswizzle.py` - R1188 test mode now uses correct DBW=512
- `build/textures_to_edit/R1188_CORRECT_dbw512.png` - Correctly deswizzled grayscale
- `build/textures_to_edit/R1188_CORRECT_dbw512_rgba.png` - With actual CLUT colors
