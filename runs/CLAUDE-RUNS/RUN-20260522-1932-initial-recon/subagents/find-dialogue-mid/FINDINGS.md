# FINDINGS: Untranslated MSG Resources 1042-1346

**Date:** 2026-05-22  
**Agent:** find-dialogue-mid  
**Range:** Resources 1042-1346 (the "densest cluster" -- 97 resources)

---

## Critical Finding: NO Dialogue Text in This Range

**All 97 resources in the 1042-1346 range that were classified as "MSG" are actually binary data.** None contain translatable dialogue or text.

These resources contain:
- **PS2 Graphics Synthesizer (GS) packet data** -- 3D models, vertex data, textures, and level rendering commands
- **Compound resources** with header structure: `{version=1, sub1_offset, total_size, sub_count=2}`
- The GS packet signature `04800000 00000010 0e000000` appears in the first 128 bytes of nearly all resources

## Why the Misclassification Happened

The original classifier (`tools/classify_resources.py`) flags a resource as "MSG" if:
```
ffff_count >= 5 AND fffe_count >= 3
```

This threshold is far too loose for large binary files (100KB-900KB). Any binary file of that size will have coincidental 0xFFFF and 0xFFFE byte pairs. The actual MSG resources in the game (e.g., R34-R50, R1053, R2654) are typically small (<40KB) and have:
- **>90%** of non-zero values in valid MSG token ranges
- **Consecutive runs of 5+ hiragana/katakana** glyph IDs (real Japanese text)
- Meaningful FFFF delimiter density (messages every ~50-200 bytes, not every 10000+ bytes)

## Strict Validation Results

Using stricter criteria (ratio >= 0.90, map_ratio >= 0.50, consecutive kana run >= 5):

| Category | Count | Description |
|----------|-------|-------------|
| Actual MSG | **0** | No resources passed strict validation |
| Compound/binary (GS) | 92 | PS2 rendering data with compound header |
| Unknown binary | 5 | Large binary blobs (R1042, R1161, R1178, R1180, R1186) |

## Resource Type Distribution

| Type Code | Count | Size Range | Content |
|-----------|-------|------------|---------|
| type01 | 49 | 22KB-330KB | GS packets / compound data |
| type02 | 36 | 22KB-373KB | Compound (2 sub-resources) |
| type03 | 2 | 35KB-66KB | GS packet data |
| type04 | 1 | 938KB | Large binary (R1042) |
| type05 | 1 | 66KB | Compound data |
| type06 | 1 | 68KB | Compound data |
| type07-59 | 7 | 302KB-938KB | Large binary blobs |

## Compound Resource Structure

Most type02 resources have this header (little-endian):
```
Offset 0x00: uint32  version (always 1)
Offset 0x04: uint32  offset to sub-resource 2
Offset 0x08: uint32  total size (matches file size + 16 from extraction)
Offset 0x0C: uint32  sub-resource count (always 2)
```

Sub-resource 1 (offset 0x10 to sub2_offset) contains GS packet headers:
```
04800000 00000010 0e000000 00000000  -- GIF tag
00000000 00000000 08000000 00000000  -- more GIF
00800000 04004000 34000000 00000000  -- vertex descriptor
60000000 6?ffffff 14000000 00000000  -- data descriptor
```

Sub-resource 2 contains what appears to be vertex/texture data.

## Notable Individual Resources

- **R1042, R1178, R1180** (938KB each): Nearly identical content, likely same level/dungeon data stored in different type codes (type04/57/59)
- **R1161** (73KB): High valid-ratio (0.94) but maxHiraRun=1, suggesting structured numeric data rather than text
- **R1053** (35KB): Previously decoded, contains some text fragments but mostly GS packet data

## Implications for Translation

1. **This range does NOT contain the "main story dialogue"** as hypothesized
2. The actual game dialogue likely resides in resources already identified (R34-R50 range, R1053, R2654, etc.)
3. The classifier's `msg_resource_indices` list is significantly inflated -- most entries are false positives from binary data
4. A fix to the classifier should require `ratio >= 0.80` and `max_consecutive_kana_run >= 5` to eliminate false positives

## Recommendation

Update the classifier threshold to prevent binary resources from being flagged as MSG:
- Require valid-token ratio >= 0.80 (instead of just ffff >= 5)
- Require at least one run of 5+ consecutive hiragana/katakana glyph IDs
- Consider file size: resources > 50KB should have higher thresholds since random binary data produces more coincidental matches

## Output Files

- `data/untranslated_1042_1346.txt` -- Full classification details for all 97 resources
