# R1188 GS Register Analysis - Definitive Texture Format

## DEFINITIVE ANSWER

| Property | Value |
|----------|-------|
| **Pixel Storage Mode (PSM)** | **PSMT4** (value 20 = 4-bit indexed, 16 colors per pixel) |
| **Texture Dimensions** | **1024 x 1024** (TW=10, TH=10) |
| **Buffer Width** | 1024 pixels (TBW=16, meaning 16 * 64 = 1024) |
| **CLUT Format (CPSM)** | PSMCT16 (value 2 = 16-bit color, 5-5-5-1 RGBA) |
| **CLUT Load (CLD)** | 1 (load CLUT at draw time) |
| **Sub-textures** | 17 (each with its own GIF packet, all sharing identical format) |

## TEX0_1 Register Decode

Register value: `0x20100006A9440000`

```
Bits  0-13: TBP0  = 0      (texture base pointer)
Bits 14-19: TBW   = 16     (buffer width = 1024px)
Bits 20-25: PSM   = 20     (PSMT4)
Bits 26-29: TW    = 10     (width = 2^10 = 1024)
Bits 30-33: TH    = 10     (height = 2^10 = 1024)
Bit     34: TCC   = 1      (RGBA mode)
Bits 35-36: TFX   = 0      (modulate)
Bits 37-50: CBP   = 0      (CLUT base pointer)
Bits 51-54: CPSM  = 2      (PSMCT16)
Bit     55: CSM   = 0      (CSM1 layout)
Bits 56-60: CSA   = 0      (CLUT storage offset)
Bits 61-63: CLD   = 1      (load CLUT)
```

## Header Structure (0xC00 = 3072 bytes)

```
Offset  Size    Description
------  ------  -----------
0x0000  0x0020  Resource descriptor
                  0x00: 0x00000000 (reserved)
                  0x04: 0x00080C00 (total data size = 527,360 bytes)
                  0x08: 0x00000010 (flags/type = 16)
                  0x10: 0x00000011 (17 = sub-image count)
                  0x14: 0x00000011 (17 = GS block count)

0x0020  0x0550  17 GIF packets (80 bytes each)
                  Each packet is a GIF tag + 4 A+D register writes:
                    GIF tag: NLOOP=4, EOP=1, FLG=0(PACKED), NREG=1, REGS=A+D(0x0E)
                    Write 1: CLAMP_1  (0x08) = 0x05 (clamp to edge)
                    Write 2: MIPTBP1_1(0x34) = mipmaps config
                    Write 3: TEX1_1   (0x14) = 0x00 (no LOD)
                    Write 4: TEX0_1   (0x06) = 0x20100006A9440000 (PSMT4 1024x1024)

0x0570  0x0150  Sprite/frame table (18 entries x 16 bytes)
                  References sub-image indices 0-16 with UV coords

0x06C0  0x0008  Dimensions header: 1024 x 1024

0x06C8  0x0010  Sub-sprite table header (count=332?, type flags)

0x06D8  0x0110  Sub-sprite entries (17 entries x 16 bytes)
                  Each: data_offset, w=8, h=8, stride=2, type=1
                  Offsets: 0x013C, 0x016C, ..., 0x040C (spacing = 0x30)

0x07E8  0x0068  Zero padding

0x0850  0x03B0  Embedded tile/glyph data (referenced by sub-sprite offsets)

0x0C00  END     Pixel data region
```

## Data Region (after header)

```
0x0C00 - 0x80BFF:  524,288 bytes = PSMT4 pixel data (1024x1024 / 2)
0x80C00 - 0x80FFF: 1,024 bytes = CLUT region
```

CLUT region contains only 4 non-zero PSMCT16 color entries (indices 0-3):
- `0x0DF9`, `0x121A`, `0x123A`, `0x165B`
- Remaining 12 colors are black (0x0000)
- The pixel data uses all 16 indices (0-15), so the CLUT may be partially
  loaded at runtime or the trailing colors are intentionally black.

## Comparison with R1272 (Known PSMT4 Font Atlas)

| Property | R1188 | R1272 |
|----------|-------|-------|
| PSM | PSMT4 (20) | PSMT4 (20) |
| Dimensions | 1024x1024 | 256x512 |
| TBW | 16 (1024px) | 4 (256px) |
| CPSM | PSMCT16 (2) | PSMCT32 (0) |
| Sub-images | 17 | 1 |
| Header size | 0xC00 (3072) | 0x100 (256) |
| GIF packets | 17 x 80 bytes | 1 x 80 bytes |

Both use identical GIF packet structure (GIF tag + 4 A+D writes).
R1272 uses PSMCT32 for its CLUT while R1188 uses PSMCT16.

## Implications for Translation

R1188 is definitively **PSMT4** format -- the same indexed-color format as the font
atlas R1272. This means:
- Each byte encodes 2 pixels (4 bits each)
- 16 color palette via CLUT
- PS2 PSMT4 column/block swizzling applies (32x16 pixel blocks, with column swizzle)
- Any decoder/encoder must handle PSMT4 swizzle patterns
- The CLUT uses PSMCT16 (16-bit 5551 RGBA), not PSMCT32 like R1272
