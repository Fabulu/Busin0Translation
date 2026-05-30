# Menu Label Textures with Colored Backgrounds — Full Audit
**Date**: 2026-05-28
**Source**: 411 PCSX2 texture dumps in `build/pcsx2_dumps/`

---

## Executive Summary

After examining all 411 PCSX2 texture dumps plus decoded PACKDATA resources, the
search for pre-rendered text labels with colored backgrounds yielded a clear conclusion:

**Most "menu labels" in Busin 0 are NOT pre-rendered textures.** They are glyph-rendered
at runtime using composite glyph IDs from EXE Table 2C, pulling tiles from R1272
(the main font atlas). This was already established in Wave 3 findings (FINDINGS_LEDGER.md).

Only **two resources** contain pre-rendered Japanese text with colored/styled backgrounds
that need texture editing:

1. **R2124** (PSMT4, type-01, 33,808 bytes) — Main UI overlay atlas with location names
2. **R2548** (PSMT4, type-01, 34,880 bytes) — Floor/level digit indicators and UI elements

Additionally, **R2118-R2122** contain Japanese demo disc screens (pre-rendered text with
backgrounds), but these are demo leftovers not visible in retail gameplay.

---

## Detailed Findings by CLUT Group

### Group 1: `be78468b72d277cd` (25 textures, heights 24px, widths 72-336px)
- **Address**: 0x2654
- **Content**: White Japanese text on TRANSPARENT background
- **What it is**: Story/narrative text rendered by the glyph engine during cutscenes
- **Examples**: "そもそもの発端であったが", "ドゥーハン王国を血と恐怖に", "地上から消えていたであろう。"
- **Action needed**: NONE — these are glyph-rendered dialogue, handled by existing MSG pipeline
- **Files**: `e6b43842cb94b14a-*-r72x24-00002654.png` through `4526b964a9c741b9-*-r336x24-00002654.png`

### Group 2: `3cb39bf7659ef15f` (16 textures: 8x r48x20, 7x r64x16, 1x r40x24)
- **Address**: 0x2214
- **Content**: Tiny white text fragments on transparent background
- **What it is**: Runtime-rendered glyph text (small labels, numbers, abbreviations)
- **Example**: "FIG" (class abbreviation, 32x12 at same address)
- **Action needed**: NONE — runtime glyph rendering, handled by font tile replacement

### Group 3: `29f5bda4efe25375` (7 textures, heights 48-56px, widths 88-248px)
- **Address**: 0x2254
- **Content**: ALREADY ENGLISH — character creation labels
- **Labels found**: "Name", "Gender", "Attribute", "Personality", "Status", "Class&Parameter", "Race"
- **Action needed**: NONE — already translated

### Group 4: `73d6533c7af7f8fd` (3 textures: r128x32, r176x24, r128x160)
- **Address**: 0x2214
- **Content**: Gradient UI panel elements (button backgrounds, not text)
- **Action needed**: NONE

### Group 5: `2f77f3ea806d10cb` (36 textures, all r24x24)
- **Address**: 0x2a94
- **Content**: Small cursor/pointer icons
- **Action needed**: NONE — no text

### Group 6: `c3a3794aa961b0e8` (11 textures: 10x r16x40, 1x r90x56)
- **Address**: 0x1dd4
- **Content**: Stylized individual digits (0-9) with green/colored tint — floor number indicators
- **Action needed**: NONE — digits are language-neutral

### Group 7: `2c185630146e6fea` / `4143b4401f775695` / `71c19dc32b6d752a` (3 textures, all r96x36)
- **Address**: 0x1e14
- **Content**: Button/panel background shapes (dark rounded rectangles)
- **Action needed**: NONE — no text

### Group 8: `47c4ff7756c15630` (2 textures: r56x40, r88x38)
- **Address**: 0x1dd4
- **Content**: ALREADY ENGLISH — "Level" and "Bonus Point" labels
- **Action needed**: NONE — already translated

### Group 9: Title screen labels (address 0x1613)
- **Content**: ALREADY ENGLISH — "New Game", "Press START button"
- **Action needed**: NONE

### Group 10: Location title (CLUT `c6cd31dd61d9b711`, r288x96)
- **Address**: 0x1e54
- **Content**: ALREADY ENGLISH — "Duhan The Imperial City"
- **Action needed**: NONE

---

## Pre-Rendered Japanese Text Requiring Translation

### TEXTURE 1: R2124 — UI Overlay Atlas
- **PACKDATA**: R2124, type-01, 33,808 bytes payload
- **Format**: PSMT4 (4-bit indexed color)
- **Best deswizzle**: dbw=128, header=0x0400 (see `R2124_hdr0400_final.png`)
- **Dimensions**: 256x256 (estimated from payload size)
- **Japanese text visible**:
  - フォブール地区 (Faubourg District)
  - ボローラ地区 (Borora District)
  - ヴァレー地区 (Valley District)
  - ドゥーハン城 (Duhan Castle)
  - 新規登録 (New Registration) — also captured as standalone PCSX2 dump `a2d3fce36c8c719d-e786e0650b284c64-r120x24-00002214.png`
  - "NEW" label (already English)
  - Copyright (C) symbol
  - Various button/panel elements
