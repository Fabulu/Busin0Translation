# Recon 23: Multiple Font Atlas Search in PACKDATA.DIG

## Summary

**Resource 1272 is the ONLY font atlas in PACKDATA.DIG.** There is exactly ONE main font texture -- a PSMT4 (4-bit indexed) 256x512 atlas at resource index 1272 (65,792 bytes). The EXE's `FCD_event_font`, `FCD_battle_font`, and `FCD_event_frame` references are debug logging strings for resource lifecycle management, NOT pointers to separate font resources. The 13 font descriptor structs at 0x3C0700 all reference the SAME 256x512 atlas, treating it as two 256x256 pages via different GS VRAM page offsets.

## Evidence

### 1. Exhaustive PSMT4 Texture Census

A full scan of ALL type01 resources in PACKDATA.DIG (parsing the GS TEX0 register at offset 0x50) found exactly **519 PSMT4 (PSM=20) textures**. They break down as:

| Size Class | Dimensions | Count | Index Range | Purpose |
|------------|-----------|-------|-------------|---------|
| 736 bytes | 32x32 | ~15 | 2123, 2552, 2558, 2562-2569, 2586, 2638 | Tiny icons/cursors |
| 2,272 bytes | 64x64 | 3 | 1886, 2557, 2560 | Small icons |
| 4,832 bytes | 128x128 | 7 | 1901-1907 | UI element sprites |
| 8,416 bytes | 128x128 | ~30 | 927, 1481-1501, 1538-1547, 2559, 2579 | Sprite/icon sheets |
| 8,448 bytes | 128x128 | ~450 | 1372-1480, 1502-1537, 1548-1882, 1723-1882 | Character/monster portrait sprites |
| 33,808 bytes | 256x256 | 1 | 2124 | UI texture (menu background?) |
| 34,880 bytes | 256x256 | 1 | 2548 | UI texture |
| **65,792 bytes** | **256x512** | **1** | **1272** | **THE FONT ATLAS** |
| 527,360 bytes | 1024x1024 | 1 | 1188 | Large texture (world map?) |

**Resource 1272 is the only 256x512 PSMT4 texture in the entire archive.** It is unique.

### 2. Resource 1272 Context

Resource 1272 sits surrounded by PSMT8 (PSM=19, 8-bit indexed) textures in the 1250-1290 range. Every single neighbor (1250-1271 and 1273-1290) is PSMT8 at either 256x512 or 512x512. Resource 1272 is the lone PSMT4 outlier -- consistent with it being a special-purpose font atlas loaded into a dedicated GS VRAM page.

### 3. Font Descriptor Analysis Cross-Reference

The 13 font descriptor structs at EXE 0x3C0700 (per recon26) all specify `tex_dim = 256x256`. The 4 descriptor groups use `tex_param_b` values of 16, 32, 48, 64 -- these are GS VRAM page offsets that address different 256x256 regions of the same texture. The 256x512 atlas at resource 1272 is treated as **two stacked 256x256 halves** by the rendering system.

The 4 groups x 3 sub-variants (12 active descriptors) represent:
- 4 text rendering contexts (likely: menu, dialogue, battle, system)
- 3 glyph sub-sets per context (likely: ASCII/kana, kanji page 1, kanji page 2)

All groups reference the same underlying texture data. No descriptor points to a different resource.

### 4. FCD Debug Strings Are NOT Resource References

The EXE strings found at these offsets are debug/logging messages, not data pointers:

```
0x3F03B1: "BattleFontKill : FCD_battle_font\n"
0x3F34B8: "TextEventSystemDelete : FCD_event_font\n"
0x3F34E8: "TextEventSystemDelete : FCD_event_frame\n"
0x3F3670: "FCD_wallevent"
```

"FCD" appears to stand for "Free/Clear Data" or similar -- these are resource deallocation messages printed when the game unloads font-related data from memory. `FCD_event_font` and `FCD_battle_font` refer to different runtime instances of the same font atlas being loaded into GS VRAM for different game modes (events vs battles), not to separate font texture resources.

`FCD_event_frame` likely refers to the text box/frame border texture -- this is a PSMT8 texture, probably one of the 256x512 neighbors (e.g., resource 1271 or 1273).

