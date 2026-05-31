# Comprehensive EXE Hardcoded Japanese Label Inventory

**Date**: 2026-05-28
**EXE**: `extracted/SLPM_653.78` (4,185,776 bytes)
**Scan range**: Full data section 0x3AB000-0x3FD000
**Method**: 56-byte menu struct signature scan, SJIS string search, glyph-ID cluster detection, code-reference verification

---

## Executive Summary

The EXE contains **161 menu struct records** across 4 contiguous blocks (not 106 as previously documented). Of these, **107 are covered** by `menu_labels.csv` and **48 have labels but are NOT covered** (plus 6 empty/separator records). Additionally, there are **6 SJIS save-slot strings** and **1 glyph-ID cluster** (IDs 1162-1174) that need attention.

**Total remaining Japanese items requiring translation: 55**
- 48 uncovered menu struct records (70 unique label glyph IDs)
- 6 SJIS save-slot display strings
- 1 glyph-ID cluster at 0x3C5320 (13 entries, purpose TBD)

**NO hardcoded Japanese was found for**: battle UI, dungeon HUD, status screen, or equipment screen. These all use MSG resources (R38/R39/R35/R41-R48) which are already handled by the translation pipeline.

---

## 1. Menu Struct Table: TRUE Boundaries

The 56-byte menu struct table is larger than previously documented:

| Block | Offset Range | Records | Status |
|-------|-------------|---------|--------|
| 1 | 0x3C2F58 - 0x3C3738 | 36 | 3 uncovered (idx 47-49) |
| gap | 0x3C3738 - 0x3C3770 | -- | 56 bytes padding |
| 2 | 0x3C3770 - 0x3C3968 | 9 | 1 uncovered (idx 87) |
| gap | 0x3C3968 - 0x3C39A0 | -- | 56 bytes padding |
| 3 | 0x3C39A0 - 0x3C4E30 | 94 | 30 uncovered |
| gap | 0x3C4E30 - 0x3C4E68 | -- | 56 bytes padding |
| 4 | 0x3C4E68 - 0x3C5338 | 22 | 14 uncovered |
| **Total** | 0x3C2F58 - 0x3C5338 | **161** | **48 uncovered with labels** |

The CSV currently covers entries starting at 0x3C3000, missing 3 records before that base and all records after entry ~105.

---

## 2. Uncovered Menu Records by Game Screen

### idx=47 -- Unknown/Special Menu (1 record)

| Offset | Icon | Label 1 | Label 2 | Ref |
|--------|------|---------|---------|-----|
| 0x3C2F58 | 味(604) | 鑑(677) | 異(678) | 噂(477) |

Likely meaning: "Appraise" or "Identify" (鑑=examine, 異=different/unusual). Possibly item identification at shop or guild.

### idx=48 -- Unknown/Special Menu (1 record)

| Offset | Icon | Label 1 | Label 2 | Ref |
|--------|------|---------|---------|-----|
| 0x3C2F90 | 持(605) | 殿(679) | 解(680) | 彼(478) |

Likely meaning: "Release" or "Dismiss" (殿=lord/hall, 解=release/explain). Possibly party member dismissal.

### idx=49 -- Unknown/Special Menu (1 record)

| Offset | Icon | Label 1 | Label 2 | Ref |
|--------|------|---------|---------|-----|
| 0x3C2FC8 | 使(606) | [681] | 功(682) | 対(479) |

Likely meaning: "Achievement" or "Merit" (功=achievement/merit). Glyph 681 is unmapped.

### idx=70 -- Dungeon/Exploration (1 record)

| Offset | Icon | Label 1 | Label 2 | Ref |
|--------|------|---------|---------|-----|
| 0x3C5098 | 振(657) | 跡(916) | 略(917) | 方(601) |

Likely meaning: "Ruins" or "Relics" (跡=traces/ruins, 略=abbreviation/strategy). Linked to dungeon exploration.

### idx=93 -- Personality/Trait Menu (1 record, extends existing group)

| Offset | Icon | Label 1 | Label 2 | Ref |
|--------|------|---------|---------|-----|
| 0x3C4730 | 死(654) | 助(867) | 連(868) | 嫌(569) |

Likely meaning: "Assist" or "Cooperation" (助=help, 連=connect/continuous). Personality trait label.

### idx=96 -- Character Status (2 records)

