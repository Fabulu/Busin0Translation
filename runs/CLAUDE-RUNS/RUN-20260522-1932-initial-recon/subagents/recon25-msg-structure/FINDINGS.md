# MSG Structure Analysis - BUSIN 0: Wizardry Alternative Neo

**Date**: 2026-05-22
**Total MSG resources analyzed**: 296 / 296

## 1. Type Code Distribution

MSG resources are stored with these PACKDATA entry type codes:

| Type Code | Count |
|-----------|-------|
| type01 | 195 |
| type02 | 65 |
| type03 | 12 |
| type04 | 9 |
| type20 | 2 |
| type06 | 2 |
| type15 | 1 |
| type05 | 1 |
| type57 | 1 |
| type18 | 1 |
| type59 | 1 |
| type12 | 1 |
| type07 | 1 |
| type08 | 1 |
| type19 | 1 |
| type16 | 1 |
| type44 | 1 |

MSG resources use **17 different type codes**.

## 2. File Size Statistics

- **Min**: 524 bytes
- **Max**: 944588 bytes
- **Mean**: 136556.7 bytes
- **Median**: 72384 bytes

## 3. Message Count Statistics (FFFF separators)

- **Min**: 5 messages
- **Max**: 93213 messages
- **Mean**: 6821.8 messages
- **Median**: 678 messages

## 4. First-Bytes Pattern Analysis (Structural Subtypes)

**CRITICAL DISCOVERY**: The original classification assumed BE uint16 glyph streams, but the
first bytes reveal these resources have **structured binary headers**, not raw glyph data.

The dominant pattern `0100_0000` (262 resources) corresponds to raw bytes `01 00 00 00`,
which is **LE uint32 = 1**. This is a header field, not a glyph index.

Example header from resource 34 (first 32 bytes as LE uint32s):
```
01 00 00 00 = 1        (possible version/type field)
3C 17 00 00 = 5948     (possible data offset or count)
10 05 00 00 = 1296     (possible secondary count)
00 00 00 00 = 0        (padding/reserved)
02 00 00 00 = 2        (possible sub-type)
5A 09 00 00 = 2394     (possible offset)
50 1C 00 00 = 7248     (possible offset)
00 00 00 00 = 0        (padding/reserved)
```

Resources 36-45, 48-49 in the early block (indices 36-49) have patterns like
`009e_0000`, `007e_0000`, `00bc_0000` -- as raw bytes these are `00 9E 00 00`,
`00 7E 00 00`, etc., which are LE uint32 values 158, 126, 188.
These could be message counts or offsets specific to each menu/system text block.

| First 4 bytes (as BE u16 pair) | LE uint32 interpretation | Count | Sample indices |
|-------------------------------|--------------------------|-------|----------------|
| `0100_0000` | 1 (common header marker) | 262 | 34, 35, 39, 46, 47... |
| `0e00_0000` | 14 | 4 | 702, 742, 838, 2401 |
| `1313_1313` | 0x13131313 (magic/sentinel?) | 3 | 899, 900, 901 |
| `0003_0032` | 0x32000300 (mixed format?) | 2 | 636, 638 |
| `1e00_0000` | 30 | 2 | 830, 2549 |
| Various small values | Per-resource counts | 14 | 36-45, 48-49 (early block) |
| `0c00`-`4300_0000` | 12-67 | 6 | 758, 786, 1104, 1114... |

## 5. Internal Headers / Metadata

**All 296 MSG resources appear to have binary headers.** The data does NOT begin with
raw glyph indices as originally assumed. The header structure needs further reverse-engineering
to determine:
- Where the header ends and glyph data begins
- Whether the header contains a pointer/offset table to individual messages
- The exact meaning of each header field

Resources where first LE uint32 < 0x0020 (small integer header values): **271 of 296**
This overwhelmingly confirms a structured header format, not raw glyph data.

Resources with unusual first-bytes patterns that may indicate different sub-formats:
- `1313_1313` (resources 899, 900, 901): Possible magic number `0x13131313` -- these are
  the largest files (944KB), likely a different container format entirely.