### 5. MOJI Battle Effect Files Are Separate

The `IMAGE/BATTLE/EFFECT/MOJI.TMZ` and `MOJI1.TMZ` files (from the disc filesystem, not PACKDATA) contain tiny battle damage number sprites (0-9, "MISS", "HIT"), stored as TMZ-compressed TMX textures. These are NOT font atlases -- they are 3D billboard sprites rendered via MDT vertex data.

### 6. Pixel Data Confirms Font Content

Resource 1272's pixel data:
- Starts at file offset 256 (0x100)
- First 3 rows are all 0xFF (filled, likely the "full white" glyph area or border)
- 326 out of 512 rows contain glyph data (non-0xFF content)
- Pattern values like 0xAA, 0xCC, 0xFE confirm anti-aliased glyph rendering in 4-bit grayscale

### 7. Other PSMT4 Resources Are NOT Fonts

- **Resource 927** (128x128): Pixel data contains colorful image data (values like 0x58, 0x87, etc.), NOT monochrome glyph patterns. Surrounded by type02 data resources. Likely a UI icon sheet.
- **Resources 1371-1882** (128x128, ~500 resources): Sprite sheets with multi-color pixel data. These are character/monster portrait sprites based on their quantity and uniform size.
- **Resources 2124, 2548** (256x256): Found near type06/type03 resources. These are likely UI background textures or menu art.
- **Resource 1188** (1024x1024): Very large texture, possibly a world map or environment texture.

## Header Structure of Resource 1272

```
Offset  Hex                               Description
0x00    01 00 00 00 02 00 00 00           GIFtag NLOOP=1, NREG=2
0x10    04 80 00 00 00 00 00 10           BITBLTBUF params
0x20    05 00 00 00 ... 08 00 00 00       TRXREG/TRXDIR
0x30    00 80 00 00 04 00 40 00           Width/height params (128 qwords, 256 width)
0x50    00 00 41 61 06 00 00 20           TEX0: TBP0=0, TBW=4, PSM=20(PSMT4), TW=8(256), TH=9(512)
0x60    00 00 FF FF FF FF FF FF           Palette (all white)
0x70    00 01 00 02 ... 80 00 80 00       CLUT params, tex=256x128 (for CLUT addressing)
0x80    00 01 00 00 ... 3C 00 01 00       Additional GS state
0xC0    FF FF FF FF (x16 colors)          16-color PSMT4 palette: all 0xFFFF (opaque white in ABGR1555)
0x100   [pixel data starts]              65,536 bytes of 4-bit indexed pixel data
```

## Conclusions for Translation Project

1. **Only ONE font atlas needs to be modified** -- resource 1272 (65,792 bytes, PSMT4 256x512).

2. **The atlas is divided into two 256x256 halves** by the rendering engine. The top half and bottom half may contain different character sets (e.g., kana/ASCII vs kanji).

3. **No separate battle font exists** -- the same atlas is loaded for both event text and battle text. `FCD_battle_font` and `FCD_event_font` are runtime allocation names for the same texture data.

4. **The text frame/box** (`FCD_event_frame`) is a separate PSMT8 texture, probably a neighbor of 1272 (likely 1271 or 1273), but this is a UI decoration element, not a font.

5. **Battle damage numbers** are in MOJI.TMZ/MOJI1.TMZ on the disc filesystem, separate from the main font system. These need separate handling if translation requires them.

6. **The 16-color palette is trivial** -- all white (0xFFFF in ABGR1555). The 4-bit pixel values encode opacity/anti-aliasing levels (0=transparent to 15=opaque white). This makes font color changes easy -- the game applies color via the GS modulate blend mode using the RGBA values in the font descriptors (default 128,128,128,128 = neutral).

## Files Referenced

- Font atlas: `C:/Programmieren/wizardrytranslation/extracted/packdata_resources/1272_type01.bin`
- EXE: `C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78`
- Font descriptors in EXE: virtual address 0x3C0700, file offset 0x2C0780
- Manifest: `C:/Programmieren/wizardrytranslation/extracted/packdata_resources/manifest.json`
