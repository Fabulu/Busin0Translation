# PS2 Multi-Texture Resource Format Research

**Date**: 2026-05-28
**Subject**: How R1188 packs 17 sub-entries with GS register blocks into one file

---

## 1. PS2 GS Texture Upload Mechanism

### Register Sequence for Texture Upload

Uploading a texture from EE RAM to GS VRAM requires setting four GS registers via A+D (Address+Data) GIF packets:

1. **BITBLTBUF** (reg 0x50) - Destination buffer configuration:
   - DBP (bits 32-45): Destination Base Pointer = VRAM address / 256
   - DBW (bits 48-53): Destination Buffer Width = pixels / 64
   - DPSM (bits 56-61): Destination Pixel Storage Mode (e.g., PSMT4=0x14)
   - Destination buffer must be aligned on 256-byte boundary
   - Buffer width must be a multiple of 64 pixels

2. **TRXPOS** (reg 0x51) - Transfer position:
   - Source X/Y (for host-to-VRAM, typically 0,0)
   - Destination X/Y within the VRAM buffer

3. **TRXREG** (reg 0x52) - Transfer dimensions:
   - Width and height in pixels

4. **TRXDIR** (reg 0x53) - Transfer direction (initiates the transfer):
   - 0 = Host (EE) to Local (GS VRAM)
   - 1 = Local to Host
   - 2 = Local to Local (VRAM-to-VRAM copy)
   - 3 = Deactivate

After setting TRXDIR, the actual pixel data follows via IMAGE-mode GIF packets (writes to HWREG register).

### GIF Tag Modes

GIF tags support three data formats:

- **PACKED** (FLG=0): Each register value takes one full quadword (128 bits). NLOOP * NREGS quadwords total.
- **REGLIST** (FLG=1): Each register value is one doubleword (64 bits). Two register values per quadword.
- **IMAGE** (FLG=2): Raw pixel data for HWREG writes. NLOOP quadwords of pixel data. Each quadword = two HWREG writes.

### Multi-Texture Upload in One DMA Chain

Yes, a single DMA chain CAN upload multiple textures to different VRAM locations. The sequence is:

```
GIFtag (PACKED, A+D, NLOOP=4)
  BITBLTBUF -> configure destination 1
  TRXPOS    -> position 1
  TRXREG    -> dimensions 1
  TRXDIR    -> 0 (start transfer)
GIFtag (IMAGE, NLOOP=N1)
  [pixel data for texture 1]
GIFtag (PACKED, A+D, NLOOP=4)
  BITBLTBUF -> configure destination 2
  TRXPOS    -> position 2
  TRXREG    -> dimensions 2
  TRXDIR    -> 0 (start transfer)
GIFtag (IMAGE, NLOOP=N2)
  [pixel data for texture 2]
... repeat ...
```

Each BITBLTBUF/TRXPOS/TRXREG/TRXDIR block reconfigures the destination, then IMAGE data follows. The gsKit library (`gsTexture.c`) demonstrates this pattern -- it splits large textures into blocks of `GS_GIF_BLOCKSIZE` quadwords, each preceded by DMA tags and GIF headers.

---

## 2. Texture Rendering Configuration (Not Upload)

### TEX0 Register (reg 0x06 / 0x07)

TEX0 configures how the GS **reads** a texture from VRAM when rendering polygons/sprites:

- TBP0 (bits 0-13): Texture Base Pointer = VRAM address / 256
- TBW (bits 14-19): Texture Buffer Width = texels / 64
- PSM (bits 20-25): Pixel Storage Mode
- TW (bits 26-29): Texture Width = 2^TW
- TH (bits 30-33): Texture Height = 2^TH
- TCC (bit 34): Texture Color Component (0=RGB, 1=RGBA)
- TFX (bits 35-36): Texture Function (modulate/decal/highlight)
- CBP (bits 37-50): CLUT Base Pointer
- CPSM (bits 51-54): CLUT Pixel Storage Mode
- CSM (bit 55): CLUT Storage Mode
- CSA (bits 56-60): CLUT Start Address (for 4-bit textures, selects which 16-color sub-palette)
- CLD (bits 61-63): CLUT Load control (0=no load, 1=load, etc.)

