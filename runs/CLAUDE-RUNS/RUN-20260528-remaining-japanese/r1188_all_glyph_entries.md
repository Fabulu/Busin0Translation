# R1188 Complete Glyph Entry Analysis

**Date**: 2026-05-28
**EXE**: `extracted/SLPM_653.78`
**Atlas**: R1188 = 1024x1024 PSMT4 texture (4-bit indexed, 16 colors)

---

## 1. Two Table Systems in the EXE

### Table A: Disk Page Table (VA 0x4DB100, file 0x3DB180)

- 50 pages (0x00-0x31), 8 bytes each
- Format: `[uint32 desc_idx] [uint32 cell_data_ptr_VA]`
- `desc_idx`: selects texture descriptor (0=R1188 main, 1=R1188 alt, 2=other atlas, 9=special)
- `cell_data_ptr_VA`: virtual address of cell data array in EXE data section

### Table B: BSS Runtime Table (VA 0x4EB100, populated at runtime)

- Used by the actual render function at VA 0x494350
- Same layout: `[uint32 desc_idx] [uint32 cell_data_ptr]`
- Populated by registration function at VA 0x493F20 from source data at VA 0x4EBBEC
- The BSS cell_data_ptr likely points to the SAME cell data arrays as Table A

### Relationship

The disk table (Table A) contains the static cell data arrays in the EXE's initialized data segment. The BSS table (Table B) is populated at runtime when font resources load, with pointers that reference the same cell data. The renderer at VA 0x494350 reads exclusively from Table B (BSS).

---

## 2. Cell Data Entry Format (8 bytes each)

```
struct cell_entry {
    uint8  U;          // byte[0]: Column tile index (0-4)
    uint8  V;          // byte[1]: Row tile index (60-105)
    uint8  W;          // byte[2]: Width/type code (0, 100, or 120)
    uint8  flag;       // byte[3]: Rendering flag (0 or 1), checked at VA 0x4942E8
    uint16 vram_blk;   // bytes[4:6] LE: VRAM block address (TBP0-style, stride 8 per entry)
    uint16 gs_config;  // bytes[6:8] LE: GS register config (always 0x004F)
};
```

### Field Details

- **U** (column tile): 0-4, selects horizontal position in 256x256 sub-atlas
- **V** (row tile): 60-105, selects vertical position in 256x256 sub-atlas
  - V is NOT a simple row offset in the 1024x1024 deswizzled atlas
  - V is a coordinate within a TBW=4 (256px wide) PSMT4 re-read of the VRAM data
  - Due to PSMT4 block/column swizzle, V=60 does NOT map to y=0 in the deswizzled atlas
- **W** (width/type): Almost always 100 (0x64). Values seen: 0, 100, 120.
  - Passed as second argument to submit_sprite_packet (VA 0x474D30)
- **flag**: 0 or 1. Checked by helper at VA 0x4942C8. Likely "two-cell-wide" indicator.
- **vram_blk**: VRAM block address. Each entry increments by 8 blocks (8 * 256 = 2048 bytes).
  - For PSMT4 TBW=4, 2048 bytes = 16 rows of 256 4-bit pixels = one 256x16 tile
- **gs_config**: Always 0x004F = 79. Likely encodes sprite height or other GS parameter.

---

## 3. How the Renderer Works (VA 0x494350)

```c
void render_bitmap_glyph(uint16 glyph_id) {
    // a0 = glyph_id, e.g., 0x1900

    if (!check_glyph_loaded(glyph_id))  // JAL 0x494300
        return 0;

    uint8 group = glyph_id >> 8;     // SRA r2, a3, 8  -> 0x19
    uint8 index = glyph_id & 0xFF;   // ANDI r2, a3, 0xFF -> 0x00

    // Read BSS table at VA 0x4EB100
    uint32 cell_data_ptr = *(uint32*)(0x4EB104 + group * 8);  // ptr to cell array
    uint32 desc_idx      = *(uint32*)(0x4EB100 + group * 8);  // texture descriptor

    uint8* cell = cell_data_ptr + index * 8;
    uint8 u_tile = cell[0];    // LBU r2, 0(a1)
    uint8 v_tile = cell[1];    // LBU r4, 1(a1)
    uint8 width  = cell[2];    // LBU a1, 2(a1)

    // Pack: a0 = u_tile | (v_tile << 8) | (desc_idx << 16)
    uint32 packed = u_tile | (v_tile << 8) | (desc_idx << 16);

    submit_sprite_packet(packed, width);  // JAL 0x474D30
}
```

The renderer ONLY reads bytes 0, 1, 2 from the cell entry. Bytes 3-7 are used by other code paths.

---

