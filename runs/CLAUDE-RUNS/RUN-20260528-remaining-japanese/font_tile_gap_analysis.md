# Font Tile Gap Analysis: R1272 Menu Label Coverage

**Date:** 2026-05-28
**Purpose:** Identify glyph IDs used by the EXE menu table but not covered by `data/menu_labels.csv`

## Summary

| Category | Count |
|----------|-------|
| CSV-covered glyph IDs (entries 0-105) | 184 |
| Gap glyph IDs (entries 106-159) | 62 |
| **Total menu table glyph IDs** | **246** |

The menu button table at EXE offset `0x3C3000` extends to entry 159 (`0x3C52C8`), but `menu_labels.csv` only covers entries 0-105. Entries 106-159 contain **33 unique button pairs** referencing **62 additional glyph IDs** that need font tile replacement.

## Atlas Capacity

- R1272 PNG is 256x512 (21x42 grid = 882 cells, IDs 0-881)
- R1272 raw data is 67,584 bytes = 256x528 at 4bpp (21x44 grid = 924 cells, IDs 0-923)
- The PNG only shows the first 42 rows; 2 additional rows exist in raw data (IDs 882-923)
- 8 gap glyph IDs (924-931) exceed even the extended atlas; these may reside in row 44+ or use a wrap/overflow mechanism

## Gap Entries by Range

### In Original Atlas (IDs 867-881) -- 15 glyphs

These are in the last row of the visible atlas. Already within the 882-cell range shown in the PNG.

| Glyph ID | Kanji | Pair Partner | 2-Kanji Label | Meaning | English | Strategy |
|----------|-------|-------------|---------------|---------|---------|----------|
| 867 | 助 | 868 | 助連 | help/assist | assist | tile_pair |
| 868 | 連 | 867 | 助連 | assist-link | assist | tile_pair |
| 869 | 携 | 870 | 携法 | co-op method | co-op | tile_pair |
| 870 | 法 | 869 | 携法 | co-op method | co-op | tile_pair |
| 871 | 売 | 872 | 売礼 | sell/gratitude | sell | tile_pair |
| 872 | 礼 | 871 | 売礼 | sell/gratitude | sell | tile_pair |
| 873 | 置 | 874 | 置願 | place/wish | set up | tile_pair |
| 874 | 願 | 873 | 置願 | place/wish | set up | tile_pair |
| 875 | 旗 | 876 | 旗錠 | flag/lock | flag | tile_pair |
| 876 | 錠 | 875 | 旗錠 | flag/lock | flag | tile_pair |
| 877 | 札 | 878 | 札募 | bill/recruit | recruit | tile_pair |
| 878 | 募 | 877 | 札募 | bill/recruit | recruit | tile_pair |
| 879 | 更 | 880 | 更何 | renew/what | renew | tile_pair |
| 880 | 何 | 879 | 更何 | renew/what | renew | tile_pair |
| 881 | 用 | 882 | 用雑 | use/misc | misc | tile_pair |

### In Extended Atlas (IDs 882-923) -- 39 glyphs

These are in the 2 extra rows of the raw texture data (not visible in PNG). The generate_font_atlas pipeline must be updated to write these rows.

| Glyph ID | Kanji | Pair Partner | 2-Kanji Label | Meaning | English | Strategy |
|----------|-------|-------------|---------------|---------|---------|----------|
| 882 | 雑 | 881 | 用雑 | use/misc | misc | tile_pair |
| 883 | 教 | 884 | 教会 | church | church | tile_pair |
| 884 | 会 | 883 | 教会 | church | church | tile_pair |
| 885 | 寺 | 886 | 寺修 | temple/repair | temple | tile_pair |
| 886 | 修 | 885 | 寺修 | temple/repair | temple | tile_pair |
| 887 | 階 | 888 | 階奉 | floor/offering | floor | tile_pair |
| 888 | 奉 | 887 | 階奉 | floor/offering | floor | tile_pair |
| 889 | 達 | 890 | 達越 | reach/surpass | level up | tile_pair |
| 890 | 越 | 889 | 達越 | reach/surpass | level up | tile_pair |
| 891 | 療 | 892 | 療頼 | heal/request | cure | tile_pair |
| 892 | 頼 | 891 | 療頼 | heal/request | cure | tile_pair |
| 893 | 潜 | 894 | 潜級 | dive/rank | rank | tile_pair |
| 894 | 級 | 893 | 潜級 | dive/rank | rank | tile_pair |
| 895 | 早 | 896 | 早好 | fast/like | like | tile_pair |
| 896 | 好 | 895 | 早好 | fast/like | like | tile_pair |
| 897 | 嫌 | 898 | 嫌杯 | dislike/cup | dislike | tile_pair |
| 898 | 杯 | 897 | 嫌杯 | dislike/cup | dislike | tile_pair |
| 902 | 受 | 903 | 受葉 | accept/leaf | accept | tile_pair |
| 903 | 葉 | 902 | 受葉 | accept/leaf | accept | tile_pair |
| 904 | 商 | 905 | 商売 | commerce/sell | trade | tile_pair |
| 905 | 売 | 904 | 商売 | commerce/sell | trade | tile_pair |
| 906 | 練 | 907 | 練平 | train/level | train | tile_pair |
| 907 | 平 | 906 | 練平 | train/level | train | tile_pair |
| 908 | 残 | 909 | 残念 | regret/pity | sorry | tile_pair |
| 909 | 念 | 908 | 残念 | regret/pity | sorry | tile_pair |
| 910 | 景 | 911 | 景整 | scene/arrange | display | tile_pair |
| 911 | 整 | 910 | 景整 | scene/arrange | display | tile_pair |
| 912 | 表 | 913 | 表調 | display/tune | status | tile_pair |
| 913 | 調 | 912 | 表調 | display/tune | status | tile_pair |
| 914 | 集 | 915 | 集遺 | gather/relic | relics | tile_pair |
| 915 | 遺 | 914 | 集遺 | gather/relic | relics | tile_pair |
| 916 | 跡 | 917 | 跡略 | trace/strategy | ruins | tile_pair |
| 917 | 略 | 916 | 跡略 | trace/strategy | ruins | tile_pair |
| 918 | 遠 | 919 | 遠朽 | far/decay | ancient | tile_pair |
| 919 | 朽 | 918 | 遠朽 | far/decay | ancient | tile_pair |
| 920 | 待 | 921 | 待忠 | wait/loyal | loyal | tile_pair |
| 921 | 忠 | 920 | 待忠 | wait/loyal | loyal | tile_pair |
| 922 | 実 | (single) | 実 | truth/real | real | abbrev |
| 923 | 戦 | (single) | 戦 | battle | war | abbrev |

