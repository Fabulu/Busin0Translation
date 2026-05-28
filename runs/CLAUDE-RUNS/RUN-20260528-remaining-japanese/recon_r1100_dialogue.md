# Recon: R1100-R1190 Type-2 Dialogue Resources
**Date**: 2026-05-28

---

## Key Finding: The "171/110/181/22 lines" Counts Were FFFE Markers, Not Messages

The prior REMAINING_JAPANESE.md listed:
- R1126: 171 dialogue lines
- R1134: 110 dialogue lines
- R1148: 181 dialogue lines
- R1118: 22 dialogue lines

**These numbers are FFFE (line/page break) counts, not message counts.** Actual analysis:

| Resource | FFFE breaks | FFFF segments | High-cov segments (>=50%, >=10 glyphs) | Sectors | Sec2 size |
|----------|-------------|---------------|----------------------------------------|---------|-----------|
| R1118    | 22          | 86            | 7                                      | 38      | 54,064B   |
| R1126    | 171         | 1,480         | 5                                      | 117     | 70,176B   |
| R1134    | 110         | 1,515         | 6                                      | 154     | 75,440B   |
| R1148    | 181         | 1,843         | 4                                      | 63      | 52,640B   |

Most FFFF-delimited segments in these resources contain **binary data / numeric tables**, not Japanese text. The high-coverage segments are short structural fragments (menu labels like "ブベ別" = variable/name placeholders, "容" = capacity/content labels).

---

## Content Classification of R1118, R1126, R1134, R1148

### R1118 (38 sectors, sec2=54KB)
- **21 messages with any mapped glyphs**, only 7 with >=3 Japanese characters
- Content: Menu/UI structure data. Messages contain layout coordinates and control codes like `[0480] ０[0E00]` (positioning data)
- Sample decoded fragments: `ブベ別` (name placeholder), `前マ低ズ` (stat labels), `下討脱限罰攻知` (stat/skill names)
- **Classification: EVENT SCRIPT DATA + STAT/SKILL TABLES** -- not translatable dialogue

### R1126 (117 sectors, sec2=70KB)
- **66 messages with mapped glyphs**, only 5 with high coverage
- Content: Same menu/UI structure pattern. First messages are positioning data. Later messages are mostly unmapped (binary data tables)
- Sample: `ブベ 別` (placeholder), `冒` (adventure), scattered stat names
- **Classification: EVENT SCRIPT DATA + BATTLE/STAT TABLES** -- not translatable dialogue

### R1134 (154 sectors, sec2=75KB)
- **43 messages with mapped glyphs**, only 6 with high coverage
- Content: Similar to R1126. Menu positioning, stat table references
- Some decoded fragments: `h退動上崩臆` (movement/action labels), `度唱仕戻受蓄` (action verbs)
- **Classification: EVENT SCRIPT DATA + ACTION TABLES** -- mostly not translatable dialogue

### R1148 (63 sectors, sec2=53KB)
- **15 messages with mapped glyphs**, only 2 with >=3 Japanese characters
- Content: Structural data. Very low actual text content
- **Classification: EVENT SCRIPT DATA** -- not translatable dialogue

---

## Full Inventory: All R1100-R1190 Type-2 Resources

### Resources with NO translatable dialogue (data/layout only)

| Resource | Sectors | Sec2 size | Content type | Notes |
|----------|---------|-----------|-------------|-------|
| R1100    | 184     | 35,104B   | Event data   | 4 segments, menu positioning |
| R1103    | 99      | 11,892B   | Data table   | 1 segment |
| R1105    | 81      | 14,100B   | Coordinate table | Already translated as [DATA] |
| R1106    | 192     | 22,816B   | Event data   | Stat/class labels scattered |
| R1107    | 48      | 7,460B    | Data table   | 1 segment |
| R1108    | 137     | 84,256B   | Event data   | Stat fragments (仲パポ消) |
| R1109    | 21      | 4,820B    | Battle layout | 2 entries already translated as [DATA] |
| R1110    | 22      | 3,616B    | Level curve data | 1 entry already translated as [DATA] |
| R1112    | 246     | 201,248B  | Animation frames | 1 entry already translated as [DATA] |
| R1116    | 164     | 66,720B   | Event data   | Stat/skill fragments |
| R1117    | 21      | 29,108B   | Menu layout  | Repeated structure patterns |
| R1118    | 38      | 54,064B   | Event/stat tables | See above |
| R1120    | 144     | 40,352B   | Event data   | Menu positioning |
| R1123    | 85      | 2,388B    | Coordinate table | Already translated |
| R1124    | 128     | 17,568B   | Data table   | Mixed stat/item names |
| R1126    | 117     | 70,176B   | Event/stat tables | See above |
| R1127    | 83      | 5,860B    | Data table   | 1 segment, no JP text |
| R1128    | 62      | 75,440B   | Stat/item tables | Scattered item names |
| R1132    | 111     | 101,792B  | Event data   | 6 segments |
| R1133    | 75      | 4,500B    | Coordinate table | Already translated |
| R1134    | 154     | 75,440B   | Event/action tables | See above |
| R1137    | 84      | 3,540B    | Data table   | No JP text |
| R1141    | 74      | 8,932B    | Coordinate table | Already translated |
| R1142    | 203     | 211,760B  | Event data   | Some class/skill names |
| R1145    | 52      | 11,636B   | Coordinate table | Already translated |
| R1146    | 111     | 37,408B   | Event flags/data | 6 entries already translated as [DATA] |
| R1147    | 56      | 5,236B    | Coordinate table | Already translated |
| R1148    | 63      | 52,640B   | Event data   | See above |
| R1152    | 103     | 52,640B   | Data table   | Scattered item/stat names |
| R1154    | 102     | 84,256B   | Event data   | 4 segments |
| R1156-R1162 | 12-18 | 276-11,332B | Binary data | No FFFF markers at all |
| R1187    | 196     | 68,896B   | Event data   | Class/skill names |
| R1189    | 33      | 88B       | Tiny data    | No content |

