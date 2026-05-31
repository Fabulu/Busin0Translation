# Font Pages R1304-R1311 Analysis: NOT Font Resources

**Date**: 2026-05-28
**Analyst**: Claude Opus 4.6

---

## Executive Summary

**R1304-R1311 are NOT font resources.** They are PSMT8 environment/background textures (512x512, full-color palettes). The table at EXE offset 0x3CA968 is a texture resource loading list, NOT a font page table.

**All kanji font glyphs (including stat labels) come from R1188**, a single 1024x1024 PSMT4 texture atlas. Stat labels, menu labels, and name entry tab labels all reference tiles within R1188 via the cell data table system.

---

## R1304-R1311 Resource Analysis

| Resource | Format | Dimensions | File Size | Content |
|----------|--------|------------|-----------|---------|
| R1304 | PSMT8 | 512x512 | 264,192 | Environment texture (tree/organic) |
| R1305 | PSMT8 | 512x512 | 264,192 | Environment texture |
| R1306 | PSMT8 | 512x512 | 264,192 | Environment texture |
| R1307 | PSMT8 | 512x512 | 264,192 | Environment texture |
| R1308 | PSMT8 | 256x512 | 133,120 | Environment texture |
| R1309 | PSMT8 | 512x512 | 264,192 | Environment texture |
| R1310 | PSMT8 | 512x512 | 264,192 | Environment texture |
| R1311 | PSMT8 | 512x512 | 264,192 | Environment texture |

**Header structure**: 2048 bytes (0x800), with pixel data at 0x800 and 1024-byte RGBA32 palette at end.
**Palette**: Full-color (earthy greens/browns), NOT monochrome font palette.
**Proof**: R1304 deswizzled to `R1304_deswizzled.png` -- shows a tree/organic environment texture, not glyphs.

---

## Table at 0x3CA968: Texture Resource List (NOT Font)

The table at EXE offset 0x3CA968 (VA 0x4CA9E8) lists 41 unique PACKDATA resource IDs as paired uint32 entries (82 total values, each `resource_id << 16`). Resources span R1269-R1311 (skipping R1272 and R1283).

This table is used by a general texture loading system, not font-specific logic. All 41 resources are PSMT8 format -- a mix of environment textures, UI backgrounds, and similar assets.

---

## The ACTUAL Font Page System

### Resources
| Resource | Format | Dimensions | Role |
|----------|--------|------------|------|
| R1188 | PSMT4 | 1024x1024 | **Main kanji/kana/symbol atlas** |
| R1272 | PSMT4 | 256x512 | **ASCII/Latin font atlas** (our replacement) |

### Architecture
```
Glyph ID (e.g., 0x015A = 346)
  |
  +-- page = id >> 8 (e.g., 0x01)
  +-- cell = id & 0xFF (e.g., 0x5A)
  |
  v
Page Table at VA 0x4DB100 (file 0x3DB180)
  |
  +-- page_entry[page].desc_idx (runtime texture descriptor)
  +-- page_entry[page].cell_data_ptr (points to cell array)
  |
  v
Cell Data Array (8 bytes per cell)
  |
  +-- byte0: U tile coordinate (column in atlas)
  +-- byte1: V tile coordinate (row in atlas)
  +-- byte2: Width in pixels (usually 100)
  +-- byte3: Flag (two-cell-wide indicator)
  +-- byte4-5: GS VRAM block address (u16 LE) - WHICH TEXTURE PAGE
  |
  v
GS renders textured sprite from VRAM at specified block address
```

### Key Insight: Per-Cell VRAM Addressing

Each cell has its own VRAM block address (bytes 4-5). This address tells the GS which texture page in VRAM to sample from. R1188's 1024x1024 PSMT4 data occupies ~2048 VRAM blocks (0x800 range). All stat label glyphs have VRAM addresses in the 0xA000-0xA800 range, confirming they all come from R1188.

---

## Stat Label Glyph Mapping

| Stat Label | Japanese | Glyph IDs | Page | Cell | U | V | VRAM |
|-----------|----------|-----------|------|------|---|---|------|
| STR | chikara | 346 | 0x01 | 0x5A | 0 | 60 | 0xA350 |
| INT char 1 | chie | 535 | 0x02 | 0x17 | 0 | 67 | 0xA178 |
| INT char 2 | e | 717 | 0x02 | 0xCD | 3 | 88 | 0xA700 |
| FTH char 1 | shin | 308 | 0x01 | 0x34 | 0 | 76 | 0xA238 |
| FTH char 2 | kou | 354 | 0x01 | 0x62 | 0 | 66 | 0xA390 |
| FTH char 3 | kokoro | 320 | 0x01 | 0x40 | 0 | 62 | 0xA290 |
| VIT char 1 | sei | 718 | 0x02 | 0xCE | 4 | 60 | 0xA708 |
| VIT char 2 | mei | 696 | 0x02 | 0xB8 | 3 | 67 | 0xA658 |
| VIT char 3 | chikara (shared with STR) | 346 | 0x01 | 0x5A | 0 | 60 | 0xA350 |
| AGI char 1 | bin | 582 | 0x02 | 0x46 | 0 | 60 | 0xA2E0 |
| AGI char 2 | soku | 719 | 0x02 | 0xCF | 4 | 61 | 0xA710 |
| AGI/LCK suffix | do (degree) | 590 | 0x02 | 0x4E | 0 | 60 | 0xA318 |
| LCK char 1 | kou | 720 | 0x02 | 0xD0 | 4 | 62 | 0xA718 |
| LCK char 2 | un | 721 | 0x02 | 0xD1 | 4 | 63 | 0xA720 |

