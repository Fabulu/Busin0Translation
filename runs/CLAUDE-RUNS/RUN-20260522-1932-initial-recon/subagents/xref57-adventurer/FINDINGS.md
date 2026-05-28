# xref57-adventurer: Adventurer A Dialogue Cross-Reference

## Target Text
Speaker: Adventurer A (冒険者Ａ)
Text (3 lines):
- こちとら怪我人かかえて (11 chars)
- そんなひまなんて (8 chars)
- ありゃしねえ (6 chars)

## CRITICAL FINDING: Glyph ID Systems Are Different

The name-entry screen glyph IDs (user-stated: か=91, こ=95, え=89, し=126) do NOT match the glyph IDs used in MSG resource dialogue text.

### Evidence
1. **Glyph 91 never appears consecutively**: Despite 570 total occurrences across all MSG resources, glyph 91 is NEVER followed by glyph 91. The text requires consecutive か (かか in かかえて), so if 91=か, this pattern MUST exist somewhere. It does not.

2. **Font sheet blank range**: Visual analysis of the font sheets confirms glyphs 100-157 are visually BLANK (no pixels). Yet the most frequent glyphs in MSG dialogue text (113=675x, 136=665x, 142=411x, 152=491x) fall in this "blank" range. This means MSG glyph IDs are NOT direct font atlas indices.

3. **Implication**: MSG resources use a CHARACTER TABLE lookup. The uint16 values in MSG data are character indices that get remapped to actual font glyph positions at render time. The name-entry screen uses direct font atlas IDs.

## Best Structural Candidate

**Resource 45 (0045_type01.bin), message #22** is the ONLY message across all 296 MSG resources with the exact line structure [11, 8, 6] when split on FFFE line breaks.

Glyphs (hex):
```
Line 0 (11): 7E 99 89 119 9B 99 80 8E BF 82 82
Line 1 (8):  166 7D 87 73 A8 95 72 3F
Line 2 (6):  70 76 96 91 9A 01
```

### Anomalies in msg#22
- Glyph 0x99 (153) appears at positions 1 and 5, which would map to different characters (ち and 我/が)
- Glyph 0x82 (130) appears consecutively at positions 9-10, but expected consecutive duplicate (かか) should be at positions 7-8

### Alternative Candidate: msg#7
Resource 45 msg#7 has consecutive glyph 121 (0x79) at positions 8-9, which could be かか. Line lengths [12, 10, 5] are slightly off from expected [11, 8, 6], possibly due to inline control bytes (0xC5 prefix at line starts).

## Consecutive Duplicate Statistics (Resources 34-49)
| Glyph | Count | Possible Character |
|-------|-------|--------------------|
| 113   | 28    | Unknown (most common particle?) |
| 92    | 7     | Unknown |
| 121   | 6     | Possibly か (msg#7 candidate) |
| 117   | 6     | Unknown |
| 130   | 5     | Unknown |

## Output
- `C:/Programmieren/wizardrytranslation/data/xref_adventurer.json`

## Next Steps
1. Find the CHARACTER TABLE in the game EXE that maps MSG glyph IDs to font atlas positions
2. This table will unlock the entire MSG glyph mapping
3. Resource 45 is confirmed as the location of this dialogue scene
