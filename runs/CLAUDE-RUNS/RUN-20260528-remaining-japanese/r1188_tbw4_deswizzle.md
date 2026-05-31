# R1188 TBW=4 Deswizzle Analysis

**Date**: 2026-05-28

## Summary

Deswizzling R1188 with TBW=4 parameters (bw_psmt4=256, dbw_ct32=512) produces a **clear, readable 256-pixel-wide glyph atlas**. This confirms the game's TBW=4 TEX0 configuration views R1188 as a 256px-wide column of glyphs -- BUT the tab labels are NOT pre-rendered bitmaps in this atlas. They are composed at runtime from individual glyph cells.

---

## TBW=4 Deswizzle Results

### Working Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| tex_w | 256 | TBW=4 means 4*64=256 pixel buffer width |
| bw_psmt4 | 256 | PSMT4 read-back buffer width |
| dbw_ct32 | 512 | Same upload buffer width as the known-working 1024x1024 deswizzle |

**Key finding**: The upload buffer width (dbw_ct32=512) must match the original DMA upload, NOT the TEX0 read width. The game uploads the texture at one buffer width (512 PSMCT32 pixels) but reads it at a different width (TBW=4 = 256 PSMT4 pixels).

### Failed Combinations

| dbw_ct32 | bw_psmt4 | Result |
|----------|----------|--------|
| 64 | 256 | Garbled -- upload width wrong |
| 128 | 256 | Garbled -- upload width wrong |
| 256 | 256 | Garbled -- upload width wrong |

The deswizzle ONLY works when dbw_ct32=512, because that's the actual PSMCT32 DMA transfer width.

### Visual Result

The 256x256 crop of the TBW=4 atlas shows a clean glyph grid:
- **Row 0** (y=5-21): Digits 5-9, punctuation `:;<=>?`
- **Row 1** (y=26-47): Copyright symbol, lowercase Latin `a b c d e f g h i`
- **Row 2** (y=50-69): Symbols `X O X <-- -->`, underscore, hiragana `あいうえ`
- **Row 3** (y=74-93): Hiragana `やゆよらりるれろわをん`
- **Row 4** (y=98-117): Katakana `えおっゥアイウエオカキ`
- **Row 5-6** (y=122-148): Punctuation, dakuten/handakuten marks
- **Row 7** (y=156-175): Latin uppercase `A B C D E F G H I`
- **Row 8** (y=178-197): Latin lowercase `j k l m n o p q r s`
- **Row 9** (y=201-221): Hiragana `おかきくけこさしすせ`
- **Row 10** (y=226-245): Katakana (dakuten) `がぎぐげござじずぜぞ`
- **Row 11** (y=249-255+): Katakana `クケコサシスセソタチ` (extends past 256)

Image files:
- `r1188_tbw4_upload512_read256_256x256.png` -- clean glyph grid
- `r1188_tbw4_upload512_read256_256x512.png` -- extended view
- `r1188_tbw4_256x256_2x.png` -- 2x scaled for inspection

---

## Cell Data Structure Reanalysis

### All Pages Share V=60+ Pattern

Examining cell data across ALL pages (0x01 through 0x31) reveals that **V=60 is NOT unique to tab labels**. Every page starts its cells at V=60 and increments sequentially:

| Page | Desc | Cell Count | V Range | b5 Range |
|------|------|-----------|---------|----------|
| 0x01 | 0 | 16 | 60-75 | 0xA1-0xA2 |
| 0x02 | 0 | 16 | 60-75 | 0xA1-0xA2 |
| 0x09 | 0 | 16 | 60-73 | 0xA3 |
| 0x0A | 0 | 16 | 60-75 | 0xA3-0xA4 |
| 0x0B | 0 | 16+ | 60-88+ | 0xA4-0xA5+ |
| 0x19 | 0 | 250+ | 60-72 (repeating) | 0xB4-0xBD |

### b4:b5 Is a Global VRAM Address

The b4:b5 LE16 value forms a **monotonically increasing sequence** across all pages and cells:
- Total non-empty cells: 11,821
- Range: 0x0000 to 0xDC80
- Most common stride: 8 (552 occurrences), 16 (204 occurrences)
- Each cell gets a unique b4:b5 value

This is a **linear VRAM slot allocator**. Each glyph cell is assigned a unique VRAM address. The game sets TBP0 to this address before drawing each glyph sprite.

