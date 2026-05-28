# Translation Completeness Audit

## Summary

| Metric | Count |
|--------|-------|
| Total decoded messages | 1,168 |
| Total resources | 21 |
| **Messages with English translation** | **791 (67.7%)** |
| Untranslated -- fully decoded (100%) | 299 |
| Untranslated -- partially decoded (<100%) | 12 |
| Untranslated -- very short (1-2 chars) | 66 |
| **Additional menu translations (not resource-mapped)** | **~42** |

**Effective translation coverage: ~71% when including non-resource-mapped menu translations and nested shop tier names.**

Adjusting for the R48 shop tier names that ARE translated but stored in nested sub-dicts (approx 99 of 107), the real coverage rises to about **~79% (890 of 1,168)**.

---

## Decode Quality

| Decode Level | Count |
|-------------|-------|
| 100% decoded | 1,057 (90.5%) |
| 80-99% decoded | 72 (6.2%) |
| Below 80% decoded | 39 (3.3%) |

---

## Per-Resource Breakdown

| Res | Total | Trans | Untrans | Coverage | Description |
|-----|-------|-------|---------|----------|-------------|
| 34 | 29 | 29 | 0 | 100.0% | Items (magic stones) |
| 35 | 23 | 23 | 0 | 100.0% | Game settings |
| 36 | 156 | 156 | 0 | 100.0% | Items/monsters (continued) |
| 37 | 18 | 16 | 2 | 88.9% | Character creation |
| **38** | **177** | **0** | **177** | **0.0%** | **Character details/stats** |
| 39 | 84 | 84 | 0 | 100.0% | Party management |
| 40 | 55 | 55 | 0 | 100.0% | Adventurer's Guild |
| 41 | 17 | 17 | 0 | 100.0% | Church of Salem |
| 42 | 13 | 13 | 0 | 100.0% | Adventurer's Inn |
| **43** | **26** | **0** | **26** | **0.0%** | **Tavern/bar dialogue** |
| 44 | 57 | 57 | 0 | 100.0% | Knight Order (Automata) |
| 45 | 191 | 163 | 28 | 85.3% | Vigger Shop |
| 46 | 7 | 7 | 0 | 100.0% | Bulletin board |
| 47 | 30 | 30 | 0 | 100.0% | Battle/treasure messages |
| **48** | **107** | **0*** | **107** | **0.0%*** | **Shop tier names** |
| 49 | 109 | 109 | 0 | 100.0% | Dungeon exploration |
| **720** | **7** | **0** | **7** | **0.0%** | **Unknown (poorly decoded)** |
| **1053** | **17** | **0** | **17** | **0.0%** | **Unknown (poorly decoded)** |
| **1908** | **8** | **0** | **8** | **0.0%** | **Unknown (poorly decoded)** |
| **2124** | **5** | **0** | **5** | **0.0%** | **Unknown (poorly decoded)** |
| 2654 | 32 | 32 | 0 | 100.0% | Alleid actions |

*\*R48 shop tier names ARE translated in `translations_menus.json` under nested `_negative_reputation_names` / `_positive_reputation_names` sub-dicts (~99 of 107 entries). The audit script could not match them because the translation file uses a nested structure that does not map directly to `(resource, message)` keys.*

---

## Fully Translated Resources (12 of 21)

Resources 34, 35, 36, 39, 40, 41, 42, 44, 46, 47, 49, 2654 are **100% translated**.

These cover: items, monsters, magic stones, game settings, party management, Adventurer's Guild, Church of Salem, Adventurer's Inn, Knight Order (Automata), bulletin board, battle/treasure messages, dungeon exploration, and Alleid (team) actions.

---

## Resources with Zero Translation (6 of 21)

### Resource 38 -- Character Details/Stats (177 messages, HIGH PRIORITY)

This is the largest untranslated block. Contains:
- **Stat labels**: HP, MHP, STR (力), INT (知恵), FTH (信仰心), VIG (生命力), AGI (敏捷度), LCK (幸運度)
- **Character sheet fields**: Name (名前), Race (種族), Gender (果別), Alignment (条果), Class (職業), Personality (果性)
- **Class names**: Warrior (戦士), Thief (盗賊), Priest (神聖), Ninja (忍者), Soldier (兵士), Noble Thief (義賊), General (将後), Professor (教授), Beauty Thief (美盗), etc.
- **Personality traits**: Bold (大胆), Cautious (慎重), Intellectual (知的), Friendship (友愛), Short-tempered (短気), Amorous (好色), Lonely (孤独), etc.
- **Alignment values**: Neutral (中立)
- **Level label**: Lv

These are mostly 1-2 character labels. 66 of the 177 entries are "very short" (1-2 chars). Most can be trivially translated using known Wizardry conventions from the guide.

