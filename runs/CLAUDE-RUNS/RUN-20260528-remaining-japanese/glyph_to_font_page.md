# Glyph-to-Font-Page Mapping: Definitive Answer

**Date**: 2026-05-28

---

## Key Finding: The Table at 0x3CAA60 is NOT Used for Glyph Dispatch

The 10-entry table at EXE offset 0x3CAA60 lists resource IDs (R1303, R1269-R1277, R1302) as paired uint32 values. These are **general texture resource handles** for environment/UI textures (PSMT8 format). They are NOT font page resources and play NO role in rendering stat label glyphs.

### Table Contents (for reference)
| Entry | Resource |
|-------|----------|
| 0 | R1303 |
| 1 | R1269 |
| 2 | R1270 |
| 3 | R1271 |
| 4 | R1273 |
| 5 | R1274 |
| 6 | R1275 |
| 7 | R1276 |
| 8 | R1277 |
| 9 | R1302 |

---

## Answer: ALL Stat Glyphs Come from R1188

**Glyph 346 (力/STR) is in resource R1188**, a single PSMT4 1024x1024 texture atlas. It is NOT in any of the R1269-R1277 or R1302-R1303 resources.

The font tile system (System 2) uses a page table at EXE offset `0x3DB180` (VA `0x4DB100`) with 50 entries. Each glyph ID maps to a page via `page = glyph_id / 256`, and every page's cell data references VRAM addresses in the 0xA140-0xA9B0 range -- all belonging to R1188.

---

## Complete Stat Glyph Mapping

| Glyph ID | Character | Stat | Page | Cell | U | V | VRAM Block | Resource |
|----------|-----------|------|------|------|---|---|------------|----------|
| **346** | **力** | **STR** | **1** | **0x5A** | **1** | **60** | **0xA450** | **R1188** |
| 535 | 知 | INT char1 | 2 | 0x17 | 0 | 67 | 0xA1F0 | R1188 |
| 717 | 恵 | INT char2 | 2 | 0xCD | 3 | 88 | 0xA700 | R1188 |
| 308 | 信 | FTH char1 | 1 | 0x34 | 0 | 76 | 0xA238 | R1188 |
| 354 | 仰 | FTH char2 | 1 | 0x62 | 0 | 66 | 0xA390 | R1188 |
| 320 | 心 | FTH char3 | 1 | 0x40 | 0 | 62 | 0xA290 | R1188 |
| 718 | 生 | VIT char1 | 2 | 0xCE | 4 | 60 | 0xA708 | R1188 |
| 696 | 命 | VIT char2 | 2 | 0xB8 | 3 | 67 | 0xA658 | R1188 |
| 346 | 力 | VIT char3 | 1 | 0x5A | 1 | 60 | 0xA450 | R1188 (shared with STR) |
| 582 | 敏 | AGI char1 | 2 | 0x46 | 0 | 60 | 0xA2E0 | R1188 |
| 719 | 速 | AGI char2 | 2 | 0xCF | 4 | 61 | 0xA710 | R1188 |
| 590 | 度 | AGI/LCK suffix | 2 | 0x4E | 0 | 60 | 0xA318 | R1188 |
| 720 | 幸 | LCK char1 | 2 | 0xD0 | 4 | 62 | 0xA718 | R1188 |
| 721 | 運 | LCK char2 | 2 | 0xD1 | 4 | 63 | 0xA720 | R1188 |

---

## How the Dispatch Works

```
Glyph ID 346 (0x015A)
  page  = 346 / 256 = 1
  cell  = 346 % 256 = 0x5A (90)

Page table[1] at 0x3DB188:
  desc_idx = 0 (primary R1188 GS texture descriptor)
  cell_data_ptr -> cell array at file offset 0x3D9040

Cell data[0x5A] (8 bytes):
  U=1, V=60, W=100, Flag=0, VRAM=0xA450

VRAM 0xA450 is within R1188's upload range (0xA140-0xA9B0)
  -> GS samples from R1188's PSMT4 texture in VRAM
```

---

## Summary

- The R1269-R1277 / R1302-R1303 resources are PSMT8 environment textures, not fonts
- ALL stat label glyphs (346, 535, 717, 308, 354, 320, 718, 696, 582, 719, 590, 720, 721) render from **R1188**
- R1188 is a single PSMT4 1024x1024 atlas containing all kanji, kana, symbols, and UI glyphs
- The font dispatch at VA 0x30B770 uses a per-glyph struct (50 bytes each) whose page_index field selects a page table entry, which in turn references R1188's GS texture descriptor
