# R1188 Kanji Position Map

Atlas: `build/textures_to_edit/R1188_CORRECT_dbw512.png` (1024x1024, PSMT4 deswizzled dbw=512)

Grid: 21 columns x 42 rows, 24x24px cells. Glyph ID -> row=ID//21, col=ID%21, pixel=(col*24, row*24).

## Stat Labels

| Kanji | Role | Glyph ID | Cell (x,y) | Tight (x,y,w,h) | Notes |
|-------|------|----------|-------------|------------------|-------|
| 力 | STR (Strength) | 323 | (192,360) | (192,361,24,23) | Also at IDs 346,503,565 |
| 知 | INT1 (Intelligence) | 535 | (240,600) | (240,601,24,23) | Also at ID 1185 (out of atlas) |
| 恵 | INT2 (Intelligence) | 639 | (216,720) | (216,721,24,23) | Also at ID 717 |
| 信 | FTH1 (Faith/Piety) | 308 | (336,336) | (336,337,24,23) | Also at IDs 363,1078 |
| 仰 | FTH2 (Faith/Piety) | 354 | (432,384) | (432,385,24,22) | Also at ID 1514 (out of atlas) |
| 心 | FTH3 (Faith/Piety) | 320 | (120,360) | (120,361,24,23) | Also at ID 458 |
| 生 | VIT1 (Vitality) | 445 | (96,504) | (96,505,24,23) | Also at ID 718 |
| 命 | VIT2 (Vitality) | 696 | (72,792) | (72,794,24,22) | Single ID |
| 敏 | AGI1 (Agility) | 582 | (360,648) | (360,649,24,23) | Single ID |
| 捷 | AGI2 (Agility) | 719 | (120,816) | (120,817,24,23) | Single ID |
| 度 | shared (degree) | 378 | (0,432) | (0,434,24,22) | Also at ID 590 |
| 幸 | LCK1 (Luck) | 460 | (456,504) | (456,505,24,23) | Also at ID 720 |
| 運 | LCK2 (Luck) | 721 | (168,816) | (168,817,24,23) | Single ID |

## Chargen UI Labels

| Kanji | Role | Glyph ID | Cell (x,y) | Tight (x,y,w,h) | Notes |
|-------|------|----------|-------------|------------------|-------|
| 性 | shared (nature) | 511 | (168,576) | (168,577,24,23) | Also at IDs 516,785 |
| 別 | gender | 512 | (192,576) | (192,577,24,23) | Single ID |
| 種 | race1 | 513 | (216,576) | (216,577,24,23) | Also at ID 967 (out of atlas) |
| 族 | race2 | 514 | (240,576) | (240,577,24,23) | Single ID |
| 属 | align | 515 | (264,576) | (264,577,24,23) | Also at ID 593 |
| 職 | class1 | 504 | (0,576) | (0,577,24,23) | Single ID |
| 業 | class2 | 517 | (312,576) | (312,577,24,23) | Single ID |
| 新 | new1 | 498 | (360,552) | (360,553,24,23) | Single ID |
| 規 | new2 | N/A | N/A | N/A | NOT in msg_glyph_map; rendered via EXE banner struct (R1272 tile IDs 721-722) |
| 登 | reg1 | 491 | (192,552) | (192,553,24,23) | Single ID |
| 録 | reg2 | 492 | (216,552) | (216,553,24,23) | Single ID |
| 男 | male | 518 | (336,576) | (336,577,24,22) | Single ID |
| 女 | female | 349 | (312,384) | (312,384,24,24) | Also at ID 418 |

## Key Findings

1. **Grid confirmed**: 24x24px cells, 21 columns, glyph_id = row*21 + col.
2. **25 of 26 kanji mapped** with exact pixel coordinates.
3. **規 (new2) is missing** from msg_glyph_map.json entirely. It is rendered via the EXE banner mechanism (R1272 font tile IDs 721-722, patched in `build/patch_exe.py` Patch 4). It does NOT have a standalone position in R1188.
4. **Duplicate glyph IDs**: Many kanji appear at multiple glyph IDs (力 has 4 copies). The first in-atlas ID with actual pixels is used as the primary.
5. **Out-of-atlas IDs**: Some secondary IDs (1078, 1185, 1514, 967) exceed row 41 (y>1007) and fall outside the visible 1024px atlas height. These have no pixels.
6. **Chargen cluster**: 性別種族属 are consecutive IDs 511-515, all at y=576 (row 24). 職 and 業 are nearby at IDs 504 and 517. This cluster was clearly assigned together for the chargen screen.

## JSON Output

Full data saved to: `data/r1188_kanji_positions.json`
