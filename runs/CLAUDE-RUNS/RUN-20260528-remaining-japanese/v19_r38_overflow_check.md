# R38 v19 ISO - Complete Overflow Check

**Source:** `C:/Programmieren/wizardrytranslation/build/BUSIN0_EN_v19.iso`
**Total messages:** 189
**Date:** 2026-05-28

## Overflow Flags Summary

Messages with >3 lines OR any line >18 chars: **49**

| MSG | Lines | Max Line Len | Longest Line Content | Flag |
|-----|-------|-------------|---------------------|------|
| 0 | 1 | 1187 | `ぅ 格 息 響 有 替 国 若 声 唱 造 挨 募 級 跡 取 店 袋 恩 宣 滅 奪 [1052]` | L1=1187ch |
| 88 | 4 | 14 | `to town often.` | LINES=4 |
| 90 | 5 | 16 | `angry if loot is` | LINES=5 |
| 92 | 4 | 17 | `loves big groups.` | LINES=4 |
| 96 | 4 | 18 | `believes in mystic` | LINES=4 |
| 100 | 5 | 13 | `obsessed with` | LINES=5 |
| 101 | 4 | 18 | `dreads the undead.` | LINES=4 |
| 102 | 4 | 17 | `values recycling.` | LINES=4 |
| 103 | 4 | 16 | `no need for men.` | LINES=4 |
| 104 | 5 | 14 | `believes women` | LINES=5 |
| 105 | 5 | 13 | `won't forgive` | LINES=5 |
| 108 | 4 | 16 | `hates bloodshed.` | LINES=4 |
| 109 | 4 | 15 | `short-tempered.` | LINES=4 |
| 111 | 4 | 18 | `bored by same sex.` | LINES=4 |
| 112 | 4 | 16 | `vain narcissist.` | LINES=4 |
| 113 | 4 | 17 | `happy then angry.` | LINES=4 |
| 114 | 5 | 11 | `hates being` | LINES=5 |
| 115 | 4 | 18 | `shuns other races.` | LINES=4 |
| 116 | 4 | 15 | `happy if others` | LINES=4 |
| 118 | 4 | 18 | `stats. Men=strong,` | LINES=4 |
| 119 | 4 | 17 | `Human: High faith` | LINES=4 |
| 120 | 5 | 15 | `Elf: High INT &` | LINES=5 |
| 121 | 4 | 17 | `Gnome: High faith` | LINES=4 |
| 122 | 4 | 16 | `strong with deep` | LINES=4 |
| 123 | 4 | 17 | `Hobbit: Small but` | LINES=4 |
| 124 | 4 | 18 | `turn Evil. FIG MAG` | LINES=4 |
| 125 | 4 | 16 | `Neutral=no bias.` | LINES=4 |
| 126 | 4 | 18 | `Evil=self-serving.` | LINES=4 |
| 127 | 4 | 16 | `cannot learn any` | LINES=4 |
| 128 | 4 | 17 | `Lowers trap level` | LINES=4 |
| 129 | 4 | 18 | `master of sorcery.` | LINES=4 |
| 130 | 4 | 18 | `Holy magic master.` | LINES=4 |
| 131 | 5 | 18 | `instant-kill foes.` | LINES=5 |
| 132 | 5 | 14 | `Learns Sorcery` | LINES=5 |
| 133 | 5 | 17 | `vs undead. Sorc &` | LINES=5 |
| 134 | 4 | 17 | `Dispel vs undead.` | LINES=4 |
| 135 | 4 | 17 | `Sorc & Holy Magic` | LINES=4 |
| 136 | 6 | 14 | `Sorc+Holy Lv3.` | LINES=6 |
| 137 | 4 | 18 | `Staffs & knuckles.` | LINES=4 |
| 138 | 5 | 17 | `Can learn Dispel.` | LINES=5 |
| 139 | 5 | 15 | `equipped items.` | LINES=5 |
| 140 | 4 | 18 | `Great EXP & insta-` | LINES=4 |
| 141 | 5 | 16 | `Dual wields same` | LINES=5 |
| 142 | 5 | 18 | `Longbow. Best trap` | LINES=5 |
| 143 | 4 | 14 | `affects damage` | LINES=4 |
| 144 | 4 | 15 | `affects sorcery` | LINES=4 |
| 145 | 4 | 18 | `affects holy magic` | LINES=4 |
| 146 | 5 | 18 | `status resistance,` | LINES=5 |
| 148 | 5 | 14 | `affects breath` | LINES=5 |

## Descriptions (MSG 87-148) - Chargen Display Detail

These are shown in the character generation description box.
Overflow risk: >3 lines or any line >18 chars.

### MSG 87 [OK]
- Lines: 2, Max line: 7 chars
- L1 ( 7 ch): `evasion`
- L2 ( 0 ch): ``
- Raw: `0045 0056 0041 0053 0049 004F 004E FFFE`

### MSG 88 [**TOO MANY LINES**]
- Lines: 4, Max line: 14 chars
- L1 (13 ch): `bores easily.`
- L2 ( 6 ch): `return`
- L3 (14 ch): `to town often.`
- L4 ( 0 ch): ``
- Raw: `0042 004F 0052 0045 0053 0000 0045 0041 0053 0049 004C 0059 000E FFFE 0052 0045 0054 0055 0052 004E FFFE 0054 004F 0000 0054 004F 0057 004E 0000 004F 0046 0054 0045 004E 000E FFFE`

### MSG 89 [OK]
- Lines: 3, Max line: 18 chars
- L1 (15 ch): `senses spirits.`
- L2 (18 ch): `trembles at death.`
- L3 ( 0 ch): ``
- Raw: `0053 0045 004E 0053 0045 0053 0000 0053 0050 0049 0052 0049 0054 0053 000E FFFE 0054 0052 0045 004D 0042 004C 0045 0053 0000 0041 0054 0000 0044 0045 0041 0054 0048 000E FFFE`

### MSG 90 [**TOO MANY LINES**]
- Lines: 5, Max line: 16 chars
- L1 (14 ch): `lives to hoard`
- L2 ( 5 ch): `gold.`
- L3 (16 ch): `angry if loot is`
- L4 ( 4 ch): `low.`
- L5 ( 0 ch): ``
- Raw: `004C 0049 0056 0045 0053 0000 0054 004F 0000 0048 004F 0041 0052 0044 FFFE 0047 004F 004C 0044 000E FFFE 0041 004E 0047 0052 0059 0000 0049 0046 0000 004C 004F 004F 0054 0000 0049 0053 FFFE 004C 004F`...

### MSG 91 [OK]
- Lines: 3, Max line: 16 chars
- L1 (16 ch): `dislikes crowds.`
- L2 (14 ch): `calmer in few.`
- L3 ( 0 ch): ``
- Raw: `0044 0049 0053 004C 0049 004B 0045 0053 0000 0043 0052 004F 0057 0044 0053 000E FFFE 0043 0041 004C 004D 0045 0052 0000 0049 004E 0000 0046 0045 0057 000E FFFE`

### MSG 92 [**TOO MANY LINES**]
- Lines: 4, Max line: 17 chars
- L1 (17 ch): `loves big groups.`
- L2 (11 ch): `hates small`
- L3 ( 8 ch): `parties.`
- L4 ( 0 ch): ``
- Raw: `004C 004F 0056 0045 0053 0000 0042 0049 0047 0000 0047 0052 004F 0055 0050 0053 000E FFFE 0048 0041 0054 0045 0053 0000 0053 004D 0041 004C 004C FFFE 0050 0041 0052 0054 0049 0045 0053 000E FFFE`

### MSG 93 [OK]
- Lines: 3, Max line: 18 chars
- L1 (18 ch): `can't resist loot.`
- L2 (17 ch): `lives to collect.`
- L3 ( 0 ch): ``
- Raw: `0043 0041 004E 0007 0054 0000 0052 0045 0053 0049 0053 0054 0000 004C 004F 004F 0054 000E FFFE 004C 0049 0056 0045 0053 0000 0054 004F 0000 0043 004F 004C 004C 0045 0043 0054 000E FFFE`

### MSG 94 [OK]
- Lines: 3, Max line: 18 chars
- L1 (18 ch): `distrusts reckless`
- L2 (12 ch): `adventurers.`
- L3 ( 0 ch): ``
- Raw: `0044 0049 0053 0054 0052 0055 0053 0054 0053 0000 0052 0045 0043 004B 004C 0045 0053 0053 FFFE 0041 0044 0056 0045 004E 0054 0055 0052 0045 0052 0053 000E FFFE`

### MSG 95 [OK]
- Lines: 3, Max line: 16 chars
- L1 (13 ch): `fascinated by`
- L2 (16 ch): `monster biology.`
- L3 ( 0 ch): ``
- Raw: `0046 0041 0053 0043 0049 004E 0041 0054 0045 0044 0000 0042 0059 FFFE 004D 004F 004E 0053 0054 0045 0052 0000 0042 0049 004F 004C 004F 0047 0059 000E FFFE`

### MSG 96 [**TOO MANY LINES**]
- Lines: 4, Max line: 18 chars
- L1 (18 ch): `believes in mystic`
- L2 (12 ch): `power. loves`
- L3 ( 6 ch): `magic.`
- L4 ( 0 ch): ``
- Raw: `0042 0045 004C 0049 0045 0056 0045 0053 0000 0049 004E 0000 004D 0059 0053 0054 0049 0043 FFFE 0050 004F 0057 0045 0052 000E 0000 004C 004F 0056 0045 0053 FFFE 004D 0041 0047 0049 0043 000E FFFE`

### MSG 97 [OK]
- Lines: 3, Max line: 18 chars
- L1 (16 ch): `skilled warrior.`
- L2 (18 ch): `seeks strong foes.`
- L3 ( 0 ch): ``
- Raw: `0053 004B 0049 004C 004C 0045 0044 0000 0057 0041 0052 0052 0049 004F 0052 000E FFFE 0053 0045 0045 004B 0053 0000 0053 0054 0052 004F 004E 0047 0000 0046 004F 0045 0053 000E FFFE`

### MSG 98 [OK]
- Lines: 3, Max line: 18 chars
- L1 (15 ch): `must adventure.`
- L2 (18 ch): `idleness is agony.`
- L3 ( 0 ch): ``
- Raw: `004D 0055 0053 0054 0000 0041 0044 0056 0045 004E 0054 0055 0052 0045 000E FFFE 0049 0044 004C 0045 004E 0045 0053 0053 0000 0049 0053 0000 0041 0047 004F 004E 0059 000E FFFE`

### MSG 99 [OK]
- Lines: 3, Max line: 16 chars
- L1 (16 ch): `reacts keenly to`
- L2 (14 ch): `sudden events.`
- L3 ( 0 ch): ``
- Raw: `0052 0045 0041 0043 0054 0053 0000 004B 0045 0045 004E 004C 0059 0000 0054 004F FFFE 0053 0055 0044 0044 0045 004E 0000 0045 0056 0045 004E 0054 0053 000E FFFE`

### MSG 100 [**TOO MANY LINES**]
- Lines: 5, Max line: 13 chars
- L1 (13 ch): `obsessed with`
- L2 ( 6 ch): `traps.`
- L3 (10 ch): `crushed by`
- L4 ( 8 ch): `success.`
- L5 ( 0 ch): ``
- Raw: `004F 0042 0053 0045 0053 0053 0045 0044 0000 0057 0049 0054 0048 FFFE 0054 0052 0041 0050 0053 000E FFFE 0043 0052 0055 0053 0048 0045 0044 0000 0042 0059 FFFE 0053 0055 0043 0043 0045 0053 0053 000E`...

### MSG 101 [**TOO MANY LINES**]
- Lines: 4, Max line: 18 chars
- L1 (10 ch): `anxious in`
- L2 ( 9 ch): `dungeons.`
- L3 (18 ch): `dreads the undead.`
- L4 ( 0 ch): ``
- Raw: `0041 004E 0058 0049 004F 0055 0053 0000 0049 004E FFFE 0044 0055 004E 0047 0045 004F 004E 0053 000E FFFE 0044 0052 0045 0041 0044 0053 0000 0054 0048 0045 0000 0055 004E 0044 0045 0041 0044 000E FFFE`

