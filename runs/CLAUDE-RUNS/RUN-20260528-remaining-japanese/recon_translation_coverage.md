# Translation Coverage Audit - Busin 0: Wizardry Alternative Neo

Date: 2026-05-28 (updated)

---

## Executive Summary

| Category | Total | Translated | Untranslated | Coverage |
|----------|-------|------------|--------------|----------|
| PACKDATA resources (all) | 2,883 | -- | -- | -- |
| Type-02 (scene/event) w/ dialogue | 510 | 124 | 381 (+ 5 false-positive) | 24.3% |
| Type-01 (MSG glyph) translated | 1,642 | 20 | see below | ~1.2% by count |
| Type-2 translated messages | -- | 13,112 | -- | -- |
| Type-1 translated messages | -- | 1,444 | -- | -- |

**Bottom line**: 124 of 510 type-02 dialogue resources have translations (24.3%). 20 of ~1,642 type-01 MSG resources have translations, but those 20 cover the core menus/items/stats (R34-R49 plus R1053, R1908, R2124, R2654). The vast majority of type-01 resources are 3D model/binary data that happen to have MSG markers but no real text.

---

## Type-02 Scene/Event Resources (Dialogue)

### What is translated (124 resources, 13,112 messages)

| Batch File | Messages | Translated | Resources |
|------------|----------|------------|-----------|
| batch_01.json | 1,989 | 1,989 | R1196, R1197 |
| batch_02.json | 936 | 936 | R1199, R1200, R1201, R1202 |
| batch_03.json | 1,580 | 1,580 | R1203 |
| batch_04.json | 1,833 | 1,833 | R1204, R1205 |
| batch_05.json | 1,761 | 1,761 | R1206, R1207 |
| batch_06.json | 1,484 | 1,484 | R1208, R1209 |
| batch_07.json | 1,368 | 1,368 | R1210, R1211 |
| batch_08.json | 750 | 750 | R1212, R1213 |
| batch_09.json | 935 | 935 | R1353, R1354 |
| batch_10.json | 137 | 137 | 48 resources (R677-R1099) |
| batch_11.json | 114 | 114 | 45 resources (R1105-R2653) |
| batch_gap1347.json | 131 | 131 | R1347, R1348, R1349, R1351, R1352, R1355 |
| batch_gap681.json | 1 | 0 | (metadata-only: R681/683/687/691/697 confirmed as binary, no dialogue) |
| batch_gap989.json | 3 | 3 | R989, R990, R1034 |
| batch_intro.json | 3 | 3 | R1193, R1194 |
| batch_r1198.json | 88 | 88 | R1198 |

**1 untranslated message**: batch_gap681.json has 1 entry that is a metadata comment, not a real message.

### What is NOT translated (381 resources, ~83,733 messages)

#### Large resources (500+ messages) - 37 resources, 64,298 messages

Many of these have very high msg_count but low line_count, suggesting most "messages" are binary/structural data, not translatable dialogue.

