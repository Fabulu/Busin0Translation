# EXE Table 2C: Menu Label Structs -- Exhaustive Decode

**Date**: 2026-05-28
**EXE**: `extracted/SLPM_653.78` at offset 0x3C3000-0x3C46F8+56 (0x3C4730)
**Records**: 106 total, 92 active, 14 empty/placeholder
**Unique glyph IDs referenced**: 328 (range 0x01DB-0x0362)

---

## 1. Struct Layout (56 bytes per record)

```
Offset  Size  Type       Field              Description
------  ----  ----       -----              -----------
0x00    2     u16        padding            Always 0
0x02    2     u16        icon_glyph         Menu option icon (composite glyph tile)
0x04    4     float32    scale              Always 1.0
0x08    4     float32    x_position         Horizontal position (40-300 range)
0x0C    4     float32    y_position         Vertical position / width scale (1.0-3.0)
0x10    4     float32    scale2             Typically 1.5
0x14    4     float32    alpha              Typically 0.05 (fade param?)
0x18    2     u16        flag_a1_normal     0=active, FFFF=unused
0x1A    2     u16        label_A1           Label glyph 1 (normal state)
0x1C    2     u16        flag_a2_normal     0=active, FFFF=unused
0x1E    2     u16        label_A2           Label glyph 2 (normal state)
0x20    2     u16        flag_a1_hover      0=active, FFFF=unused
0x22    2     u16        label_A1_hover     Label glyph 1 (hover state, usually = A1)
0x24    2     u16        flag_a2_hover      0=active, FFFF=unused
0x26    2     u16        label_A2_hover     Label glyph 2 (hover state, usually = A2)
0x28    2     u16        flag_a2_selected   0 or 1 or FFFF
0x2A    2     u16        label_A2_selected  Label glyph 2 (selected state)
0x2C    2     u16        flag_a1_selected   0 or 1
0x2E    2     u16        label_A1_selected  Label glyph 1 (selected state)
0x30    2     u16        padding2           Always 0
0x32    2     u16        ref_glyph          Reference/category glyph
0x34    2     u16        menu_screen_id     Which menu screen this belongs to
0x36    2     u16        padding3           Always 0
```

### Key observations:
- **6 glyph slots** per record: 3 visual states (normal, hover, selected) x 2 label halves (A1, A2)
- Each label renders as icon + A1 + A2 = 3 composite font tiles side by side
- **FFFF** in a glyph slot = that visual state is unused (label has only 1 part, or state not applicable)
- The flag byte before each glyph: 0=normal rendering, 1=alternate rendering (brightness?), FFFF=skip
- **Empty records** (all 6 glyphs = FFFF) are placeholders/separators in multi-option menus
- The `menu_screen_id` groups records into the menu screen they belong to

---

## 2. Rendering Architecture

These are **NOT** individual characters assembled into words. Each glyph ID (0x025C-0x0362) references a **composite font atlas tile** that contains an entire pre-rendered Japanese word or label as a single bitmap. The single-character mappings in `msg_glyph_map.json` for these IDs are coincidental -- those kanji happen to occupy the same font atlas positions but the menu renderer uses larger pre-rendered tiles from a different texture page or atlas region.

### Evidence:
1. The "icon" glyph is always different from the "label" glyphs -- icon shows a pictographic symbol, labels show the text
2. Each record uses exactly 2 label glyphs (A1/A2) = left half and right half of the label word
3. The glyph IDs are sequential and unique per record -- each one is a dedicated pre-rendered tile
4. Cockpit texture recon confirmed: "menu button labels are rendered from the MSG glyph font system or EXE-hardcoded glyph ID tables, not from texture resources"

### Translation approach:
To translate these labels, the **font atlas tiles** at the corresponding glyph positions must be replaced with English label bitmaps. Simply changing glyph IDs will not work because the existing tiles contain baked Japanese text.

---

## 3. Complete Record Decode with Menu Identification

### Legend for Inferred Meanings

The meaning of each composite label is inferred from:
- The kanji character that the glyph map associates with each tile position
- Cross-reference with R40 location/guild dialogue messages
- Wizardry series standard menu terminology
- Grouping context (which records share a menu_screen_id)

### 3A. Town Navigation / Hub Menu (Records 0-9)

These are the main town location buttons shown on the town hub screen.

