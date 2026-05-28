# Late-Range Untranslated MSG Resources (1371-2654)

## Overview
- **Resources examined**: 65
- **Total "messages" found by FFFF-delimiter scan**: 32,390
- **Unique "unknown glyph IDs"**: 62,670

## CRITICAL FINDING: Most resources are NOT pure text

The vast majority of these resources contain **sprite/image/binary data** with
occasional embedded text fragments. The 0xFFFF delimiter that separates MSG
text messages also appears frequently in binary data, causing the decoder to
produce thousands of false-positive "messages" filled with pixel values
(glyph IDs > 1000 that are not in the glyph map).

Evidence:
- Resources 1701-1726 are all 17,600 bytes (type01) -- likely fixed-size
  sprite sheets or tilemap data with embedded text labels
- Resources 2101-2122 include types 19, 06, 01, 03 -- mixed binary formats
- The "messages" contain sequences like `[ABCD][EF12]` which are clearly
  pixel/palette data, not glyph indices
- Real MSG text glyph IDs max out around ~1300 in the glyph map

## Category Breakdown (by keyword heuristic)

| Category | Count | Resource IDs |
|----------|-------|-------------|
| DIALOGUE | 44 | 1438, 1564, 1610, 1623, 1701-1714, 1716-1722, 1726, 1891, 1909, 2101, 2104-2117, 2119, 2122 |
| DUNGEON | 8 | 1715, 2156, 2283, 2303, 2325, 2343, 2400, 2418 |
| EMPTY/NO_MSG | 1 | 2103 |
| EQUIPMENT | 4 | 1371, 1762, 2102, 2120 |
| SHOP/INN | 4 | 1704, 2121, 2137, 2401 |
| UI/SYSTEM | 4 | 1723, 1724, 1725, 2118 |

**Note**: These categories are based on finding Japanese keywords in whatever
text fragments exist, but the category labels are misleading since most
"messages" are binary data artifacts.

## Resources with Most "Messages"

| Resource | Type | Size | Messages | Likely Content |
|----------|------|------|----------|----------------|
| 2105 | type01 | - | 5077 | Binary data with embedded text |
| 2101 | type19 | - | 2651 | Binary data (type19 = non-MSG format) |
| 2121 | type01 | - | 1597 | Binary data with embedded text |
| 2303 | type04 | - | 983 | Map/dungeon data (type04) |
| 2108 | type03 | - | 919 | Binary data (type03) |
| 1701-1726 | type01 | 17,600 each | 179-690 each | Sprite/tilemap data |

## Text Fragments Found

Despite the binary noise, real text fragments are visible:

### Resource 1623 (type01)
- Contains katakana character names (e.g. partial item/monster names)
- MSG format header: `ブベ` pattern found (glyph IDs for UI frame)
- Keywords detected: kana for katakana names mixed with sprite data

### Resource 2303 (type04)
- Dungeon/map data format
- Contains structural markers like `[803F]` repeated (likely tile references)
- Has embedded text labels for dungeon elements: `ち`, `影`, `種`, `血`, `条`
- Contains sprite/tile loading instructions mixed with display text

### Resource 1371 (type01, EQUIPMENT)
- Item display screens with embedded sprite data
- Small amount of actual kanji: 鎧 (armor), 勲, 携, 宝, 組, etc.
- Mostly palette/pixel data for equipment display graphics

### Resources 1891, 1909 (type04)
- Type04 resources (different binary format)
- Minimal decodable text content

## Recommendations

1. **These resources should NOT be treated as standard MSG text resources.**
   They are display/rendering resources that combine sprite data with text
   overlay positions.

2. **A specialized decoder is needed** that can:
   - Identify the header structure (the `ブベ` + dimension bytes pattern)
   - Separate image data regions from text glyph regions
   - The text portions appear to be small labels/UI overlays within larger
     graphical display definitions

3. **True MSG text resources** in this range are likely already covered by
   other extraction passes. The resources listed here are primarily
   graphical/binary resources that happen to contain 0xFFFF delimiters.

4. **The 1701-1726 block** appears to be a set of related display screens
   (all exactly 17,600 bytes), possibly character/equipment/status screens
   or dungeon display data. They share the same header pattern.

## Files
- Full decoded dump: `data/untranslated_1371_2654.txt`
- Glyph map used: `data/msg_glyph_map.json`
- Decode script: `build/decode_late_range.txt`
