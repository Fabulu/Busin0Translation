# Comprehensive Untranslated Dialogue Scan

**Date:** 2026-05-28

**Method:** Full scan of all 2,883 PACKDATA resources. Type-02 resources classified
by internal format (MSG standard, ICS scenario). Glyph map hit rate, FB00 speaker
tags, and FFFF/FFFE delimiters used to distinguish real text from binary data.

---

## Executive Summary

| Metric | Count |
|--------|-------|
| Total PACKDATA resources | 2,883 |
| Type-02 resources (primary text containers) | 617 |
| Type-02 with confirmed dialogue | 284 |
| - Already translated | 137 |
| - **Untranslated type-02** | **147** |
| Known non-type-02 text resources | 20 |
| - Already translated (R39) | 1 |
| - **Untranslated non-type-02** | **19** |
| **Total untranslated text resources** | **166** |

### Estimated Line Counts

| Category | Resources | Est. Glyph Groups |
|----------|-----------|-------------------|
| Translated type-02 | 137 | ~13,362 |
| Untranslated MSG format | 46 | ~3,774 |
| Untranslated ICS format | 101 | ~314 |
| Untranslated non-type-02 | 19 | ~unknown |
| **Total untranslated** | **166** | **~4,088+** |

### Translation Progress

- **By resource count:** 138 / 304 = **45.4%**
- **By line count (type-02 only):** ~13,362 / ~17,450 = **~76.6%**
- The bulk of remaining work is in 46 untranslated MSG-format resources
- ICS resources (101) are mostly small scenario triggers with few text lines each

---

## Type-02 Format Breakdown

Type-02 resources have three internal formats:

| Format | Total | Description |
|--------|-------|-------------|
| **MSG standard** | 265 | FFFF-delimited glyph streams, main dialogue |
| **ICS scenario** | 116 | "IECS" magic, scenario/event triggers with embedded text |
| **MSG no-FFFF** | 236 | Header=1 but no FFFF markers (non-text data, parameters) |

---

## Untranslated MSG-Format Resources (46)

These are the highest-priority targets -- full dialogue scenes with FFFF-delimited
glyph streams, speaker tags, and high glyph map coverage.

### Dungeon/Event Dialogue (R680-R911)

These are dungeon scenes and NPC interactions. Most are large (38KB-166KB) with
many dialogue groups, multiple speaker tags, and ~73% glyph hit rates.

| Resource | Size | Groups | FB Tags | Hit Rate | Priority |
|----------|------|--------|---------|----------|----------|
| R680 | 128,624 | 71 | 33 | 73% | HIGH |
| R684 | 112,096 | 23 | 12 | 73% | HIGH |
| R686 | 91,568 | 39 | 32 | 74% | HIGH |
| R694 | 38,096 | 31 | 29 | 75% | HIGH |
| R698 | 113,088 | 39 | 26 | 73% | HIGH |
| R714 | 120,784 | 31 | 72 | 73% | HIGH |
| R716 | 92,592 | 37 | 13 | 73% | HIGH |
| R718 | 125,872 | 47 | 29 | 73% | HIGH |
| R730 | 132,512 | 55 | 112 | 72% | HIGH |
| R738 | 106,208 | 27 | 13 | 73% | HIGH |
| R754 | 106,208 | 27 | 25 | 73% | HIGH |
| R760 | 138,976 | 27 | 31 | 74% | HIGH |
| R776 | 107,968 | 39 | 21 | 73% | HIGH |
| R778 | 134,032 | 63 | 50 | 73% | HIGH |
| R802 | 130,784 | 27 | 31 | 73% | HIGH |
| R812 | 84,832 | 25 | 79 | 74% | HIGH |
| R822 | 118,672 | 63 | 35 | 73% | HIGH |
| R824 | 126,864 | 63 | 32 | 73% | HIGH |
| R826 | 126,864 | 63 | 33 | 73% | HIGH |
| R832 | 107,968 | 39 | 69 | 73% | HIGH |
| R834 | 107,968 | 39 | 35 | 73% | HIGH |
| R836 | 107,968 | 39 | 37 | 73% | HIGH |
| R842 | 165,840 | 31 | 24 | 73% | HIGH |
| R846 | 138,976 | 27 | 11 | 74% | HIGH |
| R854 | 99,760 | 39 | 52 | 74% | HIGH |
| R858 | 39,504 | 31 | 17 | 74% | HIGH |
| R890 | 112,096 | 23 | 26 | 73% | HIGH |
| R909 | 5,584 | 11 | 3 | 78% | MEDIUM |
| R911 | 56,064 | 11 | 20 | 74% | HIGH |

