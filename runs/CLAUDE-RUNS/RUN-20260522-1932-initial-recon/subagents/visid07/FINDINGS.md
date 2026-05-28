# Visual Identification: Sheet 07 (Glyphs 700-799)

## Summary

Sheet 07 contains 100 glyphs (indices 700-799) from the Busin 0: Wizardry Alternative Neo font atlas. All glyphs in this range are complex kanji rendered at 12x12 pixels (displayed at 8x zoom in the sheet).

## Confidence Assessment

**Overall confidence: LOW**

At 12x12 pixel resolution, complex kanji with high stroke counts (10+ strokes) are extremely difficult to distinguish visually. Most identifications in this sheet are educated guesses based on:
- Overall character shape/silhouette
- Radical recognition where possible (e.g., rain radical for 720, gate radical for 724)
- Game context (Wizardry RPG -- magic, combat, equipment terms expected)
- Character frequency in Japanese RPG text

**All 100 entries are marked with "?" prefix indicating uncertainty.**

## Key Observations

1. **Glyph range usage**: According to msg_frequency_analysis.txt, the glyph index range 0x02BC-0x031F (approx. 700-799) falls within the observed usage range (0x0000-0x035A). These are real, used glyphs.

2. **Character complexity**: These are among the most complex kanji in the font. Many have 13+ strokes compressed into 12x12 pixels, making individual stroke discrimination nearly impossible through visual inspection alone.

3. **Expected vocabulary**: Given Wizardry RPG context, likely characters include:
   - Combat: 識(knowledge), 護(protect), 闘(fight), 襲(attack)
   - Magic: 魔(magic), 霊(spirit), 聖(holy), 闇(dark)
   - Equipment: 鎧(armor), 鍛(forge), 鋭(sharp)
   - Status: 毒(poison), 呪(curse), 麻(paralysis)
   - Locations: 墓(grave), 壁(wall), 塔(tower)

4. **Template matching was ineffective**: The automated template matching (glyph_map_template.json) produced garbage results for this range, confirming that visual/contextual identification is necessary.

## Verification Needed

These identifications MUST be cross-referenced against:
- Actual decoded game text (once message decoding is working)
- Shift-JIS code point tables (if the glyph-to-SJIS mapping can be determined)
- Known Japanese Wizardry game vocabulary lists

The "?" prefix on every entry reflects that none of these identifications should be considered reliable without verification.

## Output

- JSON file: `data/visual_id_sheet7.json`
- 100 entries, all marked uncertain with "?" prefix
- Format: `{"700": "?char", ...}`
