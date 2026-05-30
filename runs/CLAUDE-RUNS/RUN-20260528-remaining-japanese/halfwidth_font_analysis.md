# Half-Width (6px) Font Atlas Analysis for R1272

**Date:** 2026-05-28
**Subject:** Can R1272 support 6px-wide glyphs? What changes are needed?

---

## 1. How the Renderer Draws Glyphs

### Does the renderer draw a fixed 12x12 quad per glyph?

**YES -- effectively.** The renderer does not have a per-glyph width parameter for draw calls. Here is the evidence:

1. **Glyph slot structure is fixed 12 bytes** (KEY FINDING 2 in analysis_text_renderer.md). The +12 at VA 0x303E70, 0x303EF4, and 0x305BF8 are **struct strides** through the glyph slot array, not pixel advance values. Each slot is:

   | Offset | Size | Purpose |
   |--------|------|---------|
   | +0 | 4 | resource handle / glyph data |
   | +4 | 2 | attribute / Y data |
   | +6 | 2 | X scroll position (0-128, clamped) |
   | +8 | 4 | additional render data |

2. **The centering calculation** at VA 0x305980-0x305994 computes total line width as `char_count * 24` screen pixels. This formula has no per-glyph lookup. Every glyph = 24 screen pixels wide (12 atlas texels at 2x upscale).

3. **No per-glyph width table** exists in the renderer code path. The glyph width/repeat table at EXE offset 0x3B3690 (~200 bytes of paired kanji IDs) is rendering metadata for specific kanji, not a general advance table, and is not referenced in the advance loop.

4. **The GS quad drawing** is handled by subroutines called from the render dispatch (VA 0x30CE90). The actual GS primitive submission (SPRITE or TRIANGLE_STRIP) uses UV coordinates derived from the glyph index (computed as `col = id % 21`, `row = id / 21`, yielding U = col*12, V = row*12 in atlas texel space). The quad width is implicitly 12 texels (one full cell), upscaled to 24 screen pixels.

### What happens with 6px advance but 12-texel draw width?

If the advance were changed to 6px (12 screen pixels) but the GS quad still draws 12 atlas texels wide:

- Glyph N would be drawn at screen position `base_x + N * 12`
- Glyph N+1 would be drawn at `base_x + (N+1) * 12`
- The 24-screen-pixel-wide quad of glyph N would **overlap** the first 12 screen pixels of glyph N+1

**This would cause visible overlap/corruption for any glyph that has pixels in the right half of its 12x12 cell.**

---

## 2. Current Atlas Layout (generate_font_atlas.py)

The script at `tools/generate_font_atlas.py` renders glyphs as follows:

- Atlas: 256x512 pixels, PSMT4 (4bpp, 16 grays)
- Grid: 21 columns x 42 rows, each cell 12x12 pixels
- Font: Consolas 10pt (or fallback)
- **Centering**: Each character is centered within its 12x12 cell using:
  ```python
  ox = x + max(0, (CELL_W - cw) // 2) - bbox[0]
  oy = y + max(0, (CELL_H - ch) // 2) - bbox[1]
  ```
- Menu tiles (glyph IDs 683-866): injected from `render_menu_tiles.py`, each tile is a pre-rendered 12x12 cell containing a whole word fragment

---

## 3. Feasibility Assessment

### 3a. Half-width (6px advance) -- NOT FEASIBLE without EXE patches

The renderer uses a fixed 12-texel quad width and fixed 24-screen-pixel spacing. Simply changing the atlas to left-align glyphs in 6px would NOT work because:

1. The GS quad still draws 12 texels wide, so right-half pixels from cell N would show through
2. There is no advance value to change in the atlas -- the advance is hardcoded in the EXE
3. Changing the EXE advance (the struct stride and centering formula) would break kanji (588 glyphs) and menu tiles (184 glyphs)

### 3b. What would be needed for true 6px advance

To make 6px advance work, THREE things must all change:

1. **Atlas**: Left-align ASCII glyphs in the left 6 pixels of each 12x12 cell (clear right 6 pixels)
2. **EXE Patch -- Quad Width**: Change the GS quad draw from 12 to 6 texels wide for ASCII glyphs. This requires finding the actual GS SPRITE/PRIM submission code and adding a conditional on glyph ID.
3. **EXE Patch -- Advance/Centering**: Change the centering formula from `count * 24` to a sum that uses 12 for ASCII and 24 for kanji. Also change the X-position computation for each glyph.

This is the "Option 1: EXE Code Injection" from halfwidth_impact_analysis.md. It requires:
- Finding free space in the EXE for injected code
- Patching at minimum 3 display-side advance sites
- Patching the centering calculation
- Patching or hooking the GS quad width
- Testing carefully against all text display contexts

**Difficulty: HIGH. Risk: MEDIUM (scroll animation timing may break).**

### 3c. Can readable lowercase a-z fit in 6 pixels wide?