- `0003_0032` (resources 636, 638): Different byte ordering suggests a distinct sub-format.

## 6. Resource Clustering (Spatial Organization)

MSG resources cluster into **63** groups (gap > 5 indices between clusters):

| Cluster | Start | End | Count | Span | Notes |
|---------|-------|-----|-------|------|-------|
| 1 | 34 | 49 | 16 | 16 | System/menu text |
| 2 | 636 | 638 | 2 | 3 |  |
| 3 | 690 | 690 | 1 | 1 |  |
| 4 | 702 | 708 | 4 | 7 |  |
| 5 | 720 | 720 | 1 | 1 |  |
| 6 | 742 | 744 | 2 | 3 |  |
| 7 | 752 | 762 | 4 | 11 |  |
| 8 | 770 | 772 | 2 | 3 |  |
| 9 | 781 | 786 | 3 | 6 |  |
| 10 | 800 | 810 | 4 | 11 |  |
| 11 | 816 | 820 | 3 | 5 |  |
| 12 | 830 | 830 | 1 | 1 |  |
| 13 | 838 | 838 | 1 | 1 |  |
| 14 | 856 | 856 | 1 | 1 |  |
| 15 | 870 | 870 | 1 | 1 |  |
| 16 | 888 | 888 | 1 | 1 |  |
| 17 | 896 | 907 | 8 | 12 |  |
| 18 | 913 | 917 | 3 | 5 |  |
| 19 | 927 | 927 | 1 | 1 |  |
| 20 | 985 | 985 | 1 | 1 |  |
| 21 | 1042 | 1042 | 1 | 1 |  |
| 22 | 1053 | 1148 | 43 | 96 | Dense cluster |
| 23 | 1161 | 1161 | 1 | 1 |  |
| 24 | 1178 | 1187 | 8 | 10 |  |
| 25 | 1216 | 1246 | 11 | 31 | Dense cluster |
| 26 | 1254 | 1266 | 5 | 13 |  |
| 27 | 1272 | 1289 | 11 | 18 | Dense cluster |
| 28 | 1302 | 1302 | 1 | 1 |  |
| 29 | 1312 | 1314 | 2 | 3 |  |
| 30 | 1324 | 1334 | 8 | 11 |  |
| 31 | 1340 | 1346 | 6 | 7 |  |
| 32 | 1371 | 1371 | 1 | 1 |  |
| 33 | 1438 | 1438 | 1 | 1 |  |
| 34 | 1564 | 1564 | 1 | 1 |  |
| 35 | 1610 | 1610 | 1 | 1 |  |
| 36 | 1623 | 1623 | 1 | 1 |  |
| 37 | 1701 | 1726 | 19 | 26 | Dense cluster |
| 38 | 1762 | 1762 | 1 | 1 |  |
| 39 | 1891 | 1891 | 1 | 1 |  |
| 40 | 1908 | 1909 | 2 | 2 |  |
| 41 | 2101 | 2124 | 12 | 24 | Dense cluster |
| 42 | 2137 | 2137 | 1 | 1 |  |
| 43 | 2156 | 2156 | 1 | 1 |  |
| 44 | 2283 | 2283 | 1 | 1 |  |
| 45 | 2303 | 2303 | 1 | 1 |  |
| 46 | 2325 | 2325 | 1 | 1 |  |
| 47 | 2343 | 2343 | 1 | 1 |  |
| 48 | 2400 | 2401 | 2 | 2 |  |
| 49 | 2418 | 2418 | 1 | 1 |  |
| 50 | 2478 | 2478 | 1 | 1 |  |
| 51 | 2484 | 2484 | 1 | 1 |  |
| 52 | 2492 | 2492 | 1 | 1 |  |
| 53 | 2500 | 2500 | 1 | 1 |  |
| 54 | 2513 | 2517 | 3 | 5 |  |
| 55 | 2525 | 2533 | 3 | 9 |  |
| 56 | 2540 | 2542 | 2 | 3 |  |
| 57 | 2549 | 2568 | 10 | 20 | Dense cluster |
| 58 | 2579 | 2579 | 1 | 1 |  |
| 59 | 2592 | 2592 | 1 | 1 |  |
| 60 | 2654 | 2654 | 1 | 1 |  |
| 61 | 2778 | 2797 | 9 | 20 |  |
| 62 | 2806 | 2806 | 1 | 1 |  |
| 63 | 2816 | 2876 | 55 | 61 | Large text block |