**Subtotal: 29 resources, ~1,073 groups**

### System/Battle Text (R1054-R1367)

These appear to be battle system, shop, or UI-related text resources.

| Resource | Size | Groups | FB Tags | Hit Rate | Priority |
|----------|------|--------|---------|----------|----------|
| R1054 | 34,624 | 10 | 10 | 84% | MEDIUM |
| R1055 | 174,148 | 166 | 56 | 41% | MEDIUM |
| R1067 | 151,620 | 580 | 151 | 40% | HIGH |
| R1095 | 162,292 | 256 | 100 | 41% | HIGH |
| R1103 | 189,140 | 524 | 152 | 43% | HIGH |
| R1358 | 33,728 | 5 | 6 | 83% | MEDIUM |
| R1359 | 34,624 | 10 | 10 | 84% | MEDIUM |
| R1360 | 34,624 | 10 | 1 | 84% | MEDIUM |
| R1361 | 34,624 | 10 | 4 | 84% | MEDIUM |
| R1362 | 34,624 | 10 | 3 | 84% | MEDIUM |
| R1365 | 35,680 | 15 | 8 | 79% | MEDIUM |
| R1366 | 35,680 | 15 | 0 | 79% | MEDIUM |
| R1367 | 35,600 | 18 | 13 | 60% | MEDIUM |

**Subtotal: 13 resources, ~1,629 groups**

### Data/Table Resources (R2158, R2217-R2219)

Potentially item/spell descriptions or lookup tables with text.

| Resource | Size | Groups | FB Tags | Hit Rate | Priority |
|----------|------|--------|---------|----------|----------|
| R2158 | 35,360 | 15 | 10 | 82% | MEDIUM |
| R2217 | 63,770 | 1,028 | 9 | 72% | HIGH |
| R2218 | 43,050 | 641 | 4 | 73% | HIGH |
| R2219 | 44,170 | 855 | 6 | 73% | HIGH |

**Subtotal: 4 resources, ~2,539 groups (R2217-R2219 are likely large text tables)**

---

## Untranslated ICS-Format Resources (101)

ICS (Interactive Cinema Script) resources are scenario/event containers.
Range: R1911-R2026. Most are small (288-8,640 bytes) with 2-8 text groups each.

### Already Translated ICS (15 resources)
R1912, R1930, R1931, R1933-R1936, R1939-R1941, R1948, R1952, R1953, R1959, R1972

### Untranslated ICS (101 resources)

| Range | Count | Typical Size | Est. Groups |
|-------|-------|-------------|-------------|
| R1911-R1929 | 17 | 288-5,584 | ~3-8 each |
| R1932-R1958 | 18 | 288-8,640 | ~2-5 each |
| R1960-R2026 | 66 | 288-2,384 | ~2-3 each |

**Subtotal: 101 resources, ~314 groups total**

Most ICS resources contain short event triggers like item pickups, treasure
descriptions, or brief NPC interactions. Low individual word count but many
resources.

---

## Untranslated Non-Type-02 Text Resources (19)

These are known text resources in other format types. Previously identified
through manual analysis.

