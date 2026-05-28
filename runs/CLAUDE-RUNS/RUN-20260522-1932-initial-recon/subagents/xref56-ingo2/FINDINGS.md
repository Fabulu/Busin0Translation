# Ingo Dialogue Glyph Cross-Reference (xref56-ingo2)

**Date**: 2026-05-22
**Save State**: `lotsoftextgnome.p2s`
**Output**: `data/xref_ingo2.json`

## Summary

Successfully identified and mapped 28 unique glyph IDs from Ingo's dialogue text by analyzing the EE RAM of the save state. The message was found at RAM address `0x015E5B86`.

## Critical Discovery: Two Separate Glyph Tables

**The dialogue rendering system uses COMPLETELY DIFFERENT glyph IDs than the name-entry screen.** The same numeric glyph ID maps to different characters in each context:

| Glyph ID | Name-Entry (partial map) | Dialogue (this analysis) |
|----------|-------------------------|--------------------------|
| 62 (0x3E) | V | 、 (comma) |
| 112 (0x70) | ソ (katakana) | あ (hiragana) |
| 114 (0x72) | チ (katakana) | う (hiragana) |
| 126 (0x7E) | こ (hiragana) | そ (hiragana) |
| 131 (0x83) | メ (katakana) | と (hiragana) |
| 136 (0x88) | ラ (katakana) | の (hiragana) |

This means the `glyph_map_partial.json` and `katakana_glyph_map.json` are for the name-entry font only, NOT for dialogue text.

## Glyph Range

Dialogue glyph IDs extend up to **0x0467 (1127)** and beyond, far exceeding the previous assumption of max 0x035A. This is why searching packdata resources with the old GLYPH_MAX filter yielded no dialogue matches.

## Confirmed Mappings (28 unique glyphs)

### Hiragana (14 glyphs)
| Glyph | Hex | Character | Romaji |
|-------|-----|-----------|--------|
| 112 | 0x0070 | あ | a |
| 114 | 0x0072 | う | u |
| 121 | 0x0079 | こ | ko |
| 126 | 0x007E | そ | so |
| 131 | 0x0083 | と | to |
| 132 | 0x0084 | な | na |
| 136 | 0x0088 | の | no |
| 141 | 0x008D | ほ | ho |
| 152 | 0x0098 | る | ru |
| 154 | 0x009A | ろ | ro |
| 156 | 0x009C | を | wo |
| 157 | 0x009D | ん | n |
| 171 | 0x00AB | で | de |

### Punctuation (1 glyph)
| Glyph | Hex | Character |
|-------|-----|-----------|
| 62 | 0x003E | 、 (comma) |

### Kanji (13 glyphs)
| Glyph | Hex | Character | Reading |
|-------|-----|-----------|---------|
| 376 | 0x0178 | 鉄 | tetsu |
| 408 | 0x0198 | 落 | raku |
| 412 | 0x019C | 物 | butsu/mono |
| 459 | 0x01CB | 不 | fu |
| 470 | 0x01D6 | 中 | naka/chuu |
| 475 | 0x01DB | 王 | ou |
| 519 | 0x0207 | 壁 | heki/kabe |
| 659 | 0x0293 | 城 | shiro/jou |
| 679 | 0x02A7 | 殿 | den/tono |
| 692 | 0x02B4 | 宝 | takara/hou |
| 870 | 0x0366 | 法 | hou |
| 1028 | 0x0404 | 難 | nan/muzukashii |
| 1121 | 0x0461 | 攻 | kou/semeru |
| 1127 | 0x0467 | 庁 | chou |

## Verification Patterns

Three structural patterns confirmed this message match:

1. **の particle (0x0088)**: Appears exactly 5 times at positions 4, 21, 25, 34, 36 -- matching の in 難攻不落**の**城...法王庁**の**宝物殿**の**...なん**の**そ**の**
2. **であろうと sequence**: Glyphs [0x00AB, 0x0070, 0x009A, 0x0072, 0x0083] appear at positions 6-10 and 27-31, distance 21
3. **、(comma) (0x003E)**: Appears at positions 11 and 37 (end of line 1 and line 3)

## Methodology

1. Extracted EE RAM (32MB) from PCSX2 save state
2. Parsed entire RAM as big-endian uint16 stream looking for FFFF-delimited messages
3. Searched for messages with 2 FFFE line breaks, ~38 glyphs, and a repeated 5-glyph subsequence
4. Found the message at 0x015E5B86 matching all structural constraints
5. Aligned the 38-glyph sequence against the 38-character known text
6. Verified mapping consistency through repeated characters (の x5, で x2, あ x2, etc.)

## Resource Location

The exact byte sequence was NOT found in extracted packdata resources, confirming that the type01/type02 structured binary resources encode text differently than raw glyph streams. The game engine decodes the resource format into this glyph stream in RAM at runtime.

## Implications

- The `glyph_map_partial.json` is ONLY valid for the name-entry screen font
- A completely separate mapping table is needed for dialogue text
- The dialogue font atlas has 1100+ glyph positions (kanji go up to at least 0x0467)
- More cross-references from other save states/screenshots are needed to build the complete dialogue glyph table
