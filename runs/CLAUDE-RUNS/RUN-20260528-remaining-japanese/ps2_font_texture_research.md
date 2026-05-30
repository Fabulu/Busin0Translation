# PS2 Font & UI Texture Storage Formats -- Research Report

**Date**: 2026-05-28
**Purpose**: Understand how PS2 games store pre-rendered glyph/button bitmaps, with focus on Racjin-developed titles and relevance to Busin 0 translation.

---

## 1. PS2 Graphics Synthesizer Pixel Storage Modes

The PS2 GS organizes VRAM hierarchically: **Column** (64 bytes) -> **Block** (256 bytes / 4 columns) -> **Page** (8192 bytes / 32 blocks).

### Page dimensions per format

| PSM ID | Name | Bits/Pixel | Page (px) | Block (px) | Common Use |
|--------|------|------------|-----------|------------|------------|
| 0x00 | PSMCT32 | 32 | 64x32 | 8x8 | Framebuffer, full-color textures |
| 0x02 | PSMCT16 | 16 | 64x64 | 16x8 | Framebuffer, 16-bit textures |
| 0x13 | PSMT8 | 8 | 128x64 | 16x16 | **Indexed 256-color textures (fonts)** |
| 0x14 | PSMT4 | 4 | 128x128 | 32x16 | **Indexed 16-color textures (fonts, UI)** |
| 0x1B | PSMT8H | 8 | 64x32 | 8x8 | 8-bit stored in upper 8 bits of 32-bit word |
| 0x24 | PSMT4HL | 4 | 64x32 | 8x8 | 4-bit stored in bits 24-27 of 32-bit word |
| 0x2C | PSMT4HH | 4 | 64x32 | 8x8 | 4-bit stored in bits 28-31 of 32-bit word |

### PSMT8H / PSMT4HL / PSMT4HH -- "Upper half" formats

These are rarely-used variants where indexed pixel data occupies the **upper bits** of a 32-bit VRAM word. They have the same page layout as PSMCT32 (64x32). Their purpose is to allow a Z-buffer (stored in the lower 24 bits) to share VRAM pages with a small indexed texture. They are **NOT typically used for font or UI textures** -- standard PSMT4/PSMT8 are far more common for those.

---

## 2. Texture Swizzling (The Core Challenge)

### What is swizzle?

Games upload texture data to GS VRAM using PSMCT32 mode (fastest DMA path), but the GS reads it back using PSMT8 or PSMT4 mode for rendering. These two modes have **different block/column arrangements**, so bytes end up at different VRAM addresses than a linear mapping would produce. This displacement is the "swizzle."

### Two-Phase VRAM Simulation (Deswizzle Algorithm)

**To decode (deswizzle):**
1. Write raw file bytes into a VRAM buffer using **PSMCT32 addressing** (simulating the upload)
2. Read them back from that buffer using **PSMT8 addressing** (simulating how the GS reads them for rendering)

**To encode (reswizzle):**
1. Write linear pixel indices to VRAM using **PSMT8 addressing**
2. Read them back using **PSMCT32 addressing**

### Critical parameter: dbw_ct32

For PSMT8: `dbw_ct32 = texture_width / 2` (because 4 PSMT8 bytes = 1 PSMCT32 pixel)
For PSMT4: `dbw_ct32 = texture_width / 4` (because 8 PSMT4 nibbles = 1 PSMCT32 pixel, but packed differently)

### PSMT4 swizzle is game-dependent

