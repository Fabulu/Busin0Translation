# MSG Frequency Analysis Findings

## Overview

- **Resources classified as MSG**: 296
- **Valid MSG resources**: 47
- **Skipped (non-MSG binary data)**: 249
- **Total messages**: 22872
- **Total glyph tokens**: 111749
- **Unique glyph indices**: 836
- **Glyph index range**: 0x0000 - 0x035A

## Control Codes

- 0xFFFF (message delimiter): 378386
- 0xFFFE (line break): 5950
- 0xFFFD (): 515
- 0xFFFC (): 442
- 0xFFED (): 389
- 0xFFEF (): 367
- 0xFFF0 (): 349
- 0xFFFB (): 273
- 0xFFF3 (): 210
- 0xFFF2 (): 196

## Speaker Tags

- Messages starting with 0x011E 0x0247: 0 (0.0% of all messages)

## Message Statistics

- Average length: 7.9 tokens
- Median length: 1 tokens
- Longest: 512 tokens (resource 1285)
- Shortest: 1 tokens (resource 2816)

## Top 20 Most Frequent Glyphs

| Rank | Index | Hex | Count | % |
|------|-------|-----|-------|---|
| 1 | 0 | 0x0000 | 74367 | 66.55% |
| 2 | 1 | 0x0001 | 1988 | 1.78% |
| 3 | 255 | 0x00FF | 1075 | 0.96% |
| 4 | 3 | 0x0003 | 901 | 0.81% |
| 5 | 113 | 0x0071 | 675 | 0.60% |
| 6 | 136 | 0x0088 | 665 | 0.60% |
| 7 | 158 | 0x009E | 493 | 0.44% |
| 8 | 152 | 0x0098 | 491 | 0.44% |
| 9 | 93 | 0x005D | 489 | 0.44% |
| 10 | 130 | 0x0082 | 480 | 0.43% |
| 11 | 123 | 0x007B | 451 | 0.40% |
| 12 | 132 | 0x0084 | 444 | 0.40% |
| 13 | 63 | 0x003F | 430 | 0.38% |
| 14 | 156 | 0x009C | 423 | 0.38% |
| 15 | 62 | 0x003E | 421 | 0.38% |
| 16 | 2 | 0x0002 | 415 | 0.37% |
| 17 | 142 | 0x008E | 411 | 0.37% |
| 18 | 127 | 0x007F | 405 | 0.36% |
| 19 | 117 | 0x0075 | 402 | 0.36% |
| 20 | 133 | 0x0085 | 371 | 0.33% |

## Glyph Block Density (64-glyph chunks)

- 0x0000-0x003F: 83898 total, 64 unique
- 0x0040-0x007F: 6981 total, 64 unique
- 0x0080-0x00BF: 8556 total, 64 unique
- 0x00C0-0x00FF: 4534 total, 64 unique
- 0x0100-0x013F: 2134 total, 64 unique
- 0x0140-0x017F: 1011 total, 63 unique
- 0x0180-0x01BF: 437 total, 59 unique
- 0x01C0-0x01FF: 551 total, 55 unique
- 0x0200-0x023F: 966 total, 64 unique
- 0x0240-0x027F: 783 total, 63 unique
- 0x0280-0x02BF: 543 total, 63 unique
- 0x02C0-0x02FF: 633 total, 64 unique
- 0x0300-0x033F: 496 total, 60 unique
- 0x0340-0x037F: 226 total, 25 unique

## Key Observations

1. **Only 47 of 296 classified MSG resources pass validation** -- the majority (249) contain non-text binary data that happens to include FFFF/FFFE patterns. The original classifier was too aggressive.
2. **Glyph indices map to a custom font atlas**; range 0x0000-0x035A (~858 possible tiles), of which 836 are actually used.
3. **Glyph 0x0000 dominates at 66.55%** -- almost certainly padding/null/space, not a printable character. Excluding it, the effective corpus is ~37,382 printable glyph tokens.
4. **Median message length of 1 token** suggests many resources use FFFF-delimited lookup tables (e.g., item names, menu strings) rather than multi-sentence dialogue.
5. **No speaker tags (011E 0247) found** in BUSIN 0 -- the dialogue format differs from BUSIN 1 (Tale of the Forsaken Land). BUSIN 0 may use different header patterns for speaker attribution.
6. **378,386 FFFF delimiters but only 22,872 messages** -- vast majority of FFFF words are consecutive (acting as padding/terminators), not actual message boundaries.
7. **Control code diversity is high** -- beyond the known FFFE/FFD2/FFD3, many codes in the 0xFFC0-0xFFFF range appear, suggesting a richer control vocabulary in BUSIN 0 than in BUSIN 1.
8. **Glyph density is fairly uniform** across the 0x0040-0x013F range (all 16-glyph blocks have all 16 slots populated), suggesting a systematically populated font atlas: likely hiragana, katakana, then kanji in order.
9. **Top non-zero glyphs** (0x0001, 0x00FF, 0x0003, 0x0071, 0x0088) should be cross-referenced with font atlas renders to identify the actual characters and confirm Japanese frequency mapping.

## Output Files

- `dumps/msg_frequency_analysis.txt` - Full analysis with all statistics
- `dumps/glyph_frequency.json` - Top 200 glyph frequencies as structured JSON