# Monster Name Cross-Reference: xref51-monster

## Target Text
- Screenshot: fight1.p2s shows "バブリースライム" (Bubbly Slime) on the battle target selection screen
- 8 katakana characters: バ ブ リ ー ス ラ イ ム

## Known Glyph Mappings (from name entry table at 0x4C9AB0)
- リ = 137, ス = 110, ラ = 136, イ = 99, ム = 130 (size-0 basic katakana)
- バ, ブ, ー are NOT in the basic 45 katakana table

## Special Character Grid (at 0x4C9CE0)
Found the special character grid containing dakuten/handakuten/small kana entries.
Layout is 8 columns per row with 0xFFFF for empty cells.

### Row 0 (direct glyph IDs): 25, 26, 27, 28, 29, 30, 31, 32
### Row 1 (direct glyph IDs): 33, 34, 35, 36, 114
### Rows 2+ use packed IDs (0xHH00 format):

| Range | Decimal | Count | Likely Characters |
|-------|---------|-------|-------------------|
| 0x1900-0x190C | 6400-6412 | 13 | Dakuten set A (ga-row: ガギグゲゴ + za-row: ザジズゼゾ + partial da-row) |
| 0x1A00-0x1A0C | 6656-6668 | 13 | Dakuten set B (ba-row: バビブベボ + handakuten pa-row partial) |
| 0x1B00-0x1B0C | 6912-6924 | 13 | Extended set (small kana / additional specials) |
| 0x1C00-0x1C0C | 7168-7180 | 13 | (Size variant 3) |
| 0x1D00-0x1D0C | 7424-7436 | 13 | (Size variant 4) |
| 0x1E00-0x1E0F | 7680-7695 | 16 | (Size variant 5) |
| 0x1F00-0x1F04 | 7936-7940 | 5  | (Size variant 6, partial) |

### Hypothesis for dakuten mapping (0x1A00 series = バ行):
- 0x1A00 (6656) = バ
- 0x1A01 (6657) = ビ
- 0x1A02 (6658) = ブ
- 0x1A03 (6659) = ベ
- 0x1A04 (6660) = ボ

### Small kana / special marks (Row 0, glyphs 25-36):
These 13 glyphs likely map to: ァ ィ ゥ ェ ォ ッ ャ ュ ョ ー ～ ヴ ン (uncertain ordering).
Glyph 114 (= チ in base table, but appears in special grid row 1 position 4) may have dual use.

## Exhaustive Search Results

### EE RAM (32MB from fight1.p2s save state):
- ス-ラ-イ-ム (110,136,99,130) as consecutive uint16 in ANY endianness: **NOT FOUND**
- Even partial subsequences (ラ-イ-ム, ス-ラ) as consecutive uint16: **NOT FOUND**
- アイテム (98,99,116,130) as consecutive uint16: **NOT FOUND** (despite being visible on screen)
- Shift-JIS バブリースライム: **NOT FOUND**
- Unicode (U+30D0 U+30D6 U+30EA...) バブリースライム: **NOT FOUND**
- ASCII "Slime" / "Bubbly Slime": **NOT FOUND**

### MSG Resources (296 classified, 47 valid MSG format):
- スライム (110,136,99,130) as consecutive BE uint16 in any resource: **NOT FOUND**
- All size variants of スライム: **NOT FOUND**
- リ(137) within 5 positions of ス(110): **NOT FOUND** in any valid MSG resource
- Packed ID 0x1A00 near glyph 137: **NOT FOUND**

### PACKDATA.DIG (840MB):
- Shift-JIS スライム: **NOT FOUND**
- Unicode スライム: **NOT FOUND**

### EXE (SLPM_653.78, 4MB):
- Shift-JIS バブリースライム: **NOT FOUND**
- ASCII "Slime": **NOT FOUND**

## Key Finding: Text Rendering Architecture
The game does NOT store text as contiguous glyph-ID arrays in EE RAM. Even basic katakana-only menu text like "アイテム" (visible on screen) cannot be found as consecutive uint16 values. This means:

1. Text is rendered via a command buffer where glyph IDs are interleaved with positioning/formatting data
2. OR text is streamed from resources and rendered immediately without being stored as a string
3. OR the rendering system uses a completely different glyph indexing than the name entry table

## Confirmed Data Structures
- Name entry katakana table: 0x4C9AB0 (45 entries x 12 bytes, 6 size variants per char)
- Special character grid: 0x4C9CE0 (13 special chars with packed IDs 0x1900+)
- MSG text format: BE uint16, 0xFFFF delimiter, 0xFFFE line break
- MSG text is loaded at ~0xDC0000-0xE20000 in EE RAM during gameplay
- Glyph index range in MSG: 0x0000-0x035A (858 max)
- FCD_battle_font resource reference at 0x4F0341

## Status: INCOMPLETE
Unable to determine the exact glyph indices for バ, ブ, and ー from the available data.
The packed ID hypothesis (バ=0x1A00, ブ=0x1A02) remains unverified because these packed IDs
do not appear in the MSG text data in the expected pattern.

## Recommended Next Steps
1. Disassemble the EXE text rendering function to understand how glyph IDs are processed
2. Set PCSX2 breakpoints on the font rendering code to trace which glyph IDs are used for バブリースライム
3. Compare EE RAM dumps from different game states (with/without the monster name displayed) to find the delta
4. Look at the glyph atlas images more carefully (current extractions have deswizzle artifacts making glyphs 60-427 mostly blank)
