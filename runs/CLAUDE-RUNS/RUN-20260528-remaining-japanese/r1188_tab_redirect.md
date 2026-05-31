# R1188 Tab Label Glyph ID Redirect: Complete Analysis

**Date**: 2026-05-28

---

## 1. CORRECTED Understanding: Labels Are Single Sprites, NOT Multi-Character

The initial assumption that "name entry tabs are composed at runtime from individual
R1188 glyph cells" is **WRONG**. Each tab label is a SINGLE glyph ID that renders
ONE pre-baked bitmap sprite (100px wide) from the R1188 atlas.

Evidence:
- Cell data shows W=100 (100 pixels wide) for ALL 13 label glyphs
- The code at VA 0x2FB124 loads ONE uint32 glyph ID per table entry and calls
  render_glyph_sprite ONCE per label
- PCSX2 captures show 48x20 composites because PCSX2 captures the source texture
  region, which is a sub-window of the full 100px sprite

---

## 2. EXE Table 2E: Glyph ID Decode

**Location**: EXE file offset 0x3C9DA0, VA 0x4C9DA0

Table structure: uint32 values, 3 groups separated by 0xFFFFFFFF padding.

### Group 1: Tab Labels (file 0x3C9DA0-0x3C9DB0)

| File Offset | Glyph ID | Hex    | Group:Index | Japanese | English |
|-------------|----------|--------|-------------|----------|---------|
| 0x3C9DA0    | 6400     | 0x1900 | 0x19:0x00   | katakana tab   | "Kana"    |
| 0x3C9DA4    | 6401     | 0x1901 | 0x19:0x01   | hiragana tab   | "Hira"    |
| 0x3C9DA8    | 6402     | 0x1902 | 0x19:0x02   | alphanumeric   | "ABC"     |
| 0x3C9DAC    | 6403     | 0x1903 | 0x19:0x03   | symbols tab    | "Sym"     |
| 0x3C9DB0    | 6404     | 0x1904 | 0x19:0x04   | 5th tab slot   | --        |

### Group 2: Buttons (file 0x3C9DEC-0x3C9DFC)

| File Offset | Glyph ID | Hex    | Group:Index | Japanese      | English   |
|-------------|----------|--------|-------------|---------------|-----------|
| 0x3C9DEC    | 6405     | 0x1905 | 0x19:0x05   | Confirm       | "OK"      |
| 0x3C9DF0    | 6406     | 0x1906 | 0x19:0x06   | Male Name     | "M.Name"  |
| 0x3C9DF4    | 6407     | 0x1907 | 0x19:0x07   | Female Name   | "F.Name"  |
| 0x3C9DF8    | 6408     | 0x1908 | 0x19:0x08   | Delete char   | "Delete"  |
| 0x3C9DFC    | 6409     | 0x1909 | 0x19:0x09   | Clear all     | "Clear"   |

### Group 3: Extra Labels (file 0x3C9E18-0x3C9E24)

| File Offset | Glyph ID | Hex    | Group:Index | Note          |
|-------------|----------|--------|-------------|---------------|
| 0x3C9E18    | 6410     | 0x190A | 0x19:0x0A   | Sidebar label |
| 0x3C9E1C    | 6411     | 0x190B | 0x19:0x0B   | Sidebar label |
| 0x3C9E24    | 6412     | 0x190C | 0x19:0x0C   | Sidebar label |

---

## 3. Cell Data: Per-Glyph UV/Width Records

**Location**: EXE file 0x3D9B90 (VA 0x4D9B10), 8 bytes per glyph, 13 glyphs.

Each 8-byte record:
```
byte0 = U tile index (column in atlas, always 0 for these)
byte1 = V tile index (row in atlas, 60-72 for tab labels)
byte2 = W width in pixels (always 100 for these)
byte3 = flag (0 or 1, possibly "two-cell-wide" indicator)
byte4 = TBP0 low byte (GS VRAM source page)
byte5 = TBP0 high byte
byte6 = 79 (constant, possibly height or stride)
byte7 = 0 (padding)
```

### All 13 Cell Records

