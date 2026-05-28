# Recon: Untranslated Dialogue Resources (Deep Analysis)
**Date**: 2026-05-28
**Source files**: `extracted/packdata_raw/*.raw` (correct format, not `.bin`)

---

## Executive Summary

The four resources originally flagged as untranslated dialogue (R1118, R1126, R1134, R1148) are **NOT translatable dialogue**. They contain event script data, stat tables, and binary content with incidental FFFF delimiters. The "171/110/181/22 lines" counts in TODO.md were FFFE break counts within binary data, not dialogue line counts.

**Actual remaining untranslated text**: 54 messages across R1163-R1173 (9 resources), plus 1 tiny message in R1350.

---

## Primary Targets: R1118, R1126, R1134, R1148

### Verdict: NOT DIALOGUE -- Drop from translation TODO

| Resource | File size | Sec2 offset | Sec2 size | FFFF segments | Real dialogue msgs | Content type |
|----------|-----------|-------------|-----------|---------------|-------------------|--------------|
| R1118 | 77,824 B | 0x5940 | 54,064 B | 75 | 0 | Event script + stat tables |
| R1126 | 239,616 B | 0x29240 | 70,176 B | 964 | 0 | Event script + battle tables |
| R1134 | 315,392 B | 0x3A770 | 75,440 B | 1,181 | 0 | Event script + action tables |
| R1148 | 129,024 B | 0x127D0 | 52,640 B | 1,213 | 0 | Event script data |

Evidence:
- The "messages" decode as menu positioning data (`[0480] 0 [0E00]`), coordinate blocks, and binary data tables
- Glyph mapping coverage is extremely low (<5% of non-control glyphs map to real characters)
- The few mapped characters (`bu`, `be`, `betsu`, `you`) are structural placeholders, not prose
- Compare with R1196/R1197 (real dialogue): those have >95% glyph coverage and produce coherent Japanese sentences
- Translations exist: **NO** (and none needed)

---

## R1347-R1355 Gap Resources

| Resource | Messages | Text glyphs | Translated? | Notes |
|----------|----------|-------------|-------------|-------|
| R1347 | 11 | 348 | YES | In batch_gap1347.json |
| R1348 | 10 | 127 | YES | In batch_gap1347.json |
| R1349 | 11 | 300 | YES | In batch_gap1347.json |
| R1350 | 1 | 12 | **NO** | Single message: "ibakaaaa---  go" |
| R1351 | 23 | 572 | YES | In batch_gap1347.json |
| R1352 | 21 | 616 | YES | In batch_gap1347.json |
| R1353 | 652 | 17,473 | YES | In batch_gap1347.json |
| R1354 | 312 | 8,799 | YES | In batch_gap1347.json |
| R1355 | 56 | 1,990 | YES | In batch_gap1347.json |

**R1350** has one tiny message (12 glyphs): `ibakaaaa--- go` -- likely an exclamation/sound effect. This is the only untranslated gap resource.

All R1347-R1355 translations are in `data/type2_translated/batch_gap1347.json` (131 entries). They should already be included in the build pipeline since the injector auto-globs `batch_*.json`.

---

## R1163-R1173: The REAL Untranslated Text (54 messages)

These small resources (5-16 sectors) contain dense text with ~95% glyph coverage. They appear to be **narration, location descriptions, or tutorial/lore text**.

| Resource | Messages | Total glyphs | Mapped % | Sample content |
|----------|----------|-------------|----------|----------------|
| R1163 | 9 | 2,362 | 96% | Narration with `[quotation marks]`, questions |
| R1164 | 9 | 2,050 | 92% | Numbers, dialogue with `[` quotes, dashes |
| R1165 | 1 | 1,730 | 100% | Single huge block of space-padded text |
| R1166 | 3 | 1,824 | 89% | Mixed text with numbers and quotes |
| R1167 | 7 | 1,852 | 96% | Narration, questions, character references |
| R1168 | 4 | 1,855 | 88% | Dense text with numbers, quotes |
| R1169 | 14 | 1,812 | 93% | Location/scene descriptions, stats |
| R1170 | 1 | 1,954 | 90% | Single large text block |
| R1171 | 10 | 1,752 | 95% | Narration and dialogue snippets |
| R1172 | 4 | 1,855 | 96% | Character descriptions |
| R1173 | 3 | 1,632 | 94% | Scene descriptions |

**Blockers for translation**:
1. **FE:xx glyph gap**: These resources use FF:xx range values (FFE0-FFFC) extensively as text characters, not control codes. The current 810-entry glyph map does not cover this range. These need to be mapped before the text becomes readable.
2. **Low-range (00:xx) unmapped glyphs**: Values like 0002-000E appear throughout. Some may be text, some may be control codes.
3. R1174 (same format, 4 messages) is already translated and can serve as a reference for the FE:xx mappings.

---

## Full R1100-R1199 Scan: 57 Type-2 Resources

### Already Translated (17 resources)
R1105, R1109, R1110, R1112, R1123, R1133, R1141, R1145, R1146, R1147, R1174, R1193, R1194, R1196, R1197, R1198, R1199

### Binary/Event Data -- Not Translatable (~30 resources)
R1100, R1103, R1106, R1107, R1108, R1116, R1117, R1118, R1120, R1124, R1126, R1127, R1128, R1132, R1134, R1137, R1142, R1148, R1152, R1154, R1156, R1157, R1158, R1159, R1162, R1187, R1189, R1192, R1195

These have very low glyph mapping coverage. Their Section 2 data is binary (coordinates, stat tables, enemy parameters, etc.) with coincidental FFFF delimiters.

### Untranslated Text Content (9 resources, 54 messages)
R1163, R1164, R1165, R1166, R1167, R1168, R1169, R1170, R1171, R1172, R1173

These have high glyph coverage and contain real Japanese text, but need FE:xx glyph mapping expansion.

---

## Recommendations

1. **Remove R1118, R1126, R1134, R1148 from TODO.md** -- confirmed not dialogue
2. **Add R1350** to a translation batch (1 trivial message: sound effect/exclamation)
3. **Prioritize FE:xx glyph mapping** for R1163-R1173 (54 messages of narration/lore text)
4. **Verify R1347-R1355 build integration** -- batch_gap1347.json should be auto-loaded by the injector, but confirm these resources appear in the build output
5. The correct source files are `.raw` in `extracted/packdata_raw/`, not `.bin` in `extracted/packdata_resources/` -- the `.bin` files have different layout and incorrect header parsing