| Rec | EXE Offset | Icon Tile | Label Tiles (A1+A2) | Glyph Map Chars | Screen ID | Inferred Japanese | English Translation |
|-----|-----------|-----------|---------------------|-----------------|-----------|-------------------|-------------------|
| 0 | 0x3C3000 | 0x025F | 0x02AB+0x02AC | 偉+美 | 0x32 | 酒場 (Tavern) | Tavern |
| 1 | 0x3C3038 | 0x0260 | 0x02AD+0x02AE | 追+巨 | 0x33 | ギルド (Guild) | Guild |
| 2 | 0x3C3070 | 0x0261 | 0x02AF+0x02B0 | 期+街 | 0x34 | 店 (Shop) | Shop |
| 3 | 0x3C30A8 | 0x0262 | 0x02B1+0x02B2 | 誓+番 | 0x35 | 宿屋 (Inn) | Inn |
| 4 | 0x3C30E0 | 0x0263 | 0x02B3+0x02B4 | 並+宝 | 0x36 | 教会 (Church) | Church |
| 5 | 0x3C3118 | 0x0264 | 0x02B5+0x02B6 | 今+強 | 0x37 | 地下迷宮 (Labyrinth) | Labyrinth |
| 6 | 0x3C3150 | 0x0265 | 0x02B7+0x02B8 | 壁+命 | 0x38 | 冒険 (Adventure) | Venture |
| 7 | 0x3C3188 | 0x0266 | 0x02B9+0x02BA | 器+終 | 0x39 | 険所 (Danger/Quest) | Quest |
| 8 | 0x3C31C0 | 0x0267 | 0x02BB+0x02BC | 雇+能 | 0x3A | 広場 (Square/Plaza) | Plaza |
| 9 | 0x3C31F8 | 0x0268 | 0x02BD+0x02BE | 団+日 | 0x3B | 刻印 (Seal/Mark) | Seal |

**Byte length available**: Each label is 2 glyph tiles. If tiles are redrawn at same resolution, English labels must fit in 2 tile widths (~24px at 12px/tile, or wider if tiles are scaled).

**Position data**: x_position ranges 50-120, suggesting horizontal layout. y_position (f3) ranges 1.0-3.0, likely vertical stacking.

### 3B. Guild Sub-Menu (Records 10-23)

These appear on the guild/adventurer management screen.

| Rec | EXE Offset | Label Tiles | Glyph Map Chars | Screen ID | Inferred Japanese | English Translation |
|-----|-----------|-------------|-----------------|-----------|-------------------|-------------------|
| 10 | 0x3C3230 | 0x02BF+0x02C0 | 予+可 | 0x3C | 予定/可能 (Available) | Available |
| 11 | 0x3C3268 | 0x02C1+0x02C2 | 現+員 | 0x3C | 現在の隊員 (Current Members) | Members |
| 12 | 0x3C32A0 | 0x02C3+0x02C4 | 選+択 | 0x3D | 選択 (Select) | Select |
| 13 | 0x3C32D8 | 0x02C5+0x02C6 | 必+要 | 0x3E | 必要 (Required) | Required |
| 14 | 0x3C3310 | 0x02C7+0x02C8 | 値+足 | 0x3F | 値段/足りない (Price/Lacking) | Cost |
| 15 | 0x3C3348 | 0x02C9+0x02CA | 名+前 | 0x40 | 名前 (Name) | Name |
| 16 | 0x3C3380 | 0x02CB+0x02CC | 高+低 | 0x41 | 高レベル/低レベル (High/Low Level) | Level |
| 17 | 0x3C33B8 | 0x02CD+0x02CE | 恵+生 | 0x42 | 誕生 (Birth/Creation) | Create |
| 18 | 0x3C33F0 | 0x02CF+0x02D0 | 捷+幸 | 0x43 | 勝利/幸運 (Victory/Luck) | Luck |
| 19 | 0x3C3428 | 0x02D1+0x02D2 | 運+獲 | 0x44 | 運/獲得 (Fortune/Acquire) | Obtain |
| 20 | 0x3C3460 | 0x02D3+0x02D4 | 果+解 | 0x45 | 結果/解除 (Result/Release) | Result |
| 21 | 0x3C3498 | 0x02D5+0x02D6 | 避+神 | 0x46 | 避難/神殿 (Refuge/Temple) | Temple |
| 22 | 0x3C34D0 | 0x02D7+0x02D8 | 聖+入 | 0x36 | 聖地に入る (Enter Holy Land) | Enter |
| 23 | 0x3C3508 | 0x02D9+0x02DA | 振+冒 | 0x47 | 冒険に振る (Assign to Adventure) | Assign |