### CLAMP Register (reg 0x08 / 0x09)

Controls texture coordinate wrapping per-axis:

- WMS/WMT: Wrap Mode (0=repeat, 1=clamp, 2=region_clamp, 3=region_repeat)
- MINU/MAXU/MINV/MAXV: Region boundaries for modes 2 and 3

**REGION_CLAMP is the key mechanism for sub-texture addressing within an atlas:**
When WMS=2 or WMT=2, texture coordinates are clamped to [MINU,MAXU] x [MINV,MAXV], effectively windowing a sub-region of a larger texture. This allows a single large texture upload but rendering different sub-rectangles as if they were separate textures.

### TEX1 Register (reg 0x14 / 0x15)

Controls texture filtering (bilinear, mipmapping, LOD).

### MIPTBP1 Register (reg 0x34 / 0x35)

Mipmap base pointers for levels 1-3.

---

## 3. How R1188's 17 Sub-Entries Work

### The Two Possible Architectures

**Architecture A: Multiple small texture uploads to different VRAM addresses**
Each sub-entry has its own BITBLTBUF pointing to a different VRAM region. The 524KB of pixel data is partitioned, and each sub-entry uploads its slice to a different VRAM base address. At render time, TEX0.TBP0 selects which sub-texture to use.

**Architecture B: Single large texture upload, multiple render states (MOST LIKELY for R1188)**
All 524KB uploads as ONE 1024x1024 PSMT4 texture to a single VRAM location. The 17 sub-entries are not separate uploads but rather **17 different rendering configurations** for the same texture. Each A+D block specifies a different combination of:
- CLAMP register values (different REGION_CLAMP windows into the atlas)
- TEX0 register values (different CLUT palettes via CSA field, different color modes)
- TEX1 values (different filtering per element)

### Why Architecture B Fits R1188

Evidence from the existing analysis:

1. **All 17 A+D blocks are described as "identical"** with the same TEX0 (TBP0=0, TBW=16, PSM=PSMT4, 1024x1024). If they were separate uploads, TBP0 would differ.

2. **The pixel data is a single contiguous 524,288-byte block** (exactly 1024x1024 PSMT4). There are no internal boundaries or per-sub-entry pixel regions in the data section.

3. **The sprite metadata table (0x560-0x6B3)** has 17 entries with IDs 1-16 + duplicate ID 9. Each entry has w=1024, h=1024 -- they all reference the full atlas, not sub-regions.

4. **The UV/Rect table (0x6B4-0x7C3)** has 8x2 values that are likely GS register field packing, not pixel rectangles. The header record says "atlas=512x256" which may describe the renderable viewport, not the full texture.

5. **The palette region (0x840-0xBFF)** contains multiple 16-color CLUT tables. These correspond to different color schemes for different UI states (normal, highlighted, selected, disabled).

### Likely Runtime Behavior

The game's rendering code for the name entry screen:

1. **Upload phase**: Sends R1188's pixel data (0xC00 onward) as a single 1024x1024 PSMT4 texture to GS VRAM.

2. **Per-element rendering**: For each UI element (tab, button, etc.):
   a. Select the appropriate A+D block from the 17 sub-entries (determines CLUT palette and render state)
   b. Set TEX0 with the chosen sub-entry's values (same TBP0, but potentially different CSA for palette selection)
   c. Set CLAMP with REGION_CLAMP to window the desired sub-region of the atlas
   d. Draw a SPRITE primitive with UV coordinates pointing to the element's position within the 1024x1024 atlas

3. **UV coordinates come from EXE code**: The glyph resolution function (VA 0x494050) looks up the BSS table at VA 0x4EBBEC, which maps glyph ID -> {texture page, U offset, V offset, width, height}. The EXE code hardcodes or computes where each tab label sits within the atlas.