### MSG 102 [**TOO MANY LINES**]
- Lines: 4, Max line: 17 chars
- L1 (17 ch): `values recycling.`
- L2 (13 ch): `hates wasting`
- L3 ( 6 ch): `items.`
- L4 ( 0 ch): ``
- Raw: `0056 0041 004C 0055 0045 0053 0000 0052 0045 0043 0059 0043 004C 0049 004E 0047 000E FFFE 0048 0041 0054 0045 0053 0000 0057 0041 0053 0054 0049 004E 0047 FFFE 0049 0054 0045 004D 0053 000E FFFE`

### MSG 103 [**TOO MANY LINES**]
- Lines: 4, Max line: 16 chars
- L1 (13 ch): `strong maiden`
- L2 ( 6 ch): `bonds.`
- L3 (16 ch): `no need for men.`
- L4 ( 0 ch): ``
- Raw: `0053 0054 0052 004F 004E 0047 0000 004D 0041 0049 0044 0045 004E FFFE 0042 004F 004E 0044 0053 000E FFFE 004E 004F 0000 004E 0045 0045 0044 0000 0046 004F 0052 0000 004D 0045 004E 000E FFFE`

### MSG 104 [**TOO MANY LINES**]
- Lines: 5, Max line: 14 chars
- L1 (14 ch): `believes women`
- L2 ( 4 ch): `have`
- L3 (11 ch): `no place in`
- L4 ( 7 ch): `battle.`
- L5 ( 0 ch): ``
- Raw: `0042 0045 004C 0049 0045 0056 0045 0053 0000 0057 004F 004D 0045 004E FFFE 0048 0041 0056 0045 FFFE 004E 004F 0000 0050 004C 0041 0043 0045 0000 0049 004E FFFE 0042 0041 0054 0054 004C 0045 000E FFFE`

### MSG 105 [**TOO MANY LINES**]
- Lines: 5, Max line: 13 chars
- L1 (13 ch): `won't forgive`
- L2 ( 5 ch): `those`
- L3 (13 ch): `who slay tame`
- L4 ( 5 ch): `foes.`
- L5 ( 0 ch): ``
- Raw: `0057 004F 004E 0007 0054 0000 0046 004F 0052 0047 0049 0056 0045 FFFE 0054 0048 004F 0053 0045 FFFE 0057 0048 004F 0000 0053 004C 0041 0059 0000 0054 0041 004D 0045 FFFE 0046 004F 0045 0053 000E FFFE`

### MSG 106 [OK]
- Lines: 3, Max line: 18 chars
- L1 (18 ch): `lives to slay all.`
- L2 (17 ch): `despises retreat.`
- L3 ( 0 ch): ``
- Raw: `004C 0049 0056 0045 0053 0000 0054 004F 0000 0053 004C 0041 0059 0000 0041 004C 004C 000E FFFE 0044 0045 0053 0050 0049 0053 0045 0053 0000 0052 0045 0054 0052 0045 0041 0054 000E FFFE`

### MSG 107 [OK]
- Lines: 3, Max line: 17 chars
- L1 (16 ch): `values teamwork.`
- L2 (17 ch): `hates going solo.`
- L3 ( 0 ch): ``
- Raw: `0056 0041 004C 0055 0045 0053 0000 0054 0045 0041 004D 0057 004F 0052 004B 000E FFFE 0048 0041 0054 0045 0053 0000 0047 004F 0049 004E 0047 0000 0053 004F 004C 004F 000E FFFE`

### MSG 108 [**TOO MANY LINES**]
- Lines: 4, Max line: 16 chars
- L1 (16 ch): `hates bloodshed.`
- L2 (13 ch): `mourns fallen`
- L3 ( 7 ch): `allies.`
- L4 ( 0 ch): ``
- Raw: `0048 0041 0054 0045 0053 0000 0042 004C 004F 004F 0044 0053 0048 0045 0044 000E FFFE 004D 004F 0055 0052 004E 0053 0000 0046 0041 004C 004C 0045 004E FFFE 0041 004C 004C 0049 0045 0053 000E FFFE`

### MSG 109 [**TOO MANY LINES**]
- Lines: 4, Max line: 15 chars
- L1 (15 ch): `short-tempered.`
- L2 (11 ch): `long fights`
- L3 ( 7 ch): `enrage.`
- L4 ( 0 ch): ``
- Raw: `0053 0048 004F 0052 0054 000D 0054 0045 004D 0050 0045 0052 0045 0044 000E FFFE 004C 004F 004E 0047 0000 0046 0049 0047 0048 0054 0053 FFFE 0045 004E 0052 0041 0047 0045 000E FFFE`

### MSG 110 [OK]
- Lines: 3, Max line: 14 chars
- L1 (14 ch): `born merchant.`
- L2 (12 ch): `loves trade.`
- L3 ( 0 ch): ``
- Raw: `0042 004F 0052 004E 0000 004D 0045 0052 0043 0048 0041 004E 0054 000E FFFE 004C 004F 0056 0045 0053 0000 0054 0052 0041 0044 0045 000E FFFE`

### MSG 111 [**TOO MANY LINES**]
- Lines: 4, Max line: 18 chars
- L1 (14 ch): `likes opposite`
- L2 ( 4 ch): `sex.`
- L3 (18 ch): `bored by same sex.`
- L4 ( 0 ch): ``
- Raw: `004C 0049 004B 0045 0053 0000 004F 0050 0050 004F 0053 0049 0054 0045 FFFE 0053 0045 0058 000E FFFE 0042 004F 0052 0045 0044 0000 0042 0059 0000 0053 0041 004D 0045 0000 0053 0045 0058 000E FFFE`

### MSG 112 [**TOO MANY LINES**]
- Lines: 4, Max line: 16 chars
- L1 (16 ch): `vain narcissist.`
- L2 (12 ch): `shocked when`
- L3 ( 7 ch): `harmed.`
- L4 ( 0 ch): ``
- Raw: `0056 0041 0049 004E 0000 004E 0041 0052 0043 0049 0053 0053 0049 0053 0054 000E FFFE 0053 0048 004F 0043 004B 0045 0044 0000 0057 0048 0045 004E FFFE 0048 0041 0052 004D 0045 0044 000E FFFE`

### MSG 113 [**TOO MANY LINES**]
- Lines: 4, Max line: 17 chars
- L1 (17 ch): `happy then angry.`
- L2 (13 ch): `unpredictable`
- L3 ( 5 ch): `mood.`
- L4 ( 0 ch): ``
- Raw: `0048 0041 0050 0050 0059 0000 0054 0048 0045 004E 0000 0041 004E 0047 0052 0059 000E FFFE 0055 004E 0050 0052 0045 0044 0049 0043 0054 0041 0042 004C 0045 FFFE 004D 004F 004F 0044 000E FFFE`

### MSG 114 [**TOO MANY LINES**]
- Lines: 5, Max line: 11 chars
- L1 (10 ch): `thrives in`
- L2 ( 9 ch): `hardship.`
- L3 (11 ch): `hates being`
- L4 ( 7 ch): `helped.`
- L5 ( 0 ch): ``
- Raw: `0054 0048 0052 0049 0056 0045 0053 0000 0049 004E FFFE 0048 0041 0052 0044 0053 0048 0049 0050 000E FFFE 0048 0041 0054 0045 0053 0000 0042 0045 0049 004E 0047 FFFE 0048 0045 004C 0050 0045 0044 000E`...

### MSG 115 [**TOO MANY LINES**]
- Lines: 4, Max line: 18 chars
- L1 (14 ch): `bonds with own`
- L2 ( 5 ch): `race.`
- L3 (18 ch): `shuns other races.`
- L4 ( 0 ch): ``
- Raw: `0042 004F 004E 0044 0053 0000 0057 0049 0054 0048 0000 004F 0057 004E FFFE 0052 0041 0043 0045 000E FFFE 0053 0048 0055 004E 0053 0000 004F 0054 0048 0045 0052 0000 0052 0041 0043 0045 0053 000E FFFE`

### MSG 116 [**TOO MANY LINES**]
- Lines: 4, Max line: 15 chars
- L1 (13 ch): `empty-headed.`
- L2 (15 ch): `happy if others`
- L3 ( 4 ch): `are.`
- L4 ( 0 ch): ``
- Raw: `0045 004D 0050 0054 0059 000D 0048 0045 0041 0044 0045 0044 000E FFFE 0048 0041 0050 0050 0059 0000 0049 0046 0000 004F 0054 0048 0045 0052 0053 FFFE 0041 0052 0045 000E FFFE`

### MSG 117 [OK]
- Lines: 3, Max line: 18 chars
- L1 (15 ch): `use everything.`
- L2 (18 ch): `hoarding is a sin.`
- L3 ( 0 ch): ``
- Raw: `0055 0053 0045 0000 0045 0056 0045 0052 0059 0054 0048 0049 004E 0047 000E FFFE 0048 004F 0041 0052 0044 0049 004E 0047 0000 0049 0053 0000 0041 0000 0053 0049 004E 000E FFFE`

### MSG 118 [**TOO MANY LINES**]
- Lines: 4, Max line: 18 chars
- L1 (16 ch): `Gender sets base`
- L2 (18 ch): `stats. Men=strong,`
- L3 (11 ch): `women=wise.`
- L4 ( 0 ch): ``
- Raw: `0027 0045 004E 0044 0045 0052 0000 0053 0045 0054 0053 0000 0042 0041 0053 0045 FFFE 0053 0054 0041 0054 0053 000E 0000 002D 0045 004E 001D 0053 0054 0052 004F 004E 0047 000C FFFE 0057 004F 004D 0045`...

### MSG 119 [**TOO MANY LINES**]
- Lines: 4, Max line: 17 chars
- L1 (17 ch): `Human: High faith`
- L2 (16 ch): `& balanced stats`
- L3 ( 8 ch): `overall.`
- L4 ( 0 ch): ``
- Raw: `0028 0055 004D 0041 004E 001A 0000 0028 0049 0047 0048 0000 0046 0041 0049 0054 0048 FFFE 0006 0000 0042 0041 004C 0041 004E 0043 0045 0044 0000 0053 0054 0041 0054 0053 FFFE 004F 0056 0045 0052 0041`...

### MSG 120 [**TOO MANY LINES**]
- Lines: 5, Max line: 15 chars
- L1 (15 ch): `Elf: High INT &`
- L2 ( 3 ch): `VIT`
- L3 (15 ch): `but frail. Best`
- L4 ( 9 ch): `at magic.`
- L5 ( 0 ch): ``
- Raw: `0025 004C 0046 001A 0000 0028 0049 0047 0048 0000 0029 002E 0034 0000 0006 FFFE 0036 0029 0034 FFFE 0042 0055 0054 0000 0046 0052 0041 0049 004C 000E 0000 0022 0045 0053 0054 FFFE 0041 0054 0000 004D`...

### MSG 121 [**TOO MANY LINES**]
- Lines: 4, Max line: 17 chars
- L1 (17 ch): `Gnome: High faith`
- L2 (17 ch): `& agility. Suited`
- L3 (12 ch): `for Priests.`
- L4 ( 0 ch): ``
- Raw: `0027 004E 004F 004D 0045 001A 0000 0028 0049 0047 0048 0000 0046 0041 0049 0054 0048 FFFE 0006 0000 0041 0047 0049 004C 0049 0054 0059 000E 0000 0033 0055 0049 0054 0045 0044 FFFE 0046 004F 0052 0000`...

### MSG 122 [**TOO MANY LINES**]
- Lines: 4, Max line: 16 chars
- L1 (15 ch): `Dwarf: Slow but`
- L2 (16 ch): `strong with deep`
- L3 (16 ch): `faith. Fighters.`
- L4 ( 0 ch): ``
- Raw: `0024 0057 0041 0052 0046 001A 0000 0033 004C 004F 0057 0000 0042 0055 0054 FFFE 0053 0054 0052 004F 004E 0047 0000 0057 0049 0054 0048 0000 0044 0045 0045 0050 FFFE 0046 0041 0049 0054 0048 000E 0000`...

