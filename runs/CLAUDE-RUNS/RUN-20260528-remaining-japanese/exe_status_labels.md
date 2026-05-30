# EXE Status/Equipment/Camp Screen Labels Analysis

**Date:** 2026-05-28
**EXE:** `extracted/SLPM_653.78` (4,185,776 bytes)
**Scan range:** 0x3B0000-0x3FD000 (data section)
**Excluded:** 0x3C3000-0x3C5300 (menu structs), 0x3C83C0-0x3C93A0 (chargen), 0x3EE9D0-0x3F3500 (debug strings)

---

## Key Finding

**There are NO Japanese glyph-composed text labels in the EXE data section outside of the known areas.** All status screen, equipment screen, camp screen, battle UI, and shop interface labels in Busin 0 are stored in one of two places:

1. **MSG resources in PACKDATA** (glyph-indexed text) -- covers all readable text labels
2. **Pre-rendered font tiles** referenced by the menu struct system (0x3C3000-0x3C52FF)

The EXE does NOT contain SJIS-encoded UI label strings (unlike Busin 1's English release, which has format strings like `%WLEVEL`, `%WSTRENGTH`, etc.). Busin 0 uses a fundamentally different architecture where the glyph rendering engine draws all labels from MSG resource data at runtime.

---

## What WAS Found

### 1. Save Slot Labels (SJIS fullwidth strings) -- NEED TRANSLATION

| Offset | Japanese | English | Notes |
|--------|----------|---------|-------|
| 0x3F9370 | ＢＵＳＩＮ０中断データ | BUSIN0 Suspend Data | Memory card save display |
| 0x3F9678 | ＢＵＳＩＮ０ | BUSIN0 | Save header label |
| 0x3FC720 | ＢＵＳＩＮ０ | BUSIN0 | Duplicate reference |
| 0x3FC750 | ＢＵＳＩＮ０データ１ | BUSIN0 Data 1 | Save slot 1 label |
| 0x3FC770 | ＢＵＳＩＮ０データ２ | BUSIN0 Data 2 | Save slot 2 label |
| 0x3FC790 | ＢＵＳＩＮ０データ３ | BUSIN0 Data 3 | Save slot 3 label |

These are the ONLY genuine player-visible Japanese strings in the EXE outside debug/menu-struct areas. Each is 20-24 bytes of fullwidth SJIS. English replacements fit easily (ASCII is half the width of fullwidth SJIS).

### 2. Memory Card Identifiers -- DO NOT TRANSLATE

| Offset | String | Purpose |
|--------|--------|---------|
| 0x3F92B0 | BISLPM-65378BSN2-3 | MC directory ID (suspend) |
| 0x3F9450 | BISLPM-65378BSN2-0 | MC directory ID (slot 1) |
| 0x3F9470 | BISLPM-65378BSN2-1 | MC directory ID (slot 2) |
| 0x3F9490 | BISLPM-65378BSN2-2 | MC directory ID (slot 3) |
| 0x3F9660 | BISLPM-62098BUSINWZ | Cross-save ID (Busin 1 import) |

These are functional identifiers, NOT display text. Changing them breaks save compatibility.

### 3. Debug Strings (0x3EE9D0-0x3F3500) -- NOT PLAYER VISIBLE

~300+ debug/developer strings including `効果レベル = %d`, `プレイヤー攻撃武器作成!!`, `アイテム数足りんで〜！！`, etc. These are printf-format debugging messages compiled into the debug build. They are never shown to the player and do not need translation.

---

## Where the Actual Screen Labels Live

### Status Screen Labels -- MSG Resource 38

All decoded and translated in `data/translations_menus.json` under `resource_38_character_details`:

| Category | Entries | Examples |
|----------|---------|---------|
| Attributes | 7 | HP, HP/MHP, INT, FTH, VIG, AGI, LCK |
| Stat labels | 7 | Name, Level, Race, Gender, Alignment, Class, Personality |
| Magic categories | 2 | Sorceries, Holy Magic |
| Misc labels | 4 | Attributes, OFE, ACC, DEF, EVA |
| Spell levels | 7 | Lv1-Lv7 |
| Races | 8 | Human, Elf, Gnome, Dwarf, Hobbit, Automata, Io, Europa |
| Classes | 16 | Fighter through Samurai (basic/advanced/expert) |
| Personalities | 28 | Pusillanimous through Wasteful |
| Alignments | 4 | Good, Neutral, Evil |
| Reputation titles | 30 | Commoner through God Hand (3 tracks x 10) |

### Equipment/Party Screen Labels -- MSG Resource 39

All decoded and translated in `data/translations_menus.json` under `resource_39_party_management`:

| Category | Examples |
|----------|---------|
| Actions | Use, Equip, Unequip, Switch, Give Item, Heal |
| Confirmations | "Is this OK?", Yes, No |
| Error messages | "Cannot equip", "Not enough MP", "Cannot unequip due to curse" |
| Stat changes | "Change to STR/INT/FTH/VIG/AGI/LCK" |
| Synthesis | "Synthesize?", "Select combination", "Synthesis succeeded!" |

### Camp/Save Menu Labels -- MSG Resource 35

All decoded and translated:
Save, Save and Quit, Load, Game Options, Return to Title, ON/OFF, Normal/Minimal/Short, Slow/Fast, etc.

### Shop Labels -- MSG Resources 41, 42, 45, 48

Church of Salem, Adventurer's Inn, Vigger Shop, Shop Tiers -- all in translated JSON files.

### Battle UI Labels

Battle commands (Attack, Defend, Magic, Item, Flee, etc.) are rendered via the menu struct system using pre-rendered font tiles (IDs 604-931) at 0x3C3000-0x3C52FF. These tiles are baked into the font atlas (R1272) and must be replaced by modifying the atlas image.

---

## Menu Struct System (0x3C3000-0x3C52FF) -- ALREADY CATALOGUED

160 entries, each 56 bytes. Uses pre-rendered font tile IDs 604-931 for button labels across 68 different screens/menus. These reference tiles baked into the font atlas texture, not composable text. To translate these, the corresponding tiles in the R1272 font atlas must be redrawn with English text.

Label tile range: 604-674 (70 unique label tiles)
State tile range: 475-931 (includes normal, selected, disabled states)
Screens covered: 68 unique screen IDs (0x2E-0x74)

---

## Areas Scanned and Confirmed Empty

| Range | Size | Contents | Japanese Labels? |
|-------|------|----------|-----------------|
| 0x3B0000-0x3C3000 | 77 KB | Glyph tables, lookup arrays, code data | NO -- only glyph lookup tables and numeric data |
| 0x3C5300-0x3C83C0 | 12 KB | Post-menu data, code pointers, tile arrays | NO -- sequential tile ID tables (1162-1227) |
| 0x3C93A0-0x3EE9D0 | 150 KB | UI layout structs, rendering parameters | NO -- float/int rendering parameters only |
| 0x3F3500-0x3F9370 | 24 KB | Code pointers, function tables | NO -- only binary data |
| 0x3F93B0-0x3FD000 | 16 KB | Save identifiers, system data | Only save slot labels (listed above) |

### Methodology

1. **SJIS string scan**: Decoded every null-terminated byte sequence as strict SJIS, required 2+ fullwidth/JP chars, verified printability. Found only save slot labels and debug strings.
2. **Glyph ID cluster scan**: Searched for consecutive uint16 values in the mapped glyph range (95-1747). Found only glyph lookup tables and chargen data (both already known/excluded).
3. **Menu struct format scan**: Searched for `(glyph_id << 16) | flags` pattern (the format used by menu structs). Found nothing outside 0x3C3000-0x3C52FF.
4. **Fullwidth char scan**: Searched entire 4MB EXE for any SJIS string containing 2+ fullwidth characters. Confirmed only 6 save label strings outside debug area, all others are false positives from MIPS code bytes.

---

## Action Items for Translation

1. **Patch 6 save slot SJIS strings** at 0x3F9370-0x3FC790 (trivial, ASCII fits in existing space)
2. **Replace font atlas tiles** 604-931 in R1272 with English button labels (medium difficulty)
3. **Re-encode MSG resources** 35, 37, 38, 39, 40, 41, 42, 44, 45, 48 with English glyph sequences (already supported by build pipeline)
4. No other EXE data modifications needed for status/equipment/camp labels
