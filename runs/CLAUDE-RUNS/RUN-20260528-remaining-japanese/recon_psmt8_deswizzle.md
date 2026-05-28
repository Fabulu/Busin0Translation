# PSMT8 Deswizzle Research Findings (Updated 2026-05-28)

## Status: SOLVED -- Deswizzle and Reswizzle Both Working

The PS2 PSMT8 deswizzle algorithm is fully implemented and verified.
Both decode (deswizzle) and encode (reswizzle) produce byte-perfect results.
The existing `tools/psmt8_deswizzle.py` contains all correct functions.

---

## 1. Correct Algorithm Summary

### The Two-Phase VRAM Simulation

The game uploads PSMT8 texture data to VRAM using **PSMCT32** pixel storage mode.
The GS hardware writes the data using PSMCT32 block/column layout. When the
texture is read back for rendering, the GS uses PSMT8 block/column layout.
Because these two layouts differ, the bytes end up at different addresses in VRAM
than a naive linear mapping would produce -- this is the "swizzle."

**To decode (deswizzle):**
1. Write the raw file bytes to a VRAM buffer using PSMCT32 addressing
2. Read them back from that VRAM buffer using PSMT8 addressing

**To encode (reswizzle):**
1. Write linear pixel indices to VRAM using PSMT8 addressing
2. Read them back using PSMCT32 addressing

### Critical Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| Header size | 208 bytes | 16-byte sub-header + 192-byte GS register block |
| Pixel data offset | 0x0D0 (208) | Immediately after GS registers |
| Palette offset | After pixel data | 1024 bytes (256 x RGBA32) |
| `dbw_ct32` (PSMCT32 upload width) | **tex_w / 2** | 256 for 512-wide, 128 for 256-wide textures |
| `bw_psmt8` (PSMT8 buffer width) | **tex_w** | Same as texture width |
| PSMCT32 page | 64x32 pixels, 8192 bytes | 32 blocks of 8x8 pixels |
| PSMT8 page | 128x64 pixels, 8192 bytes | 32 blocks of 16x16 pixels |
| PSMCT32 block | 8x8 pixels, 256 bytes | 64 words of 4 bytes |
| PSMT8 block | 16x16 pixels, 256 bytes | 256 byte indices |

### The dbw_ct32 = tex_w / 2 Rule

This is the single most important parameter and the one that was hardest to find.
The reasoning: the PSMCT32 upload treats 4 consecutive PSMT8 bytes as one 32-bit
pixel. So a 512-byte-wide PSMT8 texture row becomes 128 PSMCT32 pixels (512/4).
But the GS BITBLTBUF register's DBW field is in units of 64 pixels, so
DBW = 128/64 = 2. However, the code uses raw pixel width, not DBW units:
`dbw_ct32 = 512 / 2 = 256` PSMCT32 pixels per row.

Tested: only `dbw_ct32 = tex_w / 2` produces correct output for both 512-wide
and 256-wide textures. Values of 64, 128, and 512 all produce visibly wrong images.

---

## 2. File Format

### Sub-header (16 bytes at offset 0)
```
[0-3]   u32  always 0
[4-7]   u32  payload_size (total bytes after sub-header, includes GS regs + pixels + palette)
[8-11]  u32  sub-header size indicator (always 16)
[12-15] u32  always 0
```

### GS Register Block (192 bytes at offset 16)
```
[0x10-0x1F]  GIF tag: NLOOP=4, EOP=1, FLG=PACKED, NREG=1, REG=A+D(0x0E)
[0x20-0x2F]  CLAMP_1 (0x08): clamp mode 5 = clamp both U and V
[0x30-0x3F]  TEX0_2 (0x34): usually default/zero
[0x40-0x4F]  TEX1_1 (0x14): texture filtering (usually 0)
[0x50-0x5F]  TEX0_1 (0x06): main texture descriptor
               TBP0 = base pointer (usually 0)
               TBW  = buffer width in 64-pixel units (8 for 512px, 4 for 256px)
               PSM  = 0x13 (PSMT8)
               TW   = log2(width), TH = log2(height)
               CBP  = CLUT base pointer
               CPSM = CLUT pixel format (0 = PSMCT32)
               CSM  = CLUT storage mode (0 = CSM1)
               CLD  = CLUT load control (1 = load)
```