### MSG 123 [**TOO MANY LINES**]
- Lines: 4, Max line: 17 chars
- L1 (17 ch): `Hobbit: Small but`
- L2 (16 ch): `agile and lucky.`
- L3 (13 ch): `Born thieves.`
- L4 ( 0 ch): ``
- Raw: `0028 004F 0042 0042 0049 0054 001A 0000 0033 004D 0041 004C 004C 0000 0042 0055 0054 FFFE 0041 0047 0049 004C 0045 0000 0041 004E 0044 0000 004C 0055 0043 004B 0059 000E FFFE 0022 004F 0052 004E 0000`...

### MSG 124 [**TOO MANY LINES**]
- Lines: 4, Max line: 18 chars
- L1 (17 ch): `Good=justice. May`
- L2 (18 ch): `turn Evil. FIG MAG`
- L3 (16 ch): `PRI SAM GIZ BIS+`
- L4 ( 0 ch): ``
- Raw: `0027 004F 004F 0044 001D 004A 0055 0053 0054 0049 0043 0045 000E 0000 002D 0041 0059 FFFE 0054 0055 0052 004E 0000 0025 0056 0049 004C 000E 0000 0026 0029 0027 0000 002D 0021 0027 FFFE 0030 0032 0029`...

### MSG 125 [**TOO MANY LINES**]
- Lines: 4, Max line: 16 chars
- L1 (16 ch): `Neutral=no bias.`
- L2 (15 ch): `FIG THI MAG SAM`
- L3 (11 ch): `GIZ ALC MON`
- L4 ( 0 ch): ``
- Raw: `002E 0045 0055 0054 0052 0041 004C 001D 004E 004F 0000 0042 0049 0041 0053 000E FFFE 0026 0029 0027 0000 0034 0028 0029 0000 002D 0021 0027 0000 0033 0021 002D FFFE 0027 0029 003A 0000 0021 002C 0023`...

### MSG 126 [**TOO MANY LINES**]
- Lines: 4, Max line: 18 chars
- L1 (18 ch): `Evil=self-serving.`
- L2 (15 ch): `FIG THI MAG PRI`
- L3 (11 ch): `NIN BIS ALC`
- L4 ( 0 ch): ``
- Raw: `0025 0056 0049 004C 001D 0053 0045 004C 0046 000D 0053 0045 0052 0056 0049 004E 0047 000E FFFE 0026 0029 0027 0000 0034 0028 0029 0000 002D 0021 0027 0000 0030 0032 0029 FFFE 002E 0029 002E 0000 0022`...

### MSG 127 [**TOO MANY LINES**]
- Lines: 4, Max line: 16 chars
- L1 (14 ch): `combat expert.`
- L2 (16 ch): `cannot learn any`
- L3 (13 ch): `magic spells.`
- L4 ( 0 ch): ``
- Raw: `0043 004F 004D 0042 0041 0054 0000 0045 0058 0050 0045 0052 0054 000E FFFE 0043 0041 004E 004E 004F 0054 0000 004C 0045 0041 0052 004E 0000 0041 004E 0059 FFFE 004D 0041 0047 0049 0043 0000 0053 0050`...

### MSG 128 [**TOO MANY LINES**]
- Lines: 4, Max line: 17 chars
- L1 (17 ch): `Lowers trap level`
- L2 (15 ch): `& finds chests.`
- L3 (12 ch): `Sorcery Lv3.`
- L4 ( 0 ch): ``
- Raw: `002C 004F 0057 0045 0052 0053 0000 0054 0052 0041 0050 0000 004C 0045 0056 0045 004C FFFE 0006 0000 0046 0049 004E 0044 0053 0000 0043 0048 0045 0053 0054 0053 000E FFFE 0033 004F 0052 0043 0045 0052`...

### MSG 129 [**TOO MANY LINES**]
- Lines: 4, Max line: 18 chars
- L1 (18 ch): `master of sorcery.`
- L2 (13 ch): `can learn all`
- L3 (15 ch): `sorcery spells.`
- L4 ( 0 ch): ``
- Raw: `004D 0041 0053 0054 0045 0052 0000 004F 0046 0000 0053 004F 0052 0043 0045 0052 0059 000E FFFE 0043 0041 004E 0000 004C 0045 0041 0052 004E 0000 0041 004C 004C FFFE 0053 004F 0052 0043 0045 0052 0059`...

### MSG 130 [**TOO MANY LINES**]
- Lines: 4, Max line: 18 chars
- L1 (18 ch): `Holy magic master.`
- L2 (18 ch): `Can Dispel undead.`
- L3 (16 ch): `All Holy spells.`
- L4 ( 0 ch): ``
- Raw: `0028 004F 004C 0059 0000 004D 0041 0047 0049 0043 0000 004D 0041 0053 0054 0045 0052 000E FFFE 0023 0041 004E 0000 0024 0049 0053 0050 0045 004C 0000 0055 004E 0044 0045 0041 0044 000E FFFE 0021 004C`...

### MSG 131 [**TOO MANY LINES**]
- Lines: 5, Max line: 18 chars
- L1 (15 ch): `Great EXP gain.`
- L2 ( 3 ch): `Can`
- L3 (18 ch): `instant-kill foes.`
- L4 (18 ch): `Sorcery up to Lv2.`
- L5 ( 0 ch): ``
- Raw: `0027 0052 0045 0041 0054 0000 0025 0038 0030 0000 0047 0041 0049 004E 000E FFFE 0023 0041 004E FFFE 0049 004E 0053 0054 0041 004E 0054 000D 004B 0049 004C 004C 0000 0046 004F 0045 0053 000E FFFE 0033`...

### MSG 132 [**TOO MANY LINES**]
- Lines: 5, Max line: 14 chars
- L1 (11 ch): `Knight gear`
- L2 ( 7 ch): `usable.`
- L3 (14 ch): `Learns Sorcery`
- L4 (10 ch): `up to Lv5.`
- L5 ( 0 ch): ``
- Raw: `002B 004E 0049 0047 0048 0054 0000 0047 0045 0041 0052 FFFE 0055 0053 0041 0042 004C 0045 000E FFFE 002C 0045 0041 0052 004E 0053 0000 0033 004F 0052 0043 0045 0052 0059 FFFE 0055 0050 0000 0054 004F`...

### MSG 133 [**TOO MANY LINES**]
- Lines: 5, Max line: 17 chars
- L1 (12 ch): `Restores HP.`
- L2 ( 6 ch): `Dispel`
- L3 (17 ch): `vs undead. Sorc &`
- L4 (15 ch): `Holy Magic Lv6.`
- L5 ( 0 ch): ``
- Raw: `0032 0045 0053 0054 004F 0052 0045 0053 0000 0028 0030 000E FFFE 0024 0049 0053 0050 0045 004C FFFE 0056 0053 0000 0055 004E 0044 0045 0041 0044 000E 0000 0033 004F 0052 0043 0000 0006 FFFE 0028 004F`...

### MSG 134 [**TOO MANY LINES**]
- Lines: 4, Max line: 17 chars
- L1 (16 ch): `Poleaxe weapons.`
- L2 (17 ch): `Dispel vs undead.`
- L3 (15 ch): `Holy Magic Lv5.`
- L4 ( 0 ch): ``
- Raw: `0030 004F 004C 0045 0041 0058 0045 0000 0057 0045 0041 0050 004F 004E 0053 000E FFFE 0024 0049 0053 0050 0045 004C 0000 0056 0053 0000 0055 004E 0044 0045 0041 0044 000E FFFE 0028 004F 004C 0059 0000`...

### MSG 135 [**TOO MANY LINES**]
- Lines: 4, Max line: 17 chars
- L1 (16 ch): `Handles alchemy.`
- L2 (17 ch): `Sorc & Holy Magic`
- L3 (10 ch): `up to Lv4.`
- L4 ( 0 ch): ``
- Raw: `0028 0041 004E 0044 004C 0045 0053 0000 0041 004C 0043 0048 0045 004D 0059 000E FFFE 0033 004F 0052 0043 0000 0006 0000 0028 004F 004C 0059 0000 002D 0041 0047 0049 0043 FFFE 0055 0050 0000 0054 004F`...

### MSG 136 [**TOO MANY LINES**]
- Lines: 6, Max line: 14 chars
- L1 (13 ch): `Longbow user.`
- L2 ( 6 ch): `Lowers`
- L3 (13 ch): `traps, steals`
- L4 ( 5 ch): `items`
- L5 (14 ch): `Sorc+Holy Lv3.`
- L6 ( 0 ch): ``
- Raw: `002C 004F 004E 0047 0042 004F 0057 0000 0055 0053 0045 0052 000E FFFE 002C 004F 0057 0045 0052 0053 FFFE 0054 0052 0041 0050 0053 000C 0000 0053 0054 0045 0041 004C 0053 FFFE 0049 0054 0045 004D 0053`...

### MSG 137 [**TOO MANY LINES**]
- Lines: 4, Max line: 18 chars
- L1 (18 ch): `Staffs & knuckles.`
- L2 (17 ch): `Dispel vs undead.`
- L3 (15 ch): `Holy Magic Lv5.`
- L4 ( 0 ch): ``
- Raw: `0033 0054 0041 0046 0046 0053 0000 0006 0000 004B 004E 0055 0043 004B 004C 0045 0053 000E FFFE 0024 0049 0053 0050 0045 004C 0000 0056 0053 0000 0055 004E 0044 0045 0041 0044 000E FFFE 0028 004F 004C`...

### MSG 138 [**TOO MANY LINES**]
- Lines: 5, Max line: 17 chars
- L1 (15 ch): `Holy aura heals`
- L2 ( 3 ch): `HP.`
- L3 (17 ch): `Can learn Dispel.`
- L4 (14 ch): `Sorc+Holy Lv6.`
- L5 ( 0 ch): ``
- Raw: `0028 004F 004C 0059 0000 0041 0055 0052 0041 0000 0048 0045 0041 004C 0053 FFFE 0028 0030 000E FFFE 0023 0041 004E 0000 004C 0045 0041 0052 004E 0000 0024 0049 0053 0050 0045 004C 000E FFFE 0033 004F`...

### MSG 139 [**TOO MANY LINES**]
- Lines: 5, Max line: 15 chars
- L1 (14 ch): `Removes curses`
- L2 ( 4 ch): `from`
- L3 (15 ch): `equipped items.`
- L4 (12 ch): `Sorcery Lv6.`
- L5 ( 0 ch): ``
- Raw: `0032 0045 004D 004F 0056 0045 0053 0000 0043 0055 0052 0053 0045 0053 FFFE 0046 0052 004F 004D FFFE 0045 0051 0055 0049 0050 0050 0045 0044 0000 0049 0054 0045 004D 0053 000E FFFE 0033 004F 0052 0043`...

### MSG 140 [**TOO MANY LINES**]
- Lines: 4, Max line: 18 chars
- L1 (18 ch): `Great EXP & insta-`
- L2 (18 ch): `kill. Sees in fog.`
- L3 (12 ch): `Sorcery Lv5.`
- L4 ( 0 ch): ``
- Raw: `0027 0052 0045 0041 0054 0000 0025 0038 0030 0000 0006 0000 0049 004E 0053 0054 0041 000D FFFE 004B 0049 004C 004C 000E 0000 0033 0045 0045 0053 0000 0049 004E 0000 0046 004F 0047 000E FFFE 0033 004F`...

### MSG 141 [**TOO MANY LINES**]
- Lines: 5, Max line: 16 chars
- L1 (16 ch): `Dual wields same`
- L2 (12 ch): `weapon type.`
- L3 ( 6 ch): `Learns`
- L4 (12 ch): `Sorcery Lv6.`
- L5 ( 0 ch): ``
- Raw: `0024 0055 0041 004C 0000 0057 0049 0045 004C 0044 0053 0000 0053 0041 004D 0045 FFFE 0057 0045 0041 0050 004F 004E 0000 0054 0059 0050 0045 000E FFFE 002C 0045 0041 0052 004E 0053 FFFE 0033 004F 0052`...

### MSG 142 [**TOO MANY LINES**]
- Lines: 5, Max line: 18 chars
- L1 (18 ch): `Longbow. Best trap`
- L2 (13 ch): `skill. Steals`
- L3 ( 5 ch): `items`
- L4 (14 ch): `Sorc+Holy Lv4.`
- L5 ( 0 ch): ``
- Raw: `002C 004F 004E 0047 0042 004F 0057 000E 0000 0022 0045 0053 0054 0000 0054 0052 0041 0050 FFFE 0053 004B 0049 004C 004C 000E 0000 0033 0054 0045 0041 004C 0053 FFFE 0049 0054 0045 004D 0053 FFFE 0033`...

