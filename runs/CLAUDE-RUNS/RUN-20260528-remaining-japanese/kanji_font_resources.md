# Kanji Font Resources: Definitive Identification

**Date**: 2026-05-28

---

## Executive Summary

The kanji font tiles (including stat labels like STR/INT/VIT/AGI/LCK) are provided by a **single PACKDATA resource: R1188**. This is a PSMT4 1024x1024 texture atlas containing all kanji, kana, symbols, and UI label glyphs. It is a completely different font system from R1272 (the ASCII/Latin VWF font used for dialogue text).

The table at EXE offset 0x3CA798 (99 entries of paired resource IDs) is **NOT a font page table** -- it is a general texture resource loading list containing character portraits, environment textures, and other game assets.

---

## The Two Font Resources

| Resource | PACKDATA File | Type | Format | Dimensions | TBW | Size | Role |
|----------|--------------|------|--------|------------|-----|------|------|
| **R1188** | `1188_type01.bin` | type01 | **PSMT4** | 1024x1024 | 16 | 527,360 bytes | Kanji/kana/symbol atlas (ALL stat labels, menu labels, tab labels) |
| **R1272** | `1272_type01.bin` | type01 | **PSMT4** | 256x512 | 4 | 65,792 bytes | ASCII/Latin font atlas (dialogue VWF text) |

### R1188 Structure
- **Header**: 17 GIF upload packets (TEX0 register writes confirming PSMT4 1024x1024 TBW=16)
- **Pixel data**: 524,288 bytes (1024 x 1024 / 2 nibbles per byte)
- **Palette**: 16-color RGBA32 CLUT (64 bytes) + header overhead = 3,072 bytes
- **VRAM range**: 0xA140 - 0xA9B0 (all glyph cells reference this range)

### R1272 Structure
- **Header**: Single GIF upload packet (TEX0: PSMT4 256x512 TBW=4)
- **Pixel data**: 65,536 bytes (256 x 512 / 2)
- **Size**: 65,792 bytes total

---

## Font Page System Architecture

### Page Table
- **Location**: EXE file offset `0x3DB180` (VA `0x4DB100`)
- **Format**: 50 entries x 8 bytes each
- **Entry structure**: `[desc_idx: u32] [cell_data_ptr: u32 VA]`

### Glyph ID to Resource Mapping
```
glyph_id (e.g., 346 for STR/chikara)
  |
  page_index = glyph_id / 256   (346 / 256 = 1)
  cell_index = glyph_id % 256   (346 % 256 = 0x5A)
  |
  v
page_table[page_index]
  -> desc_idx (runtime GS texture descriptor index)
  -> cell_data_ptr (VA pointing to 256-entry cell array)
  |
  v
cell_data[cell_index] (8 bytes per cell)
  byte 0: U (column tile coordinate in atlas)
  byte 1: V (row tile coordinate in atlas)
  byte 2: W (pixel width, typically 100)
  byte 3: Flag (two-cell-wide indicator)
  bytes 4-5: VRAM block address (u16 LE)
  bytes 6-7: Extra/padding
  |
  v
GS renders textured sprite from VRAM at (U, V) in R1188 atlas
```

### desc_idx Distribution
| desc_idx | Pages | Likely Meaning |
|----------|-------|----------------|
| 0 | 31 | Primary R1188 descriptor (kanji/stat labels) |
| 1 | 1 | Alternate R1188 descriptor (page 13) |
| 2 | 17 | Alternate R1188 descriptor (pages 3-8, 14-19) |
| 9 | 1 | Alternate descriptor (page 0, ASCII-range glyphs) |

All 50 pages use VRAM addresses in the 0xA140-0xA9B0 range, confirming they ALL reference R1188 data in VRAM.

---

## Glyph 346 (STR / chikara / 力) Specifics

| Field | Value |
|-------|-------|
| Glyph ID | 346 (0x015A) |
| Page index | 1 |
| Cell index | 0x5A (90) |
| desc_idx | 0 |
| Cell data file offset | `0x3D9040` |
| U (column tile) | 1 |
| V (row tile) | 60 |
| W (pixel width) | 100 |
| VRAM block | 0xA450 |
| **Resource** | **R1188** (PSMT4 1024x1024) |