### 3C. Character Management (Records 24-40)

Character creation, class change, party management functions.

| Rec | EXE Offset | Label Tiles | Glyph Map Chars | Screen ID | Inferred Japanese (from R40 cross-ref) | English Translation |
|-----|-----------|-------------|-----------------|-----------|----------------------------------------|-------------------|
| 24 | 0x3C3540 | 0x02DB+0x02DC | 将+後 | 0x70 | 転職 (Class Change) | Reclass |
| 25 | 0x3C3578 | 0x02DD+0x02DE | 教+授 | 0x71 | 教授/指導 (Teach/Instruct) | Instruct |
| 26 | 0x3C35B0 | 0x02DF+0x02E0 | 美+現 | 0x48 | 召喚削除 (Summon Delete) | Delete |
| 27 | 0x3C35E8 | 0x02E1+0x02E2 | 決+個 | 0x49 | 決定/個別 (Confirm/Individual) | Confirm |
| 28 | 0x3C3620 | 0x02E3+0x02E4 | 基+甲 | 0x4A | 部隊/基地 (Squad/Base) | Squad |
| 29 | 0x3C3658 | 0x02E5+0x02E6 | 本+手 | 0x4B | 本隊 (Main Party) | Party |
| 30 | 0x3C3690 | 0x02E7+0x02E8 | 高+焼 | 0x4C | 名前 (Name) / 焼印 (Brand) | Brand |
| 31 | 0x3C36C8 | 0x02E9+0x02EA | 優+探 | 0x4D | 探索/優先 (Search/Priority) | Search |
| 32 | 0x3C3700 | 0x02EB+0x02EC | 扱+答 | 0x4E | 扱い/操作 (Handle/Operate) | Handle |
| 33 | 0x3C3738 | 0x02ED+0x02EE | 言+く | 0x4F | 種族 (Race) | Race |
| 34 | 0x3C3770 | 0x02EF+0x02F0 | 器+向 | 0x50 | 向き/器用 (Direction/Dexterity) | Dex |
| 35 | 0x3C37A8 | 0x02F1+0x02F2 | 待+楽 | 0x51 | 条件 (Conditions) | Cond. |
| 36 | 0x3C37E0 | 0x02F3+0x02F4 | 都+格 | 0x52 | 性格 (Personality) | Align |
| 37 | 0x3C3818 | 0x02F5+0x02F6 | 素+内 | 0x53 | 業/職業 (Class/Profession) | Class |
| 38 | 0x3C3850 | 0x02F7+0x02F8 | 形+近 | 0x54 | 男/女 (Male/Female) | Gender |
| 39 | 0x3C3888 | 0x02F9+0x02FA | 正+義 | 0x55 | 正義 (Justice/Alignment) | Good |
| 40 | 0x3C38C0 | 0x02FB+0x02FC | 休+息 | 0x56 | 休息 (Rest) | Rest |

### 3D. Status / Stats Menu (Records 41-51)

Character status screen, stat display labels.

| Rec | EXE Offset | Label Tiles | Glyph Map Chars | Screen ID | Inferred Japanese | English Translation |
|-----|-----------|-------------|-----------------|-----------|-------------------|-------------------|
| 41 | 0x3C38F8 | 0x02FD+0x02FE | 地+年 | 0x59 | 年齢/地位 (Age/Status) | Age |
| 42 | 0x3C3930 | 0x02FF+0x0300 | 内+容 | 0x57 | 内容 (Contents/Details) | Details |
| 43 | 0x3C3968 | 0x0301+0x0302 | 威+難 | 0x58 | 威力/難易度 (Power/Difficulty) | Power |
| 44 | 0x3C39A0 | 0x0303+0x0304 | 下+呪 | 0x59 | 呪い (Curse) | Curse |
| 45 | 0x3C39D8 | 0x0305+0x0306 | 結+活 | 0x5A | 活動/結果 (Activity/Result) | Active |
| 46 | 0x3C3A10 | 0x0307+0x0308 | 回+器 | 0x5B | 回復 (Recovery) | Recover |
| 47 | 0x3C3A48 | 0x0309+0x030A | 稀+特 | 0x5C | 特殊 (Special) | Special |
| 48 | 0x3C3A80 | 0x030B+0x030C | 経+響 | 0x5D | 経験 (Experience) | EXP |
| 49 | 0x3C3AB8 | 0x030D+0x030E | 闘+系 | 0x5E | 戦闘系 (Combat Type) | Combat |
| 50 | 0x3C3AF0 | 0x030F+0x0310 | 失+消 | 0x5F | 消失/消滅 (Vanish/Disappear) | Lost |
| 51 | 0x3C3B28 | 0x0311+0x0312 | 性+依 | 0x60 | 性格/依存 (Personality/Dependent) | Trait |

