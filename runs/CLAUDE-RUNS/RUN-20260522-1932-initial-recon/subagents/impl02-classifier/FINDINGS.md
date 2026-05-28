# Resource Classification Findings

## Summary

Classified 2,881 of 2,883 resources (2 skipped as outliers: indices 1370, 2100).

### Category Counts

| Category | Count | Description |
|---|---|---|
| has_sjis | 1,934 | Resources containing >= 10 valid Shift-JIS byte pairs |
| has_ascii_strings | 1,673 | Resources with >= 5 runs of 4+ printable ASCII chars |
| likely_3d_model | 938 | Resources with >= 20 IEEE 754 floats in first 1KB |
| msg_structure | 296 | Resources with >= 5 FFFF separators and >= 3 FFFE line breaks |
| unknown | 767 | No detected pattern matched |

Note: Categories overlap -- a single resource can be classified as both msg_structure and has_sjis (and often is).

### Key Translation Targets

- **296 MSG resources** (dialogue/script files with FFFF/FFFE message structure)
- **1,934 SJIS resources** (contain Japanese text in some form -- includes MSG resources, data tables, etc.)

### Observations

1. **No texture/audio resources detected by magic bytes.** The packdata archive contains no RIFF, VAGp, TIM2, TMX0, PNG, BMP, or MPEG headers. These assets are likely stored in separate archives or use a custom/compressed container format.

2. **Zero compressed TMZ (0x12121212) signatures found.** Either compression is not used in this packdata, or the compression marker differs from the expected pattern.

3. **767 unknown resources** had no detectable pattern. These are likely binary data structures (tables, indices, collision data, etc.) that don't contain text.

4. **MSG resources cluster in specific index ranges:**
   - 34-49 (16 resources -- likely core game scripts)
   - 636-927 (scattered -- dungeon/event scripts mixed with data)
   - 1042-1346 (dense cluster -- major dialogue block)
   - 1701-1722 (NPC/quest scripts)
   - 2101-2156 (event scripts)
   - 2400-2592 (scattered)
   - 2778-2876 (dense cluster at end -- possibly UI/menu text)

5. **SJIS resources are very broadly distributed** (indices 1 through 2881), suggesting Japanese text appears in many data formats beyond just dialogue -- item names, skill descriptions, menu labels, status text, etc.

## Output Files

- **Classification JSON**: `C:/Programmieren/wizardrytranslation/dumps/resource_classification.json`
- **Classifier script**: `C:/Programmieren/wizardrytranslation/tools/classify_resources.py`