**Barely, with a condensed/pixel font.** At native resolution:

- Consolas 10pt lowercase glyphs are typically 5-7 pixels wide
- At 6px cell width, lowercase letters like m, w would be very tight (5px body + 1px spacing)
- Uppercase M, W would likely exceed 6px at any readable size
- A dedicated pixel font (e.g., 5x7 bitmap font) would fit, but readability at PS2 resolution (480i/480p upscaled to TV) would be marginal

For comparison, the PS2 renders at 2x upscale (12 atlas texels = 24 screen pixels). At 6 atlas texels = 12 screen pixels, individual character strokes would be 1-2 screen pixels wide on a standard-def TV. This is at the limit of legibility.

---

## 4. The +12 Confusion: Struct Stride vs Pixel Advance

This is the central confusion in the existing analysis. Let me clarify:

| Location | Value | What It Is | Should It Change? |
|----------|-------|-----------|-------------------|
| VA 0x303E70 | +12 | Struct stride (bytes) through glyph slot array | NO -- it's the data structure size |
| VA 0x303EF4 | +12 | Struct stride through glyph slot init loop | NO -- same reason |
| VA 0x305BF8 | +12 | Struct stride through slot init in alternate path | NO -- same reason |
| VA 0x30CEFC+ | +12 | Resource table stride (12 bytes per resource entry) | NO -- would break resource loading |
| VA 0x305990 | *24 | Screen pixel width per glyph (centering calc) | YES -- this is the pixel advance |
| VA 0x303DF0/E0C | +/-4 | Scroll animation step | Maybe -- affects reveal speed |

The **pixel advance** is encoded in the centering formula at VA 0x305988-0x305990:
```
sll  $a0, $a1, 1     ; a0 = count * 2
addu $a0, $a0, $a1   ; a0 = count * 3
sll  $a0, $a0, 3     ; a0 = count * 24
```

To change the per-glyph screen width to 12px (= 6 atlas texels at 2x), this formula would need to become `count * 12`. But this is a global calculation -- it cannot distinguish ASCII from kanji without code injection.

The actual per-glyph X position computation happens elsewhere (likely in the resource loading/positioning functions called from the render dispatch). The glyph slot +6 field is a scroll counter (0 to 128, incremented by 4 per frame), not a direct screen X coordinate. The final screen X is computed as:

```
screen_x = base_x + centering_offset + glyph_order * glyph_width
```

Where `glyph_width` = 24 screen pixels for ALL glyphs.

---

## 5. Alternatives to 6px Half-Width

### Alternative A: 2-char packing (ALREADY IMPLEMENTED)

The project already packs 2 Latin characters into each 12x12 cell. Each cell shows ~6px + 6px of two adjacent characters. The renderer still advances 24 screen pixels per glyph slot, but each slot visually contains 2 characters, effectively achieving 12 screen pixels per Latin character.

**Status:** Working. Limitation: requires pre-paired character encoding at MSG build time.

### Alternative B: Proportional width via code injection

Build a 679-byte width table in free EXE space. Hook the advance code to look up width per glyph ID. ASCII gets 12 screen px, kanji gets 24, menu tiles get 24.

**Status:** Not implemented. Would give the best result but requires EXE hacking expertise.

### Alternative C: 8px advance (compromise)

Instead of 6px, use 8px cells (16 screen pixels). Would require:
- Atlas: render each ASCII glyph in left 8px of 12px cell
- EXE: same code injection as 6px, just different constants
- Readability: much better than 6px (uppercase M/W fit in 8px)
- Capacity: 224px / 16px = 14 characters per line (only ~78% of Japanese capacity)

**Not recommended** -- still requires full EXE patching, and capacity gain over current 2-char packing is negligible.

---

## 6. Conclusion

**Half-width (6px) glyphs are NOT feasible with atlas changes alone.** The renderer draws a fixed 12-texel (24 screen pixel) quad per glyph with no per-glyph width control. Achieving variable-width rendering requires EXE code injection at multiple sites.

The existing 2-char packing approach is the correct solution given the current constraints:
- No EXE patches needed
- Each 12x12 cell displays 2 Latin characters at ~6px each
- Effective capacity: ~36 visible characters per line (18 slots * 2 chars)
- The 32-slot parser limit allows up to 64 visible characters per line

If EXE patching becomes practical in the future, the recommended path is:
1. **Option B (proportional width table)** -- cleanest, most flexible
2. Place the 679-byte width table in free EXE space (e.g., after the data section)
3. Inject a glyph-width lookup at the 3 display-side advance sites
4. Modify the centering formula to sum per-glyph widths instead of `count * 24`

### Key Files
- `tools/generate_font_atlas.py` -- atlas generation (current 2-char packing approach)
- `runs/.../analysis_text_renderer.md` -- full renderer RE with patch targets
- `runs/.../halfwidth_impact_analysis.md` -- earlier analysis confirming global advance