| Resource | Msgs | Dialogue Lines | Notes |
|----------|------|----------------|-------|
| R1094 | 9,953 | 8 | Likely mostly data |
| R1056 | 7,248 | 42 | Likely mostly data |
| R2659 | 6,276 | 439 | **Significant dialogue** |
| R1090 | 3,217 | 79 | Mixed data+dialogue |
| R2211 | 3,032 | 102 | Mixed data+dialogue |
| R2168 | 2,699 | 103 | Mixed data+dialogue |
| R1058 | 2,210 | 12 | Mostly data |
| R2341 | 2,064 | 8 | Mostly data |
| R1078 | 2,011 | 23 | Mostly data |
| R1148 | 1,843 | 181 | **Significant dialogue** |
| R2189 | 1,605 | 35 | Mixed |
| R1134 | 1,515 | 110 | **Significant dialogue** |
| R1126 | 1,480 | 171 | **Significant dialogue** |
| R1142 | 1,245 | 15 | Mostly data |
| R766 | 1,180 | 0 | All data, no dialogue |
| R814 | 1,179 | 0 | All data, no dialogue |
| R818 | 1,178 | 0 | All data, no dialogue |
| R1883 | 974 | 2 | Mostly data |
| R2205 | 943 | 47 | Mixed |
| R2190 | 931 | 31 | Mixed |
| R2191 | 839 | 23 | Mixed |
| R1895 | 819 | 0 | All data, no dialogue |
| R2644 | 816 | 1 | Mostly data |
| R1106 | 797 | 5 | Mostly data |
| R2573 | 765 | 9 | Mostly data |
| R1128 | 759 | 30 | Mixed |
| R2578 | 729 | 16 | Mixed |
| R1120 | 715 | 31 | Mixed |
| R856 | 701 | 9 | Mostly data |
| R1076 | 695 | 10 | Mostly data |
| R1064 | 629 | 12 | Mostly data |
| R914 | 599 | 10 | Mostly data |
| R2624 | 579 | 1 | Mostly data |
| R2587 | 546 | 0 | All data, no dialogue |
| R2165 | 522 | 122 | **Significant dialogue** |
| R772 | 503 | 7 | Mostly data |
| R820 | 502 | 6 | Mostly data |

#### Medium resources (100-499 messages) - 51 resources, 10,768 messages

Resources with 50+ dialogue lines (highest priority):

| Resource | Msgs | Dialogue Lines |
|----------|------|----------------|
| R1937 | 306 | 202 |
| R1954 | 384 | 196 |
| R1926 | 362 | 193 |
| R1955 | 258 | 173 |
| R1914 | 261 | 146 |
| R1944 | 283 | 137 |
| R1932 | 200 | 132 |
| R1938 | 216 | 127 |
| R1945 | 192 | 118 |
| R1924 | 141 | 116 |
| R2021 | 155 | 94 |
| R1919 | 105 | 90 |
| R1918 | 107 | 87 |
| R1951 | 103 | 81 |
| R1949 | 103 | 74 |
| R735 | 155 | 64 |
| R1921 | 114 | 66 |
| R753 | 138 | 55 |
| R1943 | 109 | 59 |
| R1928 | 134 | 58 |
| R1916 | 101 | 51 |

Other medium resources (100-499 msgs, <50 dialogue lines):
R1074(475/37), R2202(431/12), R2574(416/16), R897(398/38), R1082(395/17), R1086(350/43), R2594(332/4), R1108(286/27), R752(274/38), R2172(269/3), R808(248/10), R812(247/9), R806(246/12), R810(243/10), R2175(218/6), R781(211/37), R2577(187/2), R2199(149/7), R2186(146/2), R1068(141/0), R2575(132/0), R2576(132/0), R783(126/30), R773(115/24), R805(115/24), R807(115/24), R809(115/24), R811(115/24), R898(109/2), R727(105/16)

#### Small resources (20-99 messages) - 149 resources, 7,598 messages

#### Tiny resources (1-19 messages) - 144 resources, 1,069 messages

### Resources with 0 dialogue lines

109 resources have msg_count > 0 but line_count = 0. These likely contain only binary/structural data with FFFF markers that were misidentified as MSG entries. They may not need translation.

---

## Type-01 MSG Glyph Resources (Menus/Items/Stats)

### Translated (20 resources, 1,444 messages)

| File | Messages | Resources |
|------|----------|-----------|
| chunk_00_translated.json | 113 | R34, R35, R36 |
| chunk_01_translated.json | 113 | R36, R37, R38 |
| chunk_02_translated.json | 113 | R38 |
| chunk_03_translated.json | 113 | R38, R39 |
| chunk_04_translated.json | 113 | R39, R40, R41, R42, R43 |
| chunk_05_translated.json | 113 | R43, R44, R45 |
| chunk_06_translated.json | 113 | R45 |
| chunk_07_translated.json | 113 | R45, R46, R47, R48 |
| chunk_08_translated.json | 113 | R48, R49 |
| chunk_09_translated.json | 112 | R49, R1053, R1908, R2124, R2654 |
| chunk_r37_extra.json | 111 | R37 |
| chunk_r38_fix.json | 178 | R38 |
| chunk_r43_fix.json | 26 | R43 |

