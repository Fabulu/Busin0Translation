# Kanji Font Page Resources (R1269-R1277) - Structure Analysis

## CRITICAL FINDING: R1269-R1277 are NOT kanji font pages

R1269-R1277 are **character/monster artwork** (PSMT8 format), NOT font atlases.
They were incorrectly identified as "kanji font page resources" in the task description.
Visual inspection confirms they contain full-color character illustrations.

## The REAL Font Atlas: R1272 (PSMT4)

R1272 is the **only** font atlas among these resources.

### R1272 File Structure

- **File size:** 67,584 bytes
- **Format:** PSMT4 (4-bit palettized, 16 colors)
- **Texture dimensions:** 256x512 pixels (from TEX0: TW=8, TH=9)
- **Layout:** 1024-byte header | 65,536 bytes pixel data | 1024-byte palette (all zeros)
- **Palette:** All zeros in file -- game sets palette at runtime
- **PSMCT32 upload:** 64 pixels wide x 256 rows (DBW=1 -> 64 CT32 pixels)

### Header Structure (common to all type-01 resources)

```
Offset  Size  Description
0x00    16    DMA tag: [0x00000000] [DBW_info] [0x00000010] [0x00000000]
0x10    16    Descriptor: count=1, something=2
0x20    16    GIF tag: NLOOP=4, EOP=1, A+D mode (REG=0x0E)
0x30    16    Write 0: CLAMP_1 (reg 0x08) = 0x05
0x40    16    Write 1: MIPTBP1_1 (reg 0x34) = 0x0040000400008000
0x50    16    Write 2: TEX1_1 (reg 0x14) = 0x0000000000000000
0x60    16    Write 3: TEX0_1 (reg 0x06) = full TEX0 register value
0x70    16    Padding/marker: 0xFFFF...
0x80    16    Transfer desc: [width_u16][height_u16] [0] [0x4C] [upload_dims]
0x90    16    Transfer desc: [stride_bytes] [0] [custom] [custom]
0xA0    ...   Zero padding to 0x400
0x400   N     Pixel data (PSMCT32 upload format)
end-1024 1024 Palette data (RGBA32, may be all-zero if runtime palette)
```

### TEX0 Register Decoded (R1272)

```
TEX0 = 0x2000000661410000
  TBP0 = 0       (base pointer)
  TBW  = 4       (buffer width = 256 CT32 pixels)
  PSM  = 0x14    (PSMT4)
  TW   = 8       (width = 256)
  TH   = 9       (height = 512)
  TCC  = 1       (RGBA with alpha)
  TFX  = 0       (modulate)
  CBP  = 0       (CLUT base pointer)
  CPSM = 0       (CLUT format = PSMCT32)
  CSM  = 0       (CSM1)
  CSA  = 0       (CLUT start)
  CLD  = 1       (load CLUT)
```

### Deswizzle Status: INCOMPLETE

PSMT4 deswizzle is significantly more complex than PSMT8.
The current approach (PSMCT32 write to VRAM + PSMT4 read using PCSX2 blockTable4/columnTable4)
produces garbled output despite mathematically correct address traces.

**What works:**
- PSMCT32 write simulation is verified correct (same code as working PSMT8 deswizzle)
- blockTable4 and columnTable4 values match PCSX2 source (verified from GSTables.cpp)
- Page, block, and column address ranges are mathematically consistent

**What doesn't work:**
- The combined CT32->VRAM->PSMT4 readback produces horizontally-striped garbled output
- Multiple BW values tried (1, 2, 4) -- none produce clean glyphs
- Raw VRAM bytes at stride 256 DO show clear kanji glyphs (confirming data is present)

**Verified correct (mathematically equivalent to PCSX2 source):**
- PixelAddressOrg32 formula for CT32 write (from GSdx GSLocalMemory.h)
- PixelAddressOrg4 formula for PSMT4 read (from GSdx GSLocalMemory.h)
- blockTable4 and columnTable4 (from PCSX2 GSTables.cpp)
- Address traces match between Python and C++ for all tested coordinates
- All DBW values tried (32, 64, 128, 256 CT32 pixels) produce garbled output

**Possible remaining issues:**
1. The upload may not be a standard GIF IMAGE transfer (could be VIF DIRECT, DMA chain, or software-driven)
2. The game may do additional post-processing on the VRAM data
3. There may be a bp (base pointer) offset between upload and read that we haven't accounted for
4. The BITBLTBUF DPSM may not be PSMCT32 (could be PSMCT16 or another format)

**Recommended approach:** Use PCSX2 texture dump feature to extract the font atlas directly from the running game, bypassing the deswizzle problem entirely.

## All Resources Summary

| Resource | Size     | PSM    | Dimensions | Upload CT32 | Content          |
|----------|----------|--------|------------|-------------|------------------|
| R1269    | 264,192  | PSMT8  | 512x512    | 256x256     | Character art    |
| R1270    | 133,120  | PSMT8  | 256x512    | 128x256     | Character art    |
| R1271    | 133,120  | PSMT8  | 256x512    | 128x256     | Character art    |
| R1272    | 67,584   | PSMT4  | 256x512    | 64x256      | **FONT ATLAS**   |
| R1273    | 133,120  | PSMT8  | 256x512    | 128x256     | Character art    |
| R1274    | 264,192  | PSMT8  | 512x512    | 256x256     | Character art    |
| R1275    | 264,192  | PSMT8  | 512x512    | 256x256     | Character art    |
| R1276    | 264,192  | PSMT8  | 512x512    | 256x256     | Character art    |
| R1277    | 264,192  | PSMT8  | 512x512    | 256x256     | Character art    |

## Key Files

- Raw data: `extracted/packdata_raw/1272_type01.raw`
- Deswizzle tool: `tools/psmt8_deswizzle.py` (PSMT8 only, needs PSMT4 extension)
- VRAM visualization (shows glyphs): `R1272_vram_bytes_256x1024.png`
- Raw nibble grid (shows glyphs at wrong positions): `R1272_raw_128x1024.png`

## Next Steps

1. **Get PSMT4 deswizzle working** -- may need to extract actual PCSX2 runtime behavior via debugging
2. **Alternative approach:** Use PCSX2's texture dumping feature to extract the font atlas directly from the running game
3. **Memory file correction:** Update project_glyph_status.md -- R1272 is confirmed as PSMT4 256x512 font atlas, but deswizzle needs work
