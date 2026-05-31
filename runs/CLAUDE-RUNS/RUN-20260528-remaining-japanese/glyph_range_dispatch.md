# Glyph Range Dispatch: R1272 vs Kanji Font Pages

**Date:** 2026-05-28
**Source:** MIPS disassembly of SLPM_653.78

---

## CRITICAL FINDING: Two Completely Separate Font Systems

The game has **two independent font rendering systems** that do NOT share glyph ID spaces or resources.

### System 1: TextEvent MSG Renderer

| Property | Value |
|----------|-------|
| Functions | `func_302DB0` (draw), `func_303C60` (main), `func_302910` (queue) |
| Resource | **R1272 only** (256x512, PSMT4, 4bpp) |
| Grid | 21 cols x 42 rows, 12x12 cells = 882 glyph slots |
| Dispatch | `col = glyph_id % 21`, `row = glyph_id / 21` (hardcoded) |
| Glyph IDs | 0-881 (indices into the 21x42 grid) |
| Used for | Dialogue, narration, battle text, item descriptions -- all MSG-based text |
| Status | **REPLACED** -- R1272 is our English font atlas |

R1272 is loaded separately from the font page system. It is acquired via `JAL 0x4924A0` with handle `0x04F80000` at VA `0x30B370`. The data pointer is stored at `$gp-26820`.

### System 2: Font Tile System (Paged Kanji Fonts)

| Property | Value |
|----------|-------|
| Functions | `func_30B770` (check/load page), `func_30B840` (render loop), `func_30B3F0` (page manager) |
| Resources | 96 paged resources (R1215-R1311, excluding R1272) |
| Format | PSMT8 (8bpp), various sizes (256x512 or 512x512) |
| Dispatch | `glyph_struct[glyph_id].page_index` -> page table -> resource |
| Glyph IDs | 0-678 (indices into a 50-byte per-glyph runtime struct array) |
| Used for | Stat labels, sidebar labels, menu labels, town navigation, battle UI, all EXE-hardcoded labels |
| Status | **NOT REPLACED** -- kanji page resources are untouched |

The font tile system uses a runtime array of 50-byte structs, one per glyph (max 679 glyphs, max 32 active at once). Each struct's field[0] (int16) is a page_index that selects which font page resource provides the tile.

---

## Font Page Table

**Location:** VA `0x4CA710` (file offset `0x3CA790`)
**Structure:** Array of 4-byte resource handles (resource_id << 16), indexed by page_index.
**Entry 0** is empty (R1272 is loaded separately).

### Complete Page-to-Resource Mapping (100 entries)

| Page | Resource | Format | Size | Notes |
|------|----------|--------|------|-------|
| 0 | (empty) | - | - | Slot 0 unused |
| 1-54 | R1215-R1268 | PSMT8 | 263,360 or 132,288 | Main font pages |
| 55-57 | (gap) | - | - | No entries |
| 58 | R1283 | PSMT8 | varies | Extended |
| **59** | **R1304** | **PSMT8 512x512** | **263,360** | **Kanji page** |
| **60** | **R1305** | **PSMT8 512x512** | **263,360** | **Kanji page** |
| **61** | **R1306** | **PSMT8** | varies | **Kanji page** |
| **62** | **R1307** | **PSMT8** | varies | **Kanji page** |
| **63** | **R1308** | **PSMT8** | varies | **Kanji page** |
| **64** | **R1309** | **PSMT8** | varies | **Kanji page** |
| **65** | **R1310** | **PSMT8** | varies | **Kanji page** |
| **66** | **R1311** | **PSMT8** | varies | **Kanji page** |
| 67-71 | R1278-R1282 | PSMT8 | varies | Extended |
| 72-89 | R1284-R1301 | PSMT8 | varies | Extended |
| 90 | R1303 | PSMT8 | varies | Extended |
| 91 | R1269 | PSMT8 | varies | Base set |
| 92 | R1270 | PSMT8 256x512 | 132,288 | Kanji (known stat label source) |
| 93 | R1271 | PSMT8 256x512 | 132,288 | Kanji |
| 94 | R1273 | PSMT8 256x512 | 132,288 | Kanji |
| 95-98 | R1274-R1277 | PSMT8 | 263,360 | Extended kanji |
| 99 | R1302 | PSMT8 | varies | Final page |

**R1272 is NOT in this table.** It belongs exclusively to System 1.

---

## Glyph Dispatch Code (System 2)

### func_30B770 (VA 0x30B770) - Page Availability Check

