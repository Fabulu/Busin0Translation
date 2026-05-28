# Type-2 Resource Scene Map

## Methodology
- Loaded the 759-entry `data/msg_glyph_map.json` glyph table
- Read each type-2 resource from PACKDATA.DIG (using TOC sector offsets)
- Scanned raw bytes as big-endian uint16 for runs of valid glyph IDs (>=8 consecutive, >=40% hiragana+kanji)
- Cross-referenced decoded text fragments with `dumps/guide_full.txt` (the English fan translation guide)
- Note: Many kanji decode incorrectly due to incomplete glyph map coverage -- contextual matching was used

## Key Technical Finding
Type-2 resources do NOT use the standard FFFF/FFFE msg-encoding found in type-1/type-3 resources. Instead, dialogue text is embedded directly in the resource data as raw uint16 BE glyph sequences, interleaved with binary structural data. The "section 2" offset from `dialogue_resource_map.json` does NOT point to readable text in these resources -- the text is spread throughout the entire resource binary.

---

## Scene Map: 43 Type-2 Dialogue Resources

### GROUP 1: INTRO / OPENING SCENES (Player sees first)

| Resource | Scene | Key Evidence | Text Runs | Priority |
|----------|-------|-------------|-----------|----------|
| **R1196** | **Town Hub / Vigger Shop Intro + First City Events** | "ヴィガーしょうてん" (Vigger Shop), Orc dialogue in broken Japanese ("いらね～もの", "おとろし～のろい"), item buying/selling intro | 1388 | HIGHEST |
| **R1197** | **Bar Luna Light / Tavern Requests System** | Tavern counter service dialogue, request/commission system ("一事を光ける" = accepting requests), Jin the bartender | 1684 | HIGHEST |
| **R1198** | **Adventurer's Guild / Knight Order HQ** | "士騎戦ギルド" (Knight Guild), "討伐隊のメンバー" (subjugation party members), "エレンシカ" (Elenshika), quest board references | 134 | HIGH |

### GROUP 2: TOWN NPC EVENTS & STORY SCENES

| Resource | Scene | Key Evidence | Text Runs |
|----------|-------|-------------|-----------|
| **R1199** | **Guillaume (ギヨーム) / Ortrud (オルトルード) Story -- Alleid Lore** | "ギヨーム" (Guillaume), "オルトルード" (Ortrud = the Holy King), "アレイド" (Alleid), deep lore about the kingdom's history and magical bonds | 379 |
| **R1200** | **Church of Salem Events** | "迷宮第３名層" (Labyrinth 3rd floor), "パイプオルガン" (pipe organ), Church Sister dialogue, "シスター" (Sister), prayer scenes | 509 |
| **R1201** | **Adventurer's Inn / Konde Intro** | "コンデ" (Konde the sorcerer), "いらっしゃいませ、お落れ" (Welcome), inn rest scenes, "ローブに職を持んだ" (robed figure), waitress dialogue | 252 |
| **R1202** | **Vigger Shop Full Events / Orc Shop Expansion** | "ヴィガーしょうてん" (Vigger Shop), "オーク" (Orc shopkeeper), "ビラまきだいさくせん" (flyer distribution plan), "バザー" (bazaar), shop expansion events | 539 |
| **R1203** | **Vigger Shop Part-timer / Lucy Events** | "アルバイト" (part-time work), "オダ" (Oda the orc), "ルーシー" (Lucy), "カウンター" (counter), shop progression events, Vigger shop build-out | 2245 |

### GROUP 3: DUNGEON FLOORS (Karman's Labyrinth)

