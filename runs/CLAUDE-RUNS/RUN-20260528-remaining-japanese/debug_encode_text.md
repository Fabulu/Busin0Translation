# Debug: encode_text() Glyph ID Trace for R38 Stat Labels

## Summary: NO BUG FOUND in encode_text() or glyph table

The hypothesis that lowercase maps to "wrong positions where Japanese kanji bitmaps exist" is **incorrect**. The font atlas was fully rebuilt with English bitmaps at ALL 95 positions (0-94), including lowercase at positions 65-90. There are no Japanese kanji in the atlas.

---

## 1. Glyph Table (english_glyph_table.json)

Standard ASCII layout, 95 entries:

| Range     | Content              |
|-----------|----------------------|
| 0         | space                |
| 1-15      | ! " # $ % & ' ( ) * + , - . / |
| 16-25     | 0-9                  |
| 26-31     | : ; < = > ? (punctuation) |
| 32        | @                    |
| 33-58     | A-Z (uppercase)      |
| 59-64     | [ \ ] ^ _ `          |
| 65-90     | a-z (lowercase)      |
| 91-94     | { \| } ~             |

This is simply `glyph_id = ASCII_code - 32` (standard ASCII minus space offset).

## 2. Encoding "str" -- Trace

Both pipelines produce the same result:

- `'s'` -> table['s'] = **83**
- `'t'` -> table['t'] = **84**
- `'r'` -> table['r'] = **82**
- `' '` -> table[' '] = **0**
- `'/'` -> table['/'] = **15**

Full "str / " encoding: `[83, 84, 82, 0, 15, 0]`

## 3. Font Atlas Verification

The atlas (generate_font_atlas.py) renders English characters at ALL glyph positions:

```python
for slot, char in slot_to_char.items():
    col = slot % COLS   # COLS = 21
    row = slot // COLS
    # renders the character bitmap at this position
```

Visual inspection of `build/english_font_atlas_preview.png` confirms:
- Row 3 (slots ~42-62): `J K L M N O P Q R S T U V W X Y Z [ \ ]`
- Row 4 (slots ~63-83): `^ _ ` a b c d e f g h i j k l m n o p q r s`
- Row 5 (slots ~84-94): `t u v w x y z { | } ~`

Lowercase letters at positions 65-90 have correct English bitmaps. No Japanese kanji remain anywhere in the rebuilt atlas.

## 4. v2 Pipeline vs build_v9 Comparison

### v2 pipeline (encode_english_text.py)
```python
glyph = table.get(char)
if glyph is None:
    glyph = table.get(char.lower()) or table.get(char.upper())
if glyph is None:
    glyph = table.get("?", 31)
```
- Direct lookup first, then case-insensitive fallback.

### build_v9 enc()
```python
def enc(ch):
    if ch in table:
        return table[ch]
    if ch.lower() in table:
        return table[ch.lower()]
    return 31
```
- Direct lookup first, then lowercase fallback.

**Both produce identical results** for all ASCII characters since the table has both cases.

### R38 specifically
R38 is a type-02 resource, handled via build_v9's Step 4 (line 196-217), which uses `enc(ch)`. It does NOT go through the v2 pipeline's encode_text(). But the encoding is functionally identical since both use the same glyph table.

## 5. Conclusion

The encoding pipeline and glyph table are correct. If Japanese characters appear in R38 stat labels on screen, the cause is NOT in encode_text() or the glyph table mapping. Possible other causes:

1. **The font atlas binary is not being loaded by the game** -- perhaps the game uses a different font resource for certain UI elements (not R1272)
2. **R38 translations are not being applied** -- the translation chunks might be missing or filtered out
3. **A different rendering path** -- stat labels might use a hardcoded glyph range or a separate font texture entirely
4. **The atlas 4bpp encoding/swizzling is wrong for certain positions** -- the pixel data conversion might have issues at specific tile positions even though the preview PNG looks correct
