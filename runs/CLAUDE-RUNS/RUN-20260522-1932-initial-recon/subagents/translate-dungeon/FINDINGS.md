# Dungeon & Story Translation Findings

## Summary

Matched decoded Japanese game text from Resources 46, 47, 49, and 2654 against the English fan guide (`guide_full.txt`). Produced `data/translations_dungeon_story.json` containing 167 translated entries.

## Resources Covered

### Resource 46 - Tavern Bulletin Board (7 messages translated)
Community messages posted by Duhan citizens. Matched against guide section "QUICK LOOK AT THE MESSAGE BOARD" (guide line 1638+).

Key matches:
- **MSG 1**: Gin's bulletin board establishment notice -- exact match to guide line 1639
- **MSG 2**: Miri cancelling Kreta stone request -- directly references Tavern Request #2 (guide line 1980)
- **MSG 3-6**: Self Shop key discussion, Vigger Shop part-time job posting and Orc applicant exchange
- **MSG 7**: Adventurer's account of B4F exploration finding a Hobbit and Imp -- matches guide's B4F NPC mentions

### Resource 47 - Battle/Treasure System Messages (30 messages translated)
All 30 decoded messages translated. Core battle loop text.

Key matches:
- **MSG 2**: "Friendly monsters!!" -- matches guide friendly encounter type
- **MSG 5-7**: Surprise/ambush/initiative messages
- **MSG 11-16**: Treasure chest unlock sequence
- **MSG 15**: "You learned a new AA!" -- matches guide line 15822 ("You learned a new Coordinated Attack (Alleid)")
- **MSG 17-19**: Acquire/Dispel/Steal commands -- matched to guide lines 1839-1845
- **MSG 40-48**: All 9 trap type names confirmed: Spear, Dark Fog, Crossbow, Roof Fall, MP Drain, Poison Gas, Alarm, Stone Gas, Teleporter

### Resource 49 - Dungeon Exploration (111 messages, all translated)
Complete environmental description set for dungeon exploration.

Notable findings:
- **MSG 0**: "Nothing unusual" -- investigation default, matches guide line 2231
- **MSG 2**: Breakable wall hint ("fragile wall that looks like it could crumble")
- **MSG 34-37,52**: Treasure chest interaction sequence (open/empty/full inventory/give up/already opened)
- **MSG 38**: Trap detection prefix ("A [type] trap is set")
- **MSG 69-72,97-99**: Warp destinations cover B1F, B3F, B4F, B5F, B6F, B8F, B10F
- **MSG 82-87**: Eerie statue descriptions (multiple variants for different dungeon encounters)
- **MSG 94,110**: "Beautiful shrine" and "beautiful altar" -- altar matches B1F Altar location from Tavern Request #3
- **MSG 106**: Automata discovery ("An Automata is lurking here")

### Resource 2654 - Alleid Action Descriptions (32 messages, all translated)
All 32 cooperative combat technique descriptions matched to English guide (guide lines 5883-6317).

Complete mapping of AA names:

| MSG | Japanese AA | English Name | Guide Type |
|-----|-----------|--------------|------------|
| 1 | W-Slash description | W-SLASH | Attack Ch.1 |
| 2 | Hold Attack description | HOLD ATTACK | Attack Ch.2 |
| 3 | Stun Smash description | STUN SMASH | Attack Ch.3 |
| 4 | SJ Attack description | SJ ATTACK | Attack Ch.7 |
| 5 | Slay Crash description | SLAY CRASH | Attack Req.#9 |
| 6 | Cross-Gauge Kill description | CROSS-GAUGE KILL | Attack Ch.8 |
| 7 | Front Guard description | FRONT GUARD | Defense Ch.1 |
| 8 | Magic Shield description | MAGIC SHIELD | Defense Ch.6 |
| 9 | Anti-Magic Shell description | ANTI-MAGIC SHELL | Defense Ch.9 |
| 10 | Mirror Image description | MIRROR IMAGE | Defense Ch.7 |
| 11 | Evasive Maneuver description | EVASIVE MANEUVER | Defense Ch.4 |
| 12 | Dense Formation description | DENSE FORMATION | Defense Found |
| 13 | Restrict Shot description | RESTRICT SHOT | Support Ch.1 |
| 14 | Support Shot description | SUPPORT SHOT | Support Found |
| 15 | Magic Cancel description | MAGIC CANCEL | Support Ch.2 |
| 16 | Breath Cancel description | BREATH CANCEL | Support 50 Jobs |
| 17 | Back Cover description | BACK COVER | Support Ch.5 |
| 18 | Intercept description | INTERCEPT | Support Ch.4 |
| 19 | Concentrated Spell description | CONCENTRATED SPELL | Magic Ch.2 |
| 20 | Silence Breaker description | SILENCE BREAKER | Magic Req.#23 |
| 21 | Magic Rapid Fire description | MAGIC RAPID FIRE | Magic Found |
| 22 | Enchant description | ENCHANT | Magic Found |
| 23 | Magic Cooperation description | MAGIC COOPERATION | Magic Found |
| 24 | Concentrated Attack description | CONCENTRATED ATTACK | Attack Ch.6 |
| 25 | Back Attack description | BACK ATTACK | Attack Ch.4 |
| 26 | Gale Slash description | GALE SLASH | Attack Alt |
| 27 | Rush description | RUSH | Attack Found |
| 28 | Fake Attack description | FAKE ATTACK | Attack Alt |
| 29 | Sacred Cross description | SACRED CROSS | Attack Found |
| 30 | Warp Attack description | WARP ATTACK | Attack Lottery |
| 31 | Soul Crash description | SOUL CRASH | Attack Alt |
| 32 | Sonic Sword description | SONIC SWORD | Attack Alt |

## Decoding Artifacts

The decoded text contains systematic character substitutions due to incomplete glyph mapping. Recurring patterns identified:

- 鉄 appears where 人 (person/member) should be -- "前衛２鉄" = "2 front row members"
- 王 appears where 力 (power) should be -- "回避王" = "evasion power"
- 理 appears where 敵 (enemy) should be
- 罰動 appears where 発動 (activate) should be
- 聞動 appears where 命中 (hit) should be
- 宮 appears where 効 (effect) should be in some contexts
- 良魔 appears where the concept of "interrupt/block" should be
- 箱期 appears where 連携 (coordination) should be

These substitutions are consistent across all messages and stem from the partially decoded glyph table.

## File Output
- `C:/Programmieren/wizardrytranslation/data/translations_dungeon_story.json` -- 167 translated entries with guide line references and confidence ratings