| Resource | Type | Description | Status |
|----------|------|-------------|--------|
| R34 | 20 | System/menu text | TODO |
| R36 | 01 | System/menu text | TODO |
| R37 | 01 | System/menu text | TODO |
| R38 | 01 | System/menu text | TODO |
| R40 | 01 | System/menu text | TODO |
| R41 | 01 | System/menu text | TODO |
| R42 | 01 | System/menu text | TODO |
| R43 | 01 | System/menu text | TODO |
| R44 | 01 | System/menu text | TODO |
| R45 | 01 | System/menu text | TODO |
| R46 | 03 | System/menu text | TODO |
| R47 | 03 | System/menu text | TODO |
| R48 | 01 | System/menu text | TODO |
| R49 | 01 | System/menu text | TODO |
| R720 | 04 | Unknown text | TODO |
| R1053 | 03 | Unknown text | TODO |
| R1908 | 06 | Unknown text | TODO |
| R2124 | 01 | Unknown text | TODO |
| R2654 | 44 | Unknown text | TODO |

**Note:** R39 (type 15) is already translated.

---

## Already Translated Resources (138)

### Type-02 MSG Format (82 resources)
R35, R677, R690, R712, R715, R726, R741, R750, R757, R769, R780, R785, R787,
R793, R795, R797, R799, R801, R803, R816, R837, R839, R852, R860, R862, R864,
R866, R868, R870, R871, R873, R875, R877, R879, R881, R883, R885, R889, R917,
R920, R989, R990, R1034, R1057, R1061, R1072, R1073, R1077, R1084, R1091,
R1093, R1099, R1105, R1109, R1110, R1112, R1123, R1133, R1141, R1145, R1146,
R1147, R1168, R1169, R1170, R1171, R1172, R1173, R1174, R1193, R1194, R1196,
R1197, R1198, R1199, R1200, R1201, R1202, R1203, R1204, R1205, R1206, R1207,
R1208, R1209, R1210, R1211, R1212, R1213

### Type-02 MSG (no-FFFF variant, 17 resources)
R1347, R1348, R1349, R1350, R1351, R1352, R1353, R1354, R1355, R2144,
R2651, R2652, R2653

### Type-02 ICS (15 resources)
R1912, R1930, R1931, R1933, R1934, R1935, R1936, R1939, R1940, R1941,
R1948, R1952, R1953, R1959, R1972

### Type-02 Other translated (11 resources)
R2141, R2161, R2162, R2163, R2166, R2174, R2176, R2200, R2201, R2204,
R2206, R2207, R2208, R2588, R2589

### Non-Type-02 (1 resource)
R39

---

## Priority Recommendations

### Immediate Priority (HIGH)
1. **29 dungeon/event MSG resources** (R680-R911) -- core gameplay dialogue
2. **R1067, R1095, R1103** -- large resources with 256-580 groups each
3. **R2217-R2219** -- large text tables (~2,500 groups total)

### Medium Priority
4. **R1054-R1367** -- system/battle text (13 resources)
5. **101 ICS resources** (R1911-R2026) -- short event scripts
6. **19 non-type-02 system text** (R34-R49, R720, etc.)

### Estimated Remaining Work
- High priority: ~32 resources, ~4,200 groups
- Medium priority: ~134 resources, ~2,400 groups
- **Total: ~166 resources, ~6,600+ text groups**

---

## Notes

- "Groups" = FFFF-delimited glyph segments. Each group may be one dialogue line,
  a menu label, or an item description. Not all groups contain meaningful text.
- Hit rate = percentage of glyph IDs found in msg_glyph_map.json. Higher = more
  real Japanese text. Values ~40% may indicate mixed text/data.
- Type-01/03/04/05/06/etc. resources flagged by previous scans as having FB00 tags
  are almost entirely false positives (3D model data with coincidental byte patterns).
  Only the 20 known non-type-02 text resources listed above contain real text.
- R2217-R2219 appear to be large lookup tables (item/spell descriptions?) with
  ~2,500 combined groups -- these may represent the single largest untranslated
  text block.