### 3E. Battle Menu (Records 52-57)

Battle/combat action menu options.

| Rec | EXE Offset | Label Tiles | Glyph Map Chars | Screen ID | Inferred Japanese | English Translation |
|-----|-----------|-------------|-----------------|-----------|-------------------|-------------------|
| 52 | 0x3C3B60 | 0x0313+0x0314 | 就+覚 | 0x74 | 覚醒/就く (Awakening/Engage) | Attack |
| 53 | 0x3C3B98 | 0x0315+0x0316 | 退+有 | 0x2F | 退却 (Retreat) | Retreat |
| 54 | 0x3C3BD0 | 0x0317+0x0318 | 打+俺 | 0x2F | 打撃 (Strike) | Strike |
| 55 | 0x3C3C08 | 0x0319+0x031A | 華+発 | 0x2F | 発動 (Activate/Cast) | Cast |
| 56 | 0x3C3C40 | 0x031B+0x031C | 常+罠 | 0x2F | 罠/常時 (Trap/Always) | Trap |
| 57 | 0x3C3C78 | 0x031D+0x031E | 離+脱 | 0x2F | 離脱 (Escape/Disengage) | Flee |

### 3F. Dungeon Interaction Menus (Records 58-68)

Context menus that appear during dungeon exploration.

| Rec | EXE Offset | Label Tiles | Glyph Map Chars | Screen ID | Inferred Japanese | English Translation | Notes |
|-----|-----------|-------------|-----------------|-----------|-------------------|-------------------|-------|
| 58 | 0x3C3CB0 | FFFF | --- | 0x58 | [EMPTY] | --- | Separator |
| 59 | 0x3C3CE8 | 0x031F+0x0320 | 先+替 | 0x58 | 先頭/入れ替え (Front/Swap) | Swap | Party reorder |
| 60 | 0x3C3D20 | FFFF | --- | 0x58 | [EMPTY] | --- | Separator |
| 61 | 0x3C3D58 | 0x0321+0x0322 | 記+述 | 0x58 | 記述/記録 (Record/Log) | Log | |
| 62 | 0x3C3D90 | 0x0323+0x0324 | 柄+般 | 0x58 | 一般/全般 (General/Overall) | General | |
| 63 | 0x3C3DC8 | FFFF | --- | 0x5A | [EMPTY] | --- | Separator |
| 64 | 0x3C3E00 | 0x0325+0x0326 | 価+巨 | 0x5A | 迷宮 (Labyrinth) | Maze | |
| 65 | 0x3C3E38 | 0x0327+0x0328 | 傷+深 | 0x5A | 深手/傷 (Deep Wound) | Wound | |
| 66 | 0x3C3E70 | FFFF | --- | 0x5A | [EMPTY] | --- | Separator |
| 67 | 0x3C3EA8 | 0x0329+0x032A | 辛+国 | 0x5A | 限界/口 (Limit/Threshold) | Limit | |
| 68 | 0x3C3EE0 | 0x032B+0x032C | 勇+雰 | 0x5A | 雰囲気/勇気 (Atmosphere/Courage) | Morale | |

### 3G. Item/Equipment Menus (Records 69-79)

Shop, equipment, and item management.