## 7. Adjacent Resource Types

What types of resources neighbor MSG resources (within +/- 3 indices)?

| Offset:Type | Count |
|-------------|-------|
| offset1:type01 | 191 |
| offset2:type01 | 188 |
| offset3:type01 | 188 |
| offset-2:type01 | 187 |
| offset-1:type01 | 186 |
| offset-3:type01 | 184 |
| offset-3:type02 | 71 |
| offset-2:type02 | 70 |
| offset-1:type02 | 69 |
| offset3:type02 | 69 |
| offset2:type02 | 68 |
| offset1:type02 | 67 |
| offset2:type03 | 18 |
| offset3:type03 | 14 |
| offset-3:type03 | 14 |
| offset1:type03 | 13 |
| offset-1:type03 | 13 |
| offset-2:type03 | 13 |
| offset-3:type04 | 8 |
| offset-2:type04 | 6 |

### Neighborhood Type Combinations

| Adjacent Type Mix | Count |
|-------------------|-------|
| type01 | 148 |
| type01+type02 | 41 |
| type02 | 24 |
| type01+type03 | 11 |
| type01+type02+type03 | 6 |
| type01+type02+type05 | 6 |
| type01+type15 | 3 |
| type01+type02+type03+type04 | 3 |
| type01+type02+type04 | 3 |
| type01+type02+type15+type20 | 2 |

## 8. Even/Odd Index Pattern

- **Even indices**: 177
- **Odd indices**: 119

Roughly balanced even/odd distribution.

## 9. Late Block Analysis (Index 2816+)

**55 MSG resources** in indices 2816+.

This is a dense, late-archive block likely containing a major text database.

Pattern distribution in this block:

- `0100_0000`: 55

## 10. Key Findings Summary

1. **MSG resources HAVE internal headers**: Contrary to the initial "raw glyph stream" assumption,
   262 of 296 MSG resources begin with LE uint32 value `1` followed by what appear to be offset/count
   fields. The glyph stream starts at some offset PAST the header. Determining this offset is
   critical for the translation pipeline.
2. **Type code mapping**: MSG resources span **17 different PACKDATA type codes** (type01=195,
   type02=65, type03=12, type04=9, plus 13 others). The type code does NOT reliably identify MSG
   resources -- content-based detection (FFFF separators) was the correct approach.
3. **Three structural sub-formats identified**:
   - **Standard** (262 resources): Header starts with LE uint32 = 1, followed by offset table
   - **Large container** (3 resources: 899-901): Magic `0x13131313`, files ~944KB, likely
     a different container wrapping multiple message sets
   - **Alternate format** (31 resources): Various header values (2-67, or different byte ordering)
4. **Clustering reveals game organization**: 63 clusters map to game systems. Key clusters:
   - Cluster 1 (34-49): 16 resources -- system/menu text
   - Cluster 22 (1053-1148): 43 resources -- largest mid-game cluster (dungeon events?)
   - Cluster 37 (1701-1726): 19 resources -- dense event cluster
   - Cluster 63 (2816-2876): 55 resources -- major late-game text database, ALL have standard header
5. **Adjacent resources are predominantly type01**: MSG resources are surrounded by type01 neighbors
   (148 of 296 have ONLY type01 neighbors). This suggests type01 is the "general data" type and
   MSG resources are interspersed among other game data, not grouped into a dedicated text section.
6. **Size range is extreme**: 524 bytes to 944KB, with median 72KB. The 3 largest (899-901, ~944KB)
   are likely master text databases containing thousands of messages each.
7. **Next step needed**: Reverse-engineer the header format to find the glyph-data offset. The
   header likely contains: version/type (uint32), message count, offset table to each message,
   then the glyph stream.