```
Input: r4 = glyph_id (lower 16 bits)
1. If glyph_id < 32: error ("FontDispSetCnt Max Over")
2. Compute struct address: base + glyph_id * 50
   - SLL r2, r5, 2       ; * 4
   - ADDU r4, r2, r5     ; * 5
   - SLL r3, r4, 2       ; * 20
   - ADDU r3, r4, r3     ; * 25
   - SLL r3, r3, 1       ; * 50
   - ADDU r2, base, r3   ; final address
3. LH r4, 0(r2)          ; page_index = struct[glyph_id].field0
4. If page_index < 0: skip (uninitialized)
5. If page_index >= 679: error
6. LW r3, page_array[page_index * 8]  ; data pointer
7. LHU r3, page_array[page_index * 8 + 4]  ; refcount
8. Return: r2 = 1 if page loaded, 0 otherwise
```

### func_30B840 (VA 0x30B840) - Render All Active Font Tiles

```
Loop: r18 = 0..31 (max 32 tiles), r17 += 50 per iteration
1. r19 = glyph_struct_base + r17
2. LH r4, 0(r19)      ; page_index
3. If page_index == -1: skip
4. Load page data via page_array[page_index]
5. JAL 0x127078        ; get_sub_resource(page_data, 0)
6. Copy UV coordinates from resource to struct:
   - struct[+14] = resource[+12] (U1)
   - struct[+16] = resource[+14] (V1)
   - struct[+18] = resource[+16] - resource[+12] (width)
   - struct[+20] = resource[+18] - resource[+14] (height)
7. Render GS primitive using UV + position data from struct
```

### Per-Glyph Struct (50 bytes)

| Offset | Size | Field |
|--------|------|-------|
| +0 | 2 | page_index (int16, -1 = inactive) |
| +2 | 2 | unknown |
| +4 | 2 | Y position |
| +12 | 2 | UV source U1 |
| +14 | 2 | U1 copy |
| +16 | 2 | V1 copy |
| +18 | 2 | tile width |
| +20 | 2 | tile height |
| +36 | 2 | flags (bit 15 = hidden) |
| +38 | 2 | scale/alpha |
| +47 | 1 | visibility flag |

---

## Answer to the Critical Question

**For glyph IDs 0-94 (ASCII range), does the game use R1272 ALWAYS?**

**YES, for System 1 (TextEvent/MSG text).** The TextEvent renderer always uses R1272 with fixed grid math (`col = id % 21`, `row = id / 21`). It never touches the font page table or any kanji page resource. Glyph IDs 0-881 in MSG data always render from R1272.

**The font tile system (System 2) uses a DIFFERENT glyph ID space.** Its glyph IDs (0-678) are indices into the 50-byte struct array, not the same as TextEvent glyph IDs. When the stat screen displays kanji like 力 (glyph tile 346), it uses System 2, which looks up page_index from `glyph_struct[346].field0`, finds the corresponding kanji page resource (e.g., R1270 at page 92), and renders the Japanese character from that untouched resource.

### Why R38 English Translations Show as Japanese (for stat labels)

The stat/sidebar labels (力, 知恵, 信仰心, etc.) are NOT rendered via R38 MSG text. They are rendered through System 2 (font tiles) using hardcoded glyph tile IDs in the EXE. These tile IDs map to kanji font pages (R1270-R1277, R1304-R1311) which have never been modified.

Even though R1272 has been replaced with English glyphs, R1272 is only used by System 1 (MSG text). The font tile system has its own separate set of 96 page resources, none of which is R1272.

### There Is NO Overlap

The initial hypothesis was wrong. R1272 and R1304-R1311 do NOT serve overlapping glyph ranges. They serve completely different rendering systems:

- R1272 -> System 1 (TextEvent) -> MSG dialogue/narration
- R1304-R1311 + R1269-R1277 + others -> System 2 (Font Tiles) -> UI labels, stat names, menu text

The "glyph IDs" in each system are unrelated indices. A glyph ID of 346 in System 2 is not the same cell as glyph ID 346 in the R1272 grid.

---

## Fix Strategy

To translate the remaining Japanese stat/sidebar labels, one of these approaches is needed:

### Option A: Patch EXE glyph tile ID sequences
Find where the EXE stores the glyph tile IDs for each label (e.g., 346 for 力) and replace them with glyph IDs that display the desired English characters. This requires finding glyph tiles within the kanji pages that already contain Latin characters, or:

### Option B: Patch EXE to use R38 MSG rendering instead
Modify the stat screen rendering code to call the TextEvent renderer (System 1) with R38 message indices instead of using font tiles (System 2). This is the cleanest approach but requires significant EXE code injection.

### Option C: Replace kanji font page tiles
Edit the binary font data in R1270/R1271/R1273 etc. to replace the Japanese glyphs at positions 346, 535, 717 etc. with English letter tiles. Requires understanding each page's internal PSMT8 tile layout and UV metadata format.

### Option D: Redirect font tile page_index to R1272-compatible page
Add R1272 (or a copy) to the font page table and patch the glyph struct initialization to use that page for stat label glyphs. Would require adding an entry to the page table and understanding the struct init code path.