### Beyond Atlas (IDs 924-931) -- 8 glyphs

These IDs exceed the 924-cell atlas. They likely wrap to extended texture rows or use overflow cells. The rendering pipeline must handle these.

| Glyph ID | Kanji | Pair Partner | 2-Kanji Label | Meaning | English | Strategy |
|----------|-------|-------------|---------------|---------|---------|----------|
| 924 | ? | (single) | ? | unknown | ? | abbrev |
| 925 | 報 | (single) | 報 | report/reward | report | abbrev |
| 926 | 酬 | 927 | 酬続 | reward/continue | reward | tile_pair |
| 927 | 続 | 926 | 酬続 | reward/continue | reward | tile_pair |
| 928 | 設 | 929 | 設作 | build/make | build | tile_pair |
| 929 | 作 | 928 | 設作 | build/make | build | tile_pair |
| 930 | 取 | 931 | 取退 | take/retreat | take | tile_pair |
| 931 | 退 | 930 | 取退 | take/retreat | take | tile_pair |

## Context Analysis

Based on position in the table and cross-reference with `translations_menus.json`:

- **Entries 106-107** (assist, co-op): Likely party management / alleid coordination menus
- **Entries 108-115** (sell, set up, flag, recruit, renew, misc, church, temple): Shop management and town service submenus -- Vigger Shop and church operations
- **Entries 124-127** (floor, level up, cure, rank): Dungeon/character progression menus
- **Entries 129-130** (like, dislike): Personality/affinity system (used 5x each including duplicates)
- **Entries 131-137** (accept, trade, train, sorry, display, status, relics): Quest board and knight order menus
- **Entries 149-152** (ruins, ancient, loyal, display): Knight order / Automata storyline menus (matches R44 content about "ancient ruins" and "loyal warrior")
- **Entries 153-156** (real, battle, ?, report): Single-kanji status indicators
- **Entries 157-159** (reward, build, take): Quest reward and crafting menus

## Duplicate Usage

Several pairs appear multiple times in the table (different screen contexts):

| Pair | Meaning | Occurrences | Entry IDs |
|------|---------|-------------|-----------|
| 897,898 (dislike) | sorry/dislike | 5 | 130, 139-142 |
| 908,909 (sorry) | regret/pity | 5 | 134, 143-146 |
| 902,903 (accept) | accept | 2 | 131, 138 |
| 910,911 (display) | scene/arrange | 2 | 135, 152 |
| 785,786 (trait) | personality | 2 | 147, 148 (already in CSV) |

## Implementation Requirements

### 1. Extend menu_labels.csv
Add entries 106-159 to the CSV with English translations and strategies.

### 2. Extend Font Atlas
The `generate_font_atlas.py` pipeline currently writes 882 cells (21x42). It must be updated to write at least 932 cells (21x45 = 945 cells) to cover IDs up to 931. The raw texture buffer has room for 924 cells (21x44 = rows 0-43). IDs 924-931 require either:
- Expanding the texture to 45+ rows (21x45 = 256x540 at 4bpp = 69,120 bytes)
- Or mapping these IDs to unused cells within the existing 924

### 3. Handle Extended Rows in PNG Export
The `R1272_psmt4_deswizzled.png` (256x512) must be expanded to 256x540 (or at least 256x528) to show all cells used by the menu table.

### 4. Total Font Tiles After Gap Fill
- Current: 184 tiles (IDs 683-866)
- Gap: 62 new tiles (IDs 867-931)
- **New total: 246 font tiles**

## Missing Glyph IDs (899-901)

The glyph map contains entries for IDs 899 (掲), 900 (板), 901 (引) but these are NOT referenced in the menu table. They may be used elsewhere or are unused. No font tiles needed for these at this time.