| Offset | Icon | Label 1 | Label 2 | Ref |
|--------|------|---------|---------|-----|
| 0x3C5028 | 身(671) | 性(785) | 依(786) | 協(599) |
| 0x3C5060 | 振(657) | 性(785) | 依(786) | 進(600) |

Likely meaning: "Disposition" or "Nature" (性=nature, 依=depend). Character personality/alignment display.

### idx=97 -- Unknown (1 record)

| Offset | Icon | Label 1 | Label 2 | Ref |
|--------|------|---------|---------|-----|
| 0x3C4768 | 死(654) | 携(869) | 法(870) | 塔(570) |

Likely meaning: "Carry Law" or "Portable Magic" (携=carry/portable, 法=law/magic). Possibly spell list or item rules.

### idx=98 -- Guild/Quest Board (8 records)

| Offset | Icon | Label 1 | Label 2 | Ref | Likely Meaning |
|--------|------|---------|---------|-----|----------------|
| 0x3C47A0 | 長(660) | 売(871) | 礼(872) | - | Sell/Thanks |
| 0x3C47D8 | NONE | 置(873) | 願(874) | - | Place/Wish |
| 0x3C4810 | NONE | 旗(875) | 錠(876) | 護(571) | Banner/Lock |
| 0x3C4848 | 発(661) | 札(877) | 募(878) | 何(572) | Notice/Recruit |
| 0x3C4880 | 発(661) | 更(879) | 何(880) | 宮(573) | Update/What |
| 0x3C48B8 | 発(661) | 用(881) | 雑(882) | 探(574) | Use/Misc |
| 0x3C48F0 | 発(661) | 教(883) | 会(884) | 索(575) | Church/Temple |
| 0x3C4928 | 発(661) | 寺(885) | 修(886) | 同(576) | Temple/Repair |

This is a large cluster related to the guild quest board or town services sub-menu.

### idx=100 -- Floor/Dungeon Level (1 record)

| Offset | Icon | Label 1 | Label 2 | Ref |
|--------|------|---------|---------|-----|
| 0x3C4B20 | NONE | 階(887) | 奉(888) | 受(577) |

Likely meaning: "Floor" + "Dedicate" (階=floor/level, 奉=dedicate/serve). Dungeon floor indicator.

### idx=101 -- Achievement/Rank (1 record)

| Offset | Icon | Label 1 | Label 2 | Ref |
|--------|------|---------|---------|-----|
| 0x3C4B58 | 目(662) | 達(889) | 越(890) | 街(578) |

Likely meaning: "Exceed" or "Surpass" (達=reach, 越=exceed). Level up or rank notification.

### idx=102 -- Healing/Cure (1 record)

| Offset | Icon | Label 1 | Label 2 | Ref |
|--------|------|---------|---------|-----|
| 0x3C4B90 | 丁(663) | 療(891) | 頼(892) | 帰(579) |

Likely meaning: "Heal Request" (療=heal/cure, 頼=request/rely). Church healing service.

### idx=103 -- Rank/Level (1 record)

| Offset | Icon | Label 1 | Label 2 | Ref |
|--------|------|---------|---------|-----|
| 0x3C4BC8 | 元(664) | 潜(893) | 級(894) | 消(580) |

Likely meaning: "Hidden Rank" or "Potential Level" (潜=hidden/latent, 級=rank/grade).

### idx=105 -- Like/Dislike (1 record)

| Offset | Icon | Label 1 | Label 2 | Ref |
|--------|------|---------|---------|-----|
| 0x3C4C38 | NONE | 早(895) | 好(896) | 士(581) |

Likely meaning: "Preference" (早=early/quick, 好=like/prefer). Affinity display.

### idx=106 -- Equipment/Item Details (12 records)

This is the LARGEST uncovered group. Multiple variants using the same label pairs:

| Label Pair | Occurrences | Icons Used | Likely Meaning |
|-----------|-------------|------------|----------------|
| 嫌(897)/杯(898) | 5 | 取,持,関 | "Dislike/Cup" -- item affinity? |
| 残(908)/念(909) | 5 | 用,身,関 | "Regret/Sorry" -- unavailable item? |
| 景(910)/整(911) | 2 | 身,御 | "Scenery/Arrange" -- display/sort? |

These appear to be equipment screen sub-options for sorting, filtering, or item details.

### idx=107 -- Trade/Accept (2 records)

| Offset | Icon | Label 1 | Label 2 | Ref |
|--------|------|---------|---------|-----|
| 0x3C4CA8 | 関(667) | 受(902) | 葉(903) | 前(583) |
| 0x3C50D0 | 世(628) | 遠(918) | 朽(919) | 備(602) |

