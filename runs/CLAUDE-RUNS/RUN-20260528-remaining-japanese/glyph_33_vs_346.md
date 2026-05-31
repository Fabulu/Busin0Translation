# Glyph 33 vs 346: Byte-Level Analysis

## Summary

**Both positions have correct pixel data.** The byte layout is NOT the cause of position 346's rendering failure. The atlas data for both glyphs decodes correctly through the game's PSMCT32-to-PSMT4 VRAM pipeline. The root cause lies elsewhere.

## File Details

| Property | Value |
|---|---|
| Atlas file | `build/english_font_atlas.bin` (82,176 bytes) |
| Original R1272 | `extracted/packdata_resources/1272_type01.bin` (65,792 bytes) |
| Format | 192-byte GS header + pixel data (4bpp PSMT4) + 64-byte palette |
| Grid | 21 columns x 12px cells (12x12 each), COLS=21 |
| TEX0 PSM | PSMT4 (0x14), TBW=4 (256px), 256x512 (orig) / 256x1024 (atlas) |
| Upload method | PSMCT32 IMAGE transfer (confirmed by deswizzle tool) |

## Position 33 (ASCII 'A')

- Grid: row=1, col=12
- Pixel corner: (144, 12)
- Page: entirely in page 1 (x=144-155, y=12-23)
- Atlas byte offset: 9160 (pixel_offset=17936 in page layout)
- Non-transparent pixels: 22 (our rendered 'A' glyph)
- Original content: EMPTY (slot unused in Japanese game)
- **Result: Renders correctly**

## Position 346 (stat tile 'str')

- Grid: row=16, col=10
- Pixel corner: (120, 192)
- Pages: spans page 2 (x=120-127) and page 3 (x=128-131)
- Atlas byte offsets: 20732 (page 2 left) to 28864 (page 3 right)
- Gap at page boundary: 8132 bytes in file
- Non-transparent pixels: 35 (our rendered 'str' abbreviation tile)
- Original content: 22 non-transparent pixels (Japanese stat character)
- **Result: Does NOT render correctly**

## Byte-Level Verification

### PSMCT32 Deswizzle Test (simulates actual game VRAM)

Both positions decode perfectly when processed through the PSMCT32->PSMT4 pipeline (which is how the PS2 GS hardware reads the texture):

**Position 33 through VRAM pipeline:**
```
F F F F F F F F F F F F
F F F F F F F F F F F F
F F F F F F F F F F F F
F F F F F 4 7 F F F F F
F F F F A A 4 F F F F F
F F F F 5 E 6 C F F F F
F F F E 4 F B 7 F F F F
F F F 9 0 0 0 2 F F F F
F F F 4 D F F 5 B F F F
F F F F F F F F F F F F
F F F F F F F F F F F F
F F F F F F F F F F F F
```
Non-transparent: 22 -- correct 'A' shape

**Position 346 through VRAM pipeline:**
```
F F F F F F F F F F F F
F F F F F F F F F F F F
F F F F F F F F F F F F
F F F F F F 9 B F F F F
F 5 1 2 F 5 0 0 0 B E 5
F 4 A F F F 8 B F F E 2
F F B 3 E F 8 9 F F E 6
C 0 1 4 F F C 2 0 B E 6
F F F F F F F F F F F F
F F F F F F F F F F F F
F F F F F F F F F F F F
F F F F F F F F F F F F
```
Non-transparent: 35 -- correct 'str' tile shape

### Direct Read Tests (wrong format -- for reference)

Reading the atlas with PSMT4 block addressing (as if data were in raw PSMT4 VRAM format) produces garbage for BOTH positions -- confirming the data is in PSMCT32 upload format, not raw PSMT4.

## What IS the Problem?

The byte data is correct. The format is correct. The atlas is correctly injected into the patched resource. The following factors were checked and eliminated:

1. **Page boundary crossing** -- Position 346 spans pages 2 and 3, but the PSMCT32 pipeline handles this correctly.
2. **Byte offset mismatch** -- Both positions have non-zero data at the right offsets.
3. **Format/swizzle mismatch** -- VRAM simulation confirms correct decoding for both.
4. **Atlas injection** -- Patched raw resource exactly matches atlas binary.

### Remaining hypotheses (NOT byte-layout related):

1. **Palette issue** -- The atlas palette is ALL 0xFF (every color = white, A=255). The original palette has a proper grayscale gradient (index 0 = bright/opaque, index 15 = black/transparent). The atlas generator reads `orig[192:256]` for the palette, but that is the first 64 bytes of PIXEL DATA (all transparent = 0xFF), not the actual palette at `orig[-64:]`. However, if this were the issue, position 33 would also fail. The game likely loads the CLUT from a separate source (CBP=0 in TEX0 overlaps with texture data, suggesting external palette management).

2. **Stat tiles use a different rendering path** -- Glyph 346 is NOT referenced by any translation in `encoded_translations.json`. It is a menu/stat tile injected by `render_menu_tiles.py`. The game engine may render stat labels through a different code path that reads from a different texture or uses different UV mapping.

3. **The game does not reference glyph slot 346** -- The original Japanese glyph at position 346 is a kanji used for stat display. The game engine may look up stat labels by a hardcoded table that maps stats to specific glyph IDs. If the mapping differs from what `menu_labels.csv` assumes, the game would display a glyph from a different slot.

## Palette Bug (Confirmed)

In `tools/generate_font_atlas.py` line 19:
```python
palette = orig[192:256]  # last 64 bytes   <-- WRONG COMMENT, WRONG OFFSET
```

Should be:
```python
palette = orig[-64:]  # actual palette at end of file
```

The current code reads the first 64 bytes of pixel data (all 0xFF = transparent background) instead of the actual 64-byte palette at the end of the file. This produces an all-white, all-opaque palette. Whether the game uses this embedded palette or loads it externally is unclear, but fixing this bug is recommended regardless.