Multiple sources confirm that the 4-bit swizzle algorithm **varies between games**. Some games can be handled by converting to 8bpp first and using the standard PSMT8 deswizzle, but others (notably Racjin's Naruto: Uzumaki Chronicles) use a completely different 4bpp swizzle that only Noesis can handle correctly. This is a critical warning for our Busin 0 work -- the PSMT4 font atlas (R1272) may use a non-standard swizzle.

### Reference implementations
- [PS2 GS Memory Swizzle Visualizer (TellowKrinkle)](https://gist.github.com/TellowKrinkle/bd6c6e1735cf5e03110ec57ddeea43a9)
- [4-bit Texture Unswizzling Code (Fireboyd78)](https://gist.github.com/Fireboyd78/1546f5c86ebce52ce05e7837c697dc72)
- [C code to swizzle 4bpp PS2 textures (ResHax)](https://reshax.com/topic/696-c-code-to-swizzle-4bpp-ps2-textures/)
- [Texture Swizzling PDF (PS2Linux)](http://ps2linux.no-ip.info/playstation2-linux.com/download/ezswizzle/TextureSwizzling.pdf)

---

## 3. How PS2 Games Store Font Atlases

### Common pattern (used by most PS2 RPGs including Busin 0)

1. **Single large texture** containing all glyphs in a grid
2. **Indexed color** (PSMT4 = 16 colors, PSMT8 = 256 colors)
3. **Fixed cell size** (e.g., 12x12, 16x16, 24x24 pixels per glyph)
4. **CLUT/palette** appended after pixel data (typically 64 bytes for PSMT4, 1024 bytes for PSMT8)
5. **GS register header** (192 bytes) containing TEX0, TEX1, CLAMP parameters
6. Glyph lookup: `col = id % columns; row = id / columns; pixel_x = col * cell_w; pixel_y = row * cell_h`

### Busin 0 specifics (confirmed)

| Resource | Format | Size | Cell | Grid | Glyph Count |
|----------|--------|------|------|------|-------------|
| R1272 | PSMT4 (16-color) | 256x512 | 12x12 | 21x42 | 882 cells |
| R1189 | PSMT8 (256-color) | 512xN | varies | varies | Name entry font |
| R1188 | PSMT8 (256-color) | varies | varies | 17 sub-entries | **UI composite atlas** |

### Tales of Destiny 2 (reference case)

The Japanese font texture occupies **256x4400 pixels** -- a tall strip holding thousands of kanji glyphs, each 23x23. Rendered as a standard PS2 texture with no special tricks. This demonstrates that PS2 games routinely handle very large glyph atlases by making the texture tall.

---

## 4. TIM2 / TM2 Format (Standard PS2 Texture Container)

### Header structure

```
Offset  Size  Field
0x00    4     Signature ("TIM2" = 0x324D4954, or "CLT2")
0x04    1     Version (typically 4)
0x05    1     Alignment (0=16-byte, 1=128-byte)
0x06    2     Number of images (sub-textures)
0x08    8     Reserved (padding to 16 bytes)
```

### Per-image picture header (48 or 128 bytes)

```
Offset  Size  Field
0x00    4     Total image size (header + pixel data + CLUT)
0x04    4     Palette/CLUT data size
0x08    4     Image pixel data size
0x0C    2     Image header size (48 or 128)
0x0E    2     Number of palette colors
0x10    1     Pixel format (1=16-bit, 2=24-bit, 3=32-bit, 4=4-bit indexed, 5=8-bit indexed)
0x11    1     Number of mipmaps
0x12    1     Palette format type:
              0 = no palette
              1 = PAL_RGB16_CSM1 (16-bit, swizzled CLUT)
              3 = PAL_RGB32_CSM1 (32-bit, swizzled CLUT)
              129 = PAL_RGB16_CSM2 (16-bit, linear CLUT)
              131 = PAL_RGB32_CSM2 (32-bit, linear CLUT)
0x14    2     Image width
0x16    2     Image height
0x18    8     GS TEX0 register value
0x20    8     GS TEX1 register value
...
```

### Multi-image TIM2 files

TIM2 natively supports **multiple images packed into one file** via the "number of images" field at offset 0x06. Each image has its own picture header, pixel data, and CLUT. This is the standard PS2 mechanism for packing multiple sub-textures (e.g., UI elements, button states, icon sets) into a single resource.

### Relevance to R1188 (17 sub-entries)

R1188 in Busin 0 has 17 sub-entries, which is structurally similar to a multi-image TIM2. However, Busin 0 does NOT use standard TIM2 format -- it uses a proprietary Racjin container with GS register blocks as headers. The concept is the same: multiple indexed textures (likely button/UI bitmaps) packed into one resource, each with its own palette and dimensions.

### Multi-CLUT support

TIM2 also supports **multiple CLUTs per image** (alternate palettes). This is used for palette-swapping effects (e.g., highlighted vs. normal button states). The number of palettes = palette_data_size / (num_colors * color_byte_size).

---

## 5. Racjin-Specific Findings

### Archive formats

| Format | Used In | Structure |
|--------|---------|-----------|
| CFC.DIG | Naruto: Uzumaki Chronicles 1/2, Fullmetal Alchemist 3 | Compressed archive with at least 3 structural variations |
| CDDATA.DIG | Some Racjin PSP/Wii titles | Similar but distinct structure |
| PACKDATA.DIG | Busin 0: Wizardry Alternative Neo | **Not CFC.DIG-compatible** -- different format |

### Key differences from standard PS2 texture handling

1. **Non-standard 4bpp swizzle**: Racjin games (confirmed in Naruto: Uzumaki Chronicles) use a 4bpp swizzle algorithm that differs from the standard approach. The usual trick of converting 4bpp to 8bpp before deswizzling does NOT work. Only Noesis handles it correctly.

2. **Complex sub-texture packing**: Racjin textures are described as "a collection of pictures where individual pictures can be divided into many smaller pictures" -- this matches our R1188 structure exactly.

3. **Platform-dependent endianness**: Racjin archives use different endianness per platform (little-endian on PS2, big-endian on Wii/GC).

### Racjin game list (PS2)

- Naruto: Uzumaki Chronicles 1 & 2
- Fullmetal Alchemist 3: Kami o Tsugu Shoujo
- BUSIN 0: Wizardry Alternative Neo
- Wizardry: Tale of the Forsaken Land (BUSIN)

### Available tools for Racjin games

| Tool | Purpose | URL |
|------|---------|-----|
| Racjin-de-compression | Decompress CFC.DIG/CDDATA.DIG archives | [GitHub](https://github.com/Raw-man/Racjin-de-compression) |
| Noesis + Racjin plugin | Read/deswizzle Racjin textures | ZenHAX community |
| PS2ImageTool | GUI tool for raw PS2 binary image extraction | [GitHub](https://github.com/Surihix/PS2ImageTool) |
| Rainbow | TIM2/TM2 converter with multi-CLUT support | [GitHub](https://github.com/marco-calautti/Rainbow) |

### ZenHAX thread on Busin 0

A [ZenHAX thread](http://zenhax.com/viewtopic.php@t=13890.html) discusses PACKDATA.DIG extraction for Busin 0. Key finding: the CFC.DIG extraction script made for Naruto (a 2006 Racjin game) does NOT work on PACKDATA.DIG, confirming that Busin 0 uses a different archive format. The first files in PACKDATA.DIG do not appear to be compressed.

---

## 6. Implications for Busin 0 Translation

### What we already know works

- **PSMT8 deswizzle**: Fully implemented and byte-perfect in `tools/psmt8_deswizzle.py`
- **R1272 (PSMT4 font atlas)**: 256x512, 12x12 cells, 882 glyphs, deswizzle working
- **GS register parsing**: Header format understood (16-byte sub-header + 192-byte GS block)

### Remaining challenges for UI texture work

1. **R1188 (17 sub-entries)**: This composite UI atlas needs per-sub-entry analysis. Each sub-entry likely has its own GS register block specifying dimensions, PSM format, and CLUT. Need to parse each one individually.

2. **PSMT4 reswizzle for R1272**: If we modify font glyph bitmaps (e.g., replacing Japanese word tiles with English abbreviations), we need to reswizzle correctly. The PSMT4 swizzle may be non-standard given Racjin's track record.

3. **Palette constraints**: PSMT4 = 16 colors only. English text rendered into 12x12 cells with only 16 colors (likely mostly transparent + white/gray antialiasing) should be feasible but limiting for complex bitmap labels.

4. **Multi-state UI elements**: Menu buttons have multiple visual states (normal, highlighted, disabled). If these are stored as separate sub-textures in R1188, each state needs consistent modification.

### Recommended approach for UI bitmap replacement

1. **Parse R1188 sub-entry headers** to determine each sub-texture's dimensions, format, and palette
2. **Deswizzle each sub-texture** using the appropriate algorithm (PSMT4 or PSMT8)
3. **Identify which sub-textures contain translatable text** (button labels, navigation prompts)
4. **Render English replacements** at matching dimensions with matching palette constraints
5. **Reswizzle and reinsert** each modified sub-texture

---

## 7. Summary of PS2 Font/UI Texture Patterns

| Pattern | Description | Busin 0 Match? |
|---------|-------------|----------------|
| Single large atlas | All glyphs in one texture, grid layout | **Yes** (R1272) |
| Indexed color | PSMT4 (16 colors) or PSMT8 (256 colors) | **Yes** (both used) |
| GS register header | TEX0/TEX1/CLAMP packed before pixel data | **Yes** (192-byte block) |
| Swizzled storage | Data uploaded as PSMCT32, read as PSMT4/8 | **Yes** (confirmed) |
| Multi-image container | Multiple sub-textures in one resource | **Yes** (R1188 = 17 sub-entries) |
| Custom palette per sub-image | Each sub-texture has own CLUT | **Likely** (needs verification) |
| Fixed cell grid | Uniform glyph size, lookup by ID modulo | **Yes** (12x12, mod 21) |

---

## Sources

- [Palette shifting with the GS (Fobes)](https://fobes.dev/gs/2024/01/20/palette-shifting-with-the-gs.html)
- [TM2 format documentation (OpenKH)](https://openkh.dev/common/tm2.html)
- [TM2 TIM2 Image (RE Wiki)](https://rewiki.miraheze.org/wiki/TM2_TIM2_Image)
- [PS2 GS Memory Swizzle Visualizer (GitHub)](https://gist.github.com/TellowKrinkle/bd6c6e1735cf5e03110ec57ddeea43a9)
- [4-bit Texture Unswizzling (GitHub)](https://gist.github.com/Fireboyd78/1546f5c86ebce52ce05e7837c697dc72)
- [Texture Swizzling PDF (PS2Linux)](http://ps2linux.no-ip.info/playstation2-linux.com/download/ezswizzle/TextureSwizzling.pdf)
- [C code to swizzle 4bpp PS2 textures (ResHax)](https://reshax.com/topic/696-c-code-to-swizzle-4bpp-ps2-textures/)
- [Racjin decompression tools (GitHub)](https://github.com/Raw-man/Racjin-de-compression)
- [PS2 RAW Texture Format (ZenHAX)](http://zenhax.com/viewtopic.php@t=13414.html)
- [Busin 0 PACKDATA.DIG (ZenHAX)](http://zenhax.com/viewtopic.php@t=13890.html)
- [Rainbow texture converter (GitHub)](https://github.com/marco-calautti/Rainbow)
- [PS2ImageTool (GitHub)](https://github.com/Surihix/PS2ImageTool)
- [PS2 GS emulation (Maister)](https://themaister.net/blog/2024/07/03/playstation-2-gs-emulation-the-final-frontier-of-vulkan-compute-emulation/)
- [Raster RW Section (GTAMods Wiki)](https://gtamods.com/wiki/Raster_(RW_Section))
- [PS2tek internals documentation](https://psi-rockin.github.io/ps2tek/)
- [Font Rendering analysis (Lumina Tales)](https://luminatales.net/2021/06/05/a-glimpse-into-font-rendering/)
- [Naruto Uzumaki Chronicles 2 HD texture pack (GBAtemp)](https://gbatemp.net/threads/naruto-uzumaki-chronicles-2-slus-21594-ai-upscaled-texture-pack.664299/)