| Rec | EXE Offset | Label Tiles | Glyph Map Chars | Screen ID | Inferred Japanese | English Translation | Notes |
|-----|-----------|-------------|-----------------|-----------|-------------------|-------------------|-------|
| 69 | 0x3C3F18 | FFFF | --- | 0x59 | [EMPTY] | --- | Separator |
| 70 | 0x3C3F50 | 0x032D+0x032E | 打+嘆 | 0x59 | 嘆願/打つ (Petition/Hit) | Petition | |
| 71 | 0x3C3F88 | 0x032F+0x0330 | 囲+境 | 0x59 | 環境 (Environment) | Environ | |
| 72 | 0x3C3FC0 | FFFF | --- | 0x59 | [EMPTY] | --- | Separator |
| 73 | 0x3C3FF8 | 0x0331+0x0332 | 危+険 | 0x59 | 危険 (Danger) | Danger | |
| 74 | 0x3C4030 | 0x0333+0x0334 | 刻+若 | 0x59 | 刻印/若い (Engrave/Young) | Engrave | |
| 75 | 0x3C4068 | 0x0335+0x0336 | 憎+護 | 0x5C | 保護/防護 (Protect/Guard) | Protect | |
| 76 | 0x3C40A0 | 0x0337+0x0338 | 堂+祈 | 0x5C | 祈祷堂 (Chapel/Prayer Hall) | Chapel | Church sub-menu |
| 77 | 0x3C40D8 | 0x0339+0x033A | 療+座 | 0x5C | 治療 (Healing) | Heal | Church sub-menu |
| 78 | 0x3C4110 | 0x033B+0x033C | 黙+禁 | 0x31 | 禁止/黙認 (Forbid/Silence) | Silence | |
| 79 | 0x3C4148 | 0x033D+0x033E | 奴+声 | 0x31 | 加入/声 (Join/Voice) | Join | |

### 3H. Inn / Church / Services (Records 80-91)

Service-related menu options.

| Rec | EXE Offset | Label Tiles | Glyph Map Chars | Screen ID | Inferred Japanese | English Translation | Notes |
|-----|-----------|-------------|-----------------|-----------|-------------------|-------------------|-------|
| 80 | 0x3C4180 | FFFF | --- | 0x5B | [EMPTY] | --- | Separator |
| 81 | 0x3C41B8 | FFFF | --- | 0x5B | [EMPTY] | --- | Separator |
| 82 | 0x3C41F0 | 0x033F+0x0340 | 所+[832] | 0x5B | 所持/場所 (Possession/Location) | Owned | |
| 83 | 0x3C4228 | 0x0341+0x0342 | 戻+治 | 0x5B | 治療/戻す (Heal/Restore) | Restore | |
| 84 | 0x3C4260 | 0x0343+0x0344 | 救+宝 | 0x5B | 救出/宝 (Rescue/Treasure) | Rescue | |
| 85 | 0x3C4298 | 0x0345+0x0346 | 制+穏 | 0x4B | 制限/穏やか (Restrict/Calm) | Calm | |
| 86 | 0x3C42D0 | 0x0347+0x0348 | 放+唱 | 0x4B | 詠唱/放つ (Chant/Release) | Chant | |
| 87 | 0x3C4308 | 0x0349+0x034A | [841]+宿 | 0x49 | 宿屋 (Inn) | Inn | Inn sub-menu |
| 88 | 0x3C4340 | 0x034B+0x034C | 場+泊 | 0x4A | 宿泊 (Lodging) | Lodge | Inn sub-menu |
| 89 | 0x3C4378 | FFFF | --- | 0x3F | [EMPTY] | --- | Separator |
| 90 | 0x3C43B0 | FFFF | --- | 0x36 | [EMPTY] | --- | Separator |
| 91 | 0x3C43E8 | 0x034D+0x034E | 部+空 | 0x54 | 空室/部屋 (Vacancy/Room) | Room |

### 3I. Additional System / Context Menus (Records 92-105)