First: "Accept/Leaf" (受=accept, 葉=leaf/word). Second: "Far/Decay" (遠=far, 朽=decay).

### idx=108 -- Commerce (2 records)

| Offset | Icon | Label 1 | Label 2 | Ref |
|--------|------|---------|---------|-----|
| 0x3C4CE0 | 持(668) | 商(904) | 売(905) | 全(584) |
| 0x3C5108 | 持(668) | 待(920) | 忠(921) | 品(603) |

First: "Commerce/Sell" (商=commerce, 売=sell) -- **SHOP MAIN BUTTON**.
Second: "Wait/Loyal" (待=wait, 忠=loyal) -- **INVENTORY/HOLD**.

### idx=109 -- Training (1 record)

| Offset | Icon | Label 1 | Label 2 | Ref |
|--------|------|---------|---------|-----|
| 0x3C4D18 | 御(669) | 練(906) | 平(907) | 費(585) |

Likely meaning: "Training/Level" (練=practice/train, 平=flat/normal). Training ground option.

### idx=110 -- Display/Status (1 record)

| Offset | Icon | Label 1 | Label 2 | Ref |
|--------|------|---------|---------|-----|
| 0x3C4DC0 | 体(672) | 表(912) | 調(913) | 的(588) |

Likely meaning: "Display/Check" (表=display/table, 調=investigate/tune). Status display toggle.

### idx=111 -- Collection/Relics (1 record)

| Offset | Icon | Label 1 | Label 2 | Ref |
|--------|------|---------|---------|-----|
| 0x3C4DF8 | 意(673) | 集(914) | 遺(915) | 過(589) |

Likely meaning: "Collect/Relics" (集=collect, 遺=bequeath/relic). Item collection or relic finder.

### idx=116 -- System/Config (7 records)

Single-label entries (no second glyph) -- likely system/config keywords:

| Offset | Label | Glyph ID | Likely Meaning |
|--------|-------|----------|----------------|
| 0x3C5178 | 実 | 922 | "Real/Actual" |
| 0x3C51B0 | 戦 | 923 | "Battle" |
| 0x3C51E8 | [unmapped] | 924 | Unknown |
| 0x3C5220 | 報 | 925 | "Report/Reward" |
| 0x3C5258 | 酬/続 | 926/927 | "Reward/Continue" |
| 0x3C5290 | 設/作 | 928/929 | "Settings/Create" |
| 0x3C52C8 | 取/退 | 930/931 | "Take/Retreat" |

These appear to be system-level function labels (save, continue, settings, quit).

---

## 3. SJIS Save Slot Strings (6 strings)

These are the ONLY player-visible SJIS text in the EXE:

| Offset | Bytes | Japanese | English Replacement |
|--------|-------|----------|-------------------|
| 0x3F9370 | 22 | BUSIN0中断データ | BUSIN0 Suspend Data |
| 0x3F9678 | 12 | BUSIN0 | BUSIN0 (keep as-is) |
| 0x3FC720 | 12 | BUSIN0 | BUSIN0 (keep as-is) |
| 0x3FC750 | 20 | BUSIN0データ1 | BUSIN0 Save 1 |
| 0x3FC770 | 20 | BUSIN0データ2 | BUSIN0 Save 2 |
| 0x3FC790 | 20 | BUSIN0データ3 | BUSIN0 Save 3 |

Fullwidth SJIS uses 2 bytes per character; English ASCII fits in less space. Safe to patch in-place.

---

## 4. Glyph-ID Cluster at 0x3C5320 (13 entries)

Immediately after the menu struct table, 13 glyph IDs stored as `(u16 0, u16 glyph_id)`:

| Offset | Glyph ID | Character | Mapped? |
|--------|----------|-----------|---------|
| 0x3C5320 | 1162 | ? | No |
| 0x3C5324 | 1163 | 捨 | Yes |
| 0x3C5328 | 1164 | ? | No |
| 0x3C532C | 1165 | ? | No |
| 0x3C5330 | 1166 | 仕 | Yes |
| 0x3C5334 | 1167 | ? | No |
| 0x3C5338 | 1168 | ? | No |
| 0x3C533C | 1169 | ? | No |
| 0x3C5340 | 1170 | ? | No |
| 0x3C5344 | 1171 | ? | No |
| 0x3C5348 | 1172 | 鍵 | Yes |
| 0x3C534C | 1173 | 奥 | Yes |
| 0x3C5350 | 1174 | 狂 | Yes |