### MSG 143 [**TOO MANY LINES**]
- Lines: 4, Max line: 14 chars
- L1 (14 ch): `affects damage`
- L2 ( 5 ch): `dealt`
- L3 (13 ch): `with weapons.`
- L4 ( 0 ch): ``
- Raw: `0041 0046 0046 0045 0043 0054 0053 0000 0044 0041 004D 0041 0047 0045 FFFE 0044 0045 0041 004C 0054 FFFE 0057 0049 0054 0048 0000 0057 0045 0041 0050 004F 004E 0053 000E FFFE`

### MSG 144 [**TOO MANY LINES**]
- Lines: 4, Max line: 15 chars
- L1 (15 ch): `affects sorcery`
- L2 ( 9 ch): `power and`
- L3 (11 ch): `resistance.`
- L4 ( 0 ch): ``
- Raw: `0041 0046 0046 0045 0043 0054 0053 0000 0053 004F 0052 0043 0045 0052 0059 FFFE 0050 004F 0057 0045 0052 0000 0041 004E 0044 FFFE 0052 0045 0053 0049 0053 0054 0041 004E 0043 0045 000E FFFE`

### MSG 145 [**TOO MANY LINES**]
- Lines: 4, Max line: 18 chars
- L1 (18 ch): `affects holy magic`
- L2 ( 9 ch): `power and`
- L3 (11 ch): `resistance.`
- L4 ( 0 ch): ``
- Raw: `0041 0046 0046 0045 0043 0054 0053 0000 0048 004F 004C 0059 0000 004D 0041 0047 0049 0043 FFFE 0050 004F 0057 0045 0052 0000 0041 004E 0044 FFFE 0052 0045 0053 0049 0053 0054 0041 004E 0043 0045 000E`...

### MSG 146 [**TOO MANY LINES**]
- Lines: 5, Max line: 18 chars
- L1 (15 ch): `affects max hp,`
- L2 (18 ch): `status resistance,`
- L3 (11 ch): `and revival`
- L4 ( 8 ch): `success.`
- L5 ( 0 ch): ``
- Raw: `0041 0046 0046 0045 0043 0054 0053 0000 004D 0041 0058 0000 0048 0050 000C FFFE 0053 0054 0041 0054 0055 0053 0000 0052 0045 0053 0049 0053 0054 0041 004E 0043 0045 000C FFFE 0041 004E 0044 0000 0052`...

### MSG 147 [OK]
- Lines: 3, Max line: 18 chars
- L1 (18 ch): `affects turn order`
- L2 (10 ch): `in battle.`
- L3 ( 0 ch): ``
- Raw: `0041 0046 0046 0045 0043 0054 0053 0000 0054 0055 0052 004E 0000 004F 0052 0044 0045 0052 FFFE 0049 004E 0000 0042 0041 0054 0054 004C 0045 000E FFFE`

### MSG 148 [**TOO MANY LINES**]
- Lines: 5, Max line: 14 chars
- L1 (14 ch): `affects breath`
- L2 (10 ch): `resist and`
- L3 ( 8 ch): `critical`
- L4 (11 ch): `hit chance.`
- L5 ( 0 ch): ``
- Raw: `0041 0046 0046 0045 0043 0054 0053 0000 0042 0052 0045 0041 0054 0048 FFFE 0052 0045 0053 0049 0053 0054 0000 0041 004E 0044 FFFE 0043 0052 0049 0054 0049 0043 0041 004C FFFE 0048 0049 0054 0000 0043`...


## Complete Message Dump (All 189 Messages)


### MSG 0: Empty/Header

| MSG | Lines | MaxLen | Text | Flags |
|-----|-------|--------|------|-------|
| 0 | 1 | 1187 | `ぅ 格 息 響 有 替 国 若 声 唱 造 挨 募 級 跡 取 店 袋 恩 宣 滅 奪 [1052] [1062] 喝 [1082] 鞄 動 [1120] [1` | WIDE=1187, JP, UNMAP |

### Stat Labels (MSG 1-7)

| MSG | Lines | MaxLen | Text | Flags |
|-----|-------|--------|------|-------|
| 1 | 2 | 2 | `HP\n` | ok |
| 2 | 2 | 6 | `hp/mhp\n` | ok |
| 3 | 2 | 3 | `str\n` | ok |
| 4 | 2 | 3 | `int\n` | ok |
| 5 | 2 | 3 | `fth\n` | ok |
| 6 | 2 | 3 | `vit\n` | ok |
| 7 | 2 | 3 | `agi\n` | ok |

### Field Labels (MSG 8-16)

| MSG | Lines | MaxLen | Text | Flags |
|-----|-------|--------|------|-------|
| 8 | 2 | 3 | `lck\n` | ok |
| 9 | 2 | 4 | `name\n` | ok |
| 10 | 2 | 5 | `level\n` | ok |
| 11 | 2 | 4 | `race\n` | ok |
| 12 | 2 | 6 | `gender\n` | ok |
| 13 | 2 | 9 | `alignment\n` | ok |
| 14 | 2 | 5 | `class\n` | ok |
| 15 | 2 | 11 | `personality\n` | ok |
| 16 | 2 | 7 | `sorcery\n` | ok |

### Other Labels (MSG 17-26)

| MSG | Lines | MaxLen | Text | Flags |
|-----|-------|--------|------|-------|
| 17 | 2 | 10 | `holy magic\n` | ok |
| 18 | 2 | 10 | `attributes\n` | ok |
| 19 | 2 | 3 | `lv1\n` | ok |
| 20 | 2 | 3 | `lv2\n` | ok |
| 21 | 2 | 3 | `lv3\n` | ok |
| 22 | 2 | 3 | `lv4\n` | ok |
| 23 | 2 | 3 | `lv5\n` | ok |
| 24 | 2 | 3 | `lv6\n` | ok |
| 25 | 2 | 3 | `Lv7\n` | ok |
| 26 | 2 | 4 | `male\n` | ok |

### Gender (MSG 27-28)

| MSG | Lines | MaxLen | Text | Flags |
|-----|-------|--------|------|-------|
| 27 | 2 | 6 | `female\n` | ok |
| 28 | 2 | 2 | `Io\n` | ok |

### Race Names (MSG 29-34)

| MSG | Lines | MaxLen | Text | Flags |
|-----|-------|--------|------|-------|
| 29 | 2 | 6 | `Europa\n` | ok |
| 30 | 2 | 5 | `Human\n` | ok |
| 31 | 2 | 3 | `Elf\n` | ok |
| 32 | 2 | 5 | `gnome\n` | ok |
| 33 | 2 | 5 | `dwarf\n` | ok |
| 34 | 2 | 6 | `hobbit\n` | ok |

### Class Names (MSG 35-52)

| MSG | Lines | MaxLen | Text | Flags |
|-----|-------|--------|------|-------|
| 35 | 2 | 8 | `automata\n` | ok |
| 36 | 2 | 1 | ` \n` | ok |
| 37 | 2 | 1 | ` \n` | ok |
| 38 | 2 | 7 | `fighter\n` | ok |
| 39 | 2 | 5 | `thief\n` | ok |
| 40 | 2 | 4 | `mage\n` | ok |
| 41 | 2 | 6 | `priest\n` | ok |
| 42 | 2 | 5 | `ninja\n` | ok |
| 43 | 2 | 5 | `ninja\n` | ok |
| 44 | 2 | 6 | `bishop\n` | ok |
| 45 | 2 | 7 | `samurai\n` | ok |
| 46 | 2 | 9 | `alchemist\n` | ok |
| 47 | 2 | 6 | `gizoku\n` | ok |
| 48 | 2 | 4 | `monk\n` | ok |
| 49 | 2 | 7 | `paladin\n` | ok |
| 50 | 2 | 11 | `dark knight\n` | ok |
| 51 | 2 | 6 | `shogun\n` | ok |
| 52 | 2 | 6 | `knight\n` | ok |

### Personality Traits (MSG 53-86)

| MSG | Lines | MaxLen | Text | Flags |
|-----|-------|--------|------|-------|
| 53 | 2 | 10 | `high thief\n` | ok |
| 54 | 2 | 7 | `omnitsu\n` | ok |
| 55 | 2 | 8 | `militant\n` | ok |
| 56 | 2 | 8 | `wasteful\n` | ok |
| 57 | 2 | 6 | `lonely\n` | ok |
| 58 | 2 | 8 | `sociable\n` | ok |
| 59 | 2 | 9 | `collector\n` | ok |
| 60 | 2 | 8 | `cautious\n` | ok |
| 61 | 2 | 7 | `hoarder\n` | ok |
| 62 | 2 | 12 | `intellectual\n` | ok |
| 63 | 2 | 11 | `belligerent\n` | ok |
| 64 | 2 | 11 | `adventurous\n` | ok |
| 65 | 2 | 13 | `superstitious\n` | ok |
| 66 | 2 | 8 | `studious\n` | ok |
| 67 | 2 | 13 | `pusillanimous\n` | ok |
| 68 | 2 | 9 | `ecologist\n` | ok |
| 69 | 2 | 12 | `maiden heart\n` | ok |
| 70 | 2 | 11 | `hot-blooded\n` | ok |
| 71 | 2 | 4 | `just\n` | ok |
| 72 | 2 | 10 | `determined\n` | ok |
| 73 | 2 | 11 | `cooperative\n` | ok |
| 74 | 2 | 9 | `fraternal\n` | ok |
| 75 | 2 | 14 | `short-tempered\n` | ok |
| 76 | 2 | 9 | `economist\n` | ok |
| 77 | 2 | 7 | `lustful\n` | ok |
| 78 | 2 | 10 | `narcissist\n` | ok |
| 79 | 2 | 5 | `moody\n` | ok |
| 80 | 2 | 6 | `sadist\n` | ok |
| 81 | 2 | 11 | `tribal love\n` | ok |
| 82 | 2 | 4 | `bold\n` | ok |
| 83 | 2 | 8 | `hobbyist\n` | ok |
| 84 | 2 | 6 | `attack\n` | ok |
| 85 | 2 | 8 | `accuracy\n` | ok |
| 86 | 2 | 7 | `defense\n` | ok |

### Descriptions (MSG 87-148)