### Resources WITH text content (R1163-R1174 cluster)

These small resources (5-16 sectors) contain text with ~95-100% glyph coverage, using FE:xx range glyphs. They appear to be **narration/description text** rather than NPC dialogue.

| Resource | Sectors | Sec2 size | Messages | Avg coverage | Translated? |
|----------|---------|-----------|----------|-------------|-------------|
| R1163    | 7       | 4,740B    | 8        | 98%         | NO          |
| R1164    | 7       | 4,100B    | 7        | 96%         | NO          |
| R1166    | 6       | 3,652B    | 2        | 96%         | NO          |
| R1167    | 6       | 3,716B    | 6        | 99%         | NO          |
| R1168    | 6       | 3,716B    | 3        | 95%         | NO          |
| R1169    | 6       | 3,652B    | 11       | 99%         | NO          |
| R1171    | 6       | 3,524B    | 8        | 99%         | NO          |
| R1172    | 6       | 3,716B    | 3        | 99%         | NO          |
| R1173    | 5       | 3,268B    | 2        | 99%         | NO          |
| R1174    | 16      | 10,692B   | 4        | 95%         | YES (all 4) |

**TOTAL: 54 untranslated text messages across R1163-R1173** (9 resources)

---

## Translation Status Summary

| Category | Resources | Messages | Translated | Untranslated |
|----------|-----------|----------|------------|--------------|
| Already translated (DATA/LAYOUT) | 9 resources | 20 entries | 20 | 0 |
| Binary/event data (not translatable) | ~30 resources | N/A | N/A | N/A |
| **Text content (R1163-R1173)** | **9 resources** | **54 messages** | **0** | **54** |
| R1174 (translated) | 1 resource | 4 messages | 4 | 0 |

### What R1163-R1173 Actually Contains

These are dense text blocks using FE:xx glyph codes extensively. The glyph map currently doesn't cover FE:xx range well (these show as `{FE:xx}` control codes in the decoded output). Sample decoded text from R1169:

```
y                               ... (location/scene setup)
         ９                      ... ：  (narration)
 a  ...  「  ...  f p ...        (dialogue with quotation marks 「」)
     ２１ ４                      (numbers/stats)
```

The presence of quotation marks (「」), numbers, and contextual words suggests these may be **item descriptions, location narration, or tutorial/help text**. The FE:xx codes that dominate these messages are likely mapped to common Japanese characters not in the current 810-entry glyph map.

---

## Corrected Assessment

The original REMAINING_JAPANESE.md entries 1B-9 through 1B-12 should be **reclassified**:

- **R1118, R1126, R1134, R1148**: These are NOT "mid-game dialogue" resources. They are event script data / stat tables with binary content. The FFFE counts (22/171/110/181) represent line breaks within data structures, not dialogue lines. **These do NOT need translation.**

- **R1163-R1173** (9 resources, 54 messages): These ARE text-heavy and untranslated. However, they use FE:xx range glyphs heavily, which would need additional glyph mapping before useful translation. **These are the actual remaining translatable content in R1100-R1190.**

- **R1174**: Already fully translated (4 messages, all in batch files).

---

## Recommendations

1. **Drop R1118/R1126/R1134/R1148 from the translation TODO** -- these are data tables, not dialogue
2. **Add R1163-R1173 to the TODO** if FE:xx glyph mapping can be expanded (54 messages total)
3. **Investigate FE:xx glyphs** -- the 0xFExx range likely maps to additional kanji/kana not in the current 810-entry map. These resources have ~95-100% coverage with the current map + FE:xx codes, meaning once FE:xx is decoded, the text will be fully readable
4. R1174 is already done, serving as a reference for the format used in R1163-R1173
