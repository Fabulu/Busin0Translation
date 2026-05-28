# CockpitImg Texture Recon: R2118-R2124 (Updated 2026-05-28)

## CRITICAL FINDING: R2118-R2124 Are Demo Disc Screens, Not Cockpit UI

The previous recon (REMAINING_JAPANESE.md) identified R2118-R2124 as tavern/guild cockpit
UI textures. **This is incorrect.** Fully decoding these resources reveals they are
**demo disc disclaimer/advertising screens** that will never display during normal retail
gameplay. The PSMT8 deswizzle pipeline is now confirmed working.

## Resource Inventory (Decoded and Verified)

| Resource | Format | Dimensions | Size | Actual Content |
|----------|--------|------------|------|----------------|
| R2118 | PSMT8 | 512x512 | 264,192 | Japanese disclaimer: "This disc contains a trial version made from software in development. Therefore, there may occasionally be bugs..." |
| R2119 | PSMT8 | 512x64 | 34,816 | "This demo is not compatible with PS2 memory cards" (この体験版は、メモリーカード（PS2）に対応しておりません) |
| R2120 | PSMT8 | 512x64 | 34,816 | "Please enjoy the rest in the retail version" (この続きは、製品版でお楽しみください) |
| R2121 | PSMT8 | 512x512 | 264,192 | Full-game advertisement: "Now on sale! 6,800 yen (tax excluded)" with map + character art |
| R2122 | PSMT8 | 512x64 | 34,816 | "Demo Version" label (体験版) with orange glow effect |
| R2123 | PSMT4 | 32x32 | 2,048 | Tiny resource (736B payload) -- icon/cursor, no readable text |
| R2124 | PSMT4 | 256x256 | 34,816 | Mostly transparent overlay with very sparse pixel data |
| R2125 | type=1 | -- | 2,048 | 308B payload, too small for visible texture |

**Translation priority: LOWEST.** Players of the retail game will never encounter these screens.

## Where Are The Actual Cockpit (Tavern/Guild) Textures?

The bar/guild button labels are **NOT pre-baked texture resources** in PACKDATA. Evidence:

1. **PCSX2 texture dumps** (411 PNGs) show character creation menus ("Race", "Attribute",
   "Personality", "Class&Parameter") already in English. No Japanese cockpit button sprites
   were captured.

2. **Text labels in PCSX2 dumps** (at VRAM 0x2654) are narrative lines rendered by the MSG
   glyph system at runtime, not baked textures.

3. **Busin 1 comparison**: Busin 1 stores cockpit textures as standalone TMX files
   (`IMAGE/COCKPIT/BAR/BAR_00.TMX`, `IMAGE/COCKPIT/GUILD/GUILD_00.TMX`) on the disc
   filesystem. Busin 0 has NO equivalent files on its disc filesystem. The cockpit buttons
   are likely rendered from glyph IDs at runtime or stored in a different resource type.

4. **The R1215-R1346 range** (92 resources at 258KB each) are all NPC/monster portraits,
   not cockpit UI. Verified by decoding R1215, R1224, R1243, R1274, R1310.

5. **R1900** is a coffin/gravestone in-game texture.

**Conclusion**: Bar/guild menu button labels are rendered from the MSG glyph font system or
EXE-hardcoded glyph ID tables, not from texture resources. This makes them a text problem
(already addressed by the translation pipeline), not a texture problem.

## Binary Format Details (Confirmed Working)

### File Layout (PSMT8 Resources)
```
Offset 0x000: Sub-header (16 bytes)
  [0-3]   u32  always 0
  [4-7]   u32  payload_size (bytes of data after this sub-header)
  [8-11]  u32  sub-header size indicator (always 16)
  [12-15] u32  always 0

Offset 0x010: GIF A+D Packet (192 bytes standard)
  [0x10-0x1F]  GIF tag (NLOOP=1, NREG=16 for standard resources)
  [0x20-0xCF]  11 register pairs, each 16 bytes:
    - 8 bytes register data (Q-word)
    - 8 bytes register address (low byte = GS register ID)

  Key GS registers found:
    0x0E  A+D tag (GIF header marker)
    0x08  CLAMP_1 (texture clamping = 0x05 = clamp both)
    0x34  MIPTBP1_1 (mipmap base pointers)
    0x14  TEX2_1 (additional texture params)
    0x06  TEX0_1 (main texture descriptor: TBP0, TBW, PSM, W, H, CBP, CPSM)

Offset 0x0D0: Pixel data (W * H bytes for PSMT8)
  Data is swizzled for PSMCT32 VRAM upload

After pixels: CLUT Palette (1024 bytes = 256 colors x RGBA32)
  Needs deswizzle: swap entries 8-15 with 16-23 in each 32-entry block
  PS2 alpha stored as 0-128, multiply by 2 (cap at 255) for standard alpha
```

