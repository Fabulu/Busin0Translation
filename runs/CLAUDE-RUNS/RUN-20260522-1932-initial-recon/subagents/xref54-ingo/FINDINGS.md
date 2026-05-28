# XRef54 Ingo - Glyph Mapping Cross-Reference

## Confirmed Mappings

| Glyph | Char | Confidence |
|-------|------|------------|
| 59 | イ | HIGH |
| 341 | ン | HIGH |
| 61 | ゴ | HIGH |
| 63 | 。 | HIGH |

## Method

Extracted screenshot from greentextgnome.p2s showing NPC Ingo intro.
Text: おっ、なんだい、新米さんかい？俺はインゴってんだ、よろしくな。
インゴ is GREEN (color-highlighted).
Searched 32MB EE RAM for FF01 ctrl code + 3 glyphs + FFF0 end code.
Found [FF01] 59 341 61 [FFF0] at RAM 0xE2D572 and 0xE2D5E2.

## Control Codes

- 0xFF01: Color text start (green for NPC names)
- 0xFFF0: Color text end
- 0xFFFF: Message group delimiter
- 0xFFFE: Line break within message

## Key Finding

Dialogue glyphs use DIFFERENT IDs than name-entry screen.
Name entry: イ=99, ン=97. Dialogue: イ=59, ン=341.
The two systems are completely separate glyph tables.
