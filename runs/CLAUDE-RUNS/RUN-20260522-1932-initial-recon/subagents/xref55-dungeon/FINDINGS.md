# xref55-dungeon: Dungeon Screen Glyph Cross-Reference

## Summary

Successfully matched the dungeon screen text "特に変わったところはない" (Nothing unusual here) to **resource 49, message #0** in the MSG data.

## Matched Message

- **Resource**: 0049_type01.bin (resource index 49)
- **Message index**: 0 (first message in resource)
- **Glyph sequence**: `[1006, 133, 652, 155, 191, 127, 131, 121, 154, 137, 132, 113]`
- **Text**: 特に変わったところはない (12 characters)

## New Glyph Mappings Discovered (12 total)

| Glyph ID | Character | Type | Confidence |
|----------|-----------|------|------------|
| 113 | い | hiragana | HIGH |
| 121 | こ | hiragana | HIGH |
| 127 | た | hiragana | HIGH |
| 131 | と | hiragana | HIGH |
| 132 | な | hiragana | HIGH |
| 133 | に | hiragana | HIGH |
| 137 | は | hiragana | HIGH |
| 154 | ろ | hiragana | HIGH |
| 155 | わ | hiragana | HIGH |
| 191 | っ | hiragana (small) | HIGH |
| 652 | 変 | kanji | HIGH |
| 1006 | 特 | kanji | HIGH |

## IMPORTANT: Glyph ID Space Difference

The MSG resource glyph IDs are **completely different** from the name-entry screen glyph IDs in glyph_map_partial.json:

- Name-entry screen: い=87, こ=126/95
- MSG resources: い=113, こ=121

The name-entry screen and MSG resources use different font/glyph tables. The glyph_map_partial.json mappings (86=あ, 87=い, etc.) do NOT apply to MSG resources.

## Cross-Validation Evidence

1. **msg#27 res49**: Starts with `[652, 155, 191, 127, ...]` = "変わった..." - confirms 652=変, 155=わ, 191=っ, 127=た
2. **msg#102 res49**: Contains `[121, 121, ..., 1006, 133, ...]` = "ここ...特に..." - confirms 121=こ, 1006=特, 133=に
3. **msg#64 res49**: Ends with `[191, 127, 1]` = "った " - confirms っ+た pattern

## Additional Findings

- **Glyph 152** ends 46.7% of messages in resource 49 - very likely 。(Japanese period)
- **Glyph 113** (い) is the 5th most frequent glyph in MSG data (675 occurrences) - consistent with い being one of the most common hiragana
- **Resource 49** contains 122 messages, likely all dungeon exploration text (investigation results, trap descriptions, etc.)
- MSG glyph ID ranges: 0-85 = ASCII/Latin, ~86-200 = kana, >200 = kanji

## Corrections to Existing Data

The glyph_map_partial.json contains incorrect assignments at positions 95-96 and 126-129 for the name-entry context:
- It says 95=せ, 96=そ, 126=こ, 127=さ, 128=し, 129=す
- Based on gojuon ordering in the hiragana grid, it should be: 95=こ, 96=さ, 126=し, 127=す, 128=せ, 129=そ

However, this is IRRELEVANT to MSG resources which use a completely different glyph ID space.

## Output Files

- `C:/Programmieren/wizardrytranslation/data/xref_dungeon.json` - Full cross-reference data with all mappings and validation evidence