| MSG | Lines | MaxLen | Text | Flags |
|-----|-------|--------|------|-------|
| 87 | 2 | 7 | `evasion\n` | ok |
| 88 | 4 | 14 | `bores easily.\nreturn\nto town often.\n` | LINES=4 |
| 89 | 3 | 18 | `senses spirits.\ntrembles at death.\n` | ok |
| 90 | 5 | 16 | `lives to hoard\ngold.\nangry if loot is\nlow.\n` | LINES=5 |
| 91 | 3 | 16 | `dislikes crowds.\ncalmer in few.\n` | ok |
| 92 | 4 | 17 | `loves big groups.\nhates small\nparties.\n` | LINES=4 |
| 93 | 3 | 18 | `can't resist loot.\nlives to collect.\n` | ok |
| 94 | 3 | 18 | `distrusts reckless\nadventurers.\n` | ok |
| 95 | 3 | 16 | `fascinated by\nmonster biology.\n` | ok |
| 96 | 4 | 18 | `believes in mystic\npower. loves\nmagic.\n` | LINES=4 |
| 97 | 3 | 18 | `skilled warrior.\nseeks strong foes.\n` | ok |
| 98 | 3 | 18 | `must adventure.\nidleness is agony.\n` | ok |
| 99 | 3 | 16 | `reacts keenly to\nsudden events.\n` | ok |
| 100 | 5 | 13 | `obsessed with\ntraps.\ncrushed by\nsuccess.\n` | LINES=5 |
| 101 | 4 | 18 | `anxious in\ndungeons.\ndreads the undead.\n` | LINES=4 |
| 102 | 4 | 17 | `values recycling.\nhates wasting\nitems.\n` | LINES=4 |
| 103 | 4 | 16 | `strong maiden\nbonds.\nno need for men.\n` | LINES=4 |
| 104 | 5 | 14 | `believes women\nhave\nno place in\nbattle.\n` | LINES=5 |
| 105 | 5 | 13 | `won't forgive\nthose\nwho slay tame\nfoes.\n` | LINES=5 |
| 106 | 3 | 18 | `lives to slay all.\ndespises retreat.\n` | ok |
| 107 | 3 | 17 | `values teamwork.\nhates going solo.\n` | ok |
| 108 | 4 | 16 | `hates bloodshed.\nmourns fallen\nallies.\n` | LINES=4 |
| 109 | 4 | 15 | `short-tempered.\nlong fights\nenrage.\n` | LINES=4 |
| 110 | 3 | 14 | `born merchant.\nloves trade.\n` | ok |
| 111 | 4 | 18 | `likes opposite\nsex.\nbored by same sex.\n` | LINES=4 |
| 112 | 4 | 16 | `vain narcissist.\nshocked when\nharmed.\n` | LINES=4 |
| 113 | 4 | 17 | `happy then angry.\nunpredictable\nmood.\n` | LINES=4 |
| 114 | 5 | 11 | `thrives in\nhardship.\nhates being\nhelped.\n` | LINES=5 |
| 115 | 4 | 18 | `bonds with own\nrace.\nshuns other races.\n` | LINES=4 |
| 116 | 4 | 15 | `empty-headed.\nhappy if others\nare.\n` | LINES=4 |
| 117 | 3 | 18 | `use everything.\nhoarding is a sin.\n` | ok |
| 118 | 4 | 18 | `Gender sets base\nstats. Men=strong,\nwomen=wise.\n` | LINES=4 |
| 119 | 4 | 17 | `Human: High faith\n& balanced stats\noverall.\n` | LINES=4 |
| 120 | 5 | 15 | `Elf: High INT &\nVIT\nbut frail. Best\nat magic.\n` | LINES=5 |
| 121 | 4 | 17 | `Gnome: High faith\n& agility. Suited\nfor Priests.\n` | LINES=4 |
| 122 | 4 | 16 | `Dwarf: Slow but\nstrong with deep\nfaith. Fighters.\n` | LINES=4 |
| 123 | 4 | 17 | `Hobbit: Small but\nagile and lucky.\nBorn thieves.\n` | LINES=4 |
| 124 | 4 | 18 | `Good=justice. May\nturn Evil. FIG MAG\nPRI SAM GIZ BIS+\n` | LINES=4 |
| 125 | 4 | 16 | `Neutral=no bias.\nFIG THI MAG SAM\nGIZ ALC MON\n` | LINES=4 |
| 126 | 4 | 18 | `Evil=self-serving.\nFIG THI MAG PRI\nNIN BIS ALC\n` | LINES=4 |
| 127 | 4 | 16 | `combat expert.\ncannot learn any\nmagic spells.\n` | LINES=4 |
| 128 | 4 | 17 | `Lowers trap level\n& finds chests.\nSorcery Lv3.\n` | LINES=4 |
| 129 | 4 | 18 | `master of sorcery.\ncan learn all\nsorcery spells.\n` | LINES=4 |
| 130 | 4 | 18 | `Holy magic master.\nCan Dispel undead.\nAll Holy spells.\n` | LINES=4 |
| 131 | 5 | 18 | `Great EXP gain.\nCan\ninstant-kill foes.\nSorcery up to Lv2.\n` | LINES=5 |
| 132 | 5 | 14 | `Knight gear\nusable.\nLearns Sorcery\nup to Lv5.\n` | LINES=5 |
| 133 | 5 | 17 | `Restores HP.\nDispel\nvs undead. Sorc &\nHoly Magic Lv6.\n` | LINES=5 |
| 134 | 4 | 17 | `Poleaxe weapons.\nDispel vs undead.\nHoly Magic Lv5.\n` | LINES=4 |
| 135 | 4 | 17 | `Handles alchemy.\nSorc & Holy Magic\nup to Lv4.\n` | LINES=4 |
| 136 | 6 | 14 | `Longbow user.\nLowers\ntraps, steals\nitems\nSorc+Holy Lv3.\n` | LINES=6 |
| 137 | 4 | 18 | `Staffs & knuckles.\nDispel vs undead.\nHoly Magic Lv5.\n` | LINES=4 |
| 138 | 5 | 17 | `Holy aura heals\nHP.\nCan learn Dispel.\nSorc+Holy Lv6.\n` | LINES=5 |
| 139 | 5 | 15 | `Removes curses\nfrom\nequipped items.\nSorcery Lv6.\n` | LINES=5 |
| 140 | 4 | 18 | `Great EXP & insta-\nkill. Sees in fog.\nSorcery Lv5.\n` | LINES=4 |
| 141 | 5 | 16 | `Dual wields same\nweapon type.\nLearns\nSorcery Lv6.\n` | LINES=5 |
| 142 | 5 | 18 | `Longbow. Best trap\nskill. Steals\nitems\nSorc+Holy Lv4.\n` | LINES=5 |
| 143 | 4 | 14 | `affects damage\ndealt\nwith weapons.\n` | LINES=4 |
| 144 | 4 | 15 | `affects sorcery\npower and\nresistance.\n` | LINES=4 |
| 145 | 4 | 18 | `affects holy magic\npower and\nresistance.\n` | LINES=4 |
| 146 | 5 | 18 | `affects max hp,\nstatus resistance,\nand revival\nsuccess.\n` | LINES=5 |
| 147 | 3 | 18 | `affects turn order\nin battle.\n` | ok |
| 148 | 5 | 14 | `affects breath\nresist and\ncritical\nhit chance.\n` | LINES=5 |

### Other (MSG 149+)

| MSG | Lines | MaxLen | Text | Flags |
|-----|-------|--------|------|-------|
| 149 | 2 | 8 | `good "g"\n` | ok |
| 150 | 2 | 11 | `neutral "n"\n` | ok |
| 151 | 2 | 8 | `evil "e"\n` | ok |
| 152 | 2 | 4 | `good\n` | ok |
| 153 | 2 | 7 | `neutral\n` | ok |
| 154 | 2 | 4 | `evil\n` | ok |
| 155 | 2 | 1 | `g\n` | ok |
| 156 | 2 | 1 | `n\n` | ok |
| 157 | 2 | 1 | `e\n` | ok |
| 158 | 2 | 2 | `Lv\n` | ok |
| 159 | 2 | 8 | `Commoner\n` | ok |
| 160 | 2 | 8 | `Hooligan\n` | ok |
| 161 | 2 | 4 | `Evil\n` | ok |
| 162 | 2 | 10 | `Venom Fang\n` | ok |
| 163 | 2 | 7 | `VILLAIN\n` | ok |
| 164 | 2 | 8 | `GANGSTER\n` | ok |
| 165 | 2 | 7 | `cruelty\n` | ok |
| 166 | 2 | 7 | `VICIOUS\n` | ok |
| 167 | 2 | 9 | `dangerous\n` | ok |
| 168 | 2 | 9 | `CURIOSITY\n` | ok |
| 169 | 2 | 8 | `COMMONER\n` | ok |
| 170 | 2 | 10 | `ADVENTURER\n` | ok |
| 171 | 2 | 5 | `GUARD\n` | ok |
| 172 | 2 | 8 | `BOLDNESS\n` | ok |
| 173 | 2 | 7 | `BRAVERY\n` | ok |
| 174 | 2 | 6 | `FAMOUS\n` | ok |
| 175 | 2 | 7 | `VETERAN\n` | ok |
| 176 | 2 | 9 | `CONQUEROR\n` | ok |
| 177 | 2 | 4 | `HERO\n` | ok |
| 178 | 2 | 11 | `QUEEN GUARD\n` | ok |
| 179 | 2 | 8 | `COMMONER\n` | ok |
| 180 | 2 | 13 | `HONEST PERSON\n` | ok |
| 181 | 2 | 4 | `KIND\n` | ok |
| 182 | 2 | 8 | `RELIABLE\n` | ok |
| 183 | 2 | 11 | `GREAT HEART\n` | ok |
| 184 | 2 | 8 | `FAIRNESS\n` | ok |
| 185 | 2 | 5 | `noble\n` | ok |
| 186 | 2 | 11 | `ACHIEVEMENT\n` | ok |
| 187 | 2 | 4 | `SAGE\n` | ok |
| 188 | 2 | 8 | `GOD HAND\n` | ok |

## Raw Glyph IDs

