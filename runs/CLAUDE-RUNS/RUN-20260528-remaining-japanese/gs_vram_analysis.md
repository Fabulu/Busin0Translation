# GS VRAM Font Texture Analysis - Save State 27-6

**Date**: 2026-05-28
**Source**: `RAMdumps/27-6.p2s` (patched build, character creation screen)
**Analyst**: Claude Opus 4.6

---

## Save State Context

Screenshot shows the character creation/status screen with:
- English text from our translation (Status, HP/MAX, Personality, etc.)
- Remaining Japanese kanji stat labels (power, intellect, piety, vitality, agility, luck, gender, race, alignment, profession)
- EXE loaded: `SLPM_653.78` (at EE RAM 0x15390)

---

## GS.bin Structure

- Total size: 4,194,813 bytes (509-byte header + 4MB VRAM)
- VRAM offset in file: 509 (0x1FD)
- VRAM data: 4,194,304 bytes (exactly 4MB = 512 8KB pages)

---

## GS Register State (from header)

| Register | Value | Interpretation |
|----------|-------|----------------|
| FRAME_1 | FBP=0x040 | Frame buffer at VRAM 0x020000 (page 16), FBW=8, PSM=PSMCT32 |
| ZBUF_1 | ZBP=0x000 | Z-buffer at VRAM 0x000000 (page 0), PSM=PSMZ24 |

Frame buffer dimensions: 512x448 PSMCT32 (internal render resolution, upscaled to 640x448 for display).

---

## VRAM Layout Overview

PS2 GS VRAM is 4MB organized as physical 2D page grid. Due to GS page layout, the same 8KB page can appear at multiple linear offsets. Analysis found:

| Region | Linear Pages | VRAM Bytes | Size | Content |
|--------|-------------|------------|------|---------|
| Z-Buffer | 0-15 | 0x000000-0x020000 | 128KB | PSMZ24 depth buffer |
| Frame Buffer | 16-127 | 0x020000-0x100000 | 896KB | PSMCT32 rendered frame |
| FB Mirror 1 | 63-175 | 0x07E000-0x160000 | 904KB | Same data as pages 0-112 |
| FB Mirror 2 | 191-303 | 0x17E000-0x260000 | 904KB | ~98.7% match (double-buffered) |
| **Font Textures** | **319-368** | **0x27E000-0x2E2000** | **400KB** | **R1188 kanji atlas tiles + CLUTs** |
| FB Mirror 3 | 383-495 | 0x2FE000-0x3E0000 | 904KB | 100% identical to Mirror 1 |

**Key**: Mirrors are caused by GS 2D page addressing. The same physical VRAM bytes appear at different linear offsets. Font texture data at pages 319-368 resides in VRAM space NOT used by the frame buffer.

---

## Font Textures Found in VRAM

### 1. R1188 - Kanji/Kana/Symbol Atlas (Multiple 256x256 PSMT4 Tiles)

R1188 is a 1024x1024 PSMT4 atlas uploaded as **multiple independent 256x256 PSMT4 tiles**, each with its own TBP0 and CLUT. This was discovered by searching EE RAM for GIF TEX0_1 register writes with PSM=PSMT4.

| TBP0 | VRAM Page | CBP (CLUT) | Tile Content |
|------|-----------|------------|-------------|
| 0x2840 | 322 | 0x28C0 | Kanji rows (confirmed: glyphs visible) |
| 0x28CA | 326 | 0x294A | Kanji rows |
| 0x2954 | 330 | 0x29D4 | Kanji rows |
| 0x29DE | 334 | 0x2A5E | Kanji rows |
| 0x2B08 | 344 | 0x2B88 | Kanji rows |
| 0x2BA4 | 349 | 0x2C24 | Kanji rows |
| 0x2C34 | 353 | 0x2CB4 | Kanji rows |
| 0x2CC4 | 358 | 0x2D44 | Kanji rows |
| 0x2D56 | 362 | 0x2DD6 | Kanji rows (sparser, end of atlas) |

**Pattern**: Each tile is 256x256 PSMT4 with TBW=4. CLUT is always at TBP0+0x80 (= tile_size/256 = 32768/256 = 128 blocks = 0x80). Tile spacing varies (not uniform).

**Total VRAM used**: TBP0 0x2840 to 0x2DD6+0x80 = approximately 0x2E56. In bytes: (0x2E56-0x2840)*256 = 389,376 bytes (~380KB).

Additional smaller R1188 tiles found:
| TBP0 | Size | Notes |
|------|------|-------|
| 0x2A68 | 256x256 | Additional kanji tile (page 339) |
| 0x310F | 256x256 | Possible UI element (page 392) |
| 0x3195 | 256x256 | Possible UI element (page 396) |
| 0x3579 | 256x256 | Possible UI element (page 427) |

### 2. R1272 - English ASCII Font Atlas (256x512 PSMT4)