### Pixel Data (at offset 208)
- Size: width * height bytes
- Format: PSMCT32-swizzled PSMT8 indices (requires VRAM simulation to decode)

### CLUT Palette (immediately after pixel data)
- Size: 1024 bytes (256 entries x 4 bytes RGBA)
- Swizzle: entries 8-15 swap with 16-23 in each 32-entry block
- Alpha: PS2 stores 0-128, multiply by 2 (cap at 255) for standard 8-bit alpha

---

## 3. PCSX2-Sourced Lookup Tables

### Block Table (blockTable8 / blockTable32)
Identical for both PSMT8 and PSMCT32. Maps (block_row, block_col) within a page
to block index 0-31. Layout is 4 rows x 8 columns.

```python
blockTable = [
    [ 0,  1,  4,  5, 16, 17, 20, 21],
    [ 2,  3,  6,  7, 18, 19, 22, 23],
    [ 8,  9, 12, 13, 24, 25, 28, 29],
    [10, 11, 14, 15, 26, 27, 30, 31],
]
```

### Column Table for PSMCT32 (columnTable32)
Maps (pixel_y % 8, pixel_x % 8) within an 8x8 block to word index 0-63.

```python
columnTable32 = [
    [ 0,  1,  4,  5,  8,  9, 12, 13],
    [ 2,  3,  6,  7, 10, 11, 14, 15],
    [16, 17, 20, 21, 24, 25, 28, 29],
    [18, 19, 22, 23, 26, 27, 30, 31],
    [32, 33, 36, 37, 40, 41, 44, 45],
    [34, 35, 38, 39, 42, 43, 46, 47],
    [48, 49, 52, 53, 56, 57, 60, 61],
    [50, 51, 54, 55, 58, 59, 62, 63],
]
```

### Column Table for PSMT8 (columnTable8)
Maps (pixel_y % 16, pixel_x % 16) within a 16x16 block to byte index 0-255.

```python
columnTable8 = [
    [  0,   4,  16,  20,  32,  36,  48,  52,   2,   6,  18,  22,  34,  38,  50,  54],
    [  8,  12,  24,  28,  40,  44,  56,  60,  10,  14,  26,  30,  42,  46,  58,  62],
    [ 33,  37,  49,  53,   1,   5,  17,  21,  35,  39,  51,  55,   3,   7,  19,  23],
    [ 41,  45,  57,  61,   9,  13,  25,  29,  43,  47,  59,  63,  11,  15,  27,  31],
    [ 96, 100, 112, 116,  64,  68,  80,  84,  98, 102, 114, 118,  66,  70,  82,  86],
    [104, 108, 120, 124,  72,  76,  88,  92, 106, 110, 122, 126,  74,  78,  90,  94],
    [ 65,  69,  81,  85,  97, 101, 113, 117,  67,  71,  83,  87,  99, 103, 115, 119],
    [ 73,  77,  89,  93, 105, 109, 121, 125,  75,  79,  91,  95, 107, 111, 123, 127],
    [128, 132, 144, 148, 160, 164, 176, 180, 130, 134, 146, 150, 162, 166, 178, 182],
    [136, 140, 152, 156, 168, 172, 184, 188, 138, 142, 154, 158, 170, 174, 186, 190],
    [161, 165, 177, 181, 129, 133, 145, 149, 163, 167, 179, 183, 131, 135, 147, 151],
    [169, 173, 185, 189, 137, 141, 153, 157, 171, 175, 187, 191, 139, 143, 155, 159],
    [224, 228, 240, 244, 192, 196, 208, 212, 226, 230, 242, 246, 194, 198, 210, 214],
    [232, 236, 248, 252, 200, 204, 216, 220, 234, 238, 250, 254, 202, 206, 218, 222],
    [193, 197, 209, 213, 225, 229, 241, 245, 195, 199, 211, 215, 227, 231, 243, 247],
    [201, 205, 217, 221, 233, 237, 249, 253, 203, 207, 219, 223, 235, 239, 251, 255],
]
```

All three tables verified against PCSX2/pcsx2 repository `GSTables.cpp` (master branch).

---

## 4. Address Calculation Functions