```
MSG   0 (1L, max1187): [188, 0, 756, 0, 764, 0, 780, 0, 790, 0, 800, 0, 810, 0, 820, 0, 830, 0, 840, 0, 852, 0, 866, 0, 878, 0, 894, 0, 916, 0, 930, 0, 956, 0, 974, 0, 998, 0, 1022, 0, 1032, 0, 1042, 0, 1052, 0, 1062, 0, 1072, 0, 1082, 0, 1092, 0, 1104, 0, 1120, 0, 1128, 0, 1144, 0, 1158, 0, 1168, 0, 1182, 0, 1196, 0, 1212, 0, 1232, 0, 1238, 0, 1244, 0, 1262, 0, 1276, 0, 1288, 0, 1304, 0, 1318, 0, 1332, 0, 1348, 0, 1366, 0, 1388, 0, 1404, 0, 1416, 0, 1434, 0, 1460, 0, 1476, 0, 1492, 0, 1516, 0, 1534, 0, 1554, 0, 1574, 0, 1590, 0, 1610, 0, 1632, 0, 1652, 0, 1670, 0, 1698, 0, 1724, 0, 1750, 0, 1780, 0, 1800, 0, 1830, 0, 1852, 0, 1880, 0, 1906, 0, 1918, 0, 1942, 0, 1968, 0, 1990, 0, 2022, 0, 2044, 0, 2062, 0, 2086, 0, 2100, 0, 2116, 0, 2142, 0, 2154, 0, 2174, 0, 2190, 0, 2210, 0, 2228, 0, 2246, 0, 2320, 0, 2392, 0, 2480, 0, 2546, 0, 2626, 0, 2702, 0, 2768, 0, 2832, 0, 2912, 0, 2986, 0, 3058, 0, 3124, 0, 3208, 0, 3290, 0, 3370, 0, 3448, 0, 3530, 0, 3612, 0, 3688, 0, 3760, 0, 3840, 0, 3914, 0, 3972, 0, 4052, 0, 4130, 0, 4208, 0, 4292, 0, 4374, 0, 4446, 0, 4518, 0, 4616, 0, 4706, 0, 4800, 0, 4900, 0, 5002, 0, 5102, 0, 5212, 0, 5304, 0, 5400, 0, 5494, 0, 5590, 0, 5690, 0, 5802, 0, 5920, 0, 6014, 0, 6124, 0, 6228, 0, 6322, 0, 6436, 0, 6544, 0, 6652, 0, 6752, 0, 6856, 0, 6958, 0, 7068, 0, 7140, 0, 7218, 0, 7302, 0, 7416, 0, 7478, 0, 7574, 0, 7594, 0, 7620, 0, 7640, 0, 7652, 0, 7670, 0, 7682, 0, 7688, 0, 7694, 0, 7700, 0, 7708, 0, 7728, 0, 7748, 0, 7760, 0, 7784, 0, 7802, 0, 7822, 0, 7840, 0, 7858, 0, 7880, 0, 7902, 0, 7922, 0, 7946, 0, 7960, 0, 7980, 0, 7998, 0, 8014, 0, 8032, 0, 8054, 0, 8066, 0, 8092, 0, 8112, 0, 8142, 0, 8154, 0, 8174, 0, 8200, 0, 8220, 0, 8234, 0, 8260, 0, 8272]
MSG   1 (2L, max 2): [40, 48]  LF@[2]
MSG   2 (2L, max 6): [72, 80, 15, 77, 72, 80]  LF@[6]
MSG   3 (2L, max 3): [83, 84, 82]  LF@[3]
MSG   4 (2L, max 3): [73, 78, 84]  LF@[3]
MSG   5 (2L, max 3): [70, 84, 72]  LF@[3]
MSG   6 (2L, max 3): [86, 73, 84]  LF@[3]
MSG   7 (2L, max 3): [65, 71, 73]  LF@[3]
MSG   8 (2L, max 3): [76, 67, 75]  LF@[3]
MSG   9 (2L, max 4): [78, 65, 77, 69]  LF@[4]
MSG  10 (2L, max 5): [76, 69, 86, 69, 76]  LF@[5]
MSG  11 (2L, max 4): [82, 65, 67, 69]  LF@[4]
MSG  12 (2L, max 6): [71, 69, 78, 68, 69, 82]  LF@[6]
MSG  13 (2L, max 9): [65, 76, 73, 71, 78, 77, 69, 78, 84]  LF@[9]
MSG  14 (2L, max 5): [67, 76, 65, 83, 83]  LF@[5]
MSG  15 (2L, max11): [80, 69, 82, 83, 79, 78, 65, 76, 73, 84, 89]  LF@[11]
MSG  16 (2L, max 7): [83, 79, 82, 67, 69, 82, 89]  LF@[7]
MSG  17 (2L, max10): [72, 79, 76, 89, 0, 77, 65, 71, 73, 67]  LF@[10]
MSG  18 (2L, max10): [65, 84, 84, 82, 73, 66, 85, 84, 69, 83]  LF@[10]
MSG  19 (2L, max 3): [76, 86, 17]  LF@[3]
MSG  20 (2L, max 3): [76, 86, 18]  LF@[3]
MSG  21 (2L, max 3): [76, 86, 19]  LF@[3]
MSG  22 (2L, max 3): [76, 86, 20]  LF@[3]
MSG  23 (2L, max 3): [76, 86, 21]  LF@[3]
MSG  24 (2L, max 3): [76, 86, 22]  LF@[3]
MSG  25 (2L, max 3): [44, 86, 23]  LF@[3]
MSG  26 (2L, max 4): [77, 65, 76, 69]  LF@[4]
MSG  27 (2L, max 6): [70, 69, 77, 65, 76, 69]  LF@[6]
MSG  28 (2L, max 2): [41, 79]  LF@[2]
MSG  29 (2L, max 6): [37, 85, 82, 79, 80, 65]  LF@[6]
MSG  30 (2L, max 5): [40, 85, 77, 65, 78]  LF@[5]
MSG  31 (2L, max 3): [37, 76, 70]  LF@[3]
MSG  32 (2L, max 5): [71, 78, 79, 77, 69]  LF@[5]
MSG  33 (2L, max 5): [68, 87, 65, 82, 70]  LF@[5]
MSG  34 (2L, max 6): [72, 79, 66, 66, 73, 84]  LF@[6]
MSG  35 (2L, max 8): [65, 85, 84, 79, 77, 65, 84, 65]  LF@[8]
MSG  36 (2L, max 1): [0]  LF@[1]
MSG  37 (2L, max 1): [0]  LF@[1]
MSG  38 (2L, max 7): [70, 73, 71, 72, 84, 69, 82]  LF@[7]
MSG  39 (2L, max 5): [84, 72, 73, 69, 70]  LF@[5]
MSG  40 (2L, max 4): [77, 65, 71, 69]  LF@[4]
MSG  41 (2L, max 6): [80, 82, 73, 69, 83, 84]  LF@[6]
MSG  42 (2L, max 5): [78, 73, 78, 74, 65]  LF@[5]
MSG  43 (2L, max 5): [78, 73, 78, 74, 65]  LF@[5]
MSG  44 (2L, max 6): [66, 73, 83, 72, 79, 80]  LF@[6]
MSG  45 (2L, max 7): [83, 65, 77, 85, 82, 65, 73]  LF@[7]
MSG  46 (2L, max 9): [65, 76, 67, 72, 69, 77, 73, 83, 84]  LF@[9]
MSG  47 (2L, max 6): [71, 73, 90, 79, 75, 85]  LF@[6]
MSG  48 (2L, max 4): [77, 79, 78, 75]  LF@[4]
MSG  49 (2L, max 7): [80, 65, 76, 65, 68, 73, 78]  LF@[7]
MSG  50 (2L, max11): [68, 65, 82, 75, 0, 75, 78, 73, 71, 72, 84]  LF@[11]
MSG  51 (2L, max 6): [83, 72, 79, 71, 85, 78]  LF@[6]
MSG  52 (2L, max 6): [75, 78, 73, 71, 72, 84]  LF@[6]
MSG  53 (2L, max10): [72, 73, 71, 72, 0, 84, 72, 73, 69, 70]  LF@[10]
MSG  54 (2L, max 7): [79, 77, 78, 73, 84, 83, 85]  LF@[7]
MSG  55 (2L, max 8): [77, 73, 76, 73, 84, 65, 78, 84]  LF@[8]
MSG  56 (2L, max 8): [87, 65, 83, 84, 69, 70, 85, 76]  LF@[8]
MSG  57 (2L, max 6): [76, 79, 78, 69, 76, 89]  LF@[6]
MSG  58 (2L, max 8): [83, 79, 67, 73, 65, 66, 76, 69]  LF@[8]
MSG  59 (2L, max 9): [67, 79, 76, 76, 69, 67, 84, 79, 82]  LF@[9]
MSG  60 (2L, max 8): [67, 65, 85, 84, 73, 79, 85, 83]  LF@[8]
MSG  61 (2L, max 7): [72, 79, 65, 82, 68, 69, 82]  LF@[7]
MSG  62 (2L, max12): [73, 78, 84, 69, 76, 76, 69, 67, 84, 85, 65, 76]  LF@[12]
MSG  63 (2L, max11): [66, 69, 76, 76, 73, 71, 69, 82, 69, 78, 84]  LF@[11]
MSG  64 (2L, max11): [65, 68, 86, 69, 78, 84, 85, 82, 79, 85, 83]  LF@[11]
MSG  65 (2L, max13): [83, 85, 80, 69, 82, 83, 84, 73, 84, 73, 79, 85, 83]  LF@[13]
MSG  66 (2L, max 8): [83, 84, 85, 68, 73, 79, 85, 83]  LF@[8]
MSG  67 (2L, max13): [80, 85, 83, 73, 76, 76, 65, 78, 73, 77, 79, 85, 83]  LF@[13]
MSG  68 (2L, max 9): [69, 67, 79, 76, 79, 71, 73, 83, 84]  LF@[9]
MSG  69 (2L, max12): [77, 65, 73, 68, 69, 78, 0, 72, 69, 65, 82, 84]  LF@[12]
MSG  70 (2L, max11): [72, 79, 84, 13, 66, 76, 79, 79, 68, 69, 68]  LF@[11]
MSG  71 (2L, max 4): [74, 85, 83, 84]  LF@[4]
MSG  72 (2L, max10): [68, 69, 84, 69, 82, 77, 73, 78, 69, 68]  LF@[10]
MSG  73 (2L, max11): [67, 79, 79, 80, 69, 82, 65, 84, 73, 86, 69]  LF@[11]
MSG  74 (2L, max 9): [70, 82, 65, 84, 69, 82, 78, 65, 76]  LF@[9]
MSG  75 (2L, max14): [83, 72, 79, 82, 84, 13, 84, 69, 77, 80, 69, 82, 69, 68]  LF@[14]
MSG  76 (2L, max 9): [69, 67, 79, 78, 79, 77, 73, 83, 84]  LF@[9]
MSG  77 (2L, max 7): [76, 85, 83, 84, 70, 85, 76]  LF@[7]
MSG  78 (2L, max10): [78, 65, 82, 67, 73, 83, 83, 73, 83, 84]  LF@[10]
MSG  79 (2L, max 5): [77, 79, 79, 68, 89]  LF@[5]
MSG  80 (2L, max 6): [83, 65, 68, 73, 83, 84]  LF@[6]
MSG  81 (2L, max11): [84, 82, 73, 66, 65, 76, 0, 76, 79, 86, 69]  LF@[11]
MSG  82 (2L, max 4): [66, 79, 76, 68]  LF@[4]
MSG  83 (2L, max 8): [72, 79, 66, 66, 89, 73, 83, 84]  LF@[8]
MSG  84 (2L, max 6): [65, 84, 84, 65, 67, 75]  LF@[6]
MSG  85 (2L, max 8): [65, 67, 67, 85, 82, 65, 67, 89]  LF@[8]
MSG  86 (2L, max 7): [68, 69, 70, 69, 78, 83, 69]  LF@[7]
MSG  87 (2L, max 7): [69, 86, 65, 83, 73, 79, 78]  LF@[7]
MSG  88 (4L, max14): [66, 79, 82, 69, 83, 0, 69, 65, 83, 73, 76, 89, 14, 82, 69, 84, 85, 82, 78, 84, 79, 0, 84, 79, 87, 78, 0, 79, 70, 84, 69, 78, 14]  LF@[13, 20, 35]
MSG  89 (3L, max18): [83, 69, 78, 83, 69, 83, 0, 83, 80, 73, 82, 73, 84, 83, 14, 84, 82, 69, 77, 66, 76, 69, 83, 0, 65, 84, 0, 68, 69, 65, 84, 72, 14]  LF@[15, 34]
MSG  90 (5L, max16): [76, 73, 86, 69, 83, 0, 84, 79, 0, 72, 79, 65, 82, 68, 71, 79, 76, 68, 14, 65, 78, 71, 82, 89, 0, 73, 70, 0, 76, 79, 79, 84, 0, 73, 83, 76, 79, 87, 14]  LF@[14, 20, 37, 42]
MSG  91 (3L, max16): [68, 73, 83, 76, 73, 75, 69, 83, 0, 67, 82, 79, 87, 68, 83, 14, 67, 65, 76, 77, 69, 82, 0, 73, 78, 0, 70, 69, 87, 14]  LF@[16, 31]
MSG  92 (4L, max17): [76, 79, 86, 69, 83, 0, 66, 73, 71, 0, 71, 82, 79, 85, 80, 83, 14, 72, 65, 84, 69, 83, 0, 83, 77, 65, 76, 76, 80, 65, 82, 84, 73, 69, 83, 14]  LF@[17, 29, 38]
MSG  93 (3L, max18): [67, 65, 78, 7, 84, 0, 82, 69, 83, 73, 83, 84, 0, 76, 79, 79, 84, 14, 76, 73, 86, 69, 83, 0, 84, 79, 0, 67, 79, 76, 76, 69, 67, 84, 14]  LF@[18, 36]
MSG  94 (3L, max18): [68, 73, 83, 84, 82, 85, 83, 84, 83, 0, 82, 69, 67, 75, 76, 69, 83, 83, 65, 68, 86, 69, 78, 84, 85, 82, 69, 82, 83, 14]  LF@[18, 31]
MSG  95 (3L, max16): [70, 65, 83, 67, 73, 78, 65, 84, 69, 68, 0, 66, 89, 77, 79, 78, 83, 84, 69, 82, 0, 66, 73, 79, 76, 79, 71, 89, 14]  LF@[13, 30]
MSG  96 (4L, max18): [66, 69, 76, 73, 69, 86, 69, 83, 0, 73, 78, 0, 77, 89, 83, 84, 73, 67, 80, 79, 87, 69, 82, 14, 0, 76, 79, 86, 69, 83, 77, 65, 71, 73, 67, 14]  LF@[18, 31, 38]
MSG  97 (3L, max18): [83, 75, 73, 76, 76, 69, 68, 0, 87, 65, 82, 82, 73, 79, 82, 14, 83, 69, 69, 75, 83, 0, 83, 84, 82, 79, 78, 71, 0, 70, 79, 69, 83, 14]  LF@[16, 35]
MSG  98 (3L, max18): [77, 85, 83, 84, 0, 65, 68, 86, 69, 78, 84, 85, 82, 69, 14, 73, 68, 76, 69, 78, 69, 83, 83, 0, 73, 83, 0, 65, 71, 79, 78, 89, 14]  LF@[15, 34]
MSG  99 (3L, max16): [82, 69, 65, 67, 84, 83, 0, 75, 69, 69, 78, 76, 89, 0, 84, 79, 83, 85, 68, 68, 69, 78, 0, 69, 86, 69, 78, 84, 83, 14]  LF@[16, 31]
MSG 100 (5L, max13): [79, 66, 83, 69, 83, 83, 69, 68, 0, 87, 73, 84, 72, 84, 82, 65, 80, 83, 14, 67, 82, 85, 83, 72, 69, 68, 0, 66, 89, 83, 85, 67, 67, 69, 83, 83, 14]  LF@[13, 20, 31, 40]
MSG 101 (4L, max18): [65, 78, 88, 73, 79, 85, 83, 0, 73, 78, 68, 85, 78, 71, 69, 79, 78, 83, 14, 68, 82, 69, 65, 68, 83, 0, 84, 72, 69, 0, 85, 78, 68, 69, 65, 68, 14]  LF@[10, 20, 39]
MSG 102 (4L, max17): [86, 65, 76, 85, 69, 83, 0, 82, 69, 67, 89, 67, 76, 73, 78, 71, 14, 72, 65, 84, 69, 83, 0, 87, 65, 83, 84, 73, 78, 71, 73, 84, 69, 77, 83, 14]  LF@[17, 31, 38]
MSG 103 (4L, max16): [83, 84, 82, 79, 78, 71, 0, 77, 65, 73, 68, 69, 78, 66, 79, 78, 68, 83, 14, 78, 79, 0, 78, 69, 69, 68, 0, 70, 79, 82, 0, 77, 69, 78, 14]  LF@[13, 20, 37]
MSG 104 (5L, max14): [66, 69, 76, 73, 69, 86, 69, 83, 0, 87, 79, 77, 69, 78, 72, 65, 86, 69, 78, 79, 0, 80, 76, 65, 67, 69, 0, 73, 78, 66, 65, 84, 84, 76, 69, 14]  LF@[14, 19, 31, 39]
MSG 105 (5L, max13): [87, 79, 78, 7, 84, 0, 70, 79, 82, 71, 73, 86, 69, 84, 72, 79, 83, 69, 87, 72, 79, 0, 83, 76, 65, 89, 0, 84, 65, 77, 69, 70, 79, 69, 83, 14]  LF@[13, 19, 33, 39]
MSG 106 (3L, max18): [76, 73, 86, 69, 83, 0, 84, 79, 0, 83, 76, 65, 89, 0, 65, 76, 76, 14, 68, 69, 83, 80, 73, 83, 69, 83, 0, 82, 69, 84, 82, 69, 65, 84, 14]  LF@[18, 36]
MSG 107 (3L, max17): [86, 65, 76, 85, 69, 83, 0, 84, 69, 65, 77, 87, 79, 82, 75, 14, 72, 65, 84, 69, 83, 0, 71, 79, 73, 78, 71, 0, 83, 79, 76, 79, 14]  LF@[16, 34]
MSG 108 (4L, max16): [72, 65, 84, 69, 83, 0, 66, 76, 79, 79, 68, 83, 72, 69, 68, 14, 77, 79, 85, 82, 78, 83, 0, 70, 65, 76, 76, 69, 78, 65, 76, 76, 73, 69, 83, 14]  LF@[16, 30, 38]
MSG 109 (4L, max15): [83, 72, 79, 82, 84, 13, 84, 69, 77, 80, 69, 82, 69, 68, 14, 76, 79, 78, 71, 0, 70, 73, 71, 72, 84, 83, 69, 78, 82, 65, 71, 69, 14]  LF@[15, 27, 35]
MSG 110 (3L, max14): [66, 79, 82, 78, 0, 77, 69, 82, 67, 72, 65, 78, 84, 14, 76, 79, 86, 69, 83, 0, 84, 82, 65, 68, 69, 14]  LF@[14, 27]
MSG 111 (4L, max18): [76, 73, 75, 69, 83, 0, 79, 80, 80, 79, 83, 73, 84, 69, 83, 69, 88, 14, 66, 79, 82, 69, 68, 0, 66, 89, 0, 83, 65, 77, 69, 0, 83, 69, 88, 14]  LF@[14, 19, 38]
MSG 112 (4L, max16): [86, 65, 73, 78, 0, 78, 65, 82, 67, 73, 83, 83, 73, 83, 84, 14, 83, 72, 79, 67, 75, 69, 68, 0, 87, 72, 69, 78, 72, 65, 82, 77, 69, 68, 14]  LF@[16, 29, 37]
MSG 113 (4L, max17): [72, 65, 80, 80, 89, 0, 84, 72, 69, 78, 0, 65, 78, 71, 82, 89, 14, 85, 78, 80, 82, 69, 68, 73, 67, 84, 65, 66, 76, 69, 77, 79, 79, 68, 14]  LF@[17, 31, 37]
MSG 114 (5L, max11): [84, 72, 82, 73, 86, 69, 83, 0, 73, 78, 72, 65, 82, 68, 83, 72, 73, 80, 14, 72, 65, 84, 69, 83, 0, 66, 69, 73, 78, 71, 72, 69, 76, 80, 69, 68, 14]  LF@[10, 20, 32, 40]
MSG 115 (4L, max18): [66, 79, 78, 68, 83, 0, 87, 73, 84, 72, 0, 79, 87, 78, 82, 65, 67, 69, 14, 83, 72, 85, 78, 83, 0, 79, 84, 72, 69, 82, 0, 82, 65, 67, 69, 83, 14]  LF@[14, 20, 39]
MSG 116 (4L, max15): [69, 77, 80, 84, 89, 13, 72, 69, 65, 68, 69, 68, 14, 72, 65, 80, 80, 89, 0, 73, 70, 0, 79, 84, 72, 69, 82, 83, 65, 82, 69, 14]  LF@[13, 29, 34]
MSG 117 (3L, max18): [85, 83, 69, 0, 69, 86, 69, 82, 89, 84, 72, 73, 78, 71, 14, 72, 79, 65, 82, 68, 73, 78, 71, 0, 73, 83, 0, 65, 0, 83, 73, 78, 14]  LF@[15, 34]
MSG 118 (4L, max18): [39, 69, 78, 68, 69, 82, 0, 83, 69, 84, 83, 0, 66, 65, 83, 69, 83, 84, 65, 84, 83, 14, 0, 45, 69, 78, 29, 83, 84, 82, 79, 78, 71, 12, 87, 79, 77, 69, 78, 29, 87, 73, 83, 69, 14]  LF@[16, 35, 47]
MSG 119 (4L, max17): [40, 85, 77, 65, 78, 26, 0, 40, 73, 71, 72, 0, 70, 65, 73, 84, 72, 6, 0, 66, 65, 76, 65, 78, 67, 69, 68, 0, 83, 84, 65, 84, 83, 79, 86, 69, 82, 65, 76, 76, 14]  LF@[17, 34, 43]
MSG 120 (5L, max15): [37, 76, 70, 26, 0, 40, 73, 71, 72, 0, 41, 46, 52, 0, 6, 54, 41, 52, 66, 85, 84, 0, 70, 82, 65, 73, 76, 14, 0, 34, 69, 83, 84, 65, 84, 0, 77, 65, 71, 73, 67, 14]  LF@[15, 19, 35, 45]
MSG 121 (4L, max17): [39, 78, 79, 77, 69, 26, 0, 40, 73, 71, 72, 0, 70, 65, 73, 84, 72, 6, 0, 65, 71, 73, 76, 73, 84, 89, 14, 0, 51, 85, 73, 84, 69, 68, 70, 79, 82, 0, 48, 82, 73, 69, 83, 84, 83, 14]  LF@[17, 35, 48]
MSG 122 (4L, max16): [36, 87, 65, 82, 70, 26, 0, 51, 76, 79, 87, 0, 66, 85, 84, 83, 84, 82, 79, 78, 71, 0, 87, 73, 84, 72, 0, 68, 69, 69, 80, 70, 65, 73, 84, 72, 14, 0, 38, 73, 71, 72, 84, 69, 82, 83, 14]  LF@[15, 32, 49]
MSG 123 (4L, max17): [40, 79, 66, 66, 73, 84, 26, 0, 51, 77, 65, 76, 76, 0, 66, 85, 84, 65, 71, 73, 76, 69, 0, 65, 78, 68, 0, 76, 85, 67, 75, 89, 14, 34, 79, 82, 78, 0, 84, 72, 73, 69, 86, 69, 83, 14]  LF@[17, 34, 48]
MSG 124 (4L, max18): [39, 79, 79, 68, 29, 74, 85, 83, 84, 73, 67, 69, 14, 0, 45, 65, 89, 84, 85, 82, 78, 0, 37, 86, 73, 76, 14, 0, 38, 41, 39, 0, 45, 33, 39, 48, 50, 41, 0, 51, 33, 45, 0, 39, 41, 58, 0, 34, 41, 51, 11]  LF@[17, 36, 53]
MSG 125 (4L, max16): [46, 69, 85, 84, 82, 65, 76, 29, 78, 79, 0, 66, 73, 65, 83, 14, 38, 41, 39, 0, 52, 40, 41, 0, 45, 33, 39, 0, 51, 33, 45, 39, 41, 58, 0, 33, 44, 35, 0, 45, 47, 46]  LF@[16, 32, 44]
MSG 126 (4L, max18): [37, 86, 73, 76, 29, 83, 69, 76, 70, 13, 83, 69, 82, 86, 73, 78, 71, 14, 38, 41, 39, 0, 52, 40, 41, 0, 45, 33, 39, 0, 48, 50, 41, 46, 41, 46, 0, 34, 41, 51, 0, 33, 44, 35]  LF@[18, 34, 46]
MSG 127 (4L, max16): [67, 79, 77, 66, 65, 84, 0, 69, 88, 80, 69, 82, 84, 14, 67, 65, 78, 78, 79, 84, 0, 76, 69, 65, 82, 78, 0, 65, 78, 89, 77, 65, 71, 73, 67, 0, 83, 80, 69, 76, 76, 83, 14]  LF@[14, 31, 45]
MSG 128 (4L, max17): [44, 79, 87, 69, 82, 83, 0, 84, 82, 65, 80, 0, 76, 69, 86, 69, 76, 6, 0, 70, 73, 78, 68, 83, 0, 67, 72, 69, 83, 84, 83, 14, 51, 79, 82, 67, 69, 82, 89, 0, 44, 86, 19, 14]  LF@[17, 33, 46]
MSG 129 (4L, max18): [77, 65, 83, 84, 69, 82, 0, 79, 70, 0, 83, 79, 82, 67, 69, 82, 89, 14, 67, 65, 78, 0, 76, 69, 65, 82, 78, 0, 65, 76, 76, 83, 79, 82, 67, 69, 82, 89, 0, 83, 80, 69, 76, 76, 83, 14]  LF@[18, 32, 48]
MSG 130 (4L, max18): [40, 79, 76, 89, 0, 77, 65, 71, 73, 67, 0, 77, 65, 83, 84, 69, 82, 14, 35, 65, 78, 0, 36, 73, 83, 80, 69, 76, 0, 85, 78, 68, 69, 65, 68, 14, 33, 76, 76, 0, 40, 79, 76, 89, 0, 83, 80, 69, 76, 76, 83, 14]  LF@[18, 37, 54]
MSG 131 (5L, max18): [39, 82, 69, 65, 84, 0, 37, 56, 48, 0, 71, 65, 73, 78, 14, 35, 65, 78, 73, 78, 83, 84, 65, 78, 84, 13, 75, 73, 76, 76, 0, 70, 79, 69, 83, 14, 51, 79, 82, 67, 69, 82, 89, 0, 85, 80, 0, 84, 79, 0, 44, 86, 18, 14]  LF@[15, 19, 38, 57]
MSG 132 (5L, max14): [43, 78, 73, 71, 72, 84, 0, 71, 69, 65, 82, 85, 83, 65, 66, 76, 69, 14, 44, 69, 65, 82, 78, 83, 0, 51, 79, 82, 67, 69, 82, 89, 85, 80, 0, 84, 79, 0, 44, 86, 21, 14]  LF@[11, 19, 34, 45]
MSG 133 (5L, max17): [50, 69, 83, 84, 79, 82, 69, 83, 0, 40, 48, 14, 36, 73, 83, 80, 69, 76, 86, 83, 0, 85, 78, 68, 69, 65, 68, 14, 0, 51, 79, 82, 67, 0, 6, 40, 79, 76, 89, 0, 45, 65, 71, 73, 67, 0, 44, 86, 22, 14]  LF@[12, 19, 37, 53]
MSG 134 (4L, max17): [48, 79, 76, 69, 65, 88, 69, 0, 87, 69, 65, 80, 79, 78, 83, 14, 36, 73, 83, 80, 69, 76, 0, 86, 83, 0, 85, 78, 68, 69, 65, 68, 14, 40, 79, 76, 89, 0, 45, 65, 71, 73, 67, 0, 44, 86, 21, 14]  LF@[16, 34, 50]
MSG 135 (4L, max17): [40, 65, 78, 68, 76, 69, 83, 0, 65, 76, 67, 72, 69, 77, 89, 14, 51, 79, 82, 67, 0, 6, 0, 40, 79, 76, 89, 0, 45, 65, 71, 73, 67, 85, 80, 0, 84, 79, 0, 44, 86, 20, 14]  LF@[16, 34, 45]
MSG 136 (6L, max14): [44, 79, 78, 71, 66, 79, 87, 0, 85, 83, 69, 82, 14, 44, 79, 87, 69, 82, 83, 84, 82, 65, 80, 83, 12, 0, 83, 84, 69, 65, 76, 83, 73, 84, 69, 77, 83, 51, 79, 82, 67, 11, 40, 79, 76, 89, 0, 44, 86, 19, 14]  LF@[13, 20, 34, 40, 55]
MSG 137 (4L, max18): [51, 84, 65, 70, 70, 83, 0, 6, 0, 75, 78, 85, 67, 75, 76, 69, 83, 14, 36, 73, 83, 80, 69, 76, 0, 86, 83, 0, 85, 78, 68, 69, 65, 68, 14, 40, 79, 76, 89, 0, 45, 65, 71, 73, 67, 0, 44, 86, 21, 14]  LF@[18, 36, 52]
MSG 138 (5L, max17): [40, 79, 76, 89, 0, 65, 85, 82, 65, 0, 72, 69, 65, 76, 83, 40, 48, 14, 35, 65, 78, 0, 76, 69, 65, 82, 78, 0, 36, 73, 83, 80, 69, 76, 14, 51, 79, 82, 67, 11, 40, 79, 76, 89, 0, 44, 86, 22, 14]  LF@[15, 19, 37, 52]
MSG 139 (5L, max15): [50, 69, 77, 79, 86, 69, 83, 0, 67, 85, 82, 83, 69, 83, 70, 82, 79, 77, 69, 81, 85, 73, 80, 80, 69, 68, 0, 73, 84, 69, 77, 83, 14, 51, 79, 82, 67, 69, 82, 89, 0, 44, 86, 22, 14]  LF@[14, 19, 35, 48]
MSG 140 (4L, max18): [39, 82, 69, 65, 84, 0, 37, 56, 48, 0, 6, 0, 73, 78, 83, 84, 65, 13, 75, 73, 76, 76, 14, 0, 51, 69, 69, 83, 0, 73, 78, 0, 70, 79, 71, 14, 51, 79, 82, 67, 69, 82, 89, 0, 44, 86, 21, 14]  LF@[18, 37, 50]
MSG 141 (5L, max16): [36, 85, 65, 76, 0, 87, 73, 69, 76, 68, 83, 0, 83, 65, 77, 69, 87, 69, 65, 80, 79, 78, 0, 84, 89, 80, 69, 14, 44, 69, 65, 82, 78, 83, 51, 79, 82, 67, 69, 82, 89, 0, 44, 86, 22, 14]  LF@[16, 29, 36, 49]
MSG 142 (5L, max18): [44, 79, 78, 71, 66, 79, 87, 14, 0, 34, 69, 83, 84, 0, 84, 82, 65, 80, 83, 75, 73, 76, 76, 14, 0, 51, 84, 69, 65, 76, 83, 73, 84, 69, 77, 83, 51, 79, 82, 67, 11, 40, 79, 76, 89, 0, 44, 86, 20, 14]  LF@[18, 32, 38, 53]
MSG 143 (4L, max14): [65, 70, 70, 69, 67, 84, 83, 0, 68, 65, 77, 65, 71, 69, 68, 69, 65, 76, 84, 87, 73, 84, 72, 0, 87, 69, 65, 80, 79, 78, 83, 14]  LF@[14, 20, 34]
MSG 144 (4L, max15): [65, 70, 70, 69, 67, 84, 83, 0, 83, 79, 82, 67, 69, 82, 89, 80, 79, 87, 69, 82, 0, 65, 78, 68, 82, 69, 83, 73, 83, 84, 65, 78, 67, 69, 14]  LF@[15, 25, 37]
MSG 145 (4L, max18): [65, 70, 70, 69, 67, 84, 83, 0, 72, 79, 76, 89, 0, 77, 65, 71, 73, 67, 80, 79, 87, 69, 82, 0, 65, 78, 68, 82, 69, 83, 73, 83, 84, 65, 78, 67, 69, 14]  LF@[18, 28, 40]
MSG 146 (5L, max18): [65, 70, 70, 69, 67, 84, 83, 0, 77, 65, 88, 0, 72, 80, 12, 83, 84, 65, 84, 85, 83, 0, 82, 69, 83, 73, 83, 84, 65, 78, 67, 69, 12, 65, 78, 68, 0, 82, 69, 86, 73, 86, 65, 76, 83, 85, 67, 67, 69, 83, 83, 14]  LF@[15, 34, 46, 55]
MSG 147 (3L, max18): [65, 70, 70, 69, 67, 84, 83, 0, 84, 85, 82, 78, 0, 79, 82, 68, 69, 82, 73, 78, 0, 66, 65, 84, 84, 76, 69, 14]  LF@[18, 29]
MSG 148 (5L, max14): [65, 70, 70, 69, 67, 84, 83, 0, 66, 82, 69, 65, 84, 72, 82, 69, 83, 73, 83, 84, 0, 65, 78, 68, 67, 82, 73, 84, 73, 67, 65, 76, 72, 73, 84, 0, 67, 72, 65, 78, 67, 69, 14]  LF@[14, 25, 34, 46]
MSG 149 (2L, max 8): [71, 79, 79, 68, 0, 2, 71, 2]  LF@[8]
MSG 150 (2L, max11): [78, 69, 85, 84, 82, 65, 76, 0, 2, 78, 2]  LF@[11]
MSG 151 (2L, max 8): [69, 86, 73, 76, 0, 2, 69, 2]  LF@[8]
MSG 152 (2L, max 4): [71, 79, 79, 68]  LF@[4]
MSG 153 (2L, max 7): [78, 69, 85, 84, 82, 65, 76]  LF@[7]
MSG 154 (2L, max 4): [69, 86, 73, 76]  LF@[4]
MSG 155 (2L, max 1): [71]  LF@[1]
MSG 156 (2L, max 1): [78]  LF@[1]
MSG 157 (2L, max 1): [69]  LF@[1]
MSG 158 (2L, max 2): [44, 86]  LF@[2]
MSG 159 (2L, max 8): [35, 79, 77, 77, 79, 78, 69, 82]  LF@[8]
MSG 160 (2L, max 8): [40, 79, 79, 76, 73, 71, 65, 78]  LF@[8]
MSG 161 (2L, max 4): [37, 86, 73, 76]  LF@[4]
MSG 162 (2L, max10): [54, 69, 78, 79, 77, 0, 38, 65, 78, 71]  LF@[10]
MSG 163 (2L, max 7): [54, 41, 44, 44, 33, 41, 46]  LF@[7]
MSG 164 (2L, max 8): [39, 33, 46, 39, 51, 52, 37, 50]  LF@[8]
MSG 165 (2L, max 7): [67, 82, 85, 69, 76, 84, 89]  LF@[7]
MSG 166 (2L, max 7): [54, 41, 35, 41, 47, 53, 51]  LF@[7]
MSG 167 (2L, max 9): [68, 65, 78, 71, 69, 82, 79, 85, 83]  LF@[9]
MSG 168 (2L, max 9): [35, 53, 50, 41, 47, 51, 41, 52, 57]  LF@[9]
MSG 169 (2L, max 8): [35, 47, 45, 45, 47, 46, 37, 50]  LF@[8]
MSG 170 (2L, max10): [33, 36, 54, 37, 46, 52, 53, 50, 37, 50]  LF@[10]
MSG 171 (2L, max 5): [39, 53, 33, 50, 36]  LF@[5]
MSG 172 (2L, max 8): [34, 47, 44, 36, 46, 37, 51, 51]  LF@[8]
MSG 173 (2L, max 7): [34, 50, 33, 54, 37, 50, 57]  LF@[7]
MSG 174 (2L, max 6): [38, 33, 45, 47, 53, 51]  LF@[6]
MSG 175 (2L, max 7): [54, 37, 52, 37, 50, 33, 46]  LF@[7]
MSG 176 (2L, max 9): [35, 47, 46, 49, 53, 37, 50, 47, 50]  LF@[9]
MSG 177 (2L, max 4): [40, 37, 50, 47]  LF@[4]
MSG 178 (2L, max11): [49, 53, 37, 37, 46, 0, 39, 53, 33, 50, 36]  LF@[11]
MSG 179 (2L, max 8): [35, 47, 45, 45, 47, 46, 37, 50]  LF@[8]
MSG 180 (2L, max13): [40, 47, 46, 37, 51, 52, 0, 48, 37, 50, 51, 47, 46]  LF@[13]
MSG 181 (2L, max 4): [43, 41, 46, 36]  LF@[4]
MSG 182 (2L, max 8): [50, 37, 44, 41, 33, 34, 44, 37]  LF@[8]
MSG 183 (2L, max11): [39, 50, 37, 33, 52, 0, 40, 37, 33, 50, 52]  LF@[11]
MSG 184 (2L, max 8): [38, 33, 41, 50, 46, 37, 51, 51]  LF@[8]
MSG 185 (2L, max 5): [78, 79, 66, 76, 69]  LF@[5]
MSG 186 (2L, max11): [33, 35, 40, 41, 37, 54, 37, 45, 37, 46, 52]  LF@[11]
MSG 187 (2L, max 4): [51, 33, 39, 37]  LF@[4]
MSG 188 (2L, max 8): [39, 47, 36, 0, 40, 33, 46, 36]  LF@[8]
```