## 4. All Pages Using R1188 Atlas (desc_idx=0)

| Page | Glyph Range | Entries | Purpose |
|------|-------------|---------|---------|
| 0x01 | 0x0100-0x0102 | 3 | Special characters |
| 0x02 | 0x0200-0x0218 | 25 | Characters (25 entries, U=0-1) |
| 0x09 | 0x0900-0x0928 | 41 | Characters (41 entries, U=0-1) |
| 0x0A | 0x0A00-0x0A26 | 39 | Characters (39 entries, U=0-1) |
| 0x0B | 0x0B00-0x0BC6 | 199 | **Large character set** (U=0-4, V=60-84) |
| 0x0C | 0x0C00-0x0C6A | 107 | **Medium character set** (U=0-4, V=60-105) |
| 0x19 | 0x1900-0x190C | 13 | **Tab labels (CLUT state 0)** |
| 0x1A | 0x1A00-0x1A0C | 13 | Tab labels (CLUT state 1) |
| 0x1B | 0x1B00-0x1B0C | 13 | Tab labels (CLUT state 2) |
| 0x1C | 0x1C00-0x1C0C | 13 | Tab labels (CLUT state 3) |
| 0x1D | 0x1D00-0x1D0C | 13 | Tab labels (CLUT state 4) |
| 0x1E | 0x1E00-0x1E1C | 29 | Extended labels (16 extra + 13 base) |
| 0x1F | 0x1F00-0x1F0C | 13 | Tab labels (CLUT state 6) |
| 0x20 | 0x2000-0x200C | 13 | Tab labels (CLUT state 7) |
| 0x21 | 0x2100-0x210C | 13 | Tab labels (CLUT state 8) |
| 0x22 | 0x2200-0x220C | 13 | Tab labels (CLUT state 9) |
| 0x23 | 0x2300-0x230C | 13 | Tab labels (CLUT state 10) |
| 0x24 | 0x2400-0x240C | 13 | Tab labels (CLUT state 11) |
| 0x25 | 0x2500-0x2508 | 9 | Stat labels (truncated set) |
| 0x26 | 0x2600-0x2604 | 5 | Small label set |
| 0x27 | 0x2700-0x2714 | 21 | Labels with extras |
| 0x28 | 0x2800-0x2810 | 17 | Labels |
| 0x29 | 0x2900-0x2908 | 9 | Labels |
| 0x2A | 0x2A00-0x2A14 | 21 | Labels |
| 0x2B | 0x2B00-0x2B0C | 13 | Labels |
| 0x2C | 0x2C00-0x2C08 | 9 | Labels |
| 0x2D | 0x2D00-0x2D04 | 5 | Labels |
| 0x2E | 0x2E00-0x2E04 | 5 | Labels |
| 0x2F | 0x2F00-0x2F06 | 7 | Labels (special pointer) |
| 0x30 | 0x3000-0x3002 | 3 | Labels |
| 0x31 | 0x3100-0x3106 | 7 | Labels |

**Total**: 1264 cell entries across all pages. 762 entries use desc_idx=0 (R1188 atlas).

---

## 5. Tab Label Entries (Page 0x19, file offset 0x3D9B90)

| Index | Glyph ID | U | V | W | Flag | VRAM Block | Japanese | English |
|-------|----------|---|---|---|------|------------|----------|---------|
| 0 | 0x1900 | 0 | 60 | 100 | 0 | 0xB430 | Kana (katakana) | Kana |
| 1 | 0x1901 | 0 | 61 | 100 | 0 | 0xB438 | Hira (hiragana) | Hira |
| 2 | 0x1902 | 0 | 62 | 100 | 0 | 0xB440 | ABC (alphanumeric) | ABC |
| 3 | 0x1903 | 0 | 63 | 100 | 0 | 0xB448 | Sym (symbols) | Sym |
| 4 | 0x1904 | 0 | 64 | 100 | 0 | 0xB450 | (5th tab) | -- |
| 5 | 0x1905 | 0 | 65 | 100 | 0 | 0xB458 | OK/Confirm | OK |
| 6 | 0x1906 | 0 | 66 | 100 | 0 | 0xB460 | Male Name | M.Name |
| 7 | 0x1907 | 0 | 67 | 100 | 1 | 0xB468 | Female Name | F.Name |
| 8 | 0x1908 | 0 | 68 | 100 | 1 | 0xB470 | Delete 1 char | Del |
| 9 | 0x1909 | 0 | 69 | 100 | 1 | 0xB478 | Clear All | Clear |
| 10 | 0x190A | 0 | 70 | 100 | 0 | 0xB480 | Extra 1 | -- |
| 11 | 0x190B | 0 | 71 | 100 | 1 | 0xB488 | Extra 2 | -- |
| 12 | 0x190C | 0 | 72 | 100 | 0 | 0xB490 | Extra 3 | -- |

