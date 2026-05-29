# PSMT4 Deswizzle Analysis

## Implementation

Created `tools/psmt4_deswizzle.py` implementing PS2 GS PSMT4 deswizzle/swizzle using the same VRAM simulation approach as the existing PSMT8 tool.

### Tables Used (from PCSX2 GSTables.cpp)

- **BLOCK_TABLE_4**: 8x4 array (128/16=8 rows, 128/32=4 columns per page)
- **COLUMN_TABLE_4**: 16x32 array (block is 32x16 pixels, each entry is a nibble index 0-511)
- **BLOCK_TABLE_32** and **COLUMN_TABLE_32**: same as PSMT8 tool (for PSMCT32 upload addressing)

### PSMT4 GS Parameters

- Page size: 128x128 pixels (vs 128x64 for PSMT8)
- Block size: 32x16 pixels (vs 16x16 for PSMT8)
- 32 blocks per page (same as PSMT8)
- 512 nibbles per block (256 bytes)
- 16384 nibbles per page (8192 bytes)

### Address Calculation (verified against PCSX2 pxOffset)

```
pageX = x / 128
subpageX = x % 128
blockID = blockTable4[(y % 128) / 16][(subpageX) / 32]
nibbleOffset = columnTable4[y % 16][subpageX % 32]
address = pageX * 16384 + blockID * 512 + nibbleOffset
```

Byte address = nibble_address // 2. Low nibble if even, high nibble if odd.

## Verification Results

### R1272 (Main Font Atlas, 256x512 PSMT4)

- **Round-trip test: PASS** (deswizzle then re-swizzle produces exact original bytes)
- File layout: 1024-byte header + 65536 bytes pixel data + 1024 bytes CLUT
- CLUT is all zeros (font uses grayscale intensity directly)
- PSMCT32 upload: 256x64 pixels (dbw_ct32=256)
- Visual output shows recognizable anti-aliased glyph shapes

### .raw vs .bin Discrepancy

The `.raw` file (packdata_raw/1272_type01.raw) and `.bin` file (packdata_resources/1272_type01.bin) contain **different pixel data** (only 66% byte match). This is expected:

- `.raw` = PSMCT32-swizzled data as uploaded to GS VRAM
- `.bin` = page-linear format (128px-wide pages, no GS swizzle)

The `.bin` file uses a simpler format: 192-byte header + 64-byte palette + 65536 bytes of page-linear pixel data. This format is used by `generate_font_atlas.py` and `psmt4_deswizzle_v2.py` for direct editing.

### R1188 (Name Entry Font, 1024x1024)

R1188 is **NOT a standard PSMT4 atlas**. Analysis revealed:

- File has 17 repeated TEX0 register blocks (TBW=16, PSM=20, 1024x1024)
- Contains a structured glyph descriptor table at offset 0x560-0x7C0
- Each entry: 8x8 pixel glyph with offset, width, height fields
- Embedded glyph bitmap data from 0x840 onwards
- Has a real 16-color CLUT (non-grayscale, with actual RGB values)
- This is a glyph resource format, not a raw texture atlas

## Tool Features

- `deswizzle_psmt4(data, w, h, bw_psmt4, dbw_ct32)` - VRAM simulation deswizzle
- `swizzle_psmt4(pixels, w, h, bw_psmt4, dbw_ct32)` - inverse (for patching)
- `make_rgba_image_4bit(pixels, palette, w, h)` - visualization with CLUT
- Round-trip verification
- CLI with `--test-r1272`, arbitrary file input, configurable header/clut sizes

## Usage

```bash
# Deswizzle R1272 with verification
python tools/psmt4_deswizzle.py --test-r1272 --roundtrip

# Arbitrary PSMT4 file
python tools/psmt4_deswizzle.py input.raw -W 256 -H 512 --dbw 256 --header 1024 --clut 1024 -o output.png

# With custom buffer widths
python tools/psmt4_deswizzle.py input.raw -W 1024 -H 1024 --dbw 1024 --bw 1024 --header 2048 --clut 0 -o output.png
```