These are in the 1100+ glyph range (above normal kanji range 95-882). They likely reference composite label tiles on a secondary font atlas. Purpose unclear -- could be dungeon interaction labels (捨=discard, 仕=serve, 鍵=key, 奥=depths, 狂=madness). Followed by a VA pointer table at 0x3C5360.

---

## 5. Confirmed NOT Hardcoded in EXE (per-screen verification)

| Game Screen | Source | Evidence |
|-------------|--------|----------|
| **Battle UI** | MSG resources (R47) | 27 SJIS battle terms searched, 19 glyph-ID sequences searched -- zero player-visible hits. All battle text comes from MSG resources. |
| **Status Screen** | R38 (chargen/status MSG) | All stat labels (HP, STR, INT, etc.), race/class/alignment/personality labels are in R38, translated in chunk_r38_fix.json. |
| **Equipment Screen** | R39 (equipment MSG) | All equipment names, descriptions, and action labels come from R39. The EXE has equipment TYPE ICON glyph IDs (2036-2047) but these are sprite-atlas references, not text. |
| **Camp/Save Menu** | R35 (camp MSG) | Save, Load, Options, Return to Title -- all in R35, translated. |
| **Shop UI** | R41-R48 (shop MSGs) | All shop dialogue and menu text comes from MSG resources, translated. |
| **Dungeon HUD** | Menu struct system | Floor/compass/party HUD uses the menu struct table (covered above). |
| **Name Entry Screen** | R1188 texture + EXE tables 2A/2B/2E | Keyboard grids in EXE (already documented). Tab labels are bitmap-font references (6400+) rendered from R1188 texture atlas. |
| **Debug/TTY** | 0x3EE9D0-0x3F3500 | 300+ strings, all printf debug output. NOT player-visible. Includes battle debug, memory errors, developer notes. |

---

## 6. Priority Action Items

### HIGH PRIORITY (48 items, blocks visible Japanese removal)

1. **Add 48 uncovered menu struct records to `menu_labels.csv`** (entries at idx 47-49, 70, 93, 96-98, 100-111, 116)
2. **Render 70 new font tiles** for glyph IDs 677-682, 785-786, 867-931 with English text
3. These cover: guild sub-menus, shop buttons, personality traits, dungeon options, equipment sorting, system config

### MEDIUM PRIORITY (6 items)

4. **Patch 6 SJIS save-slot strings** at 0x3F9370, 0x3FC720-0x3FC790 with English equivalents
5. **Investigate glyph cluster** at 0x3C5320 (13 entries, glyph IDs 1162-1174) -- determine if player-visible

### LOW PRIORITY (already documented elsewhere)

6. Name entry keyboard restructuring (tables 2A/2B at 0x3C83C0-0x3C9DA0)
7. Equipment type icon sprites (glyph IDs 2036-2047, separate texture atlas)
8. NPC names "Emilia"/"Lute" at 0x3C93B0 (2 strings, trivial patch)
9. Bitmap tab labels (glyph IDs 6400-6409 in R1188 texture)

---

## 7. New Glyph IDs Requiring Font Tiles

70 unique label glyph IDs not yet in `menu_labels.csv`:

```
677, 678, 679, 680, 681, 682,                    # idx 47-49 (3 records)
785, 786,                                          # idx 96 (status)
867, 868, 869, 870,                                # idx 93, 97
871, 872, 873, 874, 875, 876, 877, 878,           # idx 98 (guild)
879, 880, 881, 882, 883, 884, 885, 886,           # idx 98 (guild cont.)
887, 888,                                          # idx 100 (floor)
889, 890,                                          # idx 101 (rank)
891, 892,                                          # idx 102 (heal)
893, 894,                                          # idx 103 (level)
895, 896,                                          # idx 105 (preference)
897, 898, 902, 903,                                # idx 106, 107 (items)
904, 905, 906, 907, 908, 909, 910, 911,           # idx 106-109 (shop/train)
912, 913, 914, 915, 916, 917, 918, 919,           # idx 110-111, 70 (display/relics)
920, 921, 922, 923, 924, 925, 926, 927,           # idx 108, 116 (system)
928, 929, 930, 931                                 # idx 116 (system)
```

Note: Glyph IDs 899-901 are not referenced by any uncovered record (gap in numbering).
