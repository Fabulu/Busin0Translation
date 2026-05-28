# Type-2 Dialogue Full Extraction -- FINDINGS

## Summary

Successfully extracted and decoded ALL dialogue from ALL type-2 resources in PACKDATA.DIG.

- **12,886 dialogue runs** extracted from **112 unique resources** (out of 448 type-2 resources with >10 sectors)
- **629,191 total text glyphs** decoded using the 759-entry glyph map
- Average coverage: **91.6%** (mapped glyphs / total glyphs)
- Average message length: **48.8 glyphs**

## Output Files

| File | Size | Description |
|------|------|-------------|
| `data/type2_dialogue_full.json` | 3.5 MB | Full structured dialogue (resource, offset, japanese, coverage, glyph_count) |
| `data/type2_dialogue_full.txt` | 2.6 MB | Human-readable text dump grouped by resource |

## Coverage Distribution

| Coverage | Count | % of Total |
|----------|-------|-----------|
| 50-59% | 129 | 1.0% |
| 60-69% | 110 | 0.9% |
| 70-79% | 479 | 3.7% |
| 80-89% | 3,203 | 24.9% |
| 90-99% | 6,485 | 50.3% |
| 100% | 2,480 | 19.2% |

Over 94% of extracted dialogue has 80%+ coverage, confirming high-quality decoding.

## Top 20 Resources by Dialogue Count

| Resource | Runs | Notes |
|----------|------|-------|
| R1203 | 1,580 | Largest dialogue resource |
| R1197 | 1,066 | |
| R1204 | 963 | |
| R1196 | 923 | |
| R1206 | 888 | |
| R1208 | 877 | |
| R1207 | 873 | |
| R1205 | 870 | |
| R1210 | 752 | |
| R1212 | 702 | |
| R1353 | 630 | |
| R1211 | 616 | |
| R1209 | 607 | |
| R1354 | 305 | |
| R1202 | 281 | |
| R1200 | 245 | |
| R1199 | 241 | |
| R1201 | 169 | |
| R1084 | 55 | |
| R1213 | 48 | |

## All 112 Resources with Dialogue

R677, R690, R712, R715, R726, R741, R750, R757, R769, R780, R785, R787, R793, R795, R797, R799, R801, R803, R816, R837, R839, R852, R860, R862, R864, R866, R868, R870, R871, R873, R875, R877, R879, R881, R883, R885, R889, R917, R920, R1057, R1061, R1072, R1073, R1077, R1084, R1091, R1093, R1099, R1105, R1109, R1110, R1112, R1123, R1133, R1141, R1145, R1146, R1147, R1174, R1196-R1213, R1353, R1354, R1912, R1930, R1931, R1933-R1936, R1939-R1941, R1948, R1952, R1953, R1959, R1972, R2141, R2144, R2161-R2163, R2166, R2174, R2176, R2200, R2201, R2204, R2206-R2208, R2588, R2589, R2651-R2653

## Method

1. Parsed TOC as 2883 x 12 bytes, LE uint32 triplets: (sector_offset, sector_count, type_code)
2. For each type-2 resource, parsed the resource header to locate Section 2 (dialogue data):
   - Section 2 size at header offset 0x14
   - Section 2 offset at header offset 0x18
3. Parsed Section 2 as BE uint16 glyph stream, splitting on FFFF message delimiters
4. Filtered control codes (>= 0xFB00), then decoded remaining glyphs via msg_glyph_map.json
5. Kept messages with 10+ text glyphs and 50%+ glyph coverage

## Extraction Script

`tools/extract_type2_dialogue.txt` (run with `python tools/extract_type2_dialogue.txt`)

## Key Observations

- The bulk of dialogue is concentrated in resources R1196-R1213 (the "main story" dialogue block)
- R1353-R1354 contain significant additional dialogue
- Resources in the 1900s and 2100s ranges also have meaningful text
- Earlier resources (600s-900s) tend to have smaller amounts of dialogue
- Some low-coverage entries (50-69%) may include binary data that passed filtering; the 80%+ entries are reliably clean dialogue