---

## All Stat Label Glyphs (all in R1188)

| Stat | Japanese | Glyph ID | Page | Cell | U | V | VRAM |
|------|----------|----------|------|------|---|---|------|
| STR | 力 (chikara) | 346 | 1 | 0x5A | 1 | 60 | 0xA450 |
| INT char1 | 知 (chie) | 535 | 2 | 0x17 | 0 | 67 | 0xA1F0 |
| INT char2 | 恵 (e) | 717 | 2 | 0xCD | 3 | 88 | 0xA700 |
| FTH char1 | 信 (shin) | 308 | 1 | 0x34 | 0 | 76 | 0xA238 |
| FTH char2 | 仰 (kou) | 354 | 1 | 0x62 | 0 | 66 | 0xA390 |
| FTH char3 | 心 (kokoro) | 320 | 1 | 0x40 | 0 | 62 | 0xA290 |
| VIT char1 | 生 (sei) | 718 | 2 | 0xCE | 4 | 60 | 0xA708 |
| VIT char2 | 命 (mei) | 696 | 2 | 0xB8 | 3 | 67 | 0xA658 |
| VIT char3 | 力 (shared) | 346 | 1 | 0x5A | 1 | 60 | 0xA450 |
| AGI char1 | 敏 (bin) | 582 | 2 | 0x46 | 0 | 60 | 0xA2E0 |
| AGI char2 | 速 (soku) | 719 | 2 | 0xCF | 4 | 61 | 0xA710 |
| AGI/LCK suffix | 度 (do) | 590 | 2 | 0x4E | 0 | 60 | 0xA318 |
| LCK char1 | 幸 (kou) | 720 | 2 | 0xD0 | 4 | 62 | 0xA718 |
| LCK char2 | 運 (un) | 721 | 2 | 0xD1 | 4 | 63 | 0xA720 |

---

## The Table at 0x3CA798 (NOT Font Pages)

The table at EXE file offset `0x3CA798` (VA `0x4CA818`) contains 99 entries (each 8 bytes: resource ID repeated twice as `resid << 16`). These are **general texture resources**, not font pages:

- **R1215-R1268** (54 entries): Character portraits, PSMT8 512x512 (e.g., R1215 = warrior portrait)
- **R1269-R1311** (42 entries, with gaps): Environment textures, UI backgrounds, PSMT8 512x512
- **3 zero/gap entries** at pages 54-56

All of these are **PSMT8 format** (not PSMT4), with full-color palettes. They are NOT font resources.

---

## Deswizzle Capability

| Resource | Format | Deswizzle Status |
|----------|--------|-----------------|
| R1188 | PSMT4 1024x1024 | Toolchain exists (`psmt4_deswizzle.py`), successfully decoded to `R1188_CORRECT_dbw512.png` |
| R1272 | PSMT4 256x512 | Already being edited for English translation |

---

## Translation Options for Stat Labels

Since stat labels render from **R1188** (not R1272), there are two approaches:

### Option A: Edit R1188 Tile Pixels
Replace the Japanese glyph pixels at the mapped U,V positions with English letter tiles. Requires PSMT4 deswizzle -> edit -> reswizzle pipeline. Affects ALL contexts using those glyph IDs (stat labels + any other screen using the same kanji).

### Option B: Redirect Cell Data in EXE
Patch the cell data bytes (U, V, VRAM address) for stat label glyph cells to point at English letter tiles within R1272's VRAM space. Requires knowing R1272's runtime VRAM upload base address and ensuring the desc_idx is compatible.

### Option C: EXE Code Hook
Intercept the `render_glyph_sprite` function (VA `0x494350`) to substitute glyph IDs at render time, redirecting stat label kanji to ASCII equivalents in R1272.

**Recommended**: Option A is most straightforward given existing deswizzle tooling.
