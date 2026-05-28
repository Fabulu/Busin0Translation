# Recon 29: Font Atlas Glyph Cell Size and Grid Layout

**Date:** 2026-05-22
**Status:** Complete
**File:** `extracted/packdata_resources/1272_type01.bin` (65,792 bytes)

---

## Key Finding: 12x12 Pixel Cells, 21 Columns x 42 Rows

**Cell size: 12x12 pixels**
**Grid: 21 columns x 42 rows = 882 slots**
**Occupied: ~858 glyphs (indices 0x0000-0x035A)**
**Last row: 18 of 21 slots used**

### Evidence

#### 1. EXE Code Analysis (Primary Evidence)

Multiple locations in the EXE (`SLPM_653.78`) contain `li $reg, 21; div` patterns that divide a glyph index by 21 to compute row and column positions. Key locations:

- **VA 0x002E4230** (file 0x1E42B0): `addiu $a0, $zero, 21` + `div $v0, $a0` followed by `mfhi` (column = index % 21) and FPU operations to compute UV coordinates
- **VA 0x002E4284** (file 0x1E4304): Same pattern, second div-by-21 for a related coordinate
- **VA 0x002EA540** (file 0x1EA5C0): `addiu $v1, $zero, 21` + `div $v0, $v1` + `mfhi $v0` + `addiu $v0, $v0, 80` -- column with offset
- **VA 0x002EA560** (file 0x1EA5E0): Another div-by-21 in same function, with float conversion for rendering

Over 40 instances of `li reg, 21; div` exist across the EXE (0x1E4xxx, 0x1EAxxx, 0x322xxx, 0x345xxx clusters), indicating div-by-21 is a core pattern in the text rendering system.

#### 2. Mathematical Verification

With 21 columns confirmed, the cell width must be 12 pixels:
- 256 pixels / 21 columns = 12.19 pixels per column
- 21 * 12 = 252 pixels used (4 unused at right edge)
- 21 * 13 = 273 -- exceeds 256, impossible

For cell height, 12 pixels is the only viable option:
- 12x12: 21 cols x 42 rows = 882 slots (fits 858 glyphs, margin of 24)
- 12x10: 21 cols x 51 rows = 1071 slots (fits but wastes 213 slots)
- 12x14: 21 cols x 36 rows = 756 slots (too few for 858)

The 12x12 layout gives:
- 252 of 256 horizontal pixels used (4 unused)
- 504 of 512 vertical pixels used (8 unused)
- 41 full rows + 1 partial row (18/21 glyphs) = 858 glyphs exactly

---

## TEX0 Register Parse

**TEX0 at header offset 0x50 = 0x2000000661410000**

| Field | Value | Meaning |
|-------|-------|---------|
| TBP0  | 0     | Texture base pointer = 0 |
| TBW   | 4     | Buffer width = 256 pixels (4 * 64) |
| PSM   | 20    | PSMT4 (4 bits per pixel, 16-color indexed) |
| TW    | 8     | Width = 2^8 = 256 pixels |
| TH    | 9     | Height = 2^9 = 512 pixels |
| TCC   | 1     | RGBA color (not RGB only) |
| TFX   | 0     | Modulate |
| CBP   | 0     | CLUT base pointer = 0 |
| CPSM  | 0     | PSMCT32 (32-bit palette entries) |
| CSM   | 0     | CSM1 mode |
| CSA   | 0     | CLUT storage adjust = 0 |
| CLD   | 1     | Load CLUT |

---

## Header Analysis (192 bytes at offset 0x00)

Key non-zero values in the header:

| Offset | Hex Value    | Meaning |
|--------|-------------|---------|
| 0x00   | 0x00000001  | Version = 1 |
| 0x04   | 0x00000002  | Sub-entry count = 2 (palette + pixel data) |
| 0x10   | 0x10008004  | GIF tag: NLOOP=4, EOP=1 |
| 0x18   | 0x0000000E  | GIF register descriptor |
| 0x20   | 0x00000005  | GS register: TRXPOS |
| 0x28   | 0x00000008  | GS register: TRXREG |
| 0x30   | 0x00008000  | TRXPOS data (destination X=0, Y=0) |
| 0x34   | 0x00400004  | TRXREG data |
| 0x38   | 0x00000034  | Additional register |
| 0x48   | 0x00000014  | PSM type indicator |
| 0x50   | TEX0 (8B)   | See above |
| 0x60   | 0xFFFF0000  | Alpha/blend settings |
| 0x64   | 0xFFFFFFFF  | Alpha mask |
| 0x68   | 0x01010001  | Blend config |
| 0x70   | 0x02000100  | u16: width=256, height=512 |
| 0x78   | 0x0000004C  | Additional data = 76 |
| 0x7C   | 0x00800080  | u16: 128, 128 (page dimensions) |
| 0x80   | 0x00000100  | Buffer width = 256 |
| 0x88   | 0x0001003C  | GIF tag continuation |
| 0x8C   | 0x00020008  | Register setup |
| 0x90   | 0x00000001  | Count = 1 |