| Glyph  | File Offset | U | V  | W   | b3 | TBP0   | b6 | Label             |
|--------|-------------|---|-----|-----|----|--------|----|-------------------|
| 0x1900 | 0x3D9B90    | 0 | 60  | 100 | 0  | 0xB430 | 79 | Katakana tab      |
| 0x1901 | 0x3D9B98    | 0 | 61  | 100 | 0  | 0xB438 | 79 | Hiragana tab      |
| 0x1902 | 0x3D9BA0    | 0 | 62  | 100 | 0  | 0xB440 | 79 | Alphanumeric tab  |
| 0x1903 | 0x3D9BA8    | 0 | 63  | 100 | 0  | 0xB448 | 79 | Symbols tab       |
| 0x1904 | 0x3D9BB0    | 0 | 64  | 100 | 0  | 0xB450 | 79 | 5th tab slot      |
| 0x1905 | 0x3D9BB8    | 0 | 65  | 100 | 0  | 0xB458 | 79 | Confirm (OK)      |
| 0x1906 | 0x3D9BC0    | 0 | 66  | 100 | 0  | 0xB460 | 79 | Male Name         |
| 0x1907 | 0x3D9BC8    | 0 | 67  | 100 | 1  | 0xB468 | 79 | Female Name       |
| 0x1908 | 0x3D9BD0    | 0 | 68  | 100 | 1  | 0xB470 | 79 | Delete character  |
| 0x1909 | 0x3D9BD8    | 0 | 69  | 100 | 1  | 0xB478 | 79 | Clear all         |
| 0x190A | 0x3D9BE0    | 0 | 70  | 100 | 0  | 0xB480 | 79 | Sidebar label 1   |
| 0x190B | 0x3D9BE8    | 0 | 71  | 100 | 1  | 0xB488 | 79 | Sidebar label 2   |
| 0x190C | 0x3D9BF0    | 0 | 72  | 100 | 0  | 0xB490 | 79 | Sidebar label 3   |

---

## 4. Rendering Pipeline (Traced from Disassembly)

```
Name entry code at VA 0x2FB0C0
  |
  |  1. Loads glyph_id from table at VA 0x4C9DA0 (file 0x3C9DA0)
  |     Each entry is uint32, e.g., 0x00001900
  |     Accessed as: base[mode*44 + slot] where base = VA 0x4C9D20
  |
  v
VA 0x494350: render_glyph_sprite(glyph_id)
  |
  |  1. page = glyph_id >> 8     => 0x19 (25)
  |     cell = glyph_id & 0xFF   => 0x00-0x0C
  |
  |  2. Page table lookup at VA 0x4DB100 + page*8:
  |     desc_idx = page_table[page*8+0]  => 0 (shared descriptor)
  |     cell_ptr = page_table[page*8+4]  => VA 0x4D9B10
  |
  |  3. Cell data read at cell_ptr + cell*8:
  |     U = byte0, V = byte1, W = byte2
  |
  |  4. Packs: r4 = U | (V << 8) | (desc_idx << 16)
  |            r5 = W (width)
  |
  v
VA 0x474D30: submit_sprite_packet(packed_uv, width)
  |
  |  GS hardware renders a textured sprite from the atlas
  v
Screen
```

---

## 5. Why the Labels Are NOT Multi-Character Compositions

The user asked about "individual R1188 glyph cells" being composed into tab labels.
This model is INCORRECT for the following reasons:

1. **W=100 pixels wide**: Each glyph renders as a 100px-wide sprite. Individual
   characters in R1188 are only 20-24px wide. These are pre-baked label images.

2. **One call per label**: The code loads ONE glyph ID and makes ONE call to
   render_glyph_sprite. There is no loop drawing individual characters.

3. **TBP0 values are unique per label**: Each label points to a different VRAM
   source page (b4:b5 values 0xB430-0xB490, incrementing by 8). Each source page
   contains one pre-rendered label.

4. **Atlas layout confirms**: The R1188 1024x1024 PSMT4 atlas has a character grid
   at rows 0-5 (ASCII) and rows 6-41 (kanji), but the V=60-72 tile coordinates
   used by the tab labels point to a SEPARATE region of the atlas containing
   pre-composed label bitmaps (not the character grid).

---

## 6. Translation Strategy: Edit R1188 Texture at Label Tile Positions

### The Problem

The tab label glyphs (V=60-72) point to specific tile positions in the R1188 atlas
where Japanese label bitmaps are pre-baked. The pixel data at those positions must
be replaced with English text.

### The Challenge

The PSMT4 deswizzle with TBW=16 (used for the character grid) produces different
pixel layout than TBW=4 (used by the GS to read tab labels). The deswizzled atlas
image (`R1188_CORRECT_dbw512.png`) shows the character grid correctly but does NOT
show the label bitmaps at their correct positions.

When the GS reads a label, it uses:
- TEX0 with TBW=4 (256px wide texture window)
- TBP0 = 0xB430 + cell_index*8 (selects a 256x256 sub-region)
- UV from (U*tile_w, V*tile_h) within that sub-region

### Recommended Approach: PCSX2 + EXE Cell Data Patch

