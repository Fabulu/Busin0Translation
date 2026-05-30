# R1188 Texture Format Investigation

## File Properties
- **File**: `extracted/packdata_raw/1188_type01.raw`
- **Size**: 528,384 bytes (NOT 527,360 as initially stated)
- **Description**: Name entry screen UI texture (tabs, buttons, title bar)

## Header Structure (Decoded from GS Register Writes)

### Master Header (0x0000-0x001F, 32 bytes)
- Offset 0x04: Payload size = 527,360 (0x80C00)
- Offset 0x08: Count = 16 (0x10)
- Offset 0x10: Sub-entry count = 17 (0x11)

### 17 GIF Tag Packets (0x0020-0x056F, each 80 bytes)
All 17 entries are IDENTICAL and set up texture rendering:
- **GIF tag**: NLOOP=4, EOP=1, FLG=PACKED, NREG=1
- **4 A+D register writes each**:
  - Register 0x08 (CLAMP_1) = 0x0000000000000005
  - Register 0x34 (TEX1_1)  = 0x0080001000020000
  - Register 0x14 (TEX2_1)  = 0x0000000000000000 (CLD=0: CLUT not loaded from this data)
  - Register 0x06 (TEX0_1)  = 0x20100006A9440000

### TEX0_1 Decoded
| Field | Value | Meaning |
|-------|-------|---------|
| TBP0  | 0     | Texture base pointer = 0 |
| TBW   | 16    | Buffer width = 16 * 64 = 1024 CT32 pixels |
| PSM   | 0x14  | **PSMT4** (4-bit palettized) |
| TW    | 10    | Texture width = 2^10 = **1024** |
| TH    | 10    | Texture height = 2^10 = **1024** |
| TCC   | 1     | RGBA mode |
| TFX   | 0     | MODULATE |
| CBP   | 0     | CLUT base pointer = 0 |
| CPSM  | 2     | **PSMCT16** (16-bit CLUT entries) |
| CSM   | 0     | CSM1 (standard CLUT storage) |
| CSA   | 0     | CLUT entry offset = 0 |
| CLD   | 1     | Load CLUT (but TEX2 CLD=0 overrides this) |

### Sub-texture UV Table (0x0570-0x06BF)
17 entries with `ff ff ff ff` markers defining sub-rectangles within the atlas.

### Sub-entry Table (0x06E0-0x07DF)
15 active entries (entries 15-16 are zero/null):
- Each: offset, w=8, h=8, flags=2
- Offsets increment by 0x30 (48): 0x016C, 0x019C, 0x01CC, ...

### Zero padding (0x07E0-0x07FF)

## Data Layout
| Offset    | Size    | Content |
|-----------|---------|---------|
| 0x0000    | 2,048   | Header (GIF tags + sub-texture tables) |
| 0x0800    | 524,288 | Pixel data (PSMT4 1024x1024 = 524,288 bytes) |
| 0x80000   | 2,048   | CLUT VRAM data (swizzled PSMCT32 format for GS upload) |
| 0x80800   | 1,088   | 17 CLUT palettes (linear, 16 entries x 4 bytes each) |
| 0x80C40   | 960     | Zero padding to 528,384 bytes |

## CLUT/Palette Data

### 17 Linear Palettes at 0x80800 (PSMCT16 format stored as 32-bit words)
Each palette: 16 entries x 4 bytes (16-bit PSMCT16 value + 2 zero bytes)

| Palette | Start Color | End Color | Notes |
|---------|-------------|-----------|-------|
| 0  | (0,0,0)     | (173,173,173) | Grayscale ramp |
| 1  | (189,189,189) | (173,90,66) | Gray + brown ramp |
| 2  | (181,99,74) | (115,156,181) | Brown to blue |
| 3  | (132,173,189) | (99,165,99) | Blue to green |
| 4  | (123,181,115) | (181,181,90) | Green to yellow |
| 5  | (197,197,115) | (165,132,173) | Yellow to purple |
| 6  | (181,156,181) | (49,33,25) | Purple to dark brown |
| 7  | (41,25,16) | (181,140,74) | Dark to gold |
| 8  | (189,148,90) | (0,0,0) | Gold fade out |
| 9-16 | ... | ... | Additional color ramps |

