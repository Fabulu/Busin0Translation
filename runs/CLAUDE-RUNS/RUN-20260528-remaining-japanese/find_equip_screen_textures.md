# Equipment/Inventory/Camp Screen Texture Analysis

**Date**: 2026-05-28
**Source**: 411 PCSX2 texture dumps + prior analysis cross-reference

---

## Executive Summary

The equipment/inventory/camp screens use **NO dedicated texture resources with baked Japanese text**. All text on these screens is rendered at runtime from two systems:

1. **Main font atlas R1272** (VRAM page 0x2a94) -- individual 24x24 glyph tiles for item names, stat numbers, descriptions
2. **EXE Table 2C menu labels** (glyph IDs 480-866) -- 2-kanji composite labels for tab/button text, rendered from R1272 tiles

Equipment type icons (sword/shield/etc.) use a **3D sprite system** (R2156/R2157/R2159), not text textures.

---

## PCSX2 Dump Evidence

### All 411 textures categorized by VRAM page:

| VRAM Page | Count | Content | Equipment-Related? |
|-----------|-------|---------|-------------------|
| 0x2214 | 208 | Name entry / chargen UI atlas (R1188) | NO -- chargen only |
| 0x2a94 | 35 | Main font atlas glyph tiles (R1272) | YES -- item names rendered here |
| 0x1dd3 | 28 | Dungeon wall/floor textures | NO |
| 0x2654 | 27 | Narration text overlay (R2118) | NO -- story text only |
| 0x1dd4 | 18 | Decorative numbers, "Bonus Point" | NO |
| 0x2254 | 17 | Status screen headers (already English) | Partially -- section labels |
| 0x1e14 | 15 | Button background frames (no text) | YES -- empty button bg used everywhere |
| 0x2653 | 9 | Splash art, NPC portraits, logos | NO |
| 0x2614 | 9 | Arrow/cursor icons, panel frames | YES -- generic UI frames |
| 0x2213 | 7 | NPC portraits | NO |
| 0x1993 | 7 | Environment textures | NO |
| 0x1994 | 5 | Environment textures | NO |
| 0x1e13 | 4 | Tree/foliage textures | NO |
| 0x19d3 | 3 | Architectural textures | NO |
| 0x1554 | 3 | Small icons (equipment type?) | Possibly -- tiny icon sprites |
| 0x1613 | 3 | Title screen text ("New Game", "Press START") | NO |
| 0x2a80 | 2 | Large atlas (513x449) | Unknown |
| 0x1e54 | 2 | "Duhan The Imperial City" (English) | NO |
| 0x1980 | 2 | Unknown small textures | NO |
| 0x2640 | 1 | Background texture atlas | NO |

### Key finding: NO equipment-specific text textures exist in the dumps

The equipment screen renders ALL text dynamically:
- **Item names**: Composed from R1272 font atlas glyphs via the MSG text system
- **Stat numbers** (ATK, DEF, etc.): Rendered as digit glyphs from R1272
- **Slot labels** (head, body, arms, legs, accessory): Rendered from EXE Table 2C glyph pairs
- **Menu buttons** (Equip, Unequip, Use, Drop): Rendered from EXE Table 2C glyph pairs
- **Comparison arrows** (up/down stat changes): Simple geometric sprites, no text

---

## Equipment Screen Text Sources

### Source 1: Main Font Atlas (R1272, VRAM 0x2a94)

All item names, descriptions, and stat values are rendered as sequences of individual glyph tiles from R1272. The PCSX2 dumps show 35 unique 24x24 glyph reads from this atlas during gameplay.

- **Resource**: R1272 (type-01, 256x512 PSMT4)
- **Translation status**: 810 glyph mappings in msg_glyph_map.json, 95%+ coverage
- **Equipment item names**: Rendered via type-02 MSG resources (R39 equipment batch)
- **Already translated**: 12,725+ type-2 messages injected via build pipeline

### Source 2: EXE Table 2C Menu Labels (106 records)

Equipment screen tabs and action buttons are rendered from hardcoded glyph ID pairs in the EXE. Each menu label is a fixed struct with exactly 3 glyph slots (1 icon + 2 label glyphs).

- **Location**: EXE offset 0x3C3000-0x3C4730
- **Glyph ID range**: 480-866 (different rendering from MSG glyphs)
- **Translation status**: 0% -- all 359 unique glyph IDs unmapped
- **Equipment-relevant groups** (from menu_index analysis):
  - idx=88 (6 records): Equipment management sub-menu (equip/unequip)
  - idx=89 (8 records): Equipment inspection/comparison
  - idx=90 (7 records): Item management (use/discard)
  - idx=91 (6 records): Item details/actions
  - idx=54 (3 records): Party management with equip option