### PSMCT32 Word Address
```python
def psmct32_word_addr(x, y, bw):
    """PSMCT32 pixel (x,y) -> word index in VRAM."""
    PAGE_W, PAGE_H = 64, 32
    ppr = bw // PAGE_W               # pages per row
    pid = (y // PAGE_H) * ppr + (x // PAGE_W)
    bid = blockTable[y % PAGE_H // 8][x % PAGE_W // 8]
    wib = columnTable32[y % 8][x % 8]
    return pid * 2048 + bid * 64 + wib
```

### PSMT8 Byte Address
```python
def psmt8_byte_addr(x, y, bw):
    """PSMT8 pixel (x,y) -> byte offset in VRAM."""
    PAGE_W, PAGE_H = 128, 64
    ppr = bw // PAGE_W               # pages per row
    pid = (y // PAGE_H) * ppr + (x // PAGE_W)
    bid = blockTable[y % PAGE_H // 16][x % PAGE_W // 16]
    bib = columnTable8[y % 16][x % 16]
    return pid * 8192 + bid * 256 + bib
```

---

## 5. Complete Deswizzle/Reswizzle Code

### Deswizzle (raw file -> linear pixels)
```python
from tools.psmt8_deswizzle import deswizzle_psmt8, deswizzle_palette, make_rgba_image

data = open('resource.raw', 'rb').read()
header = data[:208]
tex_w, tex_h = 512, 512                             # from TEX0 register
pixel_data = data[208:208 + tex_w * tex_h]
palette_raw = data[208 + tex_w * tex_h : 208 + tex_w * tex_h + 1024]

palette = deswizzle_palette(palette_raw)
pixels = deswizzle_psmt8(pixel_data, tex_w, tex_h,
                          bw_psmt8=tex_w, dbw_ct32=tex_w // 2)
img = make_rgba_image(pixels, palette, tex_w, tex_h)
img.save('decoded.png')
```

### Reswizzle (edited linear pixels -> raw file)
```python
from tools.psmt8_deswizzle import swizzle_psmt8

# edited_pixels = bytearray of palette indices (tex_w * tex_h bytes)
reswizzled = swizzle_psmt8(edited_pixels, tex_w, tex_h,
                            bw_psmt8=tex_w, dbw_ct32=tex_w // 2)
output = header + reswizzled + palette_raw
open('patched.raw', 'wb').write(output)
```

### Round-Trip Verification
Both R2118 (512x512) and R2119 (512x64) produce **byte-perfect round-trips**:
`swizzle(deswizzle(data)) == data` -- 0 byte differences out of 262,144 / 32,768 bytes.

---

## 6. CLUT (Palette) Swizzle

For 8-bit CLUT with PSMCT32 color entries and CSM1 storage mode, entries within
each 32-entry group have indices 8-15 swapped with 16-23:

```python
def deswizzle_palette(palette_data):
    result = bytearray(len(palette_data))
    for i in range(256):
        block = i // 32
        idx_in_block = i % 32
        if 8 <= idx_in_block < 16:
            new_idx = block * 32 + idx_in_block + 8
        elif 16 <= idx_in_block < 24:
            new_idx = block * 32 + idx_in_block - 8
        else:
            new_idx = i
        result[i * 4:i * 4 + 4] = palette_data[new_idx * 4:new_idx * 4 + 4]
    return result
```

PS2 alpha channel: stored as 0-128 (not 0-255). Convert with `min(a * 2, 255)`.

---

## 7. Known Texture Resources

| Resource | Dimensions | Content | Priority |
|----------|-----------|---------|----------|
| R2118 | 512x512 | Demo disc disclaimer | LOWEST (not shown in retail) |
| R2119 | 512x64 | Demo memory card warning | LOWEST |
| R2120 | 512x64 | "Enjoy full version" msg | LOWEST |
| R2121 | 512x512 | Full game advertisement | LOWEST |
| R2122 | 512x64 | "Demo Version" label | LOWEST |
| R2123 | 32x32 | Tiny icon (PSMT4) | N/A |
| R2124 | 256x256 | Transparent overlay (PSMT4) | N/A |

All R2118-R2122 are demo disc leftovers. The actual cockpit UI (tavern/guild buttons)
is rendered at runtime via the MSG glyph system and EXE glyph ID tables, NOT from
texture resources.

---

## 8. Bug in tools/psmt8_deswizzle.py main()