**Key observation**: Palettes form a CONTINUOUS color ramp across all 17 sub-textures.
Entry [4] in each palette has value 0x8000 (A=1, R=G=B=0) = an alpha marker.

## Pixel Data Analysis
- **Nibble distribution**: 39.2% value 0, 26.6% value 1 (65.8% of all pixels are 0 or 1)
- All 16 values (0-15) are used
- Max consecutive 0x00 bytes: 98 (196 zero nibbles)
- Max consecutive 0x11 bytes: 7 (14 value-1 nibbles)
- Only 226 bytes with value 0xFF in entire pixel data

## Deswizzle Attempts (120 images generated)

### PSMT4 Deswizzle (PSMCT32 upload -> PSMT4 read)
Tested ALL combinations of:
- Header offsets: 0x800, 0x1000
- Texture dimensions: 1024x1024, 512x1024, 1024x512, 512x2048, 512x512, 2048x256
- dbw_ct32 (upload width): 64, 128, 192, 256, 320, 384, 448, 512, 576, 640, 768, 896, 1024
- bw_psmt4 (readback width): 128, 256, 512, 1024, 2048
- With and without nibble swap

**Result**: NO parameter combination produces recognizable text or UI elements.
Best result: dbw=512, bw=1024 shows max run of 263 zeros (suggesting correct background alignment) but pixel-level content remains scrambled.

### PSMT4 with Nibble Swap
Swapping the high/low nibble in each byte before deswizzle:
- Max run of value 15 increases from 5 to 7
- But still no recognizable content

### PSMT8 Deswizzle 
Tested as 512x1024 and 1024x512 with dbw=64 through 512:
- Max runs reach 80-96 (better than PSMT4)
- Shows some structural patterns but no clear text
- **Result**: Also unsuccessful

### PSMCT16 Upload + PSMT4 Read
Tested 1024x256 PSMCT16 upload:
- Max run of 0: 112
- **Result**: Unsuccessful

### PSMCT32 Direct View
At 512x256 viewing as raw RGBA32 pixels:
- **VISIBLE STRUCTURE**: Rectangular shapes at bottom of image resembling UI button outlines
- Confirms the data IS a UI texture but swizzle is not correctly undone

### Direct PSMT4 Read (no upload step)
Reading data directly with PSMT4 block/column tables:
- **Result**: Different scramble pattern, still no clear text

## Key Findings

1. **Confirmed PSMT4 format** from GS register decode (PSM=0x14, 1024x1024)
2. **PSMCT16 palette** with 17 sub-palettes forming a continuous color gradient
3. **Pixel data contains UI elements** (visible in raw CT32 view at 512x256)
4. **Standard PSMT4 deswizzle FAILS** with every parameter combination tested
5. **The 17 identical TEX0 entries** suggest the game reuses the same setup for all sub-textures
6. **CLD=0 in TEX2** means the CLUT is loaded separately (not from this file's GIF tags)

## Possible Explanations for Deswizzle Failure

1. **Non-standard block/column tables**: The game might use a modified PSMT4 swizzle layout that differs from standard PCSX2 GSTables
2. **Multi-pass upload**: The data might be uploaded in multiple passes with different parameters per stripe
3. **Custom DMA chain**: The game may use a custom VIF/DMA chain that processes the data differently before uploading to GS
4. **Format mismatch**: Despite TEX0 saying PSMT4, the actual pixel data might use a proprietary packing scheme
5. **Missing intermediate processing**: The game's CPU code may transform the pixel data before uploading it to GS VRAM

## Recommended Next Steps

1. **PCSX2 VRAM capture**: Use PCSX2's GS debugger to capture the actual VRAM state when R1188 is loaded, then compare with the file data to determine the exact upload mechanism
2. **EXE reverse engineering**: Trace the code that loads type-01 resources to understand the upload pipeline
3. **Compare with working textures**: Examine R2118-R2122 (known working PSMT8) upload code paths in the EXE to identify differences
4. **Try PCSX2 texture dump**: Navigate to the name entry screen in PCSX2 with texture dumping enabled to capture the correctly decoded R1188 atlas