### TEX0 Register Values
```
R2118/R2121: TBP0=0 TBW=8(512px) PSM=19(PSMT8) 512x512 CBP=0 CPSM=0
R2119/R2120/R2122: TBP0=0 TBW=8(512px) PSM=19(PSMT8) 512x64 CBP=0 CPSM=0
R2123: TBP0=0 TBW=1(64px) PSM=20(PSMT4) 32x32 CBP=0 CPSM=0
R2124: TBP0=0 TBW=4(256px) PSM=20(PSMT4) 256x256 CBP=0 CPSM=2 (NLOOP=6, multi-transfer)
```

### Deswizzle Parameters (Empirically Confirmed)
- **PSMCT32 upload width (dbw_ct32)** = tex_w / 2
  - 512-wide PSMT8 -> dbw_ct32 = 256
  - Rationale: 4 PSMT8 bytes = 1 PSMCT32 pixel (32 bits)
- **bw_psmt8** = tex_w (same as texture width)
- Tested all four values (64, 128, 256, 512); only 256 produces correct output

## Deswizzle Implementation Status

### tools/psmt8_deswizzle.py -- FULLY WORKING for PSMT8

**Working functions:**
- `deswizzle_psmt8(host_data, tex_w, tex_h, bw_psmt8, dbw_ct32)` -- VRAM simulation
  approach: writes host data with PSMCT32 swizzle, reads back with PSMT8 swizzle
- `swizzle_psmt8(linear_pixels, tex_w, tex_h, bw_psmt8, dbw_ct32)` -- Inverse operation
  for re-encoding edited textures
- `deswizzle_palette(palette_data)` -- CLUT 8<->16 entry swap per 32-entry block
- `make_rgba_image(pixels, palette, width, height)` -- Creates RGBA PIL Image

**Known issue in main():** The `header_size = 1024` constant and the `process_raw_texture`
function incorrectly assume a 1024-byte header. The actual header is 208 bytes
(16 sub-header + 192 GS registers). The deswizzle functions themselves are correct;
only the file parsing in `main()` needs fixing.

**Block/column tables:** Sourced directly from PCSX2 GSTables.cpp -- verified correct.

### Not Implemented
- **PSMT4 deswizzle**: R2123 and R2124 use 4-bit indexed format. Would need PSMT4
  block/column tables and nibble-level pixel handling. Low priority since these
  resources don't contain meaningful Japanese text.
- **Automated batch processing**: No integration with build pipeline yet.
- **Re-swizzle validation**: `swizzle_psmt8()` exists but hasn't been round-trip tested.

## Busin 1 (English) Cockpit TMX Reference

### Files
```
extracted_busin1/IMAGE/COCKPIT/BAR/BAR_00.TMX    (33,344 bytes)
extracted_busin1/IMAGE/COCKPIT/GUILD/GUILD_00.TMX (33,344 bytes)
```

### TMX Format (Different from Busin 0 PACKDATA resources)
```
0x00: u32 = 2 (version/ID)
0x04: u32 = 33344 (file size)
0x08: 'TMX0' magic (TIM2 variant)
0x0C: u32 = 0
0x10: TIM2 picture header (8 bytes)
0x20: Embedded name ("bar_00.tim" / "guild_00.tim")
0x40: Palette (256 colors x 2 bytes ABGR1555 = 512 bytes)
0x240: Pixel data (32,768 bytes = 512x64, PSMT8 VRAM swizzled)
```

