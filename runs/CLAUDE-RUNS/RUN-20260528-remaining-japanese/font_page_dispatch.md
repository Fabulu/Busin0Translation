# Font Page Dispatch: EXE Reverse Engineering

**Date:** 2026-05-28
**Target:** VA 0x30B770 (file 0x20B7F0) in SLPM_653.78
**ELF mapping:** file_offset = VA - 0xFFF80

---

## Critical Finding: Two Independent Font Systems

The game has **two completely separate font/glyph systems**, and the stat label glyph IDs (346, 308, 320, etc.) belong to the WRONG one for this analysis.

### System A: Font Page Dispatch (func_30B770)

**Purpose:** Manages dynamically-loaded font page resources for script-driven text rendering.

| Component | Address | Details |
|-----------|---------|---------|
| Availability check | VA 0x30B770 | Checks if a page_index's resource is loaded |
| Render loop | VA 0x30B840 | Iterates 32 glyph slots, renders each |
| Page load/unload | VA 0x30B3F0 | Loads resources from PACKDATA |
| Glyph setup API | VA 0x30AFF0 | Sets slot_index and page_index |
| Struct base pointer | gp-0x68E4 (-26852) | 32 x 50-byte runtime structs |
| Page array pointer | gp-0x68E8 (-26856) | Runtime refcount array |
| **Resource table** | **VA 0x4CA710 (file 0x3CA790)** | **700 entries x 8 bytes** |

**Resource table format:** Each 8-byte entry = (resource_handle, resource_handle_duplicate), where resource_handle = PACKDATA_resource_id << 16.

**Dispatch mechanism:**
```
page_index (0-678)
  -> resource_table[page_index * 8]    @ VA 0x4CA710
  -> PACKDATA resource handle
  -> Load resource, call get_sub_resource(data, 0)  @ JAL 0x127078
  -> UV coordinates from sub-resource header (+12..+18)
  -> GS renders textured sprite
```

**Key resource mappings in this table:**

| page_index | Resource | Notes |
|------------|----------|-------|
| 0 | (empty) | |
| 1-54 | R1215-R1268 | Sequential kanji pages |
| 55-57 | (empty) | Gap |
| 58 | R1283 | Extended |
| 59-66 | R1304-R1311 | Environment textures (NOT fonts) |
| 67-71 | R1278-R1282 | Extended |
| 72-89 | R1284-R1301 | Extended |
| 90 | R1303 | Extended |
| **91** | **R1269** | |
| **92** | **R1270** | |
| **93** | **R1271** | |
| **94** | **R1273** | |
| 95-98 | R1274-R1277 | Extended kanji |
| 99 | R1302 | |
| 100-699 | Various | R1300s-R1800s, many game assets |

**R1272 is NOT in this table.** It is loaded separately for the TextEvent MSG renderer.

### System B: Cell Data Page Table (UI Tile System)

**Purpose:** Provides static UV/VRAM coordinates for UI labels, stat names, and menu tiles.

| Component | Address | Details |
|-----------|---------|---------|
| Page table | VA 0x4DB100 (file 0x3DB180) | 30 entries x 8 bytes |
| Page entry format | (desc_idx: u32, cell_data_va: u32) | |
| Cell data format | 8 bytes per cell: U, V, W, Flag, VRAM_addr(u16), extra(u16) | |
| Total cells | 519 across 30 pages | Variable cells per page |

**This is the system used by stat labels.** The "glyph IDs" (346, 308, 320, etc.) from previous analyses are sequential cell indices across the concatenated cell arrays in this table.

---

## Glyph 346 Analysis

**Glyph 346 does NOT use R1270 or R1271.** It belongs to System B.

| Property | Value |
|----------|-------|
| Sequential cell index | 346 |
| Cell data page | Page 16 (desc_idx=2) |
| Cell within page | 7 |
| Cell data VA | 0x4D9798 |
| Cell data file offset | 0x3D9818 |
| U coordinate | 2 |
| V coordinate | 60 |
| Width | 100 pixels |
| VRAM block address | 0xAD70 |
| Source texture | **R1188** (1024x1024 PSMT4 atlas) |

The VRAM address 0xAD70 falls within the R1188 atlas upload range (0xA000-0xB000+).

### All Stat Label Glyph Mappings (System B)

| Stat | Glyph ID | Page | Cell | U | V | VRAM |
|------|----------|------|------|---|---|------|
| STR (chikara) | 346 | 16 | 7 | 2 | 60 | 0xAD70 |
| FTH1 (shin) | 308 | 14 | 2 | 0 | 62 | 0xAB10 |
| FTH3 (kokoro) | 320 | 15 | 0 | 0 | 60 | 0xABD0 |
| FTH2 (kou) | 354 | 17 | 2 | 0 | 62 | 0xADF0 |
| INT1 (chie) | 535 | -- | -- | -- | -- | OUT OF RANGE (>519) |

**Note:** Glyph IDs 535, 696, 717-721 exceed the 519-cell System B range. These may use System A or a third rendering path.

---

## System A Detailed Disassembly

### func_30AFF0 (SetGlyphTile) - VA 0x30AFF0

