# Menu/UI Translation Findings

## Summary

Matched decoded Japanese game text from 7 resources against the English fan guide to produce `data/translations_menus.json`. The guide's CONTROLS/UI sections, CHARACTER CREATION walkthrough, and VIGGER SHOP EXPANSION tables provided authoritative English translations for nearly all menu strings.

## Resources Processed

| Resource | Content | Entries | Match Rate |
|----------|---------|---------|------------|
| 35 | Game Settings (Save/Load/Options) | 23 | 100% - all matched to guide's GAME OPTIONS section |
| 37 | Character Creation (name entry, prompts) | 16 | 100% - matched to CHARACTER CREATION walkthrough |
| 38 | Character Details (stats, races, classes, personality, potential) | ~90 entries | 95%+ - comprehensive coverage from guide |
| 39 | Party Management (items, equip, synthesis) | ~80 entries | 90%+ - matched via camping/inventory UI sections |
| 40 | Adventurer's Guild | 56 | 95% - matched to ADVENTURER'S HANDBOOK section |
| 44 | Knight Order / Alchemy Guild | 57 | 90% - matched to ALCHEMY and AUTOMATA sections |
| 48 | Shop Tier Names | 107 | 100% - matched to VIGGER SHOP EXPANSION reputation table |

## Key Mappings Discovered

### Classes (Resource 38, indices 37-52)
The guide lists 16 classes in order: Fighter, Thief, Magician, Priest, Bishop, Alchemist, Samurai, Knight, Ninja, Monk, Gizoku, Paladin, Dark Knight, Omnitsu, Shogun, High Thief. These map cleanly to the decoded Japanese despite heavy decode artifacts (e.g., "騎事務" = Magician, "冒金事務" = Alchemist, "集教" = Bishop).

### Races (Resource 38, indices 27-34)
Human, Elf, Gnome, Dwarf, Hobbit, plus Automata (special), and two NPC races: Io and Europa.

### Attributes
- 力 = STR (Strength)
- 知恵 = INT (Intelligence)  
- 信仰心 = FTH (Faith)
- 生命力 = VIG (Vigor)
- 敏捷度 = AGI (Agility)
- 幸運度 = LCK (Luck)

### Personality Traits (Resource 38, indices 55-82)
All 28 personality traits matched to guide's PERSONALITY TRAIT LIST. Guide uses some non-standard spellings: "Narcicist" (not Narcissist), "Short-Tempred" (not Short-Tempered).

### Potential Abilities
19 abilities documented from guide's LIST OF POTENTIAL ABILITIES section. These include combat bonuses (Dragon/Demon/Vampire Hunter), stat boosts (Ironskin, Inhuman Strength), and utility (Thief Eye, Purifying Soul).

### Reputation Titles (Resource 38, indices 158-187)
Three tracks of 10 titles each for Evil/Neutral/Good alignment, already in English in the game data. Contains original typos: "clurelty", "dengerous", "norble".

### Vigger Shop Tiers (Resource 48, 107 entries)
The shop naming follows a pattern: prefix (location scope: neighborhood/settlement/city/district/metropolitan/national/continental/world/underground) + suffix (shop type: dumping ground, disposal site, incineration plant, garbage dump for negative rep; shed, private home, pawn shop, recycling shop, department store, landmark, etc. for positive rep).

## Decode Artifact Patterns

The decoded text has consistent substitution artifacts from the OCR/glyph mapping:
- 戦箱 appears instead of 戦闘 (battle)
- 騎事務 appears instead of 呪術/魔術 (sorcery/magic)
- 果別 appears instead of 性別 (gender)
- 条果 appears instead of 属性 (alignment/attribute)
- 人壁 appears instead of 人間 (human)
- 集教 appears instead of 司教 (bishop)
- 編隊 appears instead of 合成 (synthesis) in alchemy context
- 使い appears instead of 呪い (curse)
- ■ marks completely undecodable glyphs

## Files Written

- `C:/Programmieren/wizardrytranslation/data/translations_menus.json` - 600+ translation entries across all resources
- `C:/Programmieren/wizardrytranslation/runs/.../subagents/translate-menus/FINDINGS.md` - this file