- **Background colors**: Dark navy/blue bars behind location names
- **Translation approach**: PSMT4 deswizzle (tools/psmt4_deswizzle.py), edit with image editor, reswizzle
- **Status**: Deswizzle partially working (artifacts remain), already in translation pipeline per Wave 5

### TEXTURE 2: R2548 — Floor Digit Atlas + UI Elements
- **PACKDATA**: R2548, type-01, 34,880 bytes payload
- **Format**: PSMT4 (4-bit indexed color)
- **Best deswizzle**: header=0x0840 (see `R2548_exact_hdr0840_2x.png`)
- **Dimensions**: 256x256 (estimated)
- **Content visible**:
  - Rows of digits 0-9 in colored boxes (red/dark backgrounds) — floor/level indicators
  - Additional UI elements (door frames, borders, status indicators)
  - May contain Japanese text in lower sections (hard to read due to deswizzle artifacts)
- **Translation approach**: Same PSMT4 pipeline as R2124
- **Status**: Partially decoded, needs proper deswizzle parameter tuning

---

## Demo Disc Leftovers (Low Priority)

These contain Japanese text with colored backgrounds but are NOT visible during retail gameplay:

| Resource | Dims | Content | Japanese Text |
|----------|------|---------|---------------|
| R2118 | 512x512 | Demo disclaimer | このディスクは開発途中のソフトを元に制作された体験版を収録しております... |
| R2119 | 512x64 | Memory card warning | この体験版は、メモリーカード（PS2）に対応しておりません |
| R2120 | 512x64 | Continue message | この続きは、製品版でお楽しみください |
| R2121 | 512x512 | Promotional ad | 大絶賛発売中 / 希望小売価格 6,800円 (税別) |
| R2122 | 512x64 | Demo badge | 体験版 |

- **Format**: PSMT8 (deswizzle SOLVED — tools/psmt8_deswizzle.py works perfectly)
- **Priority**: Lowest — these screens only appear on demo disc builds

---

## Textures Confirmed as Non-Text

| Category | Count | Content |
|----------|-------|---------|
| NPC/character portraits | ~50 | Full-page CG at 0x2213, 0x2253, 0x2613 |
| Dungeon/environment textures | ~30 | Walls, floors, foliage at 0x1dd3, 0x1e13 |
| 3D model textures | ~10 | Pillars, capsules at 0x19d3, 0x1554 |
| Background CG scenes | ~15 | Battle scenes, city views at 0x2653 |
| Logos | 2 | ATLUS, Racjin |
| World map | 2 | Duhan kingdom map (English labels) |
| Particle effects | ~29 | Explosions, glows at r64x64 |
| Runtime glyph captures | ~180 | Individual 16x16 font tiles, r10x16 digits |
| UI decorative frames | ~5 | Borders, panel backgrounds |

---

## Cross-Reference with PACKDATA

### Type-01 Resources with Texture-Like Sizes (R2000+)
| Resource | Size | Description |
|----------|------|-------------|
| R2087-R2097 | 0 payload (sector-only) | Large binary blobs, not text |
| R2105 | 230,560 | Large CG image (~512x448) |
| R2118-R2122 | 33,984-263,360 | Demo screens (PSMT8, translated as low-priority) |
| **R2124** | **33,808** | **UI overlay atlas (PSMT4) — HAS JAPANESE TEXT** |
| R2288-R2289 | 73,920-160,816 | CG images (no text visible) |
| R2306-R2451 | Various | CG images and portraits |
| R2471-R2543 | 132,256 each | Character/monster portraits (all same size) |
| **R2548** | **34,880** | **Floor digits + UI atlas (PSMT4) — MAY HAVE JAPANESE TEXT** |
| R2654 | 5,666 (type-44) | System data table (not a texture) |

---

## Summary of Actionable Items

### Must Fix (Japanese text visible to players):
1. **R2124** — Location name banners (フォブール地区, etc.) on dark backgrounds
   - Deswizzle: PSMT4 with dbw=128
   - Replace Japanese text with English equivalents
   - Uses canonical names from Busin 1: Faubourg, Borora, Valley, Duhan Castle

2. **R2548** — Floor/level indicators (if Japanese text confirmed in lower sections)
   - Deswizzle: PSMT4 with dbw needs tuning
   - Digits are language-neutral, check for kanji labels

### Already Working (no action needed):
- Character creation labels ("Name", "Gender", etc.) — already English
- Title screen labels ("New Game", "Press START button") — already English
- Location title ("Duhan The Imperial City") — already English
- Menu button labels — runtime glyph-rendered from R1272 font tiles (handled by font tile replacement)
- Story narration text — runtime glyph-rendered (handled by MSG pipeline)

### Low Priority:
- R2118-R2122 demo screens — not visible in retail