```mips
; Input: a0 = slot_index (0-31), a1 = page_index (0-678)
30AFF0: andi  r3, a0, 0xFFFF
30AFF8: slti  r2, r3, 32         ; validate slot < 32
30B020: andi  r3, a1, 0xFFFF
30B024: slti  r2, r3, 679        ; validate page_index < 679
30B048: sh    a0, -26828(gp)     ; store current slot index
30B04C: sh    a1, -26832(gp)     ; store current page_index
30B054: jal   0x2F15E0           ; trigger state machine
```

### func_30B120 (GlyphSlotInit) - VA 0x30B120

```mips
; Reads slot_index from gp-26828, page_index from gp-26832
; Computes struct_addr = base + slot_index * 50
; Writes: struct[0] = page_index (sh r5, 0(r6))
;         struct[2..49] = initialized defaults
```

### func_30B770 (PageAvailCheck) - VA 0x30B770

```mips
; Input: a0 = glyph_slot_id (lower 16 bits)
; 1. Compute struct address: base + glyph_slot_id * 50
;    SLL r2, r5, 2       ; *4
;    ADDU r4, r2, r5     ; *5
;    SLL r3, r4, 2       ; *20
;    ADDU r3, r4, r3     ; *25
;    SLL r3, r3, 1       ; *50
;    ADDU r2, base, r3   ; final address
; 2. LH r4, 0(r2)       ; page_index from struct
; 3. Bounds check: 0 <= page_index < 679
; 4. LW r3, page_array[page_index * 8]   ; data pointer
; 5. LHU r3, page_array[page_index * 8 + 4] ; refcount
; 6. Return: loaded or not
```

### func_30B840 (RenderAllTiles) - VA 0x30B840

```mips
; Loop: r18=0..31, r17 += 50 each iteration
; For each slot:
;   r19 = struct_base + r17
;   r4 = struct[0] (page_index), skip if -1 or >= 679
;   Load resource data from page_array[page_index * 8]
;   JAL 0x127078 (get_sub_resource)
;   Copy UV from resource: struct[14]=res[12], struct[16]=res[14]
;   struct[18] = res[16]-res[12] (width)
;   struct[20] = res[18]-res[14] (height)
;   Render GS sprite
```

---

## Per-Glyph Runtime Struct (50 bytes)

| Offset | Size | Field |
|--------|------|-------|
| +0 | 2 | page_index (int16, -1 = inactive) |
| +2 | 2 | X position |
| +4 | 2 | Y position |
| +14 | 2 | U1 (from resource) |
| +16 | 2 | V1 (from resource) |
| +18 | 2 | tile width (computed) |
| +20 | 2 | tile height (computed) |
| +22-34 | varies | position/transform data |
| +36 | 2 | flags (bit 15 = hidden) |
| +38-42 | 6 | scale/alpha (initialized to 100) |
| +44-46 | 3 | alpha channels (initialized to 128) |
| +47 | 1 | visibility flag |
| +48-49 | 2 | state flags (initialized to 2) |

---

## Key Addresses Summary

| What | VA | File Offset |
|------|-----|-------------|
| Resource table (700 entries x 8B) | 0x4CA710 | 0x3CA790 |
| Cell data page table (30 entries x 8B) | 0x4DB100 | 0x3DB180 |
| SetGlyphTile function | 0x30AFF0 | 0x20B070 |
| GlyphSlotInit function | 0x30B120 | 0x20B1A0 |
| PageAvailCheck function | 0x30B770 | 0x20B7F0 |
| RenderAllTiles function | 0x30B840 | 0x20B8C0 |
| Page load/unload function | 0x30B3F0 | 0x20B470 |
| GlyphSlotReset function | 0x30B070 | 0x20B0F0 |
| Struct base pointer | gp - 0x68E4 | (runtime) |
| Page array pointer | gp - 0x68E8 | (runtime) |

---

## Answer to Original Questions

**Q: Does glyph 346 go to R1270? R1271?**
**A: NO.** Glyph 346 is a cell index in System B (cell data pages at 0x4DB100), rendering from R1188 (the main kanji atlas) at VRAM block 0xAD70. R1270 is at page_index 92 in System A (resource table at 0x4CA710), which is a completely different dispatch system used for script-driven font tile rendering.

**Q: How does the code compute which page to use?**
**A:** System A does NOT compute the page from the glyph ID. The page_index is passed as a runtime argument to `SetGlyphTile(slot, page_index)` by the calling script system. The page_index directly indexes the 700-entry resource table.

**Q: Is it page_index = (glyph_id - 95) / page_size?**
**A: No.** There is no arithmetic computation. The page_index is stored in each glyph's runtime struct field[0], set by the caller.

**Q: What is the page size (glyphs per page)?**
**A:** In System A, each resource IS a page -- there is no fixed "glyphs per page". Each loaded resource provides its own UV coordinates via its sub-resource header. In System B, pages have variable cell counts (2-92 cells per page).

**Q: Which page does R1270 cover?**
**A:** R1270 is at page_index 92 in System A's resource table. It is a PACKDATA resource (256x512 PSMT8) that can be loaded when the script system requests page_index 92. It is NOT related to stat label glyph 346.