| Resource | Scene | Key Evidence | Text Runs |
|----------|-------|-------------|-----------|
| **R1204** | **B1F (Basement 1st Floor)** | "シムゾン" (Simson!), screaming/horror events ("たすけて!!", "俺の中に転らが!!"), leech-like creatures, first dungeon encounters, lever puzzles | 1279 |
| **R1205** | **B2F (Basement 2nd Floor)** | "レプラコーン" (Leprechaun NPC), "オークのパンツ" (Orc's Pants quest item), lever on/off puzzles, Leprechaun's inventions | 1226 |
| **R1206** | **B3F (Basement 3rd Floor)** | "ベルタン" (Bertrand NPC), "不法何理" (illegal dumping), monster ecology discussion, deeper exploration | 1314 |
| **R1207** | **B4F (Basement 4th Floor)** | "ウェブスター" (Webster), "ディアラント" (Diralanto -- ancient city), "５名層" (5th floor reference), "優臆美解" (Guillaume reference), switches and exploration | 1192 |
| **R1208** | **B5F (Basement 5th Floor)** | Ambush/trap events, knight encounters, "士騎戦の今" (knight dialogue), deeper narrative scenes, lever puzzles | 1158 |
| **R1209** | **B6F (Basement 6th Floor)** | "サキュバス" (Succubus), "ヨッペン" (Yoppen), door-locking puzzle, Succubus/Yoppen interaction scenes | 808 |
| **R1210** | **B7F (Basement 7th Floor)** | "イムプ" (Imp), "オーガのダンナ" (Ogre boss), locked door/key puzzles, Imp NPC dialogue, "カギ" (key) | 1019 |
| **R1211** | **B8F (Basement 8th Floor)** | "ワープゾーン" (Warp Zone), "ヴィガー化滅の立滅" (Vigger shop branch), deep story events, can't fight/flee scenario | 756 |
| **R1212** | **B9F (Basement 9th Floor)** | "ヨッペン" (Yoppen reappears), "たいようで捷かい におい" (warm sunlight-like smell), lost items, Vigger shop branch | 929 |
| **R1213** | **B10F-B11F / Final Dungeon Events** | "コンデ" (Konde), "ヴェーラ" (Vera), "シムゾン" (Simson), "ドゥーハン" (Duhan), final confrontation scenes, endgame dialogue | 57 |
| **R1353** | **B9F-B10F Additional Events / Post-game Content** | Overlaps with R1212 content (Yoppen), more lever puzzles, additional dungeon events, Vigger shop branch | 844 |
| **R1354** | **B5F-B7F Story Events / Webster Scenes** | "ウェブスター" (Webster), "セポイの王" (Sepoy's King), "オルトルード" (Ortrud), major plot revelations about ancient kingdom | 429 |
| **R1355** | **Dungeon Guard / Gate Events (All Floors)** | Guard/gatekeeper dialogue ("休前向いが、ここは" = sorry but this area...), discussion about subjugation parties, entry/progression checks | 100 |

### GROUP 4: MINIMAL/STRUCTURAL RESOURCES

| Resource | Scene | Key Evidence | Text Runs |
|----------|-------|-------------|-----------|
| **R816** | **Character Creation / Race-Class Data** | Katakana class/race names (ピ=Pixie?, ポ=?), character stat patterns, minimal text | 2 |
| **R1054** | **Battle System / Combat UI Data** | Structural combat data, ブベ別 patterns (menu elements), no readable dialogue | 1 |
| **R1079** | **Menu/UI Layout Data** | "錠ブ帰ブ帰" (lock/return menu items), structural UI data | 0 |
| **R1084** | **Monster/NPC Model Data** | Katakana monster names (モ,ド,ビ,ゴ patterns), embedded model/animation data with sparse text | 18 |
| **R1093** | **UI/Menu Templates** | "ボパ性業活回" (stat menu fragments), structural layout data | 0 |
| **R1145** | **Menu/Selection Screen Data** | "ブあ/いブ" (menu choice patterns), minimal structural text | 1 |
| **R1356** | **Dummy/Placeholder** | Contains only "ダミーテキスト" (Dummy Text) | 0 |
| **R1357** | **Dummy/Placeholder** | Contains only "ダミーテキスト" (Dummy Text) | 0 |
| **R1358-R1367** | **Battle/Monster Data Resources** | Structural battle data, monster stat tables, minimal readable text | 0-7 |
| **R1910** | **Minimal Data Resource** | Only 3 structural runs, no meaningful text | 1 |
| **R2141** | **Map/Layout Data** | Structural patterns, "づ" repetitions (map data), "オルトルード" possible reference | 3 |
| **R2144** | **Map/Layout Data** | Combat-related structural data, minimal text | 0 |
| **R2158** | **Map/Layout Data** | Structural tile/map patterns | 4 |
| **R2588** | **Minimal Data** | Only structural katakana patterns (ブ ブ ブ), no dialogue | 0 |
| **R2589** | **Minimal Data** | Only structural katakana patterns, no dialogue | 0 |
| **R2602** | **Minimal Data** | No text runs at all | 0 |
| **R2651** | **Large Structural Data** | 148KB, mostly ベ-pattern structural data, no readable dialogue | 0 |
| **R2652** | **Large Structural Data** | 200KB, structural/graphical data, minimal text | 3 |

---

## Chronological Play Order (What Players See First)

1. **R1196** -- FIRST: Town hub, initial Vigger Shop scene, first Orc encounter in town
2. **R1197** -- SECOND: Bar Luna Light, Vera introduction, tavern request system
3. **R1198** -- THIRD: Adventurer's Guild, knight order, quest acceptance
4. **R1201** -- FOURTH: Adventurer's Inn, Konde the sorcerer introduction
5. **R1200** -- FIFTH: Church of Salem events, prayer scenes
6. **R1199** -- SIXTH: Guillaume/Ortrud lore reveals (triggered by story progression)
7. **R1202** -- ONGOING: Vigger Shop expansion events (evolving)
8. **R1203** -- ONGOING: Vigger Shop part-timer/Lucy events (evolving)
9. **R1355** -- DUNGEON ENTRY: Guard/gatekeeper dialogue at dungeon entrance
10. **R1204** -- B1F: First dungeon floor
11. **R1205** -- B2F: Leprechaun encounters
12. **R1206** -- B3F: Bertrand NPC
13. **R1207** -- B4F: Webster, Diralanto
14. **R1354** -- B4F-B7F: Major Webster/Ortrud story scenes
15. **R1208** -- B5F: Ambush/knight encounters  
16. **R1209** -- B6F: Succubus/Yoppen
17. **R1210** -- B7F: Imp/Ogre events
18. **R1211** -- B8F: Warp zones, deep story
19. **R1212** -- B9F: Yoppen return, Vigger branch
20. **R1353** -- B9F-B10F: Additional events
21. **R1213** -- B10F-B11F: Endgame/finale (Konde, Vera, Simson, Duhan)

---

## Translation Priority Recommendations

### Tier 1 -- Immediate (Core Story, Player Sees First)
- R1196, R1197, R1198, R1199, R1200, R1201

### Tier 2 -- High (Town Events + Early Dungeon)
- R1202, R1203, R1204, R1205, R1206

### Tier 3 -- Medium (Mid-Late Dungeon)
- R1207, R1208, R1209, R1210, R1354, R1355

### Tier 4 -- Later (Late Dungeon + Endgame)
- R1211, R1212, R1213, R1353

### Tier 5 -- Low (Structural/UI, likely auto-generated)
- R816, R1054, R1079, R1084, R1093, R1145, R1356-R1367, R1910, R2141, R2144, R2158, R2588, R2589, R2602, R2651, R2652

---

## Key NPC Name Mappings Found

| Japanese (Decoded) | English (from Guide) | Appears In |
|-------------------|---------------------|------------|
| ヴェーラ | Vera Almohad | R1197, R1213 |
| コンデ | Konde (sorcerer) | R1201, R1213 |
| ウェブスター | Webster (lord) | R1207, R1354 |
| ギヨーム | Guillaume | R1199 |
| オルトルード | Ortrud (Holy King) | R1199, R1354 |
| シムゾン | Simson | R1204, R1213 |
| ベルタン | Bertrand | R1206 |
| ルーシー | Lucy | R1203 |
| レプラコーン | Leprechaun | R1205 |
| ヨッペン | Yoppen | R1209, R1212 |
| サキュバス | Succubus | R1209 |
| エレンシカ | Elenshika | R1198 |
| オダ | Oda (Orc) | R1202, R1203 |
| ディアラント | Diralanto | R1207 |
| ドゥーハン | Duhan (kingdom) | R1213, R1354 |
| セポイ | Sepoy | R1354 |

## Notes on Glyph Map Gaps
Many kanji are decoded incorrectly because the 759-entry glyph map has significant gaps:
- Common verbs/nouns appear as wrong kanji (e.g., "避" appears where "声" should be, "半物" for "怪物", etc.)
- The text is still identifiable by context (katakana names, hiragana grammar, sentence structure)
- Filling remaining ~500+ kanji glyph mappings would be needed for accurate full translation