---

## Options for Translation

### Option A: Edit R1188 Tiles (modify the kanji atlas)

Replace the kanji glyph pixels at the mapped positions with English letter glyphs.

**Pros**: Works for ALL rendering contexts that use these glyph IDs.
**Cons**: R1188 is a 1024x1024 PSMT4 texture requiring correct deswizzle/reswizzle. Tiles are shared between stat labels and other uses (e.g., glyph 696 also appears in menu entry 6 "venture", glyph 717/718 in entry 17 "create"). Editing a shared tile changes ALL contexts.

**Already available**: `R1188_CORRECT_dbw512.png` (deswizzled), `psmt4_deswizzle.py` tools exist.

### Option B: Patch Cell Data (redirect UV+VRAM)

Modify the cell data bytes (U, V, VRAM address) at known EXE file offsets to point stat label glyphs at our R1272 ASCII atlas instead.

**Pros**: Surgically precise -- only affects the specific glyph.
**Cons**: Requires knowing R1272's VRAM upload address at runtime, and the desc_idx for R1272 must match. The cell data uses desc_idx=0 (shared by R1188 pages) -- R1272 might use a different descriptor. Format mismatch: R1188 is PSMT4, R1272 is also PSMT4, so compatible.

**Cell data file offsets**:
| Glyph | File Offset | Bytes to Patch |
|-------|-------------|----------------|
| 346 | page1_base + 0x5A*8 = 0x3D8D70 + 0x2D0 = 0x3D9040 | U,V,W,VRAM |
| 535 | page2_base + 0x17*8 = 0x3D8D90 + 0xB8 = 0x3D8E48 | U,V,W,VRAM |
| etc. | (computed from page base + cell*8) | |

### Option C: Replace Glyph IDs in EXE (redirect to ASCII glyphs)

Change the glyph ID values in the EXE so stat labels use ASCII glyph IDs from R1272 instead of kanji glyph IDs from R1188.

**Critical finding**: The stat label glyph IDs are NOT stored in a simple stat-label table. They appear in:
1. **Table 2C menu entries** as shared glyph tiles (e.g., entry 17 uses glyph 717/718 for "create" label)
2. **Name entry kanji table** at 0x3C8CA8 (sequential glyph list for kanji input)
3. **Hardcoded in rendering functions** (via immediate operands in MIPS code -- 993 calls to render_glyph_sprite)

Replacing glyph IDs would break ALL contexts that share those tiles.

### Option D: Override in Rendering Code (EXE code hook)

Intercept the `render_glyph_sprite` function (VA 0x494350) or the stat screen rendering function to substitute glyph IDs at render time. This is the most flexible but requires a code cave and careful function identification.

---

## Recommended Approach

**Option A (Edit R1188) is the most practical path**, given that:
1. The deswizzle/reswizzle toolchain already works (`psmt4_deswizzle.py`)
2. The atlas has been successfully exported (`R1188_CORRECT_dbw512.png`)
3. Tile positions are mapped via cell data (U, V coordinates)
4. The rendering system is tile-based and resolution-compatible

**For shared glyphs** (e.g., glyph 346 used as both "STR" stat label AND the kanji in "chikara/seimei"), the English replacement should work in ALL contexts where that kanji appears -- since the game only displays each glyph as a visual tile, replacing the tile with an English abbreviation letter will look correct everywhere.

---

## Key Addresses

| What | VA | File Offset | Size |
|------|-----|-------------|------|
| Page table (50 entries x 8 bytes) | 0x4DB100 | 0x3DB180 | 400 bytes |
| Page 0x01 cell data | 0x4D8CF0 | 0x3D8D70 | variable |
| Page 0x02 cell data | 0x4D8D10 | 0x3D8D90 | variable |
| render_glyph_sprite function | 0x494350 | 0x3943D0 | ~256 bytes |
| Resource list (NOT font table) | 0x4CA9E8 | 0x3CA968 | 328 bytes |
| R1188 atlas resource | PACKDATA index 1188 | packdata_raw/1188_type01.raw | 528,384 bytes |
| R1272 ASCII font resource | PACKDATA index 1272 | packdata_raw/1272_type01.raw | 67,584 bytes |

---

## Corrected Understanding

The original hypothesis was wrong: R1304-R1311 are NOT kanji font pages. The game's font system uses exactly **two** texture atlas resources:
- **R1188** (1024x1024 PSMT4): All kanji, kana, symbols, UI labels, tab graphics
- **R1272** (256x512 PSMT4): ASCII/Latin characters for dialogue text

The "font page table at 0x3CA968" is actually a general texture resource loading list unrelated to fonts. The actual font page system uses the page table at 0x3DB180, which maps glyph page numbers to cell data arrays with per-cell UV coordinates and VRAM addresses pointing into R1188's VRAM space.