Resources covered: R34-R49, R1053, R1908, R2124, R2654

These 20 resources contain the core game text: menu labels, item names, spell names, monster names, stat labels, shop/church text.

### Untranslated type-01 with real text (60 resources)

Per remaining_real_text.json, 60 type-01 resources contain actual decodable Japanese text that is not yet translated:

**Large type-01 (dungeon data, R2087-R2097)**: 11 resources, enormous files (7-14 MB each), 907-2758 msgs each. These are dungeon map containers that embed MSG text for in-dungeon labels/descriptions.

**Medium type-01 (R1283-R1343 range)**: ~15 resources, 264KB each, ~200-450 msgs. Likely dungeon floor data with embedded text.

**Small type-01 (R2817-R2866 range)**: ~28 resources, 67KB each. Purpose unclear but contain glyph-indexed text.

**Others**: R758, R838, R850, R899, R1138, R2105, R2119, R2121, R2122, R2418, R2791

Full list: R758, R838, R850, R899, R1138, R1283, R1285, R1286, R1289, R1295, R1317, R1322, R1327, R1329, R1330, R1333, R1336, R1337, R1342, R1343, R2087, R2088, R2089, R2090, R2091, R2092, R2093, R2094, R2095, R2096, R2097, R2105, R2119, R2121, R2122, R2418, R2791, R2817, R2819, R2820, R2821, R2822, R2823, R2824, R2825, R2826, R2827, R2828, R2835, R2836, R2840, R2841, R2842, R2854, R2855, R2856, R2858, R2860, R2863, R2866

### Untranslated type-01 without real text (~1,562 resources)

The remaining ~1,562 type-01 resources are 3D models, textures, binary data, or structural data that happen to share type_code=1 but contain no translatable text.

---

## Type-15/20/44 Variant MSG Resources

| Type | Resource | Size | Status |
|------|----------|------|--------|
| 15 | R39 | 2,462 | TRANSLATED |
| 15 | R2129 | 326,612 | NOT translated |
| 15 | R2139 | 68 | NOT translated (tiny, likely no text) |
| 15 | R2881 | 1,640 | NOT translated |
| 20 | R34 | 972 | TRANSLATED |
| 20 | R1186 | 500,328 | NOT translated |
| 20 | R1892 | 304 | NOT translated (tiny) |
| 44 | R2654 | 5,666 | TRANSLATED |

R2129 (327KB, type-15) and R1186 (500KB, type-20) are the notable untranslated variant resources.

---

## Gap/Fix Translations Status

| File | Purpose | Status |
|------|---------|--------|
| batch_gap1347.json | R1347-R1355 gap | Done (R1347, R1348, R1349, R1351, R1352, R1355 = 131 msgs) |
| batch_gap681.json | R681/683/687/691/697 | Confirmed as binary/no dialogue |
| batch_gap989.json | R989/990/1034 gap | Done (3 msgs) |
| batch_r1198.json | R1198 | Done (88 msgs) |
| chunk_r37_extra.json | R37 extra entries | Done (111 msgs) |
| chunk_r38_fix.json | R38 corrections | Done (178 msgs) |
| chunk_r43_fix.json | R43 corrections | Done (26 msgs) |

Note: R1350 is NOT in batch_gap1347.json (missing from the 1347-1355 range).

---

## Priority Untranslated Resources

### Tier 1: High dialogue content (50+ dialogue lines, untranslated)

These resources have the most actual dialogue and should be translated first:

| Resource | Dialogue Lines | Total Msgs |
|----------|---------------|------------|
| R2659 | 439 | 6,276 |
| R1937 | 202 | 306 |
| R1954 | 196 | 384 |
| R1926 | 193 | 362 |
| R1148 | 181 | 1,843 |
| R1955 | 173 | 258 |
| R1126 | 171 | 1,480 |
| R1914 | 146 | 261 |
| R1944 | 137 | 283 |
| R1932 | 132 | 200 |
| R1938 | 127 | 216 |
| R2165 | 122 | 522 |
| R1945 | 118 | 192 |
| R1924 | 116 | 141 |
| R1134 | 110 | 1,515 |
| R2168 | 103 | 2,699 |
| R2211 | 102 | 3,032 |
| R2021 | 94 | 155 |
| R1919 | 90 | 105 |
| R1918 | 87 | 107 |
| R1951 | 81 | 103 |
| R1090 | 79 | 3,217 |
| R1949 | 74 | 103 |
| R35 | 69 | 37 |
| R1921 | 66 | 114 |
| R1923 | 65 | 93 |
| R735 | 64 | 155 |
| R2002 | 64 | 74 |
| R1917 | 62 | 89 |
| R1920 | 61 | 98 |
| R1943 | 59 | 109 |
| R1928 | 58 | 134 |
| R753 | 55 | 138 |
| R1916 | 51 | 101 |

**Total Tier 1: 34 resources, ~3,950 dialogue lines**

### Tier 2: Moderate dialogue (20-49 lines)

~62 resources with 20-49 dialogue lines each.

### Tier 3: Low dialogue (1-19 lines)

~176 resources with 1-19 dialogue lines each.

### Tier 4: Zero-line resources (109 resources)

Resources with MSG markers but 0 identified dialogue lines. Likely binary/structural data, probably do not need translation. Should be audited to confirm.

---

## Full Untranslated Type-02 Resource List (381 resources)

