# PS2 TIM2 Format & PSMT4 Texture Swizzle Research

Research date: 2026-05-22

---

## 1. TIM2 File Format Specification

### 1.1 File Header (16 or 128 bytes)

| Offset | Size   | Field       | Description                                      |
|--------|--------|-------------|--------------------------------------------------|
| 0x00   | 4 bytes| fileId      | Magic: `0x54494D32` ("TIM2")                     |
| 0x04   | 1 byte | version     | Format version (typically 0x04)                   |
| 0x05   | 1 byte | format/align| Alignment: 0 = 16-byte header, 1 = 128-byte header |
| 0x06   | 2 bytes| numImages   | Number of images/pictures in the file (uint16)   |
| 0x08   | 8 or 120 bytes | padding | Padding to align to 16 or 128 bytes         |

When `format` (offset 0x05) is 0, the header is 16 bytes total (8 bytes padding).
When `format` is 1, the header is 128 bytes total (120 bytes padding).

Alternative magic for palette-only files: `0x434C5432` ("CLT2").

### 1.2 Picture Header (48 bytes minimum, can be larger)

Each image has its own picture header immediately following the file header (or the previous image's data).

| Offset | Size   | Field        | Description                                        |
|--------|--------|--------------|----------------------------------------------------|
| 0x00   | 4 bytes| totalSize    | Total size of this picture entry (header+image+palette) |
| 0x04   | 4 bytes| clutSize     | Size of palette/CLUT data in bytes                 |
| 0x08   | 4 bytes| imageSize    | Size of pixel/image data in bytes                  |
| 0x0C   | 2 bytes| headerSize   | Size of this header (typically 0x30 = 48 bytes)    |
| 0x0E   | 2 bytes| clutColors   | Number of palette colors (16 for 4bpp, 256 for 8bpp) |
| 0x10   | 1 byte | pictFormat   | Picture format (related to bit depth)              |
| 0x11   | 1 byte | mipMapTextures| Number of mipmap levels: 0=palette only, 1=main only, >1=mipmaps |
| 0x12   | 1 byte | clutType     | Palette storage mode (see below)                   |
| 0x13   | 1 byte | imageType    | Pixel storage format (see below)                   |
| 0x14   | 2 bytes| width        | Image width in pixels                              |
| 0x16   | 2 bytes| height       | Image height in pixels                             |
| 0x18   | 8 bytes| GsTex0       | PS2 GS TEX0 register value (uint64)               |
| 0x20   | 8 bytes| GsTex1       | PS2 GS TEX1 register value (uint64)               |
| 0x28   | 4 bytes| GsRegs       | GS register flags (uint32)                        |
| 0x2C   | 4 bytes| GsTexClut    | PS2 GS TEXCLUT register value (uint32)            |

If `mipMapTextures > 1`, an additional mipmap header follows:
- 8 bytes: GS MIPTBP1 register data
- 8 bytes: GS MIPTBP2 register data

### 1.3 Image Type Values (imageType at offset 0x13)

| Value | Name         | Description                    |
|-------|-------------|--------------------------------|
| 1     | TIM2_RGB16  | 16bpp RGBA5551                 |
| 2     | TIM2_RGB24  | 24bpp RGB888 (stored as 32bpp RGBX8888) |
| 3     | TIM2_RGB32  | 32bpp RGBA8888                 |
| 4     | TIM2_IDTEX4 | 4-bit indexed (PSMT4)          |
| 5     | TIM2_IDTEX8 | 8-bit indexed (PSMT8)          |

### 1.4 CLUT Type Values (clutType at offset 0x12)

| Value | Name            | Description                           |
|-------|----------------|---------------------------------------|
| 0     | PAL_NONE       | No palette                            |
| 1     | PAL_RGB16_CSM1 | 16-bit palette, CSM1 (swizzled)       |
| 2     | PAL_RGB24_CSM1 | 24-bit palette, CSM1 (swizzled)       |
| 3     | PAL_RGB32_CSM1 | 32-bit palette, CSM1 (swizzled)       |
| 129 (0x81) | PAL_RGB16_CSM2 | 16-bit palette, CSM2 (linear)    |
| 130 (0x82) | PAL_RGB24_CSM2 | 24-bit palette, CSM2 (linear)    |
| 131 (0x83) | PAL_RGB32_CSM2 | 32-bit palette, CSM2 (linear)    |

**Key point**: Bit 7 (0x80) distinguishes CSM1 (0) from CSM2 (1). Lower bits encode color depth.

### 1.5 Data Layout After Header

After the picture header (and optional mipmap header), the data is arranged as:
1. **Image/pixel data** (imageSize bytes) -- the raw texture indices
2. **Palette/CLUT data** (clutSize bytes) -- the color lookup table

### 1.6 TIM2 Tools

- **Rainbow** (by marco-calautti): Texture format converter supporting TIM2. GitHub: https://github.com/marco-calautti/Rainbow
- **Noesis**: General-purpose model/texture viewer that supports TIM2
- **tim2view**: Simple TIM2 viewer
- **TextER**: Can extract .tm2 files from archives (romhacking.net)
- **PS2ImageTool** (by Surihix): GUI tool for PS2 raw image data. GitHub: https://github.com/Surihix/PS2ImageTool

---

## 2. PS2 Graphics Synthesizer Pixel Storage Formats (PSM)

### 2.1 PSM Values

| Value  | Name      | Bits/pixel | Description              |
|--------|-----------|------------|--------------------------|
| 0x00   | PSMCT32   | 32         | 32-bit RGBA              |
| 0x01   | PSMCT24   | 24         | 24-bit RGB (stored as 32)|
| 0x02   | PSMCT16   | 16         | 16-bit RGBA5551          |
| 0x0A   | PSMCT16S  | 16         | 16-bit RGBA (swizzled variant) |
| 0x13   | PSMT8     | 8          | 8-bit indexed            |
| 0x14   | PSMT4     | 4          | 4-bit indexed            |
| 0x1B   | PSMT8H    | 8          | 8-bit indexed (high nibble of 32-bit) |
| 0x24   | PSMT4HL   | 4          | 4-bit indexed (bits 24-27 of 32-bit) |
| 0x2C   | PSMT4HH   | 4          | 4-bit indexed (bits 28-31 of 32-bit) |
| 0x30   | PSMZ32    | 32         | 32-bit Z-buffer          |
| 0x31   | PSMZ24    | 24         | 24-bit Z-buffer          |
| 0x32   | PSMZ16    | 16         | 16-bit Z-buffer          |
| 0x3A   | PSMZ16S   | 16         | 16-bit Z-buffer (swizzled) |

### 2.2 GS Memory Hierarchy

The PS2 Graphics Synthesizer has 4 MB of local VRAM, organized hierarchically:

| Level  | Size      | Description                                   |
|--------|-----------|-----------------------------------------------|
| Column | 64 bytes  | Smallest addressable unit (single cycle access)|
| Block  | 256 bytes | 4 columns                                     |
| Page   | 8192 bytes (8 KB) | 32 blocks                             |
| Total  | 4 MB      | 512 pages                                     |

### 2.3 Page and Block Dimensions Per Format

| Format   | Page (pixels) | Block (pixels) | Blocks/Page | Columns/Block |
|----------|--------------|----------------|-------------|---------------|
| PSMCT32  | 64 x 32      | 8 x 8          | 32          | 4             |
| PSMCT24  | 64 x 32      | 8 x 8          | 32          | 4             |
| PSMCT16  | 64 x 64      | 16 x 8         | 32          | 4             |
| PSMCT16S | 64 x 64      | 16 x 8         | 32          | 4             |
| PSMT8    | 128 x 64     | 16 x 16        | 32          | 4             |
| PSMT4    | 128 x 128    | 32 x 16        | 32          | 4             |
| PSMZ32   | 64 x 32      | 8 x 8          | 32          | 4             |
| PSMZ16   | 64 x 64      | 16 x 8         | 32          | 4             |
| PSMZ16S  | 64 x 64      | 16 x 8         | 32          | 4             |

**PSMT4 key dimensions:**
- **Page**: 128 x 128 pixels = 8192 bytes (each pixel is 4 bits = 0.5 bytes)
- **Block**: 32 x 16 pixels = 256 bytes
- **Column**: 32 x 4 pixels = 64 bytes

---

## 3. PS2 PSMT4 Swizzle Algorithm

### 3.1 Overview

Texture swizzling is the process of rearranging pixels so that when data is transferred in PSMCT32 format (which is faster -- 200-300% speed advantage), it ends up stored in GS VRAM in the same layout as if it had been transferred in the native format (e.g., PSMT4).

The swizzle operates at three levels:
1. **Block ordering within a page** (which of the 32 blocks in a page contains a given pixel)
2. **Column ordering within a block** (which of the 4 columns in a block)
3. **Pixel ordering within a column** (position within 64 bytes)

### 3.2 Block Layout Table for PSMT4

Within a page (128x128 for PSMT4), the 32 blocks (each 32x16 pixels) are arranged in a Z-order/Morton-code-like swizzle pattern. The block table maps (blockX, blockY) to block number within the page.

For PSMCT32 (the base format, 8x8 blocks in a 64x32 page), blocks are arranged in Z-order:
```
Block layout in a page (8 columns x 4 rows of blocks):
Row 0:  0,  1,  4,  5, 16, 17, 20, 21
Row 1:  2,  3,  6,  7, 18, 19, 22, 23
Row 2:  8,  9, 12, 13, 24, 25, 28, 29
Row 3: 10, 11, 14, 15, 26, 27, 30, 31
```

For PSMT4 (32x16 blocks in a 128x128 page = 4 columns x 8 rows of blocks):
```
Block layout in a PSMT4 page (4 columns x 8 rows):
Row 0:  0,  2,  8, 10
Row 1:  1,  3,  9, 11
Row 2:  4,  6, 12, 14
Row 3:  5,  7, 13, 15
Row 4: 16, 18, 24, 26
Row 5: 17, 19, 25, 27
Row 6: 20, 22, 28, 30
Row 7: 21, 23, 29, 31
```

This is a Z-order curve (Morton code) pattern applied to the block grid.

### 3.3 Column Layout Within Blocks

Each block has 4 columns, each 32x4 pixels (64 bytes) for PSMT4. Within each column, pixels are packed 2 per byte (4-bit each), with the low nibble being the first pixel and the high nibble being the second.

The column ordering within a block also follows a specific pattern, and the pixel arrangement within columns varies based on even/odd column index.

### 3.4 Pixel Address Calculation (Conceptual Algorithm)

To compute the GS VRAM byte address of a pixel at (x, y) in a PSMT4 texture:

```
// Constants for PSMT4
PAGE_WIDTH  = 128  // pixels
PAGE_HEIGHT = 128  // pixels
BLOCK_WIDTH = 32   // pixels
BLOCK_HEIGHT = 16  // pixels
COLUMN_WIDTH = 32  // pixels (same as block)
COLUMN_HEIGHT = 4  // pixels

// 1. Determine which page
pageX = x / PAGE_WIDTH
pageY = y / PAGE_HEIGHT
page = pageX + pageY * (bufferWidth / PAGE_WIDTH)  // bufferWidth from TBW

// 2. Within the page, determine which block
localX = x % PAGE_WIDTH
localY = y % PAGE_HEIGHT
blockX = localX / BLOCK_WIDTH    // 0..3
blockY = localY / BLOCK_HEIGHT   // 0..7
block = blockTable_PSMT4[blockY][blockX]  // lookup from table above

// 3. Within the block, determine which column
colY = (localY % BLOCK_HEIGHT) / COLUMN_HEIGHT  // 0..3
column = colY  // (simplified -- actual hardware has additional swizzle)

// 4. Within the column, determine pixel position
pixelX = localX % COLUMN_WIDTH
pixelY = localY % COLUMN_HEIGHT
// Column-internal pixel arrangement uses a complex bit-interleaving pattern

// 5. Final address
address = page * 8192 + block * 256 + column * 64 + columnOffset
```

### 3.5 Working Deswizzle Implementation (C# - from Fireboyd78 gist)

Source: https://gist.github.com/Fireboyd78/1546f5c86ebce52ce05e7837c697dc72

This gist provides a complete PS2 4-bit texture unswizzling implementation. The algorithm:
1. Works in blocks of 16 bytes x 4 lines (the "column" unit)
2. Uses specific byte-level reordering within each column
3. Handles the block-level Z-order swizzle
4. Processes data treating the texture as if it were transferred in PSMCT32 and needs to be reinterpreted as PSMT4

### 3.6 Texture Swizzle for Transfer Optimization (ezswizzle approach)

Source: http://ps2linux.no-ip.info/playstation2-linux.com/download/ezswizzle/TextureSwizzling.pdf
Project page: https://ps2linux.no-ip.info/playstation2-linux.com/projects/ezswizzle.html
HOWTO: https://ps2linux.no-ip.info/playstation2-linux.com/docs/howto/display_docef7c.html?docid=75

The ezswizzle approach (by Victor Suba) implements functions that read/write data to a simulated 4MB GS memory array. The key functions are:
- `writeTexPSMT4(dbp, dbw, dsax, dsay, rrw, rrh, data)` -- writes texture data into simulated GS memory using PSMT4 layout
- `readTexPSMCT32(dbp, dbw, dsax, dsay, rrw, rrh, data)` -- reads back from simulated GS memory in PSMCT32 layout

The "swizzle" is achieved by:
1. Write the texture into simulated memory using the native format's write function
2. Read it back using PSMCT32's read function
3. The resulting data can be transferred via DMA in PSMCT32 mode at full speed

### 3.7 PS2 GS Memory Swizzle Visualizer

Source: https://gist.github.com/TellowKrinkle/bd6c6e1735cf5e03110ec57ddeea43a9

This gist provides visualization code for the GS memory swizzle layout, showing how pixels map to memory addresses across all formats. It contains lookup tables and algorithms for all PSM formats.

### 3.8 Additional Code Resources

- **Console-Swizzler** (C library): https://github.com/matyamod/Console-Swizzler -- C library to swizzle DDS textures for console games
- **pyswizzle** (Python): https://github.com/Aclios/pyswizzle -- Python library for swizzle/deswizzle (primarily Switch/PS4, but architecture is reusable)
- **ResHax thread**: https://reshax.com/topic/696-c-code-to-swizzle-4bpp-ps2-textures/ -- C code for 4bpp PS2 texture swizzling
- **ResHax EA type 3 discussion**: https://reshax.com/topic/17924-ps2-how-does-ea%E2%80%99s-type-3-4-bit-swizzle-actually-work/ -- EA's variant of 4-bit swizzle

---

## 4. PS2 TEX0 Register Format

### 4.1 Bit Field Layout (64-bit register)

The TEX0 register configures texture parameters for the Graphics Synthesizer.

| Bits    | Field | Width | Description                                    |
|---------|-------|-------|------------------------------------------------|
| 0-13    | TBP0  | 14    | Texture Buffer Base Pointer (Address / 256)    |
| 14-19   | TBW   | 6     | Texture Buffer Width (Width_in_texels / 64)    |
| 20-25   | PSM   | 6     | Pixel Storage Mode (see PSM table above)       |
| 26-29   | TW    | 4     | Texture Width: actual_width = 2^TW             |
| 30-33   | TH    | 4     | Texture Height: actual_height = 2^TH           |
| 34      | TCC   | 1     | Texture Color Component: 0=RGB, 1=RGBA         |
| 35-36   | TFX   | 2     | Texture Function: 0=modulate, 1=decal, 2=highlight, 3=highlight2 |
| 37-50   | CBP   | 14    | CLUT Buffer Base Pointer (Address / 256)       |
| 51-54   | CPSM  | 4     | CLUT Pixel Storage Mode (format of palette entries) |
| 55      | CSM   | 1     | CLUT Storage Mode: 0=CSM1, 1=CSM2              |
| 56-60   | CSA   | 5     | CLUT Entry Offset (starting index in CLUT buffer) |
| 61-63   | CLD   | 3     | CLUT Buffer Load Control                       |

### 4.2 Field Details

**TBP0**: Base pointer to texture data in GS local memory. Multiply by 256 to get byte address. Max addressable: 2^14 * 256 = 4 MB (full GS memory).

**TBW**: Buffer width in units of 64 texels. For a 128-pixel wide texture, TBW = 2.

**PSM**: Pixel storage mode. For PSMT4 indexed textures, PSM = 0x14.

**TW, TH**: Texture dimensions as power-of-2 exponents. Width = 2^TW, Height = 2^TH. For a 128x128 texture: TW = 7, TH = 7.

**TCC**: Whether alpha channel is used. For opaque textures, TCC = 0 (RGB only). For textures with transparency, TCC = 1 (RGBA).

**TFX**: How the texture color is combined with vertex color:
- 0 (MODULATE): Cv = Ct * Cf (multiply texture by fragment color)
- 1 (DECAL): Cv = Ct (texture color replaces fragment color)
- 2 (HIGHLIGHT): Cv = Ct * Cf + Ca (texture * fragment + alpha)
- 3 (HIGHLIGHT2): Cv = Ct * Cf + Ca (variant)

**CBP**: Base pointer to CLUT data. Same units as TBP0 (address / 256).

**CPSM**: Pixel format of CLUT entries:
- 0x00 = PSMCT32 (32-bit RGBA palette entries)
- 0x02 = PSMCT16 (16-bit palette entries)
- 0x0A = PSMCT16S

**CSM**: CLUT storage mode:
- 0 = CSM1 (swizzled CLUT, faster rendering)
- 1 = CSM2 (linear/sequential CLUT, slower but simpler)

**CSA**: Starting offset into CLUT buffer. For 4-bit textures with CSM1, this selects which block of 16 colors to use from a larger palette buffer, allowing palette animation or sharing.

**CLD**: Controls when/how the CLUT buffer is loaded:
- 0: Do not load
- 1: Load
- 2: Load and copy to buffer 0
- 3: Load and copy to buffer 1
- 4: Load, compare buffer 0, load if different
- 5: Load, compare buffer 1, load if different

### 4.3 Macro Definition (from gsKit/ps2dev)

```c
// From ps2dev gsKit: gsInit.h
#define GS_TEX0(TBP0, TBW, PSM, TW, TH, TCC, TFX, CBP, CPSM, CSM, CSA, CLD) \
    ((u64)(TBP0)        | ((u64)(TBW) << 14)  | ((u64)(PSM) << 20) | \
     ((u64)(TW) << 26)  | ((u64)(TH)  << 30)  | ((u64)(TCC) << 34) | \
     ((u64)(TFX) << 35) | ((u64)(CBP) << 37)  | ((u64)(CPSM)<< 51) | \
     ((u64)(CSM) << 55) | ((u64)(CSA) << 56)   | ((u64)(CLD) << 61))
```

### 4.4 Reading TEX0 from TIM2 Header

The TIM2 picture header stores the GsTex0 value at offset 0x18 (8 bytes). This is the pre-computed TEX0 register value that can be directly loaded into the GS. To extract fields:

```python
def parse_tex0(value):
    return {
        'TBP0': (value >>  0) & 0x3FFF,
        'TBW':  (value >> 14) & 0x3F,
        'PSM':  (value >> 20) & 0x3F,
        'TW':   (value >> 26) & 0xF,
        'TH':   (value >> 30) & 0xF,
        'TCC':  (value >> 34) & 0x1,
        'TFX':  (value >> 35) & 0x3,
        'CBP':  (value >> 37) & 0x3FFF,
        'CPSM': (value >> 51) & 0xF,
        'CSM':  (value >> 55) & 0x1,
        'CSA':  (value >> 56) & 0x1F,
        'CLD':  (value >> 61) & 0x7,
    }
```

---

## 5. CSM1 vs CSM2 CLUT Modes

### 5.1 CSM1 (CLUT Storage Mode 1) -- Swizzled

In CSM1, the CLUT entries are stored in GS memory in a swizzled pattern. The GS hardware reads them in a specific non-linear order optimized for the renderer's internal cache.

**For 4-bit indexed (16 colors):** CSM1 does not require palette unswizzling because there are only 16 entries and they fit within a single CSM1 block. The palette can be stored linearly.

**For 8-bit indexed (256 colors):** CSM1 swizzles palette entries. The standard unswizzle pattern for 256-entry palettes swaps groups of 8 entries:

```
Indices 0-7:   stay at 0-7
Indices 8-15:  swap with 16-23
Indices 16-23: swap with 8-15
Indices 24-31: stay at 24-31
(pattern repeats every 32 entries)
```

In other words, within every group of 32 palette entries, entries 8-15 and 16-23 are swapped. This can be expressed as:

```python
def unswizzle_palette_csm1(palette_256):
    """Unswizzle a 256-entry CSM1 palette for 8-bit indexed textures."""
    result = list(palette_256)
    for i in range(0, 256, 32):
        # Swap entries [i+8..i+15] with [i+16..i+23]
        for j in range(8):
            result[i + 8 + j], result[i + 16 + j] = result[i + 16 + j], result[i + 8 + j]
    return result
```

**Important note for 4-bit textures:** Since PSMT4 only uses 16 palette entries (indices 0-15), and the CSM1 swap pattern only affects indices 8-15 vs 16-23 within a group of 32, the CSM1 swizzle has **no effect** on 4-bit palette data. The 16 entries fit entirely within the first 16 positions, which are never swapped.

### 5.2 CSM2 (CLUT Storage Mode 2) -- Linear

In CSM2, palette entries are stored sequentially in memory, in the order they are indexed. No reordering is needed. This is simpler but the GS accesses it more slowly.

---

## 6. PSMT4 Texture Swizzle -- Detailed Technical Notes

### 6.1 The Core Problem

When a PS2 game sends texture data to the GS via DMA, it can use different transfer modes. The fastest is PSMCT32 (32-bit mode), which uses the full 256-bit DMA bus efficiently. But if the texture is PSMT4, the GS stores each pixel in a specific 4-bit slot determined by the PSMT4 memory layout.

If you send raw linear PSMT4 pixel data using PSMCT32 transfer mode, the pixels end up in the wrong locations because PSMCT32 and PSMT4 have different page/block/column layouts.

**The swizzle pre-arranges the pixel data** so that a PSMCT32 transfer places each pixel exactly where PSMT4 would have placed it.

### 6.2 Relationship Between PSMCT32 and PSMT4 Layouts

Since a PSMCT32 page is 64x32 pixels (at 4 bytes/pixel = 8192 bytes) and a PSMT4 page is 128x128 pixels (at 0.5 bytes/pixel = 8192 bytes), one PSMT4 page maps to exactly one PSMCT32 page in terms of bytes, but the pixel coordinates are completely different.

The swizzle algorithm must map:
- PSMT4 coordinate (x4, y4) -> VRAM byte address -> PSMCT32 coordinate (x32, y32)

### 6.3 Block-Level Swizzle

The 32 blocks within a page are numbered 0-31. Each format assigns different pixel regions to each block number:

**PSMCT32 block assignment** (8x8 pixel blocks, 8 cols x 4 rows):
```
Block(bx, by) = blockTablePSMCT32[by][bx]

blockTablePSMCT32[4][8] = {
    { 0,  1,  4,  5, 16, 17, 20, 21},
    { 2,  3,  6,  7, 18, 19, 22, 23},
    { 8,  9, 12, 13, 24, 25, 28, 29},
    {10, 11, 14, 15, 26, 27, 30, 31}
};
```

**PSMT4 block assignment** (32x16 pixel blocks, 4 cols x 8 rows):
```
Block(bx, by) = blockTablePSMT4[by][bx]

blockTablePSMT4[8][4] = {
    { 0,  2,  8, 10},
    { 1,  3,  9, 11},
    { 4,  6, 12, 14},
    { 5,  7, 13, 15},
    {16, 18, 24, 26},
    {17, 19, 25, 27},
    {20, 22, 28, 30},
    {21, 23, 29, 31}
};
```

Both tables use the same set of numbers (0-31) -- they're just indexed differently because the block dimensions differ between formats.

### 6.4 Column-Level Swizzle

Within each 256-byte block, there are 4 columns of 64 bytes each.

For PSMT4, each column is 32 pixels wide x 4 pixels tall:
- Column 0: rows 0-3 of the block
- Column 1: rows 4-7
- Column 2: rows 8-11
- Column 3: rows 12-15

Within each column, the 64 bytes contain 128 nibbles (4-bit values). The arrangement of these nibbles follows a specific pattern that interleaves pixels from different positions.

### 6.5 Practical Swizzle Code Pattern

The general pattern for swizzling a PSMT4 texture (from references):

```c
// Pseudocode for PSMT4 swizzle (for fast PSMCT32 transfer)
void swizzle_psmt4(uint8_t* input, uint8_t* output, int width, int height) {
    // Simulated GS memory
    uint8_t gs_mem[4 * 1024 * 1024];
    
    // Step 1: Write input data to simulated GS memory using PSMT4 layout
    writeTexPSMT4(gs_mem, /*dbp=*/0, /*dbw=*/width/128, 0, 0, width, height, input);
    
    // Step 2: Read back from simulated GS memory using PSMCT32 layout
    // Width in PSMCT32 terms: width/2 (since 2 PSMT4 pixels = 1 byte = 1/4 of 32-bit pixel)
    // Actually the read dimensions need careful calculation based on buffer width
    int psmct32_width = width / 2;  // simplified
    int psmct32_height = height / 2; // simplified  
    readTexPSMCT32(gs_mem, /*dbp=*/0, /*dbw=*/width/128, 0, 0, psmct32_width, psmct32_height, output);
}
```

### 6.6 Deswizzle (Reverse Operation)

To deswizzle (convert from swizzled PSMCT32-transfer format back to linear PSMT4):

```c
void deswizzle_psmt4(uint8_t* swizzled, uint8_t* output, int width, int height) {
    uint8_t gs_mem[4 * 1024 * 1024];
    
    // Step 1: Write swizzled data using PSMCT32 layout
    writeTexPSMCT32(gs_mem, 0, width/128, 0, 0, psmct32_w, psmct32_h, swizzled);
    
    // Step 2: Read back using PSMT4 layout
    readTexPSMT4(gs_mem, 0, width/128, 0, 0, width, height, output);
}
```

---

## 7. Key Reference URLs

### Primary Documentation
- **PS2 Linux Texture Swizzling PDF**: http://ps2linux.no-ip.info/playstation2-linux.com/download/ezswizzle/TextureSwizzling.pdf
- **ps2tek (PS2 internals documentation)**: https://psi-rockin.github.io/ps2tek/
- **Maister's GS emulation blog post**: https://themaister.net/blog/2024/07/03/playstation-2-gs-emulation-the-final-frontier-of-vulkan-compute-emulation/

### TIM2 Format
- **OpenKH TM2 documentation**: https://openkh.dev/common/tm2.html
- **TCRF TIM2 Information (Kojin)**: https://tcrf.net/User:Kojin/TIM2_Information
- **VG Resource Wiki TIM2**: https://wiki.vg-resource.com/TIM2
- **Reverse Engineering Wiki TM2**: https://rewiki.miraheze.org/wiki/TM2_TIM2_Image

### Code Implementations
- **PS2 4-bit Texture Unswizzling (C#, Fireboyd78)**: https://gist.github.com/Fireboyd78/1546f5c86ebce52ce05e7837c697dc72
- **PS2 GS Memory Swizzle Visualizer (TellowKrinkle)**: https://gist.github.com/TellowKrinkle/bd6c6e1735cf5e03110ec57ddeea43a9
- **ps2dev gsKit (official PS2 homebrew SDK)**: https://github.com/ps2dev/gsKit
- **gsKit texture source**: https://github.com/ps2dev/gsKit/blob/master/ee/gs/src/gsTexture.c
- **gsKit header with GS macros**: https://github.com/ps2dev/gsKit/blob/master/ee/gs/include/gsInit.h
- **Console-Swizzler**: https://github.com/matyamod/Console-Swizzler
- **PS2ImageTool**: https://github.com/Surihix/PS2ImageTool
- **Rainbow (TIM2 converter)**: https://github.com/marco-calautti/Rainbow

### Forums and Discussions
- **ps2dev forum -- How to swizzle textures**: https://forums.ps2dev.org/viewtopic.php?t=3021
- **ps2dev forum -- Putting textures in VRAM**: https://forums.ps2dev.org/viewtopic.php?t=3030
- **ResHax -- C code to swizzle 4bpp**: https://reshax.com/topic/696-c-code-to-swizzle-4bpp-ps2-textures/
- **ResHax -- EA type 3 4-bit swizzle**: https://reshax.com/topic/17924-ps2-how-does-ea%E2%80%99s-type-3-4-bit-swizzle-actually-work/
- **Fobes -- Palette shifting with the GS**: https://fobes.dev/gs/2024/01/20/palette-shifting-with-the-gs.html
- **PCSX2 PSM meaning discussion**: https://github.com/PCSX2/pcsx2/discussions/4313
- **Linux kernel PS2 GS structures**: https://lore.kernel.org/linux-mips/25b6c975d334c0678ab3963d6c76584ed9471c35.1567326213.git.noring@nocrew.org/

### PCSX2 Emulator Source (GS implementation)
- **PCSX2 GitHub**: https://github.com/PCSX2/pcsx2
- **GS source directory**: https://github.com/PCSX2/pcsx2/tree/master/pcsx2/GS

---

## 8. Summary for Fan Translation Work

### What You Need for a Wizardry PS2 Translation

1. **Parse TIM2 headers**: Read the 16-byte file header, then the 48-byte picture header for each image. Extract width, height, imageType, clutType, and the GsTex0 register value.

2. **Identify PSMT4 textures**: If `imageType == 4`, the texture is 4-bit indexed (PSMT4). It has 16 palette entries.

3. **Handle the palette**: 
   - Read `clutSize` bytes of palette data after the image data
   - If `clutType` has bit 7 clear (CSM1), and this is a 4-bit texture, no palette unswizzle is needed (only affects 8-bit palettes)
   - If `clutType` has bit 7 set (CSM2), palette is stored linearly
   - Each palette entry is typically 32-bit RGBA (if CPSM in TEX0 indicates PSMCT32)

4. **Handle pixel data swizzle**:
   - The pixel data in the TIM2 file may or may not be pre-swizzled depending on the game
   - If the game stores textures in swizzled (PSMCT32-transfer) format, you need to deswizzle to get linear PSMT4 pixel data
   - After editing (e.g., replacing Japanese font glyphs with English), re-swizzle before writing back

5. **Pixel data format**: In linear PSMT4 format, each byte contains 2 pixel indices. The low nibble (bits 0-3) is the first pixel, and the high nibble (bits 4-7) is the second pixel.

6. **Key dimensions to verify**: Check your TIM2 files' GsTex0 to confirm:
   - PSM field = 0x14 (PSMT4)
   - TW/TH fields for actual texture dimensions
   - TBW for buffer width (determines page layout)

### Note on WebFetch Limitations

WebFetch was denied during this research session, which prevented fetching the full source code from the GitHub gists and detailed wiki pages. The following resources contain critical implementation code that should be manually reviewed:

1. **Fireboyd78's 4-bit unswizzle gist** -- contains a complete working C# implementation
2. **TellowKrinkle's GS swizzle visualizer** -- contains lookup tables for all formats
3. **ezswizzle PDF** -- contains the definitive writeTexPSMT4/readTexPSMCT32 algorithm
4. **PCSX2 GSTables.h** -- contains the authoritative block and column tables used by the leading PS2 emulator
5. **TCRF Kojin's TIM2 page** -- contains the most detailed TIM2 header documentation found

These should be fetched manually via browser for the complete implementation details.