## Messages Still Containing Japanese (1)

| MSG | Text | JP Glyphs |
|-----|------|-----------|
| 0 | `ぅ 格 息 響 有 替 国 若 声 唱 造 挨 募 級 跡 取 店 袋 恩 宣 滅 奪 [1052] [1062] 喝 ` | 188=ぅ, 756=格, 764=息, 780=響, 790=有, 800=替, 810=国, 820=若, 830=声, 840=唱 |

## Messages with Unmapped Glyphs (1)

| MSG | Text | Unmapped IDs |
|-----|------|--------------|
| 0 | `ぅ 格 息 響 有 替 国 若 声 唱 造 挨 募 級 跡 取 店 袋 恩 宣 滅 奪 [1052] [1062] 喝 ` | [1052, 1062, 1082, 1120, 1128, 1144, 1158, 1168, 1182, 1196, 1212, 1232, 1238, 1244, 1262, 1288, 1304, 1318, 1332, 1348, 1366, 1388, 1416, 1434, 1460, 1476, 1492, 1516, 1534, 1554, 1574, 1590, 1610, 1632, 1652, 1670, 1698, 1724, 1750, 1780, 1800, 1830, 1852, 1880, 1906, 1918, 1942, 1968, 1990, 2022, 2044, 2062, 2086, 2100, 2116, 2142, 2154, 2174, 2190, 2210, 2228, 2246, 2320, 2392, 2480, 2546, 2626, 2702, 2768, 2832, 2912, 2986, 3058, 3124, 3208, 3290, 3370, 3448, 3530, 3612, 3688, 3760, 3840, 3914, 3972, 4052, 4130, 4208, 4292, 4374, 4446, 4518, 4616, 4706, 4800, 4900, 5002, 5102, 5212, 5304, 5400, 5494, 5590, 5690, 5802, 5920, 6014, 6124, 6228, 6322, 6436, 6544, 6652, 6752, 6856, 6958, 7068, 7140, 7218, 7302, 7416, 7478, 7574, 7594, 7620, 7640, 7652, 7670, 7682, 7688, 7694, 7700, 7708, 7728, 7748, 7760, 7784, 7802, 7822, 7840, 7858, 7880, 7902, 7922, 7946, 7960, 7980, 7998, 8014, 8032, 8054, 8066, 8092, 8112, 8142, 8154, 8174, 8200, 8220, 8234, 8260, 8272] |
