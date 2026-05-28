# Font Atlas Page Boundary Diagnostic

**Date:** 2026-05-22
**Status:** CRITICAL BUG FOUND (not page boundary -- file assembly order)

---

## 1. Page Mapping Verification

The generator's page mapping formula (lines 92-100 of `generate_font_atlas.py`):

```python
page_col = x // 128       # 0 or 1
page_row = y // 128       # 0-3
page_idx = page_row * 2 + page_col  # 0-7
local_x = x % 128
local_y = y % 128
pixel_offset = page_idx * 128 * 128 + local_y * 128 + local_x
```

This **matches exactly** the verified algorithm from impl10-deswizzle-v2. The page mapping itself is correct.

### Glyph Position Verification

| Glyph | Char | Col | Row | Pixel (x,y) | Page | Status |
|-------|------|-----|-----|-------------|------|--------|
| 1     | space| 1   | 0   | (12, 0)     | 0    | Correct |
| 5     | !    | 5   | 0   | (60, 0)     | 0    | Correct |
| 21    | (row1)| 0  | 1   | (0, 12)     | 0    | Correct |
| 112   | A    | 7   | 5   | (84, 60)    | 0    | Correct |

All listed glyphs fall within page 0 (top-left 128x128 region). No page boundary issue for these specific slots.

### Page Boundary Locations

The 256x512 atlas has 8 pages of 128x128, arranged 2 wide x 4 tall:

- **Horizontal boundary** at x=128: affects glyph slots where `slot % 21 >= 11` (col 11+, x >= 132)
- **Vertical boundary** at y=128: affects glyph slots where `slot // 21 >= 11` (row 11+, y >= 132)
- First glyph crossing horizontal page boundary: slot 11 (col=11, x=132, page 1)
- First glyph crossing vertical page boundary: slot 231 (row=11, y=132, page 2)
- First glyph in page 3 (bottom-right quadrant): slot 242 (col=11, row=11)

For our English glyph table, the highest slot is 137 ('Z'), which is:
- col = 137 % 21 = 11, row = 137 // 21 = 6
- pixel = (132, 72)
- page_col = 132 // 128 = 1, page_row = 0
- **page_idx = 1** (top-right page)

So glyphs 'P' through 'Z' (slots 127-137) DO cross the horizontal page boundary into page 1. The page mapping math handles this correctly.

---

## 2. CRITICAL BUG: File Assembly Order is Wrong

The page mapping is fine, but the generator has a **fatal file assembly bug** that would corrupt all output.

### Original file layout (verified by deswizzle scripts)

```
Offset   Size     Content
0x000    192      Header (GIF tags + GS register setup)
0x0C0    64       Palette (16 RGBA32 entries)
0x100    65536    Pixel data (8 pages of 8192 bytes, linear 4bpp)
Total: 65792 bytes
```

Evidence: `deswizzle_font.pyw` lines 24-28:
```python
HEADER_SIZE = 192
PALETTE_SIZE = 64
PIXEL_OFFSET = HEADER_SIZE + PALETTE_SIZE  # = 256 = 0x100
palette_data = data[HEADER_SIZE:HEADER_SIZE + PALETTE_SIZE]
pixel_data = data[PIXEL_OFFSET:]
```

### Generator file assembly (generate_font_atlas.py lines 16-18, 110-111)

```python
header = orig[:192]          # bytes 0x00-0xBF -- CORRECT
palette = orig[-64:]         # bytes 65728-65791 -- WRONG (last 64 of pixel data, NOT palette)
# ...
output = header + bytes(pixel_data) + palette  # WRONG ORDER
```

### Bug 1: Wrong palette extraction

`orig[-64:]` takes the **last 64 bytes of the file**, which is the tail end of the pixel data section (bytes 0xFF00-0xFFFF of pixel data). The actual palette is at `orig[192:256]`.

### Bug 2: Wrong assembly order

The output is assembled as `header + pixel_data + palette`, putting:
- Pixel data at offset 0xC0 (where palette should be)
- "Palette" at offset 0x100C0 (past the end of where the game reads)

The correct assembly should be: `header + palette + pixel_data`

### Combined effect

The game would:
1. Read bytes 0xC0-0xFF as palette -- but those are the first 64 bytes of our pixel data, producing a garbage color table
2. Read bytes 0x100-0x100FF as pixel data -- but those are offset by 64 bytes, so every glyph is shifted and the last 64 bytes are the wrong "palette" data

This explains garbled rendering regardless of whether the page mapping is correct.

### Fix

```python
# Line 18: Extract palette from correct position
palette = orig[192:256]  # bytes 0xC0-0xFF

# Line 111: Correct assembly order
output = header + palette + bytes(pixel_data)
```

---

## 3. 4bpp Nibble Packing (Verified Correct)

The nibble packing logic (lines 102-108) is correct:
- Even pixel index -> low nibble
- Odd pixel index -> high nibble

This matches the "lo nibble first" convention confirmed in deswizzle-v2 findings.

---

## 4. Pixel Value Inversion (Verified Correct)

The value mapping (line 89):
```python
game_val = 15 - min(val * 15 // 255, 15)
```

Maps PIL 0 (black/background) to 15 (transparent) and PIL 255 (white/character) to 0 (opaque). This matches the game's convention documented in recon-font-atlas findings.

---

## 5. pixel_data Buffer Size

The generator allocates `pixel_data = bytearray(65536)` for 256x512 at 4bpp = 65536 bytes. This is correct.

However, the `pixel_offset` calculation:
```python
pixel_offset = page_idx * 128 * 128 + local_y * 128 + local_x
byte_offset = pixel_offset // 2
```

For `page_idx * 128 * 128`: this is in PIXELS, so max value = 7 * 16384 + 127 * 128 + 127 = 130943 pixels. `byte_offset = 130943 // 2 = 65471`. Buffer size is 65536. This fits.

---

## Summary

| Check | Result |
|-------|--------|
| Page mapping formula | CORRECT - matches verified deswizzle algorithm |
| Glyph slot positions | CORRECT - all user-listed slots verified |
| Page boundary for English glyphs | Slots 127-137 cross into page 1 - handled correctly |
| Nibble packing | CORRECT - lo nibble first |
| Value inversion | CORRECT - 0=opaque, 15=transparent |
| Palette extraction | **BUG** - reads last 64 bytes of file instead of bytes 192-255 |
| File assembly order | **BUG** - outputs header+pixels+palette instead of header+palette+pixels |

### Files Examined

- `tools/generate_font_atlas.py` - the font atlas generator (contains bugs)
- `data/english_glyph_table.json` - glyph slot assignments
- `runs/.../subagents/recon21-deswizzle/deswizzle_font.pyw` - reference file layout
- `runs/.../subagents/impl10-deswizzle-v2/FINDINGS.md` - verified format documentation
- `runs/.../subagents/recon29-glyph-grid/FINDINGS.md` - grid layout confirmation
- `runs/.../subagents/impl04-font/FINDINGS.md` - resource format documentation