### Source 3: Equipment Type Icons (3D Sprite System)

Equipment type category icons (sword, shield, helmet, etc.) use glyph IDs 2036-2086 which are NOT font atlas glyphs but 3D scene entities.

- **Resources**: R2155 (GS setup), R2156 (texture data), R2157 (mesh), R2159 (scene)
- **Icon animation table**: EXE 0x3F9CF0 (52 icons x 4 variants each)
- **Translation relevance**: LOW -- these are graphical icons, not text
- **See**: `find_equipment_icons.md` for full analysis

### Source 4: Status Screen Section Headers (VRAM 0x2254)

Already-translated pre-rendered labels visible on the character status screen:

| Texture | Content | Status |
|---------|---------|--------|
| 152x48 | "Attribute" | DONE (English) |
| 248x48 | "Class&Parameter" | DONE (English) |
| 168x48 | "Personality" | DONE (English) |
| 120x48 | "Gender" | DONE (English) |
| 108x48 | "Name" | DONE (English) |
| 88x48 | "Race" | DONE (English) |
| 168x56 | "Status" | DONE (English) |
| 48x18 | "Level" | DONE (English) |

These come from a separate texture atlas (likely R2121 or R1188 sub-region) and are already translated.

---

## UI Frame Textures (No Text, Used on Equipment Screen)

These textures provide the visual frame/background for equipment screens but contain no text:

| VRAM Page | Size | Content |
|-----------|------|---------|
| 0x1e14 | 96x36 | Rounded button backgrounds (3 variants: outline, filled, bordered) |
| 0x1e14 | 16x16 | Small corner/tile pieces |
| 0x1e14 | 0x20 | Horizontal divider bars |
| 0x2614 | 168x52 | Ornate panel background (gold bordered) |
| 0x2614 | 176x32 | Panel background (flat gray) |
| 0x2614 | 32x32 | Arrow/cursor icons |
| 0x2614 | 32x24 | Triangle selection arrows (green/pink) |
| 0x2254 | 32x56, 24x56 | Decorative border elements |
| 0x2214 | 128x160 | Large gradient panel background |
| 0x2214 | 128x32 | Small gradient panel background |

---

## Translation Priority for Equipment Screens

### Already Done
- Item names (type-02 MSG via R39 batches) -- 12,725+ messages
- Status screen section headers (VRAM 0x2254) -- all English
- Core stat labels (R38 messages 1-18) -- STR, INT, FTH, VIT, AGI, LCK
- Combat stat labels (R38 messages 83-87) -- Attack, Accuracy, Defense, Evasion
- Equipment type icons -- graphical, no translation needed

### Still Remaining
1. **EXE Table 2C menu labels** (P1 priority) -- Equipment action buttons (Equip, Use, Drop, etc.)
   - Requires: Font atlas tile replacement for glyph IDs 480-866
   - Approach: Replace R1272 tiles with pre-rendered English abbreviations
   - Effort: HIGH -- 359 glyph IDs to map, 106 records to decode/translate
   
2. **Equipment slot labels** -- Head, Body, Arms, Legs, Accessory
   - Source: Likely EXE Table 2C or a companion table
   - These appear as Japanese kanji labels next to each slot
   - Part of the EXE glyph system, not texture resources

3. **EXE Table 2C entries 106-159** (M1 in REMAINING_WORK.md) -- 62 additional glyph IDs
   - Some are equipment-related (sell, trade, cure, etc.)

---

## Key Conclusion

**There are NO separate texture files to replace for equipment screen text.** The equipment/inventory/camp screens are entirely glyph-rendered. Translation requires:

1. Completing glyph ID mapping for the 480-866 range in R1272
2. Replacing font atlas tiles with English text bitmaps
3. Patching EXE Table 2C width/spacing floats for English label widths
4. No texture editing beyond the main font atlas R1272

This contrasts with:
- The **name entry screen** (R1188 texture atlas with baked Japanese tab labels -- M3)
- The **narration overlay** (R2118 texture with baked story text -- separate task)
- The **cockpit backgrounds** (R2118-R2122 with baked location headers)

---

## Files Referenced

- PCSX2 dumps: `build/pcsx2_dumps/` (411 files)
- Main font atlas: `extracted/packdata_raw/1272_type01.raw` (R1272)
- EXE table: `extracted/SLPM_653.78` offset 0x3C3000
- Menu label analysis: `analysis_menu_buttons.md`
- Equipment icon analysis: `find_equipment_icons.md`
- Tab label analysis: `find_tab_label_atlas.md`
- Status screen analysis: `analysis_status_screen.md`
- Text texture analysis: `find_text_textures.md`
- Remaining work: `REMAINING_WORK.md`
