# Recon 40: Katakana Glyph Grid Alignment

**Date:** 2026-05-22
**Save State:** `Nameentrystate.p2s` (katakana tab active)
**EXE:** `extracted/SLPM_653.78`

---

## Critical Finding: The Table at 0x4C9AB0 is NOT a Single 100-Group Table

The initial hypothesis that RAM 0x004C9AB0 contains a contiguous 100-group table (10x10 grid, 6 uint16 per group) is **incorrect**. The actual structure is:

**Multiple small sub-tables** scattered across RAM 0x4C99B8-0x4C9CD4, each referenced by separate `lui/addiu` instruction pairs in the name entry code at EXE region 0x2F5410-0x2F6554.

---

## Table Structure

### Character Entry Format
Each character uses a 12-byte entry: **6 consecutive uint16 LE values** representing the same glyph rendered at 6 different font sizes. The stride between sizes is **57** (each size page holds 57 glyphs).

Example for glyph "ア":
```
Size 0: glyph  98
Size 1: glyph 155  (98 + 57)
Size 2: glyph 212  (155 + 57)
Size 3: glyph 269  (212 + 57)
Size 4: glyph 326  (269 + 57)
Size 5: glyph 383  (326 + 57)
```

### Sub-Table Layout

The code loads these sub-tables in pairs (LEFT + RIGHT of visual grid rows):

| Sub-Table Addr | Count | Base Glyphs | Characters |
|----------------|-------|-------------|------------|
| 0x4C9AB0 | 7 | 98-104 | ア イ ウ エ オ カ キ |
| 0x4C9B10 | 7 | 105-111 | ク ケ コ サ シ ス セ |
| 0x4C9B70 | 7 | 112-118 | ソ タ チ ツ テ ト ナ |
| 0x4C9BD0 | 7 | 119-125 | ニ ヌ ネ ノ ハ ヒ フ |
| 0x4C9A50 | 3 | 126-128 | ヘ ホ マ |
| 0x4C9A78 | 1 | 129 | ミ |
| 0x4C9C30 | 6 | 130-135 | ム メ モ ヤ ユ ヨ |
| 0x4C9C80 | 6 | 136-139,134*,141 | ラ リ ル レ ロ* ワ |
| 0x4C9CC8 | 1 | 142 | ヲ |

**Total: 45 characters** covering basic katakana in gojuon order (ア through ヲ).

### Code References (EXE disassembly)

Pairs loaded together by the name entry rendering code:
- `0x2F5C48`: Pair (0x4C9AB0, 0x4C9B10) -- 7+7 chars
- `0x2F5CE8`: Pair (0x4C9B70, 0x4C9BD0) -- 7+7 chars
- `0x2F5DB4`: 0x4C9A50 (3 chars) + `0x2F5EF0`: 0x4C9A78 (1 char)
- `0x2F5F70`: Pair (0x4C9C30, 0x4C9C80) -- 6+6 chars (referenced 7 times)
- `0x2F6554`: 0x4C9CC8 -- 1 char

---

## Key Anomalies

### 1. Glyph 134 Shared Between ユ and ロ

Entry at 0x4C9C60 (ユ): `(134, 191, 248, 305, 362, 419)` -- strict stride 57
Entry at 0x4C9CB0 (ロ): `(134, 191, 254, 305, 362, 425)` -- NON-strict stride

These two characters share glyph IDs at sizes 0, 1, 3, 4 (glyphs 134, 191, 305, 362) but differ at sizes 2 and 5:
- Size 2: ユ=248, ロ=254
- Size 5: ユ=419, ロ=425

This is likely intentional -- at small font sizes, ユ and ロ may share the same bitmap.

### 2. Missing ン (Katakana N)

The character ン is NOT present in any of the stride-57 sub-tables. The glyph ID 97 (which would be the expected position between 96 and 98) does not appear anywhere in the table region. ン may be:
- Stored in a completely separate mechanism
- Part of the large table at 0x4C9D20 (which contains glyph IDs in the 6400-29185 range)
- Handled as a special character by the name entry code

### 3. Gap at Glyph IDs 126-129

Glyphs 126-129 (ヘ ホ マ ミ) are stored at 0x4C9A50-0x4C9A78, separate from the main sequential blocks. This is likely due to the glyph IDs crossing a page boundary (the ASCII range uses glyphs 1-93, so 94-97 may be reserved/special).