**Priority: CRITICAL for playable patch -- the character screen is one of the most-viewed UI screens.**

### Resource 43 -- Tavern/Bar Dialogue (26 messages, MEDIUM PRIORITY)

The tavern bartender's dialogue for the mini-game system:
- "Hey, how'd that request go?" (おうおう、あの依頼はどうなった？)
- "Wanna grab a drink?" (一杯ひっかけてくかい？)
- "Wanna check the bulletin board?" (掲鉄板を見るのか？)
- "The game costs 500g per play" (ゲームは１回５００gだぜ)
- "Want to trade medals for prizes?" (ゲームで集めたメダルとアイテムを交更するぜ)
- Yes/No prompts, insufficient gold warnings, prize exchange dialogue

**Priority: MEDIUM -- needed for the tavern mini-game to be playable in English.**

### Resource 48 -- Shop Tier Names (107 messages, ALREADY MOSTLY TRANSLATED)

As noted above, ~99 of these are translated in the menus file under nested dicts. The remaining ~8 are likely edge cases. These are the evolving names for the Vigger Shop as reputation changes (e.g., "Illegal Dumping Ground" -> "Commonplace Store" -> "Department Store" -> "World Heritage Site").

**Priority: LOW -- translations exist, just need to be wired into the resource mapping.**

### Resources 720, 1053, 1908, 2124 -- Unknown (37 messages total, LOW PRIORITY)

These are very poorly decoded (20-60% coverage). Content is mostly garbled: "ブベ ■■別", "容ベ ■■■", etc. Likely:
- Font/graphic metadata misinterpreted as text
- Debug/system strings
- Tile map or sprite data

**Priority: VERY LOW -- not displayable game text.**

---

## Partially Translated Resources

### Resource 37 -- Character Creation (2 of 18 untranslated)

Missing message 18 (katakana input grid "アイウエオ...") -- this is the character name entry keyboard layout, not meaningful text.
The other missing entry is a minor label.

**Priority: LOW -- nearly complete, missing entry is a keyboard grid.**

### Resource 45 -- Vigger Shop (28 of 191 untranslated)

Messages 168-191 are untranslated. These include:
- "You've accepted too many requests, go complete some first!" (msg 168)
- "Cannot accept any more" (msg 169)
- Floor labels: "B1F", "B2F" etc. (msgs 170+)
- Additional shop dialogue for edge cases

**Priority: MEDIUM -- shop is playable but some edge-case dialogues will remain Japanese.**

---

## The Missing ~10%: What's Not Covered

The guide covers ~90% of game content. The remaining ~10% that lacks guide coverage:

1. **Resource 43 (Tavern mini-game)**: 26 messages of bartender dialogue for the medal/prize gambling mini-game. The guide mentions the tavern but does not transcribe the bartender's lines.

2. **Resource 38 (Character stats UI)**: 177 stat labels, class names, personality traits, race names. These are standard Wizardry terminology and can be translated from genre knowledge alone -- the guide does reference them in context (e.g., "STR", "INT", class descriptions) but not as an explicit label list.

3. **Resource 45 tail (msgs 168-191)**: Edge-case shop dialogues and dungeon floor labels not covered in the guide's shop walkthrough.

4. **Resources 720/1053/1908/2124**: Poorly decoded system data -- likely not player-facing text at all.

---

## Recommended Translation Priorities

### Tier 1 -- CRITICAL (needed for playable English patch)
- [ ] **Resource 38**: Character stats screen labels (177 msgs). Most are trivial 1-2 word translations using standard Wizardry vocabulary. Estimated effort: 1-2 hours.

### Tier 2 -- IMPORTANT (needed for complete experience)
- [ ] **Resource 43**: Tavern bartender dialogue (26 msgs). All fully decoded, straightforward dialogue. Estimated effort: 30 minutes.
- [ ] **Resource 45 tail**: Remaining Vigger Shop dialogue (28 msgs). Mix of dialogue and floor labels. Estimated effort: 30 minutes.

### Tier 3 -- CLEANUP
- [ ] **Resource 48**: Wire the existing nested translations into the resource mapping (already translated, just needs structural fix in the translation files).
- [ ] **Resource 37**: Character name input grid (cosmetic, 2 msgs).

### Tier 4 -- SKIP
- [ ] **Resources 720, 1053, 1908, 2124**: Poorly decoded, likely system data. Not worth translating until decode quality improves.

---

## File Locations

- Decoded messages: `data/full_decoded_text.json`
- Translation files:
  - `data/translations_items_monsters.json` (array format, resources 34+36)
  - `data/translations_menus.json` (dict format, resources 35,37-40,44,48 + common UI)
  - `data/translations_dungeon_story.json` (dict format, resources 46,47,49,2654)
  - `data/translations_shop_church.json` (dict format, resources 41,42,45)
