# Font Atlas Resource Search Results

Scanned 2,883 resources in PACKDATA.DIG for font-related textures.

## Key Findings

### Confirmed Font Atlas

**Resource 1272** (`1272_type01.bin`): 65,792 bytes
- Format: 256x512 PSMT4 (4 bits per pixel)
- Header: 192 bytes (GIFtag + A+D register setup)
- Pixel data: 65,536 bytes (256 * 512 / 2)
- CLUT: 64 bytes at file end (16 RGBA colors, grayscale ramp 172 -> 0, alpha=128)
- TEX0: TBP0=0, TBW=4, CLD=1, CPSM=0 (PSMCT32)
- Role: Main event/dialogue font (FCD_event_font). This is the ONLY PSMT4 resource with a grayscale descending CLUT suitable for font rendering.

### PSMT4 Resources > 30KB (Eliminated Candidates)

| Resource | Size | Dimensions | CLUT Type | Verdict |
|----------|------|------------|-----------|---------|
| 1188 | 527,360B | 1024x1024 | Colored (CPSM=2, PSMCT16) | NOT font - multi-segment sprite sheet |
| 1272 | 65,792B | 256x512 | Grayscale PSMCT32 | CONFIRMED font |
| 2124 | 33,808B | 256x256 | Colored (CPSM=2, PSMCT16) | NOT font - colored texture |
| 2548 | 34,880B | 256x256 | Colored (CPSM=2, PSMCT16) | NOT font - colored texture |

### Possible Second Font (PSMT8 Candidates)

Resource 2118 (`2118_type01.bin`): 263,360 bytes
- Format: 512x512 PSMT8, grayscale CLUT (217 -> 0 ramp)
- Accompanied by 2119 (512x64) and 2120 (512x64) - could be related metadata
- Located in a UI-related resource cluster (near type03/type181 entries)
- Strong candidate for FCD_battle_font or FCD_event_frame

Resource 2121 (`2121_type01.bin`): 263,360 bytes
- Format: 512x512 PSMT8, grayscale CLUT
- Accompanied by 2122 (512x64)
- Another candidate in the same cluster

### Neighboring Resources (1265-1285)

All neighbors of resource 1272 are PSMT8 textures (256x512 or 512x512). None are PSMT4. These are likely other game graphics (monster sprites, dungeon textures) stored adjacently, not additional font textures.

### Font Descriptors in EXE

At EXE offset 0x3C0700, there are 12 font size/style descriptors with 28-byte stride:
- Each record: `02 00 WW 00 XX 00 YY 00 00 00 00 00 80 80 80 80 00 01 00 01 00 00 00 00 ZZ ZZ ZZ ZZ`
- These control font rendering parameters (size, spacing, position), NOT resource indices
- 4 groups of 3 sizes each (small/medium/large at different Y positions)
- 13th entry is a terminator (FF FF)

### FCD_ Names in EXE

Font-related:
- `FCD_event_font` (0x3F34C8) - dialogue/event text font
- `FCD_battle_font` (0x3F03C1) - battle message font
- `FCD_event_frame` (0x3F34F8) - text box frame graphics

Other FCD resources:
- `FCD_battle_common_effect`, `FCD_battle_weapon`, `FCD_battle_weapon_add`
- `FCD_battle_result`, `FCD_wallevent`, `FCD_haikai`
- `FCD_effect_mnist`, `FCD_game_common_effect`, `FCD_death`, `FCD_notice_data`

### Glyph Width Tables

No standalone glyph width table resources found in PACKDATA.
No variable-width glyph tables found in the EXE (searched for byte sequences of 256-1716 values in range 4-24).
The font appears to use fixed-width rendering or computes widths at runtime.

### CLUT (Palette) Details for Resource 1272

16-color grayscale ramp (brightest to transparent):
```
Color  0: R=172 G=172 B=172 A=128  (lightest, for glyph body)
Color  1: R=155 G=155 B=155 A=128
Color  2: R=140 G=140 B=140 A=128
...
Color 13: R= 17 G= 17 B= 17 A=128
Color 14: R=  8 G=  8 B=  8 A=128
Color 15: R=  0 G=  0 B=  0 A=  0  (transparent background)
```

### Header Signature for Resource 1272

```
00: 01 00 00 00 02 00 00 00  GIFtag: NLOOP=1, NREG=2
08: 00 00 00 00 00 00 00 00
10: 04 80 00 00 00 00 00 10  GIFtag: EOP, A+D mode
18: 0e 00 00 00 00 00 00 00  NREG=0x0E (A+D register)
20: 05 00 00 00 00 00 00 00  BITBLTBUF register data
28: 08 00 00 00 00 00 00 00
30: 00 80 00 00 04 00 40 00  TRXPOS register
38: 34 00 00 00 00 00 00 00  TRXREG register (0x34)
40: 00 00 00 00 00 00 00 00
48: 14 00 00 00 00 00 00 00  TRXDIR register (0x14)
50: 00 00 41 61 06 00 00 20  TEX0 register
58: 06 00 00 00 00 00 00 00  TEX0 register address (0x06)
60: 00 00 FF FF FF FF FF FF  CLAMP register
68: 01 00 01 01 00 00 00 00  CLAMP register address (0x08)
70: 00 01 00 02 00 00 00 00  (additional GS state)
78: 4C 00 00 00 80 00 80 00  (image transfer params)
```

## Summary

**Resource 1272 is the ONLY confirmed font atlas in PACKDATA.DIG.** It is a 256x512 PSMT4 texture with a 16-level grayscale anti-aliased palette, containing Japanese glyphs for event/dialogue text.

The game references both `FCD_event_font` and `FCD_battle_font` in its EXE, but these may share the same texture resource (resource 1272) with different rendering parameters from the font descriptors at 0x3C0700. Alternatively, `FCD_battle_font` could use one of the PSMT8 grayscale textures (2118 or 2121) in the UI resource cluster.

`FCD_event_frame` is a separate non-font resource containing text box border/frame graphics.