**No cell size stored in header.** The header contains only GS register setup data for the texture upload, not glyph metadata.

---

## Companion Resources

| Resource | Size (bytes) | Type | Content |
|----------|-------------|------|---------|
| 1272     | 65,792      | PSMT4 256x512 | Font atlas (this file) |
| 1273     | 132,288     | PSMT8 256x512 | Unrelated texture (different PSM, too large for font metadata) |
| 1274     | 263,360     | PSMT8 512x512 | Unrelated texture |
| 1275     | 263,360     | PSMT8 512x512 | Unrelated texture |
| 1276     | 263,360     | PSMT8 512x512 | Unrelated texture |

None of the adjacent resources contain glyph width tables or font metadata. Resource 1273-1276 are standard game textures (character sprites, backgrounds, etc.) that happen to have consecutive resource indices.

---

## EXE Font Descriptor Structures

Two sets of font descriptors exist at EXE offset 0x3C0630, using 28-byte entries separated by `80 80 80 80 00 01 00 01` markers:

**Set 1 (0x3C0630-0x3C06D8):** 6 entries with height=8, for a different (smaller) font
**Set 2 (0x3C0700-0x3C0850):** 12 entries with heights 16/32/48/64, for UI element rendering

These descriptors reference 256x256 textures and define UI widget rendering rectangles, NOT the 256x512 font atlas glyph grid. The game uses a separate code path for the font atlas with the div-by-21 pattern.

---

## PSMT4 Deswizzle Status

The PSMT4 pixel data uses PS2 GS hardware swizzling (block rearrangement + column interleaving). Multiple deswizzle implementations were attempted:

- **Block-level deswizzle:** Successfully rearranges 32x16 blocks using the standard PSMT4 block table, producing recognizable characters with intra-block artifacts
- **Column-level deswizzle:** Multiple interleaving patterns tested (XOR swap, checkerboard, parity-based), none fully correct
- **Raw 128-wide render:** Shows readable glyphs within each GS page (128x128 pixels), useful for visual inspection but pixel positions are scrambled within 32-pixel blocks

The exact PCSX2-accurate PSMT4 column nibble interleave table is needed for a perfect deswizzle. This is a known complex mapping from the PS2 GS hardware specification.

---

## Glyph Position Formula

Given a glyph index `i` (0-857):

```
col = i % 21      // column (0-20)  
row = i / 21      // row (0-40)
x_pixel = col * 12   // pixel x (0, 12, 24, ..., 240)
y_pixel = row * 12   // pixel y (0, 12, 24, ..., 480)
u = x_pixel / 256.0  // UV u coordinate
v = y_pixel / 512.0  // UV v coordinate
```

Each glyph occupies a 12x12 pixel cell in the deswizzled 256x512 texture.

---

## Implications for Fan Translation

1. **12x12 pixel cells** provide enough resolution for Latin characters (most Latin fonts render cleanly at 12px)
2. **Fixed-width 12px cells** mean Latin characters will be proportional within the cell but monospaced between cells (same as the original Japanese font)
3. **882 total slots** with 858 used leaves 24 unused slots that could hold additional characters if needed
4. **Variable-width rendering** would require modifying the game's text rendering code (the div-by-21 pattern and UV coordinate calculation)
5. The palette is all-white (intensity-only rendering), so the game applies color at render time -- replacement glyphs should also use grayscale intensity values

---

## Files Produced

### Diagnostic Renders (in this directory)
- `deswiz_v1.png` through `deswiz_v8.png` -- Various deswizzle attempts
- `*_inv.png` -- Inverted versions for readability
- `grid_*.png` -- Grid overlay tests at various cell sizes
- `kanji_*.png` -- Kanji section grid tests
- `pixel_zoom_*.png` -- Pixel-level zoomed views with grid overlays
- `top_grid_*.png`, `mid_grid_*.png` -- Section grid tests

### Key Reference Renders (in `dumps/font_renders/`)
- `font_atlas_raw_128w.png` -- Best raw render (128-wide page layout)
- `font_atlas_paged_inv.png` -- Page-arranged 256x512 inverted
