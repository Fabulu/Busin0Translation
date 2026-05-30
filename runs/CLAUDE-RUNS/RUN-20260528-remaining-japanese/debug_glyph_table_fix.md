# Glyph Table / Font Atlas Consistency Check

Date: 2026-05-28

## Summary

**No fix needed.** The glyph table, font atlas generator, and encoder are all consistent. Both uppercase and lowercase English letters are rendered in the atlas at their correct positions.

## Details

### Glyph Table (data/english_glyph_table.json)

- Uppercase A-Z mapped to positions 33-58
- Lowercase a-z mapped to positions 65-90
- Full ASCII printable range (space through tilde) covered at positions 0-94

### Font Atlas Generator (tools/generate_font_atlas.py)

The generator iterates `slot_to_char` (reverse of glyph table) and renders each character at its assigned slot position. It renders:
- 'A' at slot 33, 'B' at slot 34, ... 'Z' at slot 58
- 'a' at slot 65, 'b' at slot 66, ... 'z' at slot 90

Both uppercase AND lowercase bitmaps are present in the atlas.

### Visual Confirmation (build/english_font_atlas_preview.png)

Inspected the preview image. Rows show:
- Row 3-4: `@ABCDEFGHI` (uppercase starting at position 33)
- Row 5-6: backtick then `abcdefghijklmnopqrs` (lowercase starting at position 65)
- Row 6: `tuvwxyz{|}~`

Both character sets are clearly rendered with distinct glyphs. Lowercase letters are NOT copies of uppercase -- they are properly rendered lowercase bitmaps.

### Encoder (tools/encode_english_text.py)

- Direct lookup: `table.get(char)` -- maps 'a' to 65, 'A' to 33
- Fallback: tries `char.lower()` then `char.upper()` if exact match fails
- This means lowercase input correctly maps to positions 65-90

### Conclusion

The premise of the task was "if positions 65-90 are Japanese kanji from the original atlas." This is NOT the case. The generate_font_atlas.py creates a fresh atlas from scratch (black background, then renders English characters into it). Positions 65-90 contain proper lowercase English letter bitmaps.

The glyph table encoding is correct. If remaining Japanese characters appear on screen, the issue is elsewhere (e.g., messages referencing glyph IDs outside the 0-94 English range, or menu/UI text using a different rendering path).