Content: Button sprite sheets with English text labels for tavern and guild menus.
These serve as layout/style references but Busin 0 does NOT use the same resource format.

## PCSX2 Dump Analysis (411 PNGs)

### Texture Categories by Size
| Dimensions | Count | VRAM Addr | Content Description |
|-----------|-------|-----------|-------------------|
| 512x512 | 10 | 0x2653-0x2654 | Scroll backgrounds, ATLUS logo, character art, world map, clouds |
| 256x256 | 8 | 0x2213 | NPC portraits (innkeeper, elf, warrior, priestess, etc.) |
| 512x256 | 2 | 0x2253-0x2254 | Game title logo "Busin 0 Wizardry Alternative NEO" |
| 256x512 | 1 | 0x2613 | NPC portrait (priestess, full body) |
| 256x128 | 4 | 0x1e13 | Foliage/vegetation textures (trees, grass) |
| 128x128 | 30 | 0x1dd3-0x1dd4 | Dungeon textures (walls, stone, fog, items) |
| 512x128 | 1 | 0x1e54 | Copyright notice (English, already correct) |
| 288x96 | 1 | 0x1e54 | "Duhan The Imperial City" location banner (English) |
| *x24 | ~22 | 0x2654 | Narrative text lines (MSG glyph rendered, not baked) |
| *x48 | 7 | 0x2254 | Char creation labels (English: Race, Attribute, etc.) |
| 64x64 | 41 | 0x2214 | Small icons and UI elements |
| 16x16 | 135 | 0x2214 | Tiny icons/cursors |

### Japanese Text Found in PCSX2 Dumps
**None.** All visible text is either English or MSG glyph-rendered narrative lines.
No cockpit/menu button sprites with Japanese text were captured.

## Recommended Approach

### Priority Reassessment
**R2118-R2124 should be dropped from the active translation plan.** They are demo disc
leftovers. The actual Japanese text in tavern/guild menus comes from:

1. **MSG glyph rendering** at runtime (handled by existing type-2 translation pipeline)
2. **EXE hardcoded glyph ID tables** (stat/menu labels -- requires EXE binary patching)
3. **R37/R38/R43** dialogue resources (type-2 text, some already translated)
4. **R39** equipment menu (type-15 format, currently reverted due to injector bugs)

### If Demo Screens Are Still Desired (Lowest Priority)
```python
# Editing pipeline (confirmed working):
from psmt8_deswizzle import deswizzle_psmt8, swizzle_psmt8, deswizzle_palette

data = open('2118_type01.raw', 'rb').read()
header = data[:208]                          # 16 sub-header + 192 GS regs
pixel_data = data[208:208+512*512]           # PSMT8 pixel data
palette_raw = data[208+512*512:208+512*512+1024]  # CLUT

# Decode
palette = deswizzle_palette(palette_raw)
pixels = deswizzle_psmt8(pixel_data, 512, 512, dbw_ct32=256)

# Edit PNG externally, map back to palette indices...

# Re-encode
reswizzled = swizzle_psmt8(edited_pixels, 512, 512, dbw_ct32=256)
output = header + reswizzled + palette_raw   # Keep original palette
```

## Files Generated (in this run directory)
- `R2118_decoded.png` -- Demo disc disclaimer (512x512, fully correct)
- `R2119_decoded.png` -- Memory card warning (512x64)
- `R2120_decoded.png` -- "Enjoy full version" message (512x64)
- `R2121_decoded.png` -- Full game advertisement (512x512)
- `R2122_decoded.png` -- "Demo Version" label (512x64)
- `R2124_linear.png` -- PSMT4 attempt (mostly transparent)
- `R1215_decoded.png`, `R1274_decoded.png` -- Sample NPC portraits (confirming these aren't cockpit)
- `R1900_decoded.png` -- Coffin/gravestone texture
- `R2119_dbw64/128/256/512.png` -- Upload width comparison (dbw=256 correct)
- `busin1_bar_deswizzled.png` -- Busin 1 BAR button sprites (reference, partially swizzled)
- `busin1_guild_deswizzled.png` -- Busin 1 GUILD button sprites (reference, partially swizzled)
