# Non-MSG Text Scan Findings

## Key Conclusion

**The 1,657 SJIS-flagged non-MSG resources contain ZERO genuine Japanese text.
All SJIS byte-pattern matches are false positives from binary data (textures,
3D models, audio, etc.).**

BUSIN 0 (Wizardry Alternative Neo) stores ALL game-visible text -- including
item names, spell names, class names, monster names, UI labels, and dialogue --
using a 16-bit glyph-index encoding system in the 296 MSG resources. Raw
Shift-JIS text is NOT used for game content in PACKDATA resources. This was
also confirmed by recon24-name-tables.

## Scan Methodology

Multiple scan passes were performed with progressively stricter criteria:

| Pass | Criteria | Strings Found | Verdict |
|------|----------|---------------|---------|
| 1 | Any 1+ JP char, 15% ratio | 586,146 | Overwhelmed by binary noise |
| 2 | Hiragana required, skip 3D models | 43,095 | Still mostly texture data |
| 3 | High SJIS density filter, kana required | 14,351 | Repeating kanji from textures |
| 4 | Null-terminated, strict decode, score>=6 | 62 | All gibberish on inspection |
| 5 | 2+ consecutive hiragana OR 3+ consecutive katakana | 0 | Definitive result |

### Final methodology (Pass 5):
1. Extracted all null-terminated byte sequences from each resource
2. Strict Shift-JIS decode (errors="strict", reject any invalid byte pairs)
3. Quality scoring: hiragana 3pts, katakana 2pts, fullwidth 2pts, kanji 0.5pts
4. Required score >= 10
5. Rejected strings with control characters, high ASCII ratio, or high half-width katakana ratio
6. **Required 2+ consecutive hiragana OR 3+ consecutive katakana characters**
   - This is the definitive filter: binary data essentially never produces
     consecutive hiragana sequences, which are the hallmark of real Japanese text

## Summary Statistics

- Total SJIS-flagged non-MSG resources scanned: **1,657**
- Resources with genuine Japanese text: **0**
- Total genuine strings found: **0**
- SJIS flag false positive rate: **100.0%**

## Why So Many False Positives?

The Shift-JIS encoding uses lead bytes in the ranges 0x81-0x9F and 0xE0-0xEF,
with trail bytes 0x40-0x7E and 0x80-0xFC. These byte values are extremely common
in binary data:

- **Texture/image data**: Pixel values regularly fall in SJIS lead/trail ranges,
  producing "valid" kanji sequences. Resources of exactly 132,288 bytes (256x256
  textures) are the worst offenders.
- **3D model data**: Floating-point vertex coordinates frequently contain bytes
  in the 0x80-0xFC range.
- **Audio data**: Sample values span the full byte range.

The kanji range (0x889F-0x9FFC, 0xE040-0xEAA4) is particularly problematic
because it covers a huge byte space. However, hiragana (0x829F-0x82F1) occupies
a very narrow range, making consecutive hiragana nearly impossible from random data.

## Implications for Translation

1. **The 296 MSG resources contain ALL translatable text** in PACKDATA
2. **Non-MSG resources do not need text extraction or modification**
3. The SJIS classifier's `has_sjis` flag is unreliable for non-MSG resources
4. **Focus translation efforts entirely on the MSG glyph-index format**
5. The only raw SJIS text in the entire game is in the EXE file (debug strings,
   save slot labels) -- not in PACKDATA resources
