# xref58-knight2: Knight Dialogue Search Results

## Target Text
- **Speaker**: 騎士団 (Knight Order, 3 kanji characters)
- **Text**: 君が、行方不明になったレジーナ達を探してくれる者かね。
- **Structure**: 11 chars + line break + 16 chars = 27 total

## Critical Finding: Glyph Mapping Mismatch

The user-provided glyph IDs (レ=139, ナ=118, か=91, く=93) are from the **name-entry screen RAM table** and do NOT correspond to dialogue text glyphs:

- `visual_id_sheet0.json` identifies glyph 91 as 'q' and 93 as 's' (ASCII lowercase)
- Glyph 139 is completely absent from the top 200 most frequent MSG glyphs
- Glyph 91 appears only 77 times (rank 114) -- far too rare for か
- The name-entry screen uses a separate font texture from the dialogue system
- The stride-57 variant system maps multiple glyph IDs to the same visual character in the name-entry font, but these IDs render as different characters in the dialogue font

**The name-entry glyph table cannot be used to identify dialogue text.**

## MSG Format Discoveries

### Speaker Tag Format
Dialogue messages use the pattern:
```
FF01 [speaker_name_glyph_ids...] FFF0 [dialogue_text...] FFFE [more_text...]
```
- `FF01` = speaker tag start
- `FFF0` = speaker tag end / dialogue begin
- `FFFE` = line break within dialogue
- `FFFF` = message delimiter

### Resource Statistics
- 296 resources classified as MSG
- Only 47 pass validity check (70%+ glyphs in valid range + 2+ FFFF)
- 249 are misclassified binary data (textures, models with incidental 0xFFFF)
- 83 resources contain FF01 speaker tag patterns
- Only resource 46 (`0046_type03.bin`) contains 3-character speaker tags

## Candidate Knight Speaker

**Speaker glyphs: [0x118, 0x146, 0x136] (decimal: 280, 326, 310)**

Evidence this is 騎士団:
- A 2-character speaker [0x118, 0x146] also exists in the same resource (msg 12)
- The 2-char and 3-char versions sharing the first two glyphs is consistent with 騎士 (knight) vs 騎士団 (knight order)
- The 3-char speaker appears in what looks like an NPC dialogue scene (msg 13)

The dialogue found under this speaker:
```
00AB 02A3 0073 0098 0085 FFFE
0076 008E 00BF 0082 009D 00A4 00B7 0087 005D 0075 0001
```
This is only 20 glyphs -- a different, shorter line from the knight, NOT the レジーナ dialogue.

## Why the レジーナ Dialogue Was Not Found

1. **Only resource 46 has 3-char speaker tags** among the valid resources
2. The レジーナ line is not present under the candidate knight speaker in resource 46
3. Quest-dependent dialogue may be stored in resources with binary headers that cannot be parsed with the current approach
4. The 249 "invalid" resources need proper header parsing to extract embedded dialogue
5. Some resources may use a different dialogue format without FF01/FFF0 speaker tags

## All 3-Character Speaker Tags (Resource 46 only)

| Offset | Name Glyphs | Text Glyphs | Likely Identity |
|--------|------------|-------------|-----------------|
| 785 | 0xC2, 0xEE, 0x105 | 60 | Unknown |
| 1245 | 0x118, 0x146, 0x136 | 20 | 騎士団 (Knight Order) |
| 1448 | 0xE8, 0x5D, 0x105 | 52 | Unknown |
| 1846 | 0xE8, 0x5D, 0x105 | 35 | Unknown (same as above) |
| 4193 | 0x114, 0x12A, 0x112 | 29 | Unknown |
| 6026 | 0xDF, 0x110, 0x105 | 86 | Unknown |
| 6187 | 0x107, 0x107, 0x5D | 54 | Unknown |
| 8619 | 0xCD, 0xE9, 0x5D | 79 | Unknown |

## Recommended Next Steps

1. **Parse binary headers properly**: The type01 resources with 82-byte config blocks need header format reverse-engineering to find where glyph data actually starts
2. **Confirm 騎士団 mapping**: Use a save state or emulator screenshot to verify that glyphs [0x118, 0x146, 0x136] render as 騎士団
3. **Search event script resources**: The レジーナ dialogue may be triggered by event scripts that reference string indices in shared text tables
4. **Font atlas OCR**: Fix the deswizzle pipeline to produce readable glyph images, then OCR the full font atlas to build a reliable glyph mapping
5. **Cross-reference with BUSIN 1**: The English version's MSG files contain the same Japanese glyph encoding -- comparing known English translations with Japanese glyph sequences could help crack the mapping