R29(2/3), R30(3/0), R31(4/1), R35(37/69), R675(22/8), R679(15/7), R680(8/0), R684(14/0), R685(12/8), R686(16/0), R688(35/0), R689(91/5), R693(82/0), R694(22/0), R695(2/5), R698(24/0), R699(8/7), R701(79/18), R703(84/9), R704(8/0), R705(5/6), R706(41/10), R707(34/0), R708(83/3), R709(7/2), R711(6/0), R713(6/0), R714(8/4), R716(5/3), R717(6/0), R718(3/0), R721(6/2), R723(7/0), R724(7/0), R725(9/0), R727(105/16), R729(8/0), R730(3/0), R731(3/5), R732(88/25), R733(36/0), R734(61/6), R735(155/64), R737(10/0), R738(6/0), R739(7/5), R745(3/2), R749(4/0), R751(38/11), R752(274/38), R753(138/55), R754(12/3), R755(4/0), R756(4/0), R759(7/0), R760(6/0), R761(6/0), R762(48/5), R763(93/0), R765(17/0), R766(1180/0), R767(72/0), R768(69/3), R770(5/0), R771(6/1), R772(503/7), R773(115/24), R774(7/0), R775(6/0), R776(6/0), R777(6/0), R778(6/0), R779(5/4), R781(211/37), R782(3/4), R783(126/30), R788(5/0), R800(6/0), R802(6/0), R804(6/0), R805(115/24), R806(246/12), R807(115/24), R808(248/10), R809(115/24), R810(243/10), R811(115/24), R812(247/9), R813(79/2), R814(1179/0), R815(3/0), R817(3/0), R818(1178/0), R819(3/0), R820(502/6), R821(3/0), R822(3/0), R823(3/0), R824(5/2), R825(3/0), R826(3/0), R827(3/0), R829(3/0), R831(3/0), R832(3/0), R833(3/0), R834(3/0), R835(3/0), R836(5/0), R841(3/0), R842(3/0), R843(3/0), R845(3/0), R846(3/0), R847(3/0), R849(3/0), R851(3/0), R853(5/0), R854(4/0), R855(5/2), R856(701/9), R857(4/0), R858(3/0), R859(3/0), R861(4/0), R863(4/0), R865(4/0), R867(4/0), R869(4/0), R887(4/0), R888(5/0), R890(3/0), R897(398/38), R898(109/2), R902(3/0), R903(3/0), R906(3/3), R907(3/0), R908(3/3), R909(3/3), R910(3/0), R911(3/0), R912(3/3), R913(3/3), R914(599/10), R915(83/8), R916(3/3), R918(3/3), R923(3/3), R924(3/3), R925(3/3), R931(5/2), R1055(85/20), R1056(7248/42), R1058(2210/12), R1059(93/0), R1060(92/0), R1062(93/14), R1063(86/13), R1064(629/12), R1065(87/7), R1066(87/0), R1067(83/0), R1068(141/0), R1069(84/0), R1070(86/0), R1071(85/0), R1074(475/37), R1076(695/10), R1078(2011/23), R1079(88/5), R1080(85/0), R1082(395/17), R1085(85/4), R1086(350/43), R1087(87/0), R1088(86/0), R1089(89/0), R1090(3217/79), R1092(85/0), R1094(9953/8), R1095(86/0), R1096(89/0), R1100(86/0), R1103(85/8), R1106(797/5), R1107(85/0), R1108(286/27), R1116(17/3), R1117(18/3), R1118(17/3), R1120(715/31), R1124(29/3), R1126(1480/171), R1127(21/3), R1128(759/30), R1132(30/3), R1134(1515/110), R1137(30/3), R1142(1245/15), R1148(1843/181), R1152(35/3), R1154(31/3), R1163(9/2), R1164(20/5), R1166(12/4), R1167(18/5), R1168(12/4), R1169(18/5), R1171(12/4), R1172(18/5), R1173(12/4), R1187(5/3), R1192(7/2), R1195(3/0), R1214(3/0), R1356(40/17), R1357(63/25), R1883(974/2), R1884(70/1), R1894(75/36), R1895(819/0), R1896(74/30), R1911(83/34), R1913(84/41), R1914(261/146), R1915(78/30), R1916(101/51), R1917(89/62), R1918(107/87), R1919(105/90), R1920(98/61), R1921(114/66), R1922(75/29), R1923(93/65), R1924(141/116), R1925(62/35), R1926(362/193), R1927(79/49), R1928(134/58), R1929(41/11), R1932(200/132), R1937(306/202), R1938(216/127), R1942(76/27), R1943(109/59), R1944(283/137), R1945(192/118), R1946(71/17), R1947(71/19), R1949(103/74), R1950(61/25), R1951(103/81), R1954(384/196), R1955(258/173), R1956(78/36), R1957(68/29), R1958(77/34), R1960(74/44), R1961(71/23), R1962(73/24), R1963(72/33), R1964(66/21), R1965(44/6), R1966(70/28), R1967(71/26), R1968(82/37), R1969(40/2), R1971(82/38), R1973(73/24), R1974(73/31), R1975(73/39), R1976(73/28), R1977(72/26), R1978(71/26), R1979(72/27), R1980(72/28), R1981(73/29), R1982(73/33), R1983(72/29), R1984(73/29), R1985(74/30), R1986(72/31), R1987(72/31), R1988(72/29), R1989(74/33), R1990(72/26), R1991(73/28), R1992(71/24), R1993(72/26), R1994(72/31), R1995(73/27), R1996(80/45), R1997(77/38), R1998(76/38), R1999(87/48), R2000(73/33), R2001(72/30), R2002(74/64), R2004(77/40), R2005(73/26), R2006(72/27), R2007(72/27), R2008(73/30), R2009(72/28), R2010(71/24), R2011(73/30), R2012(72/31), R2013(72/27), R2014(74/31), R2015(72/30), R2016(72/28), R2017(72/30), R2018(71/26), R2019(72/30), R2020(71/23), R2021(155/94), R2022(73/25), R2023(71/26), R2024(76/42), R2025(72/25), R2026(71/23), R2099(75/30), R2158(21/6), R2164(4/1), R2165(522/122), R2168(2699/103), R2171(10/6), R2172(269/3), R2173(8/5), R2175(218/6), R2177(7/0), R2178(7/0), R2179(7/0), R2180(7/0), R2181(7/0), R2182(7/0), R2183(7/0), R2184(7/0), R2185(7/0), R2186(146/2), R2187(7/0), R2188(7/0), R2189(1605/35), R2190(931/31), R2191(839/23), R2192(7/0), R2193(7/0), R2194(7/0), R2195(7/0), R2196(7/0), R2197(7/0), R2199(149/7), R2202(431/12), R2205(943/47), R2211(3032/102), R2215(8/6), R2341(2064/8), R2361(5/3), R2398(5/0), R2572(7/0), R2573(765/9), R2574(416/16), R2575(132/0), R2576(132/0), R2577(187/2), R2578(729/16), R2585(7/2), R2587(546/0), R2594(332/4), R2602(7/2), R2603(7/0), R2604(7/0), R2605(7/0), R2608(7/0), R2612(7/0), R2624(579/1), R2625(7/0), R2632(7/0), R2644(816/1), R2659(6276/439)