### 4. Gap at Glyph ID 140

Expected between レ(139) and ワ(141), glyph 140 is unused. ロ uses the non-strict entry at base 134 instead.

---

## Pre-Katakana Entries (Glyphs 86-96)

11 additional stride-57 entries exist at 0x4C99B8-0x4C9A98 with base glyphs 86-96. These are referenced by separate code at 0x2F5410-0x2F57EC and likely represent characters on a DIFFERENT tab of the name entry screen (possibly symbols or special characters). The ASCII glyph table (recon20) maps glyphs 1-93 to ASCII, so glyphs 86-96 overlap with the ASCII range ('f' through 's').

---

## Other Tabs in the Table Region

Beyond the stride-57 katakana entries, additional data structures exist:

| Address | Content | Glyph Range |
|---------|---------|-------------|
| 0x4C9CE0 | 13 single-value entries (value, 0 pairs) | 25-114 |
| 0x4C9D20 | 161 non-zero values in 2288 bytes | 6400-29185 |

The 0x4C9CE0 entries (glyphs 25-36, 114) likely correspond to alphanumeric characters on the name entry screen. The 0x4C9D20 entries use glyph IDs on different atlas pages (6400 = page 25, 6656 = page 26, etc.) and likely correspond to hiragana, symbols, or kanji used in the name entry system.

---

## Complete Glyph Mapping (Size 0 / Base Glyphs)

```
Glyph  98 = ア    Glyph 112 = ソ    Glyph 126 = ヘ    Glyph 136 = ラ
Glyph  99 = イ    Glyph 113 = タ    Glyph 127 = ホ    Glyph 137 = リ
Glyph 100 = ウ    Glyph 114 = チ    Glyph 128 = マ    Glyph 138 = ル
Glyph 101 = エ    Glyph 115 = ツ    Glyph 129 = ミ    Glyph 139 = レ
Glyph 102 = オ    Glyph 116 = テ    Glyph 130 = ム    Glyph 134 = ロ*
Glyph 103 = カ    Glyph 117 = ト    Glyph 131 = メ    Glyph 141 = ワ
Glyph 104 = キ    Glyph 118 = ナ    Glyph 132 = モ    Glyph 142 = ヲ
Glyph 105 = ク    Glyph 119 = ニ    Glyph 133 = ヤ
Glyph 106 = ケ    Glyph 120 = ヌ    Glyph 134 = ユ*
Glyph 107 = コ    Glyph 121 = ネ    Glyph 135 = ヨ
Glyph 108 = サ    Glyph 122 = ノ
Glyph 109 = シ    Glyph 123 = ハ
Glyph 110 = ス    Glyph 124 = ヒ
Glyph 111 = セ    Glyph 125 = フ

* Glyph 134 shared between ユ and ロ at sizes 0,1,3,4
```

---

## Comparison with Previous Mapping

The existing `data/katakana_mapping.json` had several errors due to incorrect table structure assumptions:
- Used 100 groups of 12 bytes starting at 0x4C9AB0, but the table is actually multiple small sub-tables
- Misaligned entries after group 37 (the data after the first sub-table bleeds into the second)
- Missing characters ヘ-ミ (stored at 0x4C9A50-0x4C9A78, before the main katakana block)
- Incorrect character assignments for many glyphs

The new mapping in `data/katakana_glyph_map.json` corrects all these issues.

---

## Output Files

- **`data/katakana_glyph_map.json`** -- Complete mapping with all 6 font sizes, 45 characters, 266 glyph ID entries
- **This file** -- Analysis findings

---

## Implications

1. **The name entry table only covers the 45 basic katakana** (ア-ヲ). Dakuten variants (ガ,ザ,ダ,etc.), handakuten (パ-ポ), small katakana (ァ-ォ,ャ-ョ), ヴ, ー, ～, and ン are NOT in these stride-57 tables. They must be stored elsewhere (possibly in the 0x4C9D20 region or generated programmatically).

2. **The grid layout on screen (10x10 with 82 positions) does NOT match the table structure.** The tables store characters in gojuon order across multiple small arrays, not in grid-position order.

3. **For font atlas replacement:** The glyph IDs in size 0 (98-142) locate characters on the main font atlas at positions computed as `col = id % 21, row = id / 21` in a 12x12 pixel grid (per recon29 findings).
