# xref53-knight: Knight Commander Dialogue Cross-Reference

## Status: INCONCLUSIVE

## Target
- Speaker: 騎士団長 (Knight Commander, 4 chars)
- Text: 聞いたかもしれないが、迷宮の第２階層において討伐隊のメンバーが消息を絶った。
- Total: 38 characters
- Key structural constraints: い at positions 1,8,20; が at 9,30; の at 13,25; た at 2,36

## Search Summary

### Phase 1: Message-level search (FFFF-delimited)
- Searched all 296 classified MSG resources
- Found 163 messages with exactly 38 glyphs (after stripping control codes >= 0xFFC0)
- **ZERO** have g[1]==g[8] (the two い positions)
- This means no standalone message matches the target pattern

### Phase 2: Sliding window within dialogue blocks
- Resource 46 (type03) stores entire dialogue scenes as single large messages (60-165 glyphs)
- Internal lines separated by 0xFF01 control codes, not FFFF/FFFE
- Sliding window search found one weak match (score 2/5) but it crosses scene boundaries and doesn't satisfy comma/period position constraints

### Phase 3: Real text resource identification
Resources with genuine text content (all glyphs < 1100):
- R45: 197 text messages
- R38: 188 text messages  
- R36: 158 text messages
- R2108: 422 text messages (type03)
- R2106: 390 text messages (type03)
- R2115: 377 text messages (type03)

### Key Format Discoveries
1. **type01 resources** (R36-49 etc): Short messages delimited by FFFF/FFFE. Most dialogue is here.
2. **type03 resources** (R46, R2106-2115): Large scene blocks with 0xFF01 internal separators. 
3. **Control codes**: Values >= 0xFFC0 are formatting codes (not text). Must be stripped before counting glyphs.
4. **Glyph frequency**: Top text glyphs are 113 (675x), 136 (665x), 158 (493x), 152 (491x), 93 (489x)
5. **Assumed punctuation**: 62 = 、(comma), 63 = 。(period) based on message patterns

### Possible Reasons for Failure
1. The knight dialogue may be in a resource not classified as MSG
2. The glyph encoding might differ from assumptions (e.g., kanji indices above 858)
3. The dialogue may be dynamically loaded from a resource outside the packdata
4. The partial glyph map (data/glyph_map_partial.json) has incorrect/duplicate assignments that led to wrong initial assumptions about glyph indices

## Output Files
- `C:/Programmieren/wizardrytranslation/data/xref_knight.json` - Search results and format notes
- Scripts in this directory: scan*.py, s*.py - Various search approaches