**Step 1**: The PCSX2 texture replacement approach (already in `tools/patch_r1188_tabs.py`)
works for emulator testing. This is already implemented.

**Step 2**: For ISO-level patching, edit the R1188 raw pixel data:
1. Determine the pixel byte offsets within the PSMT4 data (file offset 0xC00+)
   that correspond to each label's TBP0+UV position
2. Render English labels into those byte positions
3. This requires computing the PSMT4 block/column swizzle for TBW=4 addressing

**Step 3** (alternative): Patch the cell data bytes in the EXE to redirect labels
to atlas positions where English text already exists (e.g., the A-Z row). This
would require:
- Finding unused glyph positions in the atlas
- Rendering English labels at those positions in R1188
- Updating the V byte and TBP0 bytes at file offsets 0x3D9B90-0x3D9BF0

---

## 7. Cell Data Patch Points (for EXE patching)

To change what text a tab label displays, modify these bytes in the EXE:

| Label         | File Offset | Byte to Modify | Current | Change to |
|---------------|-------------|----------------|---------|-----------|
| Katakana tab  | 0x3D9B91    | V (byte1)      | 60      | new_V     |
| Hiragana tab  | 0x3D9B99    | V (byte1)      | 61      | new_V     |
| ABC tab       | 0x3D9BA1    | V (byte1)      | 62      | new_V     |
| Symbols tab   | 0x3D9BA9    | V (byte1)      | 63      | new_V     |
| 5th tab       | 0x3D9BB1    | V (byte1)      | 64      | new_V     |
| Confirm       | 0x3D9BB9    | V (byte1)      | 65      | new_V     |
| Male Name     | 0x3D9BC1    | V (byte1)      | 66      | new_V     |
| Female Name   | 0x3D9BC9    | V (byte1)      | 67      | new_V     |
| Delete char   | 0x3D9BD1    | V (byte1)      | 68      | new_V     |
| Clear all     | 0x3D9BD9    | V (byte1)      | 69      | new_V     |
| Sidebar 1     | 0x3D9BE1    | V (byte1)      | 70      | new_V     |
| Sidebar 2     | 0x3D9BE9    | V (byte1)      | 71      | new_V     |
| Sidebar 3     | 0x3D9BF1    | V (byte1)      | 72      | new_V     |

Additionally, U (byte0 at offset-1), W (byte2 at offset+1), and TBP0 (bytes 4-5)
can be modified if the English labels are at different atlas positions or widths.

---

## 8. Key File References

| Item | Location |
|------|----------|
| EXE (SLPM_653.78) | `extracted/SLPM_653.78` |
| R1188 raw resource | `extracted/packdata_raw/1188_type01.raw` |
| R1188 pixel data start | R1188 file offset 0xC00 (524,288 bytes of PSMT4) |
| Deswizzled atlas | `build/textures_to_edit/R1188_CORRECT_dbw512.png` |
| PCSX2 tab replacement tool | `tools/patch_r1188_tabs.py` |
| EXE glyph ID table (Table 2E) | EXE file 0x3C9DA0 (VA 0x4C9DA0) |
| EXE cell data (page 0x19) | EXE file 0x3D9B90 (VA 0x4D9B10), 13x8 bytes |
| EXE page table | EXE file 0x3DB180 (VA 0x4DB100), stride 8 per page |
| render_glyph_sprite function | EXE VA 0x494350 (file 0x3943D0) |
| submit_sprite_packet function | EXE VA 0x474D30 (file 0x374DB0) |
| Name entry glyph loader | EXE VA 0x2FB0C0 (file 0x1FB0C0) |
| VA-to-file mapping | file_offset = VA - 0xFFF80 |

---

## 9. Summary of Findings

1. **13 glyph IDs** (6400-6412 / 0x1900-0x190C) in EXE Table 2E at file 0x3C9DA0.
2. Each glyph ID maps to a **single 100px-wide pre-baked label sprite**, NOT individual characters.
3. The per-glyph UV data lives in the EXE at file 0x3D9B90 (cell data array for page 0x19).
4. Each cell record is 8 bytes: {U_tile, V_tile, Width, flag, TBP0_lo, TBP0_hi, 79, 0}.
5. V tiles 60-72 and TBP0 values 0xB430-0xB490 identify 13 distinct label positions in the R1188 atlas.
6. To translate: either edit R1188 pixel data at those VRAM positions, or redirect the cell data to new atlas positions containing English labels.
7. The PCSX2 replacement approach (`tools/patch_r1188_tabs.py`) already handles the emulator case. For ISO-level patching, the cell data at 0x3D9B90 can be modified in the EXE.