### Revised Cell Format

```
Cell[8 bytes]:
  byte0 (U):  Horizontal tile coordinate within the local texture region
  byte1 (V):  Vertical tile coordinate within the local texture region  
  byte2 (W):  Sprite width in pixels (always 100 for name entry chars)
  byte3:      Flag (0 or 1) -- purpose unclear (two-cell-wide?)
  byte4-5:    VRAM address (LE16) -- used as TBP0 or VRAM offset
  byte6:      Always 79 (0x4F) -- possibly sprite height or palette index
  byte7:      Always 0 -- padding or high byte
```

### Tile Size Determination

Sprite descriptors at R1188 offset 0x570 all contain bytes `[0, 4, 0, 4, ...]`, indicating **tile_w=4, tile_h=4** pixel tiles.

With tile_h=4:
- V=60 -> pixel y = 240
- V=72 -> pixel y = 288
- Each V increment = 4 pixels

### b6=79 as Sprite Height

If b6=79 represents the sprite height in pixels, that would make each glyph sprite 100x79 pixels -- too large for a name entry character cell. More likely b6 is used for something else (palette CSA, or it's a fixed constant).

---

## Tab Label Rendering Mechanism

### Tab Labels Are NOT Pre-Rendered Bitmaps

The PCSX2 texture dumps show tab labels ("性別", "かな", "英数", etc.) as 48x20 pixel sprites, but these are **runtime-composed textures**, not pre-baked atlas entries.

Evidence:
1. Page 0x19 cell data uses the same U/V/W format as individual glyph cells
2. All pages share desc_idx=0 (same texture source as ASCII/kana/kanji)
3. V=60-72 maps to CJK character positions in the atlas, not to pre-rendered labels
4. The PCSX2 texture replacement system captures RENDERED textures from VRAM, including any runtime-composed text

### Runtime Composition Flow

1. Game loads R1188 atlas to VRAM at base TBP0
2. For each tab label, game renders individual glyphs to a VRAM scratch area
3. Game then uses the scratch area as a texture source for the tab button sprite
4. PCSX2 captures this scratch area as a "texture" (48x20 with composed text)

### Implication for Translation

To translate tab labels, we do NOT need to:
- Find pre-rendered label bitmaps in R1188
- Deswizzle at TBW=4 to find labels

Instead, we need to:
- Identify the glyph composition code that renders tab labels
- Patch the glyph IDs used for each tab (e.g., change "性別" to "SEX" glyphs)
- OR patch the cell data to point to English replacement glyphs
- OR intercept at the render function and substitute English text

---

## Open Questions

1. **How does the game set TBP0 per-cell?** The render_glyph_sprite function packs U, V, desc_idx into $a0 but b4:b5 is not included. Where/how does b4:b5 get used?

2. **What is b6=79?** Constant across all cells. Could be:
   - Sprite height in some unit
   - CLUT CSA value (PSMT4 supports 0-31)
   - GS register configuration index

3. **Which code composes tab labels?** The tab label PCSX2 dumps show composed multi-character text, suggesting a render-to-texture step. This code path needs to be found to redirect it to English text.

---

## Files Generated

| File | Description |
|------|-------------|
| `r1188_tbw4_upload512_read256_256x256.png` | Clean TBW=4 atlas (256x256, correct deswizzle) |
| `r1188_tbw4_upload512_read256_256x512.png` | Extended TBW=4 view (256x512) |
| `r1188_tbw4_upload512_read256_256x1024.png` | Full TBW=4 view (256x1024) |
| `r1188_tbw4_256x256_2x.png` | 2x scaled for inspection |
| `r1188_tbw4_y236_300_4x.png` | V=60 region at tile_h=4 (y=236-300, 4x) |
| `r1188_tbw4_all_tabs_v60_72_4x.png` | Cells 0-12 of page 0x19 at tile_h=4 in 256-wide atlas |
| `r1188_full1024_all_tabs_v60_72_4x.png` | Same cells in full 1024x1024 atlas |
| `r1188_tbw4_both64_256x256.png` | Failed: dbw=64 garbled |
| `r1188_tbw4_both128_256x256.png` | Failed: dbw=128 garbled |
| `r1188_tbw4_b4_as_y_w48_3x.png` | b4 interpreted as pixel Y (shows glyph rows, not labels) |
| `r1188_tbw4_b4_as_y_w100_3x.png` | Same at 100px width |