---

## 4. Sub-Entry Purposes (Hypothesized)

Given 17 sub-entries for a UI screen with ~13 distinct elements:

| Sub-entries | Likely Purpose |
|-------------|---------------|
| 1-4 | Tab labels (katakana, hiragana, alphanumeric, symbols) -- normal state |
| 5-8 | Same tabs -- highlighted/selected state (different CLUT palette) |
| 9 | Shared state (duplicate ID 9 in sprite table) |
| 10-13 | Bottom buttons (confirm, male name, female name, delete, clear) |
| 14-16 | Title bar, instruction text, border/frame elements |
| 17 | Possibly a fallback or overlay state |

The different CLUT palettes in the 0x840-0xBFF region explain how the same pixel pattern renders in different colors for normal vs. selected states -- a common PS2 UI technique using PSMT4's 16-color indexed format with palette swapping.

---

## 5. Implications for Translation

### What This Means for Editing R1188

1. **The pixel data is one big atlas**: Edit the single 524,288-byte PSMT4 block at offset 0xC00. No need to worry about per-sub-entry pixel boundaries.

2. **Tab label positions are in EXE code**: The UV rectangles for each tab/button label are determined by the BSS lookup table populated at runtime. To find exact pixel positions, either:
   - Dump the texture from PCSX2 during name entry screen
   - Trace the EXE code that populates the BSS glyph table

3. **CLUT palette affects colors**: When editing, use the correct palette from 0x840-0xBFF. Different sub-entries may render the same pixels with different colors.

4. **The 17 A+D blocks can remain unchanged**: Since they configure rendering state (not pixel content), replacing the Japanese text pixels with English text in the atlas is sufficient. The register blocks will still correctly reference the same atlas regions.

5. **Potential gotcha -- REGION_CLAMP boundaries**: If sub-entries use REGION_CLAMP to window sub-regions, and the English text is wider than the Japanese, the clamp values in the A+D blocks may need adjustment. However, the existing analysis says CLAMP=0x05 (standard clamp), suggesting full-atlas addressing rather than region clamp.

---

## 6. Key Technical References

- [ps2tek - PS2 Internals Documentation](https://psi-rockin.github.io/ps2tek/) -- GIF tag format, GS registers
- [Maister's PS2 Graphics Introduction](https://themaister.net/blog/2025/03/20/graphics-programming-like-its-2000-an-esoteric-introduction-to-playstation-2-graphics-part-1/) -- Modern deep-dive into PS2 rendering
- [Maister's PS2 GS Emulation](https://themaister.net/blog/2024/07/03/playstation-2-gs-emulation-the-final-frontier-of-vulkan-compute-emulation/) -- CLUT handling, REGION_CLAMP
- [fobes.dev Palette Shifting](https://fobes.dev/gs/2024/01/20/palette-shifting-with-the-gs.html) -- BITBLTBUF/TRXPOS/TRXREG/TRXDIR DMA chain examples
- [gsKit gsTexture.c](https://github.com/ps2dev/gsKit/blob/master/ee/gs/src/gsTexture.c) -- Reference implementation of texture upload via DMA
- [PS2 Tutorials (ps2-home.com)](https://www.ps2-home.com/forum/viewtopic.php?t=337) -- TRXDIR values and transfer setup
- [PS2 Texture Mapping Tutorial](http://ps2-edu.tensioncore.com/texmap1/texmap1.html) -- TEX0 register setup
- [PCSX2 GIF Unit Source](https://github.com/PCSX2/pcsx2/blob/master/pcsx2/Gif_Unit.cpp) -- How emulator processes GIF packets
- [ps2sdk draw.c](https://github.com/ps2dev/ps2sdk/blob/master/ee/draw/src/draw.c) -- Low-level drawing primitives
- [PS2 Graphics Synthesizer Wiki](https://www.psdevwiki.com/ps2/Graphics_Synthesizer) -- Register reference
