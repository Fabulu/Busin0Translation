# First Dialogue Cross-Reference -- Findings

## Critical Discovery: Name-Entry Glyph IDs Do NOT Match Dialogue Text

The "confirmed" glyph IDs from the name-entry screen (し=126, い=87, あ=86, え=89, く=93, か=91) are from a SEPARATE glyph encoding system. Searching all 296 MSG resources for the adjacent pair (し, い) = (126, 87) or (128, 87) returned **zero matches**. The name-entry screen and dialogue text use different glyph ID spaces.

The name-entry system uses base IDs 86-96 and 126-129 with stride-57 size variants (pages at +57, +114, etc.). Dialogue text uses a completely different sequential block starting at glyph ID 112.

## Dialogue Hiragana Mapping (Bigram-Verified)

Through bigram frequency analysis of dialogue resources 34-49, the following glyph-to-hiragana mappings were confirmed:

| Glyph ID | Character | Evidence |
|----------|-----------|----------|
| 112 | あ | Position 0 in display table; gojuuon offset from ま=142 |
| 113 | い | (130,113)=116 = てい; (132,113)=95 = ない |
| 117 | か | (117,31)=106 = か。; part of ますか pattern |
| 123 | し | (123,130)=94 = して |
| 124 | す | (142,124)=155 = ます (strongest bigram) |
| 127 | た | (191,127)=80 = った |
| 130 | て | (191,130)=153 = って; (123,130)=94 = して |
| 132 | な | (132,113)=95 = ない |
| 136 | の | Rank 2 frequency (665), consistent with の as most common particle |
| 142 | ま | (142,124)=155 = ます |
| 191 | っ | (191,130)=153 = って; (191,127)=80 = った |

## Full Hiragana Table (Extrapolated)

Glyphs 112-155 follow standard gojuuon order with ら=93 and り=94 inserted out-of-sequence (between よ=149 and る=150). This ordering was confirmed by the glyph display table in resource 37 sequence 17, which shows all 46 basic hiragana plus modified kana in a grid layout.

Glyphs 158-192 contain dakuten, handakuten, and small kana variants. Confirmed: 191 = っ (small tsu). Estimated: 168-172 = だ行, 183 = ゃ, 184 = ゅ, 185 = ょ.

## Target Text Search Results

Searched for the bigram なあ (132, 112) across all MSG resources. Found only 3 occurrences (resources 45 and 46), none matching the full target text pattern "なあ、教えてくれよ～。俺、早くあの事を言わなきゃ、ならないんだよ。"

Possible explanations:
1. The first dialogue may be in a non-MSG resource or cutscene data
2. The exact text may differ from what was transcribed from the screenshot
3. Inline control codes may disrupt the expected glyph sequence
4. The first game dialogue may be loaded from a different pack file

## Punctuation

- Glyph 31 = 。 (period) -- confirmed by (か,31)=106
- Glyph 63 = ？ (question mark) -- supported by (す,63)=76 and (い,63)=45
- Glyph 62 = speaker name delimiter -- appears at end of speaker names in dialogue

## Key Output Files

- `data/xref_firstdialogue.json` -- Full analysis with all mappings and evidence
- `data/glyph_map_partial.json` -- Original name-entry mappings (SEPARATE from dialogue)

## Resource 37 Display Table

Resource 37 sequence 17 contains a sequential glyph display grid that enumerates glyphs 112-192. This is critical evidence for the glyph atlas layout:
- Left column (5 per row): basic hiragana 112-149, then 93-94, then 150-157
- Right column (5 per row): modified kana 158-192
- Total: 48 left + 35 right = 83 kana characters
