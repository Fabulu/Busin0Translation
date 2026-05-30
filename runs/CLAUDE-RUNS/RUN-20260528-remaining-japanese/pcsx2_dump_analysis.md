# PCSX2 Texture Dump Analysis

## Filename Format (from PCSX2 source)

PCSX2 texture dump filenames follow this pattern:

```
[TEX0Hash]-[CLUTHash]-r[width]x[height]-[bits].png
```

### Fields

| Segment | Description |
|---------|-------------|
| `TEX0Hash` | xxhash64 of the texture pixel data (hex, variable width) |
| `CLUTHash` | xxhash64 of the CLUT/palette data (only present for indexed formats) |
| `rWxH` | Region dimensions -- sub-rectangle extracted from the full atlas (only present when PCSX2 detects a partial texture draw) |
| `bits` | 32-bit bitfield encoding GS register state (always 8 hex digits) |

### Bitfield Layout of `bits` (from `TextureName` struct)

```
bits 0-5:   TEX0_PSM   (6 bits) -- Pixel Storage Mode
bits 6-9:   TEX0_TW    (4 bits) -- atlas width  = 1 << TW
bits 10-13: TEX0_TH    (4 bits) -- atlas height = 1 << TH
bit 14:     unused     (1 bit, formerly TCC)
bits 15-22: TEXA_TA0   (8 bits) -- alpha expansion value 0
bit 23:     TEXA_AEM   (1 bit)  -- alpha expansion method
bits 24-31: TEXA_TA1   (8 bits) -- alpha expansion value 1
```

### PS2 PSM Values Observed

| PSM hex | PSM name | BPP | Description |
|---------|----------|-----|-------------|
| 0x00 | PSMCT32 | 32 | 32-bit RGBA |
| 0x13 | PSMT8 | 8 | 8-bit indexed (256-color palette) |
| 0x14 | PSMT4 | 4 | 4-bit indexed (16-color palette) |

## Dump Statistics

- **Total dumps:** 411 (all PNG, RGBA 8-bit)
- **Region sub-textures:** 331 (partial draws from a larger atlas)
- **Full atlas textures:** 80 (complete texture uploads)
- **Unique TEX0 hashes:** 392
- **Multi-CLUT textures:** 15 (same pixel data rendered with different palettes)

## Decoded `bits` Values

| bits | PSM | Atlas Size | Count | Context |
|------|-----|-----------|-------|---------|
| 00002214 | PSMT4 | 256x256 | 208 | Most common -- UI elements, glyphs, name entry |
| 00002a94 | PSMT4 | 1024x1024 | 35 | Large textures (24x24 icons) |
| 00001dd3 | PSMT8 | 128x128 | 28 | Various game textures |
| 00002654 | PSMT4 | 512x512 | 27 | Text labels, UI strings |
| 00001dd4 | PSMT4 | 128x128 | 18 | Menu elements |
| 00002254 | PSMT4 | 512x256 | 17 | Wide textures |
| 00001e14 | PSMT4 | 256x128 | 15 | Compact UI elements |
| 00002653 | PSMT8 | 512x512 | 9 | Character portraits |
| 00002614 | PSMT4 | 256x512 | 9 | Tall textures |
| 00002213 | PSMT8 | 256x256 | 7 | Character portraits |

## CLUT Groups (Textures Sharing Same Palette)

### Group 1: `2396a88fd6b4cb36` -- 117 textures, PSMT4 256x256
- All 16x16 regions
- **Identity:** Individual character glyphs (hiragana/katakana/kanji) for the name entry keyboard grid

### Group 2: `2f77f3ea806d10cb` -- 35 textures, PSMT4 1024x1024
- All 24x24 regions
- **Identity:** Icon sprites (status icons, menu icons)

### Group 3: `be78468b72d277cd` -- 25 textures, PSMT4 512x512
- Variable widths, all 24px height: 72, 80, 96, 120, 144, 168, 192, 216, 240, 288, 312, 336
- **Identity:** Rendered Japanese text strings (confirmed: "死霊に取り憑かれた", "バンクォー", "ドゥーハン王国を血と恐怖に", "地上から消えていたであろう。", etc.)
- These are pre-rendered text labels from the game's dialogue/UI system

### Group 4: `3cb39bf7659ef15f` -- 16 textures, PSMT4 256x256
- 48x20 (8 textures), 64x16 (7 textures), 40x24 (1 texture)
- **Identity:** Name entry screen tab labels and UI buttons
- The 48x20 textures are the tab category labels (e.g., hiragana/katakana/alphabet tabs)
- The 64x16 textures are likely button labels (confirm, back, etc.)

