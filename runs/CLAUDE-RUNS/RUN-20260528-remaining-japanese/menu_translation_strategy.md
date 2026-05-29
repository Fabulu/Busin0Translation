# Menu Label Translation Strategy

**Date**: 2026-05-28
**Source CSV**: `data/menu_labels.csv` (106 records, 92 active, 14 separators)

---

## 1. Architecture Summary

Each menu button in the EXE struct (56 bytes, at 0x3C3000-0x3C4730) renders as:

```
[icon tile] [label tile A1] [label tile A2]
```

- Each tile is a 12x12 pixel cell from the R1272 font atlas (PSMT4, 256x512)
- Label glyph IDs range 683-866, occupying dedicated font atlas cells
- These are **composite pre-rendered bitmaps** -- each cell contains a full Japanese word half, NOT individual characters
- The struct is fixed at exactly 2 label glyph slots; no room for additional characters

## 2. Translation Approach: Font Atlas Tile Replacement

The ONLY viable approach is to replace the font atlas bitmap at each glyph ID position with a pre-rendered English text bitmap.

### Per-tile rendering budget

- Each tile = 12x12 pixels
- Two tiles side-by-side = 24x12 pixels total for the label
- At ~4px per lowercase character, each tile fits 2-3 characters
- Total label capacity: 4-6 lowercase characters

### Strategy categories

| Strategy | Description | When to use |
|----------|-------------|-------------|
| `abbrev` | Short word fits in one tile, second tile blank or continuation | Words <= 4 chars (inn, shop, flee, rest, etc.) |
| `tile_pair` | Word split across two tiles (e.g., "tav" + "ern") | Words 5-6 chars that can split cleanly |
| `skip` | No translation needed | Empty/separator records (glyph IDs = 0xFFFF) |

### Tile splitting rules

When a word is split across two tiles:
- Split at a natural boundary (syllable, consonant cluster)
- Tile A1 = left half, Tile A2 = right half
- Example splits: tav|ern, chu|rch, gui|ld, att|ack, str|ike, sea|rch

### Width/spacing float adjustment

Each struct has a `width` float (offset 0x08) and `spacing` float (offset 0x0C). These can be patched in the EXE to give English labels more rendering room:
- Current widths range 40-300px
- Current spacing ranges 1.0-3.0
- Wider labels (like "tavern") may benefit from increased width

## 3. Priority Tiers

### Tier 1 -- Town Hub (records 0-9, most visible)
10 buttons always shown on the main town screen. These are the first thing players see.

| ID | Japanese | English | Split |
|----|----------|---------|-------|
| 0 | 酒場 | tavern | tav + ern |
| 1 | ギルド | guild | gui + ld |
| 2 | 商店 | shop | sho + p |
| 3 | 宿屋 | inn | inn + [blank] |
| 4 | 教会 | church | chu + rch |
| 5 | 迷宮 | maze | maz + e |
| 6 | 冒険 | venture | ven + ture |
| 7 | 依頼 | quest | que + st |
| 8 | 広場 | plaza | pla + za |
| 9 | 刻印 | seal | sea + l |

### Tier 2 -- Battle Menu (records 52-57)

| ID | Japanese | English | Split |
|----|----------|---------|-------|
| 52 | 覚醒 | attack | att + ack |
| 53 | 退却 | retreat | ret + reat |
| 54 | 打撃 | strike | str + ike |
| 55 | 発動 | cast | cas + t |
| 56 | 罠 | trap | tra + p |
| 57 | 離脱 | flee | fle + e |

### Tier 3 -- Guild/Character Management (records 10-40)
31 records covering character creation, party management, class change.

### Tier 4 -- Status/Stats (records 41-51)
11 records for character stat display.

### Tier 5 -- Dungeon/Item/Service Menus (records 58-105)
Remaining context menus, church services, inn options, system menus.

## 4. Tile Creation Pipeline

1. **Extract** current font atlas tiles at glyph positions 683-866 from R1272
2. **Verify** visually which Japanese word each tile pair renders (cross-check with analysis)
3. **Render** English replacement bitmaps at 12x12px using a pixel font (4-5px char width)
4. **Inject** replacement tiles back into R1272 atlas at the same cell positions
5. **Rebuild** R1272 resource and repack into PACKDATA.DIG
6. **Patch** EXE width/spacing floats if needed for proper rendering

### Font rendering spec
- Canvas: 12x12 pixels per tile (PSMT4 4-bit indexed color)
- Font: monospace or narrow pixel font, ~4px wide per character
- Colors: match existing palette (white text on transparent background)
- Alignment: vertically centered, horizontally flush (A1 left-aligned, A2 left-aligned continuing from A1)

## 5. Separator Records (strategy = "skip")

14 records with all glyph slots set to 0xFFFF are visual separators. No translation needed:
Records 58, 60, 63, 66, 69, 72, 80, 81, 89, 90, 92, 93, 100, 102

## 6. Risk Assessment

| Risk | Mitigation |
|------|------------|
| English too long for 24px | Use abbreviations (exp, dex, cond, str) |
| Font atlas palette mismatch | Extract palette from existing tiles before rendering |
| Icon tiles need translation too | Icon tiles show pictographic symbols -- likely fine as-is |
| PSMT4 tile injection breaks layout | Use validated psmt4_deswizzle.py for correct pixel mapping |
| Width float too narrow | Patch EXE floats to widen label rendering area |

## 7. Files

- **Source of truth**: `data/menu_labels.csv`
- **Analysis references**: `analysis_town_navigation.md`, `analysis_menu_buttons.md`
- **Font atlas**: R1272 (PSMT4, 256x512, cells 0-881)
- **EXE table**: `extracted/SLPM_653.78` at 0x3C3000-0x3C4730
- **Deswizzle tool**: `tools/psmt4_deswizzle.py`
