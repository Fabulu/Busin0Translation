# Infersplosion R1053 -- Findings

## Status: NO INFERENCES POSSIBLE

Resource 1053 (`1053_type03.bin`) is **not a text/dialogue resource**. It is a type03 binary resource containing control/rendering data.

## Evidence

### File structure
- File size: 35,200 bytes (17,600 uint16 values)
- Header ends at offset 1330 (contains an offset table with 2 entries)
- 90 FFFF terminators, 9 FFFE line breaks
- Stride: 48 bytes (type03 = 3 * 16)

### Value distribution after header (16,935 values)
| Category | Count | Percentage |
|---|---|---|
| Values in glyph range (2-1131) | 2,098 | 12.4% |
| Values above glyph range (<0xFFC0) | 9,540 | 56.3% |
| Zero values (mapped to space) | 4,921 | 29.1% |
| Control codes (>=0xFFC0) | 329 | 1.9% |

### Why this is NOT text
1. Only 12% of values fall within the known glyph ID range (0-1131). Normal text resources like r46 (type03, same format) have **84.8%** in range.
2. The 9,540 values above the glyph range (e.g., 40960, 65280, 64000, 44800) are NOT unknown kanji -- they are binary data (coordinates, pointers, rendering parameters).
3. "Text" fragments found are isolated single characters: katakana labels (ブ, ベ, ギ, ゾ, ヂ) and hiragana markers (ち, ぐ, べ), not readable sentences.
4. Values 8, 10, 11, 12, 14, 15 appear repeatedly in patterns consistent with coordinate/index data, not text glyphs.

### What this resource likely contains
Based on the structure (repeating patterns, coordinate-like values, single-character labels), this appears to be:
- UI layout / menu configuration data
- Graphics rendering control sequences
- Sprite/tile positioning data

The resource was classified as `msg_structure` + `has_sjis` by the automated classifier because it contains FFFF terminators and some glyph-range values, but these are coincidental structural similarities, not actual text content.

## Comparison with genuine type03 text resources

| Resource | In glyph range | Above range | Text quality |
|---|---|---|---|
| r46 (type03, genuine text) | 84.8% | 1.9% | High - readable dialogue |
| r1053 (type03, this resource) | 12.4% | 56.3% | None - binary data |

## Output
- `infersplosion_r1053.json`: Empty inference file (0 inferences)
- No kanji could be inferred from this resource

## Recommendation
The task description mentioned "1053_type02.bin" but no such file exists. Resource 1053 only exists as `1053_type03.bin`. Nearby type02 resources (1054-1059) also appear to contain structured/binary data rather than dialogue. For text inference work, focus on the msg resources in the lower ranges (34-49) or the classified msg resources in the 636+ range.