### Group 5: `8cef486a60d73b78` -- 16 textures, PSMT4 256x256
- All 64x64 regions
- **Identity:** Larger UI icons or item sprites

### Group 6: `e5121c8caf7d1dd` -- 10 textures, PSMT4 256x256
- All 10x16 regions
- **Identity:** Small individual glyphs for text input (digits, punctuation)
- Same TEX0 hashes appear with 2-3 different CLUTs (color variants: normal, selected, disabled)

### Group 7: `29f5bda4efe25375` -- 7 textures, PSMT4 512x256
- Variable width, 48px height: 88, 108, 120, 152, 168, 248
- **Identity:** Wider pre-rendered text labels (longer strings)

## Cross-Reference with R1188

R1188 (`1188_type01.raw`) is 528,384 bytes (0x81000).

### Size Analysis for R1188

| Format | Width | Height | Match? |
|--------|-------|--------|--------|
| PSMT4 (4bpp) | 256 | 4128 | Too tall for single atlas |
| PSMT4 (4bpp) | 512 | 2064 | Too tall |
| PSMT4 (4bpp) | 1024 | 1032 | Close to 1024x1024 atlas |
| PSMT8 (8bpp) | 256 | 2064 | Too tall |
| PSMT8 (8bpp) | 512 | 1032 | Close to 512x1024 |

### Key Finding: R1188 is Likely NOT a Single Atlas

R1188 at 528,384 bytes doesn't cleanly fit any standard PS2 texture atlas size:
- A PSMT4 256x256 atlas = 32,768 bytes
- A PSMT4 512x512 atlas = 131,072 bytes
- A PSMT4 1024x1024 atlas = 524,288 bytes (close! Only 4,096 bytes short of R1188)
- Difference: 528,384 - 524,288 = 4,096 bytes = likely a header or CLUT data

**This strongly suggests R1188 is a PSMT4 1024x1024 texture with a 4,096-byte header (possibly containing CLUT data).**

A 16-color CLUT in PSMCT32 format = 16 colors x 4 bytes = 64 bytes. But 4,096 bytes could hold:
- 64 CLUTs of 16 colors each (256 palettes worth)
- Or a header structure + CLUTs
- Or a TIM2 / game-specific header

### Matching PCSX2 Dumps to R1188

The PCSX2 dumps with `bits=00002a94` (PSMT4 1024x1024) are the best candidates for R1188:
- 35 dumps, all 24x24 regions, CLUT `2f77f3ea806d10cb`
- These are sub-regions of a 1024x1024 PSMT4 atlas

However, the name entry tab labels (48x20, CLUT `3cb39bf7659ef15f`) come from a 256x256 PSMT4 atlas, which is a different resource -- likely NOT R1188.

## Texture Replacement Approach

PCSX2's texture replacement system can be used to:
1. **Replace individual sub-textures** by placing modified PNGs with matching filenames in the `textures/[GAME-ID]/replacements/` folder
2. **Dimensions can be scaled up** -- PCSX2 handles upscaled replacements
3. **CLUT hash must match** -- the palette determines which replacement is used

### For Name Entry Screen Translation:
- Replace the 8 x `r48x20` tab label textures (CLUT `3cb39bf7659ef15f`)
- Replace the 7 x `r64x16` button label textures (same CLUT)
- Replace individual `r10x16` and `r16x16` glyph textures if needed

### For Pre-rendered Text Labels:
- The 25 textures with CLUT `be78468b72d277cd` (various widths x 24px) are Japanese text strings
- These can be replaced with English equivalents

## Format Information for R1188 Investigation

Based on PCSX2 dump analysis:
- The game overwhelmingly uses **PSMT4** (4-bit indexed/paletted) for UI textures
- PSMT8 is used for character portraits and some game textures
- PSMCT32 is rare (only large background textures like the map)
- All text/UI elements use 4-bit indexed format with separate CLUTs
- The PS2 GS applies block-based swizzling to indexed textures in VRAM, which is why raw dumps of R1188 look scrambled -- PCSX2 unswizzles automatically when dumping

## Sources

- [GS: Add texture dumping and replacement system (PR #5547)](https://github.com/PCSX2/pcsx2/pull/5547)
- [GSdx: Texture Dumping and Replacing (PR #4199)](https://github.com/PCSX2/pcsx2/pull/4199)
- [PCSX2 HD Textures Project Tutorial](https://sites.google.com/view/pcsx2-hd-textures-project/tutorial)
- [PCSX2 GSTextureReplacements.cpp source](https://raw.githubusercontent.com/PCSX2/pcsx2/master/pcsx2/GS/Renderers/HW/GSTextureReplacements.cpp)