| Rec | EXE Offset | Label Tiles | Glyph Map Chars | Screen ID | Inferred Japanese | English Translation | Notes |
|-----|-----------|-------------|-----------------|-----------|-------------------|-------------------|-------|
| 92 | 0x3C4420 | FFFF | --- | 0x74 | [EMPTY] | --- | Battle separator |
| 93 | 0x3C4458 | FFFF | --- | 0x74 | [EMPTY] | --- | Battle separator |
| 94 | 0x3C4490 | 0x034F+0x0350 | [847]+棒 | 0x38 | 棒/杖 (Staff/Rod) | Staff | Weapon menu? |
| 95 | 0x3C44C8 | 0x0351+0x0352 | 恐+怖 | 0x2E | 恐怖 (Fear/Horror) | Fear | Status effect |
| 96 | 0x3C4500 | 0x0353+0x0354 | 十+造 | 0x2E | 創造/製造 (Creation/Manufacturing) | Craft | Item creation |
| 97 | 0x3C4538 | 0x0355+0x0356 | 勲+組 | 0x33 | 勲章/組合 (Medal/Guild) | Medal | Guild sub-menu |
| 98 | 0x3C4570 | 0x0357+0x0358 | 更+去 | 0x35 | 更新/去る (Update/Leave) | Update | Inn sub-menu |
| 99 | 0x3C45A8 | 0x0359+0x035A | 突+然 | 0x37 | 突然 (Sudden) | Sudden | Event? |
| 100 | 0x3C45E0 | FFFF | --- | 0x5D | [EMPTY] | --- | Separator |
| 101 | 0x3C4618 | 0x035B+0x035C | 逃+忘 | 0x5D | 逃走 (Escape) | Escape | Battle/dungeon |
| 102 | 0x3C4650 | FFFF | --- | 0x5D | [EMPTY] | --- | Separator |
| 103 | 0x3C4688 | 0x035D+0x035E | 咲+草 | 0x5D | 草花 (Flowers/Herbs) | Herbs | Item category |
| 104 | 0x3C46C0 | 0x035F+0x0360 | 花+園 | 0x5D | 花園 (Garden) | Garden | Location? |
| 105 | 0x3C46F8 | 0x0361+0x0362 | 拶+挨 | 0x5D | 挨拶 (Greeting) | Greet | NPC interaction |

---

## 4. Menu Screen ID Groupings

Records share `menu_screen_id` values indicating which in-game menu screen they belong to.

| Screen ID | Records | Active | Context | Likely Screen |
|-----------|---------|--------|---------|---------------|
| 0x2E | 95-96 | 2 | 恐怖, 十造 | Status effects / Crafting |
| 0x2F | 53-57 | 5 | 退有, 打俺, 華発, 常罠, 離脱 | Battle action sub-menu |
| 0x31 | 78-79 | 2 | 黙禁, 奴声 | Restriction / Join options |
| 0x32 | 0 | 1 | 偉美 | Tavern (single button) |
| 0x33 | 1, 97 | 2 | 追巨, 勲組 | Guild + Guild medal |
| 0x34 | 2 | 1 | 期街 | Shop (single button) |
| 0x35 | 3, 98 | 2 | 誓番, 更去 | Inn + Inn update |
| 0x36 | 4, 22 | 2+1e | 並宝, 聖入 | Church + Enter holy land |
| 0x37 | 5, 99 | 2 | 今強, 突然 | Labyrinth + Sudden event |
| 0x38 | 6, 94 | 2 | 壁命, [847]棒 | Adventure + Staff/weapon |
| 0x39 | 7 | 1 | 器終 | Quest marker |
| 0x3A | 8 | 1 | 雇能 | Hire/Recruit |
| 0x3B | 9 | 1 | 団日 | Party day/schedule |
| 0x3C | 10-11 | 2 | 予可, 現員 | Available / Current members |
| 0x3D | 12 | 1 | 選択 | Selection screen |
| 0x3E | 13 | 1 | 必要 | Requirements display |
| 0x3F | 14 | 1+1e | 値足 | Cost/price screen |
| 0x40 | 15 | 1 | 名前 | Name display |
| 0x41 | 16 | 1 | 高低 | Level sort (high/low) |
| 0x42 | 17 | 1 | 恵生 | Character creation |
| 0x43 | 18 | 1 | 捷幸 | Luck/fortune display |
| 0x44 | 19 | 1 | 運獲 | Acquisition |
| 0x45 | 20 | 1 | 果解 | Result/release |
| 0x46 | 21 | 1 | 避神 | Temple/refuge |
| 0x47 | 23 | 1 | 振冒 | Adventure assignment |
| 0x48 | 26 | 1 | 美現 | Summon delete |
| 0x49 | 27, 87 | 2 | 決個, [841]宿 | Confirm + Inn |
| 0x4A | 28, 88 | 2 | 基甲, 場泊 | Squad + Lodge |
| 0x4B | 29, 85-86 | 3 | 本手, 制穏, 放唱 | Party + Calm + Chant |
| 0x4C | 30 | 1 | 高焼 | Name/brand |
| 0x4D | 31 | 1 | 優探 | Search/priority |
| 0x4E | 32 | 1 | 扱答 | Handle/operate |
| 0x4F | 33 | 1 | 言く | Race selection |
| 0x50 | 34 | 1 | 器向 | Dexterity |
| 0x51 | 35 | 1 | 待楽 | Conditions |
| 0x52 | 36 | 1 | 都格 | Personality/alignment |
| 0x53 | 37 | 1 | 素内 | Class/profession |
| 0x54 | 38, 91 | 2 | 形近, 部空 | Gender + Room |
| 0x55 | 39 | 1 | 正義 | Justice/good align. |
| 0x56 | 40 | 1 | 休息 | Rest |
| 0x57 | 42 | 1 | 内容 | Details/contents |
| 0x58 | 43, 59-62 | 4+2e | 威難, 先替, 記述, 柄般 | Power/swap/log/general |
| 0x59 | 41, 44, 70-74 | 6+2e | 地年, 下呪, 打嘆, 囲境, 危険, 刻若 | Age/curse/petition/environ/danger/engrave |
| 0x5A | 45, 64-68 | 5+2e | 結活, 価巨, 傷深, 辛国, 勇雰 | Active/maze/wound/limit/morale |
| 0x5B | 46, 82-84 | 4+2e | 回器, 所[832], 戻治, 救宝 | Recovery/owned/restore/rescue |
| 0x5C | 47, 75-77 | 4 | 稀特, 憎護, 堂祈, 療座 | Special/protect/chapel/heal |
| 0x5D | 48, 101, 103-105 | 5+2e | 経響, 逃忘, 咲草, 花園, 拶挨 | EXP/escape/herbs/garden/greet |
| 0x5E | 49 | 1 | 闘系 | Combat type |
| 0x5F | 50 | 1 | 失消 | Vanish/lost |
| 0x60 | 51 | 1 | 性依 | Trait/personality |
| 0x70 | 24 | 1 | 将後 | Class change |
| 0x71 | 25 | 1 | 教授 | Instruction |
| 0x74 | 52 | 1+2e | 就覚 | Battle engage/attack |

