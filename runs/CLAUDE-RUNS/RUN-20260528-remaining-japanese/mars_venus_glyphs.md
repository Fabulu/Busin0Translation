# Mars/Venus Gender Symbols

## Summary
Replaced M/F gender labels with Mars (U+2642) and Venus (U+2640) symbols for the character creation gender selection screen.

## Glyph ID Mapping
| Symbol | Unicode | Glyph ID | Original JP | Notes |
|--------|---------|----------|-------------|-------|
| Mars   | U+2642  | 518      | 男          | Primary male glyph |
| Venus  | U+2640  | 349      | 女          | Primary female glyph |
| Venus  | U+2640  | 418      | 女          | Alt female glyph (safety) |

## Files Modified

### data/english_glyph_table.json
Added two entries mapping Unicode symbols to glyph slots:
- `"\u2642": 518` (Mars -> glyph slot for 男)
- `"\u2640": 349` (Venus -> glyph slot for 女)

### data/translate_chunks/chunk_r38_fix.json
Changed MSG 25 (male) and MSG 26 (female):
- MSG 25: `"M / "` -> `"\u2642 / "`
- MSG 26: `"F / "` -> `"\u2640 / "`

### data/menu_labels.csv
Added 3 entries with `symbol` strategy:
- `gender_male`: glyph 518, renders Mars symbol
- `gender_female`: glyph 349, renders Venus symbol
- `gender_female2`: glyph 418, renders Venus symbol (alt position)

### tools/render_menu_tiles.py
Added `render_symbol_tile()` function that draws pixel-art Mars/Venus symbols using PIL drawing primitives (ellipses, lines). Added `symbol` strategy handling in `load_menu_tiles()`.

## Rendering Details
Both symbols are rendered as 12x12 pixel-art tiles:
- **Mars**: Circle at lower-left (ellipse 1,4 to 7,10), diagonal arrow shaft to upper-right, arrowhead lines. 26 foreground pixels.
- **Venus**: Circle at top (ellipse 2,1 to 9,7), vertical stem (2px wide), horizontal cross bar. 30 foreground pixels.

## Verification
Font atlas regenerated successfully: 199 menu tiles injected (3 new symbol tiles). All three glyph positions verified with correct foreground pixel counts. The `encode_text` pipeline correctly maps the Unicode symbols to glyph IDs 518 and 349.
