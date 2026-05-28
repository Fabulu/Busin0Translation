# Phase 5a: Glossary Builder - Findings

## Task
Parse `dumps/guide_full.txt` (27,600 lines) and build a structured glossary at `data/glossary.json`.

## Script
`tools/build_glossary.py` - Parses guide text dump and produces structured JSON glossary.

## Output
`data/glossary.json` - 38KB, 1823 lines of structured JSON.

## Extraction Summary

| Category           | Count | Notes                                           |
|--------------------|-------|-------------------------------------------------|
| Spells             | 56    | 28 sorcery + 28 holy, 7 levels x 4 each        |
| Classes            | 16    | 4 basic, 6 advanced, 6 expert                   |
| Races              | 5     | Human, Elf, Gnome, Dwarf, Hobbit                |
| Attributes         | 6     | STR, INT, FTH, VIT, AGI, LCK                    |
| Weapons            | 101   | 16 categories (Dagger through Longbow)           |
| Armor              | 54    | 11 categories (Helmet through Cloak)             |
| Accessories        | 24    | 5 categories (Talisman, Hair Ornament, etc.)     |
| Monsters           | 117   | Auto-extracted via regex from "NAME LVLn" patterns|
| NPCs/Companions    | 17    | 7 companions + 10 named NPCs/lore characters     |
| Locations          | 16    | City areas, facilities, kingdoms                 |
| Alleid Attacks     | 37    | 20 attack, 6 defense, 6 support, 5 magic        |
| Personality Traits | 30    | All traits with likes/dislikes compatibility     |

## Key Findings

### Spells
- All 56 spells accounted for with level, school, element, target, and description
- Sorcery progression: fire/elec (L1) -> cold/fire (L3) -> universal/instant death (L7)
- Holy progression: heal/holy (L1) -> debuff/cure (L2-L4) -> resurrection (L6-L7)
- Mutation spells (ANALYZE, THROUGH, RIPU, CANNIBAL, REFLECT, VALHALLA, TRANS, FEARKEA, REVIVE, OFFSET) are created via synthesis mutations

### Classes
- Three tiers: basic (Fighter/Thief/Mage/Priest), advanced (Bishop/Alchemist/Samurai/Knight/Ninja/Monk), expert (Gizoku/Paladin/Dark Knight/Omnitsu/Shogun/High Thief)
- Alignment restrictions vary per class (Knight=Good only, Ninja=Evil only, etc.)
- Class abbreviations match the 3-letter codes used in equipment tables (FIG/THI/MAG/PRI/BIS/ALC/SAM/KNI/NIN/MON/GIZ/PAL/DAR/OMN/SHO/HIG)

### Items
- Weapons organized by type; katanas are the strongest (Muramasa: +235 OFE)
- Cursed items have CURSE power values and negative effects (HP degeneration, trust loss, etc.)
- Equipment sections span guide lines ~9500-13000

### Monsters
- 117 unique monsters auto-extracted from "NAME LVLn" patterns in monster data sections
- Level range: LVL1 (Bubble Slime) to LVL999 (Silver Slime)
- Post-game monsters reach LVL85-120 (Fuma Ninja, Ninetails, Incubus)
- Maelific at LVL512 is a special boss
- Class-based enemies (e.g., "LVL3 Fighter LVL12") are human-type enemies

### Companions
- 5 main story companions: Vera (Knight), Konde (Mage), Erika (Priest), Iris (Fighter), Frieder (Automata)
- 2 late-game companions: Turgot Martell (Ninja), Lidi Wallenstein (Gizoku)
- Frieder is unique as an Automata with no personality traits and levels via feeding magic stones

### Alleid System
- Unique team-based combat mechanic with 4 categories (Attack/Defense/Support/Magic)
- Many attacks have EX versions requiring specific class compositions
- Soul Crash noted as "strongest AA in the game"
- Alleid slots grow with Trust rank (12 starting, 30 max)

### Guide Structure Notes
- Lines 1-1200: Introduction, character creation, class/race/personality data
- Lines 1200-1900: UI/controls documentation
- Lines 1900-5800: Story events, tavern requests, quests
- Lines 5800-6400: Alleid actions system
- Lines 6400-7600: Companion data sheets
- Lines 7500-8900: Alchemy/synthesis system
- Lines 8900-9500: Ingredient tables
- Lines 9500-13000: Equipment tables (weapons/armor/accessories)
- Lines 13000-15500: Vigger Shop, consumables, misc items
- Lines 15500-16200: Potential abilities, intelligence events
- Lines 16200-27600: Floor-by-floor dungeon guide with monster data