| Parameter | Value |
|-----------|-------|
| TBP0 | 0x3000 |
| VRAM Offset | 0x300000 (page 384) |
| TBW | 4 |
| Dimensions | 256x512 |
| PSM | PSMT4 |
| CBP (CLUT) | 0x310B |

**CRITICAL FINDING**: R1272 at TBP0=0x3000 overlaps with the frame buffer mirror region (pages 383-495). In the save state snapshot, the frame buffer has been rendered OVER the R1272 location, making R1272 data unrecoverable from this save state. The R1272 was uploaded, used for rendering the English text visible on screen, and then the frame buffer rendering overwrote that VRAM region.

This is consistent with PS2 games commonly sharing VRAM between textures and frame buffers -- textures are uploaded before rendering, used, and then the rendered frame replaces them.

**Verified from build artifacts**: `build/v27_r1272_deswizzled.png` confirms R1272 contains our English ASCII font atlas (letters A-Z, a-z, 0-9, punctuation) followed by recently-rendered text fragments.

### 3. Smaller UI/Font Textures

Additional PSMT4 textures found in the kanji VRAM region:

| TBP0 | Size | CBP | Notes |
|------|------|-----|-------|
| 0x3327 | 256x256 | 0x33A8 | UI element (page 409) |
| 0x319F | 256x256 | 0x321F | UI element (page 396) |
| 0x34F8 | 256x256 | 0x3578 | UI element (page 423) |
| 0x3220 | 512x256 | 0x3322 | UI element (page 401) |
| 0x3432 | 256x128 | 0x3472 | Small texture (page 417) |
| 0x30C6 | 256x128 | 0x3106 | Small texture (page 390) |
| 0x33AE | 256x128 | 0x33EE | Small texture (page 413) |
| 0x3478 | 256x128 | 0x33F8 | Small texture (page 419) |
| 0x34B8 | 128x128 | 0x33FA | Small texture (page 421) |
| 0x34D8 | 128x128 | 0x33FC | Small texture (page 422) |
| 0x3223 | 128x128 | 0x3243 | Small texture (page 401) |

These appear to be UI tab graphics, icons, and other small elements loaded alongside the font textures.

---

## Cell Data VRAM Addressing System

The font page table (50 entries at EXE VA 0x4DB100, file 0x3DB180) maps glyph page numbers to cell data arrays. Each cell has 8 bytes:

```
byte 0: U (column/X position in atlas)
byte 1: V (row/Y position in atlas - pixel coordinate)
byte 2: W (width in pixels, typically 100)
byte 3: flag
byte 4-5: VRAM address (u16 LE, in 64-byte word units)
byte 6-7: extra data
```

**Address conversion**: cell_vram_addr * 64 = VRAM byte offset. TBP0 = cell_vram_addr * 64 / 256 = cell_vram_addr / 4.

**Range**: Cell VRAM addresses span 0xA140 to 0xBF38 (in 64-byte words), corresponding to TBP0 range 0x2850 to 0x2FCE, spanning VRAM pages 322-383.

**V-stride**: Consecutive V values (V, V+1) increment the VRAM address by 8 64-byte words = 512 bytes. This equals one pixel row of a 1024-pixel-wide PSMT4 texture (1024 pixels * 0.5 bytes/pixel = 512 bytes/row).

**Descriptor indices used**: 0 (most pages), 1 (page 13), 2 (pages 3-8, 14-24), 9 (page 0 only). These index runtime texture descriptors at VA 0x4DBBE0.

---

## Summary of All Font Textures

| Resource | Format | Dimensions | VRAM TBP0 | VRAM Pages | Role |
|----------|--------|------------|-----------|------------|------|
| R1188 | PSMT4 | 1024x1024 (as 9+ 256x256 tiles) | 0x2840-0x2D56 | 322-362 | Kanji, kana, symbols, UI labels |
| R1272 | PSMT4 | 256x512 | 0x3000 | 384-391 | ASCII/Latin dialogue font |

**Total font VRAM usage**: ~448KB (R1188 tiles + CLUTs + R1272 + CLUT)

---

## Implications for Translation

1. **R1188 tiles are independently addressable**: Each 256x256 PSMT4 tile has its own TBP0. Editing specific kanji glyphs requires modifying the correct tile. The cell data maps glyph IDs to specific VRAM addresses within these tiles.

2. **R1272 shares VRAM with frame buffer**: The English font at TBP0=0x3000 is uploaded before each render pass and then overwritten by the frame buffer. This is normal PS2 behavior -- the game re-uploads textures as needed.

3. **CLUT is always 0x80 blocks after TBP0**: For all R1188 tiles, CBP = TBP0 + 0x80. This is a consistent pattern the game uses for palette placement.

4. **Cell VRAM addressing confirms single atlas model**: Despite being uploaded as separate 256x256 tiles, all R1188 cells reference positions within a conceptual 1024-pixel-wide atlas. The VRAM address increments by 8 per pixel row, matching a 1024px-wide texture layout.
