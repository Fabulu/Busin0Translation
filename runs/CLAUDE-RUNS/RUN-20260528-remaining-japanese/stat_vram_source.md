# Stat Label VRAM Texture Source: Definitive Analysis

**Date**: 2026-05-28
**Savestate**: `RAMdumps/27-5.p2s` (chargen screen)
**Analyst**: Claude Opus 4.6 (1M context)

---

## Executive Summary

The stat labels (力/知恵/信仰心/生命力/敏捷度/幸運度) are rendered from **kanji font page resources (R1269-R1276, R1303)**, NOT from R1272. These are PSMT8 (8-bit palettized) textures, distinct from R1272's PSMT4 format.

**The game uses a two-tier font system:**
- **R1272** (PSMT4, 256x512): Base font for ASCII/simple glyphs (positions 0-94 replaced with English)
- **Kanji font pages** (PSMT8, 256x512 or 512x512): JIS kanji bitmaps for glyph IDs 95+

---

## GS VRAM Texture Identification

### Active Texture During Stat Label Rendering

From PCSX2 texture dumps (filenames in this directory):
- `stat_alpha_*-r64x16-00002214.png`: Individual stat label sprites
- TBP0 = 0x2214 (8724) for the rendered 64x16 sprite tiles
- The sprites contain Japanese kanji rendered from the kanji font pages

### TEX0 Register Analysis (from EE memory GIF packets)

The most-used PSMT4 texture on the chargen screen:

| Register | Value | Meaning |
|----------|-------|---------|
| TBP0 | 10304 (0x2840) | VRAM block pointer |
| TBW | 4 | Buffer width |
| PSM | PSMT4 (0x14) | 4-bit palettized |
| Size | 256x256 | Texture dimensions |
| CBP | 10432 (0x28C0) | CLUT base pointer |
| Usage | 90 references | Most-used texture on screen |

VRAM byte offset: 0x284000 - 0x290000

### R1272 Location (for comparison)

| Register | Value |
|----------|-------|
| TBP0 | 12288 (0x3000) |
| Size | 256x512 |
| VRAM range | 0x300000 - 0x340000 |

**These are completely separate VRAM regions with no overlap.**

---

## Font Page Architecture

### Font Page Table in EXE

Location: EXE file offset `0x3CAA60` (8 entries, each duplicated as u32 pairs)

| Page | Resource | Format | Size | Glyph Capacity |
|------|----------|--------|------|----------------|
| 0 | R1303 | PSMT8 | 512x512 | ~1024 |
| 1 | R1269 | PSMT8 | 512x512 | ~1024 |
| 2 | R1270 | PSMT8 | 256x512 | ~512 |
| 3 | R1271 | PSMT8 | 256x512 | ~512 |
| 4 | R1273 | PSMT8 | 256x512 | ~512 |
| 5 | R1274 | PSMT8 | 512x512 | ~1024 |
| 6 | R1275 | PSMT8 | 512x512 | ~1024 |
| 7 | R1276 | PSMT8 | 512x512 | ~1024 |

**R1272 is NOT in this table** -- it is handled separately as the base font.

### Resource File Sizes

| Resource | File Size | Pixel Data | Format |
|----------|-----------|------------|--------|
| R1272 | 65,792 | 65,536 | PSMT4 256x512 |
| R1303 | 263,328 | 262,144 | PSMT8 512x512 |
| R1269 | 263,360 | 262,144 | PSMT8 512x512 |
| R1270 | 132,288 | 131,072 | PSMT8 256x512 |
| R1271 | 132,288 | 131,072 | PSMT8 256x512 |
| R1273 | 132,288 | 131,072 | PSMT8 256x512 |
| R1274 | 263,360 | 262,144 | PSMT8 512x512 |
| R1275 | 263,360 | 262,144 | PSMT8 512x512 |
| R1276 | 263,360 | 262,144 | PSMT8 512x512 |

### PSMT8 Textures in VRAM (from save state)

The kanji pages load into VRAM as a series of 256x256 PSMT8 tiles:

| TBP0 | TBW | Size | CBP | Notes |
|------|-----|------|-----|-------|
| 12288 | 4/8 | 256x256 / 512x512 | 12544-13312 | First kanji page(s) |
| 12548 | 4 | 256x256 | 12804 | Second sub-page |
| 12808 | 4 | 256x256 | 13064 | Third sub-page |
| ... | 4 | 256x256 | ... | Continues at 260-block intervals |
| 15148 | 4 | 256x256 | 15404 | Last visible sub-page |

These span VRAM from block 12288 to ~15404, which is 0x300000 to 0x3C3800.

---

## Stat Label Glyph ID to Font Page Mapping

### Glyph IDs Used by Stat Labels

| Label | Japanese | Glyph IDs | In R1272 Range (0-511)? |
|-------|----------|-----------|------------------------|
| STR | 力 | 346 | YES but NOT read from R1272 |
| INT | 知恵 | 535, 717 | NO (both > 511) |
| FTH | 信仰心 | 308, 354, 320 | YES but NOT read from R1272 |
| VIT | 生命力 | 718, 696, 346 | MIXED |
| AGI | 敏捷度 | 582, 719, 378 | MIXED |
| LCK | 幸運度 | 720, 721, 378 | MIXED |
| Gender | 性別 | 511, 512 | MIXED |
| Race | 種族 | 513, 514 | NO |
| Alignment | 属性 | 515, 511 | NO |

### Glyph Dispatch

The game dispatches **all glyph IDs 95+** to the kanji font page system, bypassing R1272 entirely. Even though glyph 346 could theoretically fit in R1272's 512-cell grid, the dispatch logic routes it to the kanji pages.

This explains why replacing R1272 bitmap positions 95-882 has no effect on stat labels.

---

## R1272 Upload Status in VRAM

R1272 pixel data was **NOT found** in the VRAM dump at the time of this save state. Extensive byte-pattern matching confirmed:
- No 16-byte chunk from R1272's pixel data matched anywhere in the 4MB VRAM
- This suggests R1272 may not have been uploaded yet, or was overwritten

The kanji font pages ARE loaded (PSMT8 TEX0 entries present at TBP0=12288+).

---

## Conclusions for Translation Fix

### Why R1272 replacement alone does NOT fix stat labels

1. Stat label glyph IDs (346, 535, 717, etc.) are dispatched to kanji font pages, not R1272
2. R1272 positions 95+ are never consulted for these glyphs
3. The kanji font pages (R1269-R1276, R1303) have not been modified

### Fix Options

**Option A: Replace kanji bitmaps in font page resources**
- Identify which font page serves each glyph ID (requires glyph-to-page dispatch RE)
- Replace the specific kanji bitmaps with English text bitmaps in the correct font page
- Risk: these kanji may appear in dialogue text elsewhere

**Option B: Patch EXE glyph dispatch**
- Redirect glyph IDs 95+ (or specific stat label IDs) to R1272 instead of kanji pages
- Font page table at EXE offset 0x3CAA60 and dispatch logic at ~0x3C8B10 are involved
- Lets existing R1272 English bitmaps at positions 346, 535, etc. actually get used

**Option C: Patch rendering code**
- Change chargen renderer to read stat labels from R38 MSG (already English)
- Most correct but requires complex MIPS patching of function at VA 0x2F1090

---

## Key File Paths

| File | Purpose |
|------|---------|
| `extracted/packdata_resources/1272_type01.bin` | Base font (PSMT4, our English atlas) |
| `extracted/packdata_resources/1303_type01.bin` | Kanji page 0 (PSMT8 512x512) |
| `extracted/packdata_resources/1269_type01.bin` | Kanji page 1 (PSMT8 512x512) |
| `extracted/packdata_resources/1270_type01.bin` | Kanji page 2 (PSMT8 256x512) |
| `extracted/packdata_resources/1271_type01.bin` | Kanji page 3 (PSMT8 256x512) |
| `extracted/packdata_resources/1273_type01.bin` | Kanji page 4 (PSMT8 256x512) |
| `extracted/packdata_resources/1274_type01.bin` | Kanji page 5 (PSMT8 512x512) |
| `extracted/packdata_resources/1275_type01.bin` | Kanji page 6 (PSMT8 512x512) |
| `extracted/packdata_resources/1276_type01.bin` | Kanji page 7 (PSMT8 512x512) |
| `extracted/SLPM_653.78` | EXE (font page table at offset 0x3CAA60) |