Format: R{id}(msgs/dialogue_lines)

---

## Untranslated Type-01 MSG Resources with Real Text (60 resources)

R758, R838, R850, R899, R1138, R1283, R1285, R1286, R1289, R1295, R1317, R1322, R1327, R1329, R1330, R1333, R1336, R1337, R1342, R1343, R2087, R2088, R2089, R2090, R2091, R2092, R2093, R2094, R2095, R2096, R2097, R2105, R2119, R2121, R2122, R2418, R2791, R2817, R2819, R2820, R2821, R2822, R2823, R2824, R2825, R2826, R2827, R2828, R2835, R2836, R2840, R2841, R2842, R2854, R2855, R2856, R2858, R2860, R2863, R2866

These contain glyph-indexed Japanese text but have not been translated. The R2087-R2097 group are large dungeon containers (7-14 MB each). The R2817-R2866 group are smaller (67KB each) and may be dungeon floor labels or UI elements. The R1283-R1343 group (264KB each) appears to be dungeon data with embedded text.

---

## Untranslated Type-15/20 Variant Resources

- R2129 (type-15, 327KB) - likely contains offset-table MSG text
- R1186 (type-20, 500KB) - likely contains offset-table MSG text
- R2881 (type-15, 1.6KB) - small, may have a few entries
- R1892 (type-20, 304 bytes) - tiny, possibly header-only
- R2139 (type-15, 68 bytes) - tiny, likely no text

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total PACKDATA resources | 2,883 |
| Type-02 with dialogue | 510 |
| Type-02 translated | 124 (24.3%) |
| Type-02 untranslated | 381 (+ 5 false-positive binary) |
| Type-02 untranslated dialogue lines | ~7,631 |
| Type-01 translated | 20 (core menus/items) |
| Type-01 with untranslated real text | 60 |
| Type-15/20/44 translated | 3 (R34, R39, R2654) |
| Type-15/20/44 untranslated | 5 (R1186, R1892, R2129, R2139, R2881) |
| Total translated messages | 14,556 (13,112 type-2 + 1,444 type-1) |
| Estimated remaining dialogue lines | ~7,631 (type-2) + unknown (type-1, type-15/20) |

### Coverage by game content area (estimated)

- **Core menus/UI/items/stats**: ~95% (R34-R49 + fixes)
- **Main story dialogue (R1193-R1213)**: ~100%
- **Side events/scenes (R1347-R1355)**: ~85% (R1350 missing)
- **Dungeon events (R1900s-R2026)**: ~5% (only R1912, R1930-R1941, R1948, R1952-R1953, R1959, R1972 done)
- **NPC/shop scenes (R675-R920)**: ~25% (batch_10/11 cover many but most are 1-2 msg stubs)
- **Late-game content (R2100+)**: ~15% (a few resources in batch_11)
- **Dungeon data with embedded text (R1056-R1148, R2087-R2097)**: 0%