CLUT variant pages 0x1A-0x24 contain IDENTICAL (U,V,W) values but with different VRAM block addresses (different TBP0 -> different CLUT applied).

---

## 6. CRITICAL: Each Tab Label Is ONE Atomic Sprite

### Table 2E Structure (file 0x3C9DA0)

Table 2E stores one uint32 glyph ID per UI slot (4-byte stride, 0xFFFFFFFF = empty):

| Slot | Offset | Glyph ID | UI Element |
|------|--------|----------|------------|
| 0 | +0x000 | 0x1900 | Kana tab |
| 1 | +0x004 | 0x1901 | Hira tab |
| 2 | +0x008 | 0x1902 | ABC tab |
| 3 | +0x00C | 0x1903 | Sym tab |
| 4 | +0x010 | 0x1904 | 5th tab |
| 5-18 | +0x014-0x04B | 0xFFFFFFFF | (empty) |
| 19 | +0x04C | 0x1905 | OK button |
| 20 | +0x050 | 0x1906 | Male Name |
| 21 | +0x054 | 0x1907 | Female Name |
| 22 | +0x058 | 0x1908 | Delete |
| 23 | +0x05C | 0x1909 | Clear |
| 30 | +0x078 | 0x190A | Extra 1 |
| 31 | +0x07C | 0x190B | Extra 2 |
| 33 | +0x084 | 0x190C | Extra 3 |

**Each tab has exactly ONE glyph ID.** The rendering code calls `render_bitmap_glyph` once per tab, drawing ONE sprite. That sprite is a pre-composed multi-character bitmap in the atlas (e.g., "katakana" = 2 kanji at ~48x20 pixels within a single W=100 sprite region).

There are NO individual A, B, C character entries in group 0x19 that could be composed into English tab labels. Each tab is an atomic sprite.

Pages 0x0B (199 entries) and 0x0C (107 entries) contain individual character glyphs for the keyboard grid display, but their glyph IDs (0x0B00-0x0BC6, 0x0C00-0x0C6A) are different from the tab label IDs and cannot be substituted via Table 2E.

---

## 7. Translation Strategy for English Tab Labels

### Approach: Edit R1188 Atlas Pixel Data

Since each tab label is an atomic sprite reading from a fixed position in the atlas, the ONLY approach is to overwrite the Japanese text at those atlas positions with English text.

**Problem**: The atlas pixel positions are in TBW=4 (256px) PSMT4 space, which has a complex swizzle relationship to the deswizzled TBW=16 (1024px) atlas we can edit.

### Steps Required

1. **Compute the PSMT4 swizzle mapping** between TBW=4 and TBW=16 address spaces
   - Need PS2 GS block/page/column swizzle tables for PSMT4
   - Given (U=0, V=60..72) in TBW=4 space, compute which pixels in the 1024x1024 deswizzled atlas correspond

2. **Render English labels** at those deswizzled pixel positions
   - Each sprite is W=100 pixels wide, ~20 pixels tall (based on PCSX2 48x20 captures)
   - Labels: "Kana", "Hira", "ABC", "Sym", "OK", "M.Name", "F.Name", "Del", "Clear"

3. **Apply to all CLUT variants** (pages 0x19-0x24)
   - All CLUT variants read from the same atlas positions (only CLUT differs)
   - Editing the atlas once covers all variants

### Alternative: PCSX2 Texture Replacement (Proven Working)

PCSX2's texture replacement intercepts at the GS level and can replace the exact content hashes:

| Content Hash | Size | Japanese | English |
|-------------|------|----------|---------|
| `1f839869fab251d` | 48x20 | Kana | Kana |
| `9677cb23da53ff88` | 48x20 | Hira | Hira |
| `6f1fb24fad5cd1a` | 48x20 | ABC | ABC |
| `19a39fbc8a08d7ec` | 48x20 | Sym | Sym |
| `d09a04bdfaf715bc` | 40x24 | OK | OK |

This works for PCSX2 testing but not for hardware/other emulators.

---

## 8. Key Addresses Summary