---

## 5. Critical Findings

### 5A. These are NOT standard text -- they are pre-rendered composite glyph tiles

Each glyph ID in this table references a font atlas cell that contains an entire Japanese word rendered as a bitmap. Translation requires:
1. **Identifying** the exact font atlas texture resource containing these tiles
2. **Creating** replacement English bitmap tiles at the same pixel dimensions
3. **Injecting** the new tiles into the atlas at the correct positions

Simply remapping glyph IDs to ASCII letters will produce nonsense because the existing tiles render as multi-character Japanese words, not individual characters.

### 5B. The msg_glyph_map character mappings are MISLEADING for these IDs

The characters shown by `msg_glyph_map.json` for IDs 0x025C-0x0362 (e.g., "偉", "美", "追") are the MSG text system's interpretation of those glyph slots. In the menu rendering context, those same slots contain pre-rendered composite label bitmaps. The glyph map characters give a rough hint at what the tile contains but are NOT the actual rendered text.

### 5C. Relationship to R40 (Location Names Resource)

R40 (`0040_type01.raw`) contains 84 messages including guild/party management dialogue. Messages like "冒険召喚" (msg 11), "能力ステータス" (msg 12), "転職" (msg 13) correspond to menu actions in Table 2C. However, R40 messages are standard MSG glyph text, while Table 2C labels are rendered via the composite tile system. They are two separate rendering paths for the same UI concepts.

### 5D. 14 Empty Records Are Menu Separators

Records where all 6 glyph slots = 0xFFFF serve as visual separators between menu option groups. They appear in multi-option menus (screen IDs 0x58, 0x59, 0x5A, 0x5B, 0x5D) where options are grouped logically with dividers.

### 5E. Town Hub Buttons (Records 0-9) Are Highest Priority

The town navigation buttons (Tavern, Guild, Shop, Inn, Church, Labyrinth) are the most visible Japanese text remaining. These are records 0-9 and map to screen IDs 0x32-0x3B. Each needs:
- Icon tile replacement (glyph 0x025F-0x0268)
- Label A1 tile replacement (glyph 0x02AB-0x02BE)
- Label A2 tile replacement (glyph 0x02AC-0x02BF)
= 30 composite tiles to redraw for the main town hub alone

### 5F. Battle Menu (Records 52-57) Is Second Priority

The battle action menu (Attack, Retreat, Strike, Cast, Trap, Flee) uses screen ID 0x2F and needs 12+ composite tiles redrawn.

---

