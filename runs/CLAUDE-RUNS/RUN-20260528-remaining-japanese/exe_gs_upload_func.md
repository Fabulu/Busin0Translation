# EXE GS Upload Function & R1188 Format Analysis

## Summary

R1188 is a **PSMT4 (4-bit indexed color) 1024x1024 texture atlas** with 17 sub-textures
and individual 16-color CLUT palettes in PSMCT16 format.

The PSM (pixel storage mode) is embedded in pre-built **TEX0 GIF register packets** stored
inside the resource itself -- the EXE does not parse a separate "PSM header field" but
instead sends these pre-built GIF packets directly to the GS via DMA.

---

## R1188 Resource Structure (type-01 format)

```
File layout (raw):
  Offset   Size      Content
  ------   ----      -------
  0x0000   16 bytes  Outer header: [0, data_size=527360, sub_count=16, 0]
  0x0010   ...       Inner data begins

Inner data layout (offsets relative to inner data start):
  0x0000   16 bytes  Header: [17, 17, 0, 0]  (sub_count x2 + padding)
  0x0010   1360 B    17 x 80-byte GIF A+D blocks (TEX0 register setup)
  0x0560   360 B     18 x 20-byte UV/sub-texture descriptor entries
  0x06B4   ~332 B    CLUT offset table (17 entries x 16 bytes + header)
  0x0800   ~1024 B   CLUT palette data (17 palettes, 32 bytes each in PSMCT16)
  0x0C00   524288 B  Pixel data (PSMT4 format, 1024x1024)
```

Total inner data: 0xC00 (header/meta) + 0x80000 (pixel data) = 527360 bytes (matches header).

---

## TEX0 Register Values (PSM lives here)

Each of the 17 sub-textures has an 80-byte GIF A+D block at inner offset `0x10 + i*0x50`.
The block contains 4 GS register writes:

| Offset in block | Register    | R1188 Value          |
|-----------------|-------------|----------------------|
| +0x10           | CLAMP_1     | 0x0000000000000005   |
| +0x20           | MIPTBP1_1   | 0x0080001000020000   |
| +0x30           | TEX1_1      | 0x0000000000000000   |
| +0x40           | **TEX0_1**  | **0x20100006A9440000** |

### TEX0 Decoded (0x20100006A9440000):

| Field | Bits    | Value | Meaning                          |
|-------|---------|-------|----------------------------------|
| TBP0  | 0-13    | 0x0   | Texture base pointer (set at runtime) |
| TBW   | 14-19   | 16    | Texture buffer width (64-pixel units) = 1024 |
| **PSM** | **20-25** | **0x14** | **PSMT4 (4-bit indexed)**    |
| TW    | 26-29   | 10    | Width = 2^10 = 1024              |
| TH    | 30-33   | 10    | Height = 2^10 = 1024             |
| TCC   | 34      | 1     | RGBA mode                        |
| TFX   | 35-36   | 0     | Modulate                         |
| CBP   | 37-50   | 0x0   | CLUT base pointer (set at runtime) |
| CPSM  | 51-54   | 2     | CLUT format: PSMCT16             |
| CSM   | 55      | 0     | CSM1 mode                        |
| CSA   | 56-60   | 0     | CLUT start address               |

---

## How the EXE Processes This

### PSM Source
The EXE does **NOT** read PSM from a standalone header field. Instead:
1. The resource contains pre-built GIF A+D packets with TEX0 register values
2. TEX0 bits 20-25 contain the PSM (0x14 = PSMT4 for R1188)
3. The EXE sends these packets directly to the GS via DMA channel 2

### GS Upload Functions Found

| VA         | Purpose                | BITBLTBUF DPSM | TRXDIR |
|------------|------------------------|----------------|--------|
| 0x0047D3D0 | VRAM readback          | PSMCT32 (0)    | 1 (Local->Host) |
| 0x0047DE50 | VRAM readback (variant)| PSMCT32 (0)    | 1 (Local->Host) |
| 0x0047EC00 | VRAM-to-VRAM copy      | PSMCT32 (0)    | 2 (Local->Local) |

These functions hardcode DPSM=0 (PSMCT32) because they transfer raw data blocks.
The actual Host->Local pixel upload likely uses DMA path 2 directly with BITBLTBUF
DPSM matching the TEX0 PSM, built elsewhere in the resource loading pipeline.

### Key Helper Functions

| VA         | Purpose                                          |
|------------|--------------------------------------------------|
| 0x004835A0 | Get texture width from global struct at 0x5710A8 |
| 0x004835B0 | Get texture height from 0x5710AA                 |
| 0x004834C0 | Look up VRAM allocation from table at 0x4D6858   |
| 0x0047E710 | Allocate DMA buffer for GIF packet               |
| 0x0047E7B0 | Set up DMA chain entry                           |
| 0x0047F390 | Build GIF A+D tag (NLOOP=1, REG=TEXFLUSH)        |

### Global Texture State (0x005710A0-0x005710B5)

```
+0x00 (0x5710A0): u32  - pointer/context
+0x04 (0x5710A4): u32  - pointer/context  
+0x08 (0x5710A8): u16  - width (e.g., 512 default, set per resource)
+0x0A (0x5710AA): u16  - height (e.g., 448 default)
+0x0E (0x5710AE): u16  - flags/params
+0x10 (0x5710B0): u8   - flag
+0x11 (0x5710B1): u8   - flag
+0x12 (0x5710B2): u8   - flag
```

---

## PSM Distribution Across All Type-01 Resources

| PSM     | Count | Notes                    |
|---------|-------|--------------------------|
| PSMT8   | 515   | 8-bit indexed (256 colors) |
| PSMT4   | 497   | 4-bit indexed (16 colors)  |

Total: 1012 valid texture resources out of 1642 type-01 files.

---

## Sub-texture Descriptor Format (20 bytes each)

```
+0x00: u16  sub_index (always 0 in R1188)
+0x02: u16  uv_u1 (0xFFFF = full texture)
+0x04: u16  uv_v1 (0xFFFF)
+0x06: u16  uv_u2 (0xFFFF)  
+0x08: u16  texture_id (0-16, maps to TEX0 block index)
+0x0A: u8   flag1 (01)
+0x0B: u8   flag2 (01)
+0x0C: u32  padding (0)
+0x10: u16  width (0x0400 = 1024)
+0x12: u16  height (0x0400 = 1024)
```

---

## CLUT (Palette) Data

- Format: PSMCT16 (16-bit color per entry)
- 16 colors per CLUT (PSMT4)
- 17 individual CLUTs (one per sub-texture)
- Located at inner offset 0x800
- Each CLUT: 32 bytes (16 colors x 2 bytes)
- Spaced 48 bytes apart (32 data + 16 padding)
- CLUT offset table at inner offset 0x6B4 provides per-texture CLUT offsets

---

## Practical Implications for Translation

1. **R1188 is PSMT4**: To edit, decode as 4-bit indexed with PSMCT16 CLUT
2. **PSM is in TEX0**: When modifying texture resources, the PSM in the TEX0 GIF
   packets (bits 20-25 of the TEX0 qword) determines the format
3. **17 sub-textures share one atlas**: All are 1024x1024 with individual palettes
4. **No PSM header byte**: Unlike simpler formats, there is no single "PSM byte"
   at a fixed offset -- it is embedded in the GIF packet data structure