| What | VA | File Offset | Size |
|------|-----|-------------|------|
| Disk page table | 0x4DB100 | 0x3DB180 | 400B (50 x 8) |
| Page 0x19 cell data | 0x4D9B10 | 0x3D9B90 | 104B (13 x 8) |
| BSS runtime table (populated at load) | 0x4EB100 | -- (runtime) | -- |
| BSS source data | 0x4EBBEC | 0x3EBC6C | varies |
| render_bitmap_glyph | 0x494350 | 0x3943D0 | ~128B |
| submit_sprite_packet | 0x474D30 | 0x374DB0 | ~256B |
| check_glyph_loaded | 0x494300 | 0x394380 | ~80B |
| flag check (byte[3]) | 0x4942C0 | 0x394340 | ~60B |
| Page registration func | 0x493F20 | 0x393FA0 | ~256B |
| Font descriptor array | 0x575C10 | -- (BSS) | -- |

---

## 9. VRAM Block Address Pattern

The `vram_blk` field (bytes 4-5, LE uint16) increments by 8 per entry within a page. This means each cell occupies exactly 8 GS VRAM blocks.

- 1 GS block = 256 bytes
- 8 blocks = 2048 bytes
- For PSMT4 at TBW=4 (256px wide): 2048 bytes / (256/2 nibbles per row) = 16 rows
- **Each cell = 256 x 16 pixels in PSMT4 TBW=4 space**

The tab labels are rendered as 256x16 source rectangles, cropped to the actual label width by the rendering system (W=100 may specify horizontal extent in some unit).

Different pages start at different base VRAM block addresses:
- Page 0x02: 0xA1B8 (41400 blocks from VRAM base)
- Page 0x0B: 0xA498 (42136 blocks)
- Page 0x19: 0xB430 (46128 blocks)

These offsets correspond to different TBP0 base addresses, selecting which part of the R1188 VRAM upload to read from.

---

## 10. Definitive Answer: How to Display English Tab Labels

### Each tab label IS an atomic pre-composed sprite

Table 2E holds ONE glyph ID per tab. `render_bitmap_glyph` draws ONE sprite per call. Each sprite is approximately 48x20 pixels containing the complete Japanese label (e.g., the two katakana characters for "Kana" in a single sprite).

The (U, V) cell coordinates + the b4:b5 VRAM block address determine which region of the R1188 atlas the sprite reads from. Each label has its own dedicated region.

### Translation Approaches (ranked by feasibility)

#### Approach 1: Edit R1188 atlas pixels at swizzled label positions (RECOMMENDED)

Each label sprite reads from a specific area of the R1188 atlas. To translate:

1. Determine the exact pixel area in the 1024x1024 deswizzled atlas that maps to each label's TBW=4 read coordinates
2. Replace the Japanese label pixels with English text (e.g., "Kana", "Hira", "ABC", "Sym")
3. Re-swizzle and rebuild the atlas

The label regions in the TBW=4 atlas were visualized in `r1188_tbw4_all_tabs_v60_72_4x.png` -- these show the actual pixel data the GS reads for V=60-72. The mapping between TBW=4 coordinates and TBW=16 (1024px) pixel positions requires computing the PS2 PSMT4 block/page swizzle tables.

#### Approach 2: Render English into unused atlas area + patch cell data

1. Find unused rows in the R1188 atlas (bottom rows beyond the kanji grid)
2. Render English label sprites ("Kana", "Hira", etc.) at those positions
3. Patch the cell data entries at file 0x3D9B90 (U, V, and b4:b5) to point to the new positions
4. Must also patch CLUT variant pages 0x1A-0x24 at their respective cell data offsets

This requires understanding the exact relationship between (U, V, b4:b5) and pixel position.

#### Approach 3: PCSX2 texture replacement (for testing only)

Replace the captured textures via content hashes. Already has hashes identified:
- `1f839869fab251d` -> "Kana" (48x20)
- `9677cb23da53ff88` -> "Hira" (48x20)
- `6f1fb24fad5cd1a` -> "ABC" (48x20)
- `19a39fbc8a08d7ec` -> "Sym" (48x20)
- `d09a04bdfaf715bc` -> "OK" (40x24)

Works only in PCSX2 with texture replacement enabled. Not applicable to hardware.

### Key File Offsets for Patching

| What | File Offset | Size | Notes |
|------|-------------|------|-------|
| Table 2E (glyph IDs) | 0x3C9DA0 | ~168B | uint32 glyph IDs, 0xFFFFFFFF = empty |
| Page 0x19 cell data | 0x3D9B90 | 104B | 13 x 8-byte entries |
| Page 0x1A cell data | 0x3D9C00 | 104B | CLUT variant 1 |
| Page 0x1B cell data | 0x3D9C70 | 104B | CLUT variant 2 |
| Page 0x1C cell data | 0x3D9CE0 | 104B | CLUT variant 3 |
| Page 0x1D cell data | 0x3D9D50 | 104B | CLUT variant 4 |
| R1188 pixel data start | R1188 + 0xC00 | 524,288B | PSMT4 1024x1024 |