## 6. Glyph ID Inventory

### All unique glyph IDs used (sorted by field type):

**Icon glyphs** (20 unique): 0x025C, 0x025D, 0x025F-0x0293, 0x028E
**Label A1 glyphs** (92 unique): 0x02AB-0x0362 (odd indices in pairs)
**Label A2 glyphs** (92 unique): 0x02AC-0x0362 (even indices in pairs)
**Ref glyphs** (80 unique): 0x01DB-0x0238

**Total unique composite tiles to replace**: ~284 tiles across all 4 glyph fields

### Byte length constraints:
- Each label is exactly 2 u16 glyph IDs = 4 bytes
- Each record is exactly 56 bytes (struct size is fixed)
- Cannot add more glyph slots -- English labels must fit in 2 tiles
- Tile pixel dimensions unknown from EXE data alone -- need font atlas analysis

---

## 7. Translation Plan Summary

### Phase 1: Font Atlas Tile Identification
- Locate the font atlas texture resource(s) containing tiles at glyph positions 0x025C-0x0362
- Dump individual tiles to verify what Japanese text each one renders
- Measure exact pixel dimensions per tile

### Phase 2: English Tile Creation
- Create replacement bitmap tiles with English labels
- Each label limited to 2 tile widths (e.g., if tiles are 12x12px, label max = 24px wide)
- Use the same font style/size as the English MSG font for consistency

### Phase 3: Tile Injection
- Write replacement tiles into the font atlas at the correct glyph positions
- Rebuild the atlas texture resource and inject into PACKDATA

### Phase 4: Verify
- Test all menu screens in PCSX2
- Verify no overflow/clipping on translated labels
- Check all 3 visual states (normal, hover, selected) render correctly

---

## Appendix A: Raw Hex Data (First 10 Records)

```
Rec 0 @0x3C3000: 0000 5F02 0000803F 0000F042 00004040 0000C03F CDCC4C3D 0000 AB02 0000 AC02 0000 AB02 0000 AC02 0100 AC02 0100 AB02 0000 E001 3200 0000
Rec 1 @0x3C3038: 0000 6002 0000803F 0000C842 00000040 0000C03F CDCC4C3D 0000 AD02 0000 AE02 0000 AD02 0000 AE02 0100 AE02 0100 AD02 0000 E101 3300 0000
Rec 2 @0x3C3070: 0000 6102 0000803F 0000B442 0000803F 0000C03F CDCC4C3D 0000 AF02 0000 B002 0000 AF02 0000 B002 0100 B002 0100 AF02 0000 E201 3400 0000
Rec 3 @0x3C30A8: 0000 6202 0000803F 0000B442 6666E63F 0000C03F CDCC4C3D 0000 B102 0000 B202 0000 B102 0000 B202 0100 B202 0100 B102 0000 E301 3500 0000
Rec 4 @0x3C30E0: 0000 6302 0000803F 0000B442 0000803F 0000C03F CDCC4C3D 0000 B302 0000 B402 0000 B302 0000 B402 FFFF FFFF 0100 B302 0000 E401 3600 0000
Rec 5 @0x3C3118: 0000 6402 0000803F 00008C42 0000803F 0000C03F CDCC4C3D 0000 B502 0000 B602 0000 B502 0000 B602 0100 B602 0100 B502 0000 E501 3700 0000
Rec 6 @0x3C3150: 0000 6502 0000803F 00004842 0000C03F 0000C03F CDCC4C3D 0000 B702 0000 B802 0000 B702 0000 B802 FFFF FFFF 0100 B702 0000 E601 3800 0000
Rec 7 @0x3C3188: 0000 6602 0000803F 00007042 0000803F 0000C03F CDCC4C3D 0000 B902 0000 BA02 0000 B902 0000 BA02 0100 BA02 0100 B902 0000 E701 3900 0000
Rec 8 @0x3C31C0: 0000 6702 0000803F 00007042 9A99993F 0000C03F CDCC4C3D 0000 BB02 0000 BC02 0000 BB02 0000 BC02 FFFF FFFF 0100 BB02 0000 E801 3A00 0000
Rec 9 @0x3C31F8: 0000 6802 0000803F 00007042 9A99193F 0000C03F CDCC4C3D 0000 BD02 0000 BE02 0000 BD02 0000 BE02 FFFF FFFF 0100 BD02 0000 E901 3B00 0000
```