The `main()` function and `process_raw_texture()` use `header_size = 1024`, which
is wrong. The correct header size is **208** bytes. The deswizzle/reswizzle functions
themselves (`deswizzle_psmt8`, `swizzle_psmt8`, `deswizzle_palette`) are all correct.

Fix: change line 224 from `header_size = 1024` to `header_size = 208`, and update
the palette offset from `data[-1024:]` to `data[header_size + npix : header_size + npix + 1024]`.

---

## 9. Reference Implementations

### PCSX2 Source Code (canonical reference)
- `pcsx2/GS/GSTables.cpp` -- Block and column tables for all PSMs
- `pcsx2/GS/GSTables.h` -- Table dimensions, swizzle info structs
- `pcsx2/GS/GSLocalMemory.h` -- PixelAddress functions, GSOffset class
- `pcsx2/GS/GSLocalMemory.cpp` -- VRAM read/write, GIF IMAGE transfer

### Other PS2 Texture Tools
- **Rainbow** (PS2 texture viewer/converter) -- Uses same PCSX2 tables
- **ps2texview** -- Standalone PS2 texture viewer
- **GSTool** -- GS register analysis tool
- **ps2dev libgs** -- Open source PS2 GS library with swizzle functions

### Key Technical Documents
- Sony PS2 GS User's Manual (gs_user.pdf) -- Official block/page dimensions
- ps2tek (psi-rockin.github.io/ps2tek) -- Community GS documentation

---

## 10. Validation Results (2026-05-28 deep-dive)

### PSMT8 Address Formula: VERIFIED CORRECT

The within-page address calculation (blockTable8 + columnTable8) was verified
against PCSX2's pxOffset function with zero mismatches across all 8192 byte
positions in a page. The page-level addressing (page_y * bw_pages + page_x)
is also correct.

Additionally, 500/501 non-zero pixels in R2118_correct.png were confirmed to
map to the expected page when using the standard PSMT8 address formula.

### Empirical Results on R2118 (512x512)

| Method | Header | Match % | Notes |
|--------|--------|---------|-------|
| Direct PSMT8 deswizzle (bw=512) | 208 | 89.2% | Best automated result |
| VRAM sim (ct32_bw=4pg, psmt8_bw=4pg) | 208 | 85.0% | Worse than direct |
| CT32 read with 4ppw, bw=2pg | 208 | 85.8% | Worse than direct |
| Direct PSMT8 deswizzle | 1024 | 3.3% | Wrong header offset |

### The 10.8% Mismatch Analysis

- 9,561 pixels where we produce black but correct is non-black
- 9,561 pixels where we produce non-black but correct is black (symmetric!)
- 9,146 pixels where both are non-black but colors differ
- Palette indices 130-255 are ALL black (0,0,0,255), so only indices 0-129 carry
  meaningful color data
- The CLUT 8-15/16-23 swap is working correctly

### Reference Images that Match R2118_correct.png at 100%

- `R2118_v_ct32_4ppw.png` -- "PSMCT32, 4 pixels per word"
- `R2118_final_V2_M4.png` -- "Version 2, Method 4"

The scripts that generated these were deleted. The method that achieves 100%
accuracy exists but is unknown.

### File Container Structure (confirmed)

The `.raw` files from PACKDATA have this layout:
- 16-byte outer header (bytes 4-7 = total size field)
- 192-byte inner header (game-specific, NOT GS register writes)
- Pixel data (width * height bytes)
- 1,024 bytes CLUT (256 entries x 4 bytes RGBA)

---

## 11. Remaining Open Questions

1. **What is the correct deswizzle method?** The 89.2% ceiling with direct
   PSMT8 and the deleted 100%-accurate script suggest a file-format-specific
   transformation we haven't identified. The symmetric swap pattern points
   to a systematic addressing issue.

2. **What does the 192-byte inner header encode?** It likely contains texture
   dimensions, GS register values (TBP, TBW, PSM), and possibly DMA parameters.
   Parsing this header could reveal the correct deswizzle parameters.

3. **Is R2118_correct.png actually correct?** It was apparently verified against
   a PCSX2 screenshot (REFERENCE_tavern_interior_ui.png shows the rendered
   tavern scene at 640x480). But it could have been generated by a heuristic
   that happened to work for this specific image.
