# Debug: Save State 22-5 -- Stat/Attribute Screen Analysis
**Date**: 2026-05-28
**Source**: `RAMdumps/22-5.p2s` (character creation stat allocation screen)

---

## Screenshot Observations

The screen shows the character creation "Class & Parameter" page with:
- **English text working**: "select a class.", "thief", "female", "Human", "Bonus Point"
- **Japanese text remaining**: 力, 知恵, 信仰心, 生命力, 敏捷度, 幸運度 (stat labels)
- **Japanese text remaining**: 性別, 種族, 属性 (sidebar labels -- these are also rendered from kanji font tiles)
- **Garbled text**: "eYY" where "Level" should appear (broken glyph rendering)

---

## Root Cause: Stat Labels Are NOT From R38

### What R38 actually contains in RAM

R38 is loaded at `0x00E14090` in RAM. It contains **188 messages**, and all are **correctly patched to English**:

| RAM MSG | Content | Original |
|---------|---------|----------|
| 0 | hp/mhp | hp/mhp |
| 1 | str | 力 |
| 2 | int | 知恵 |
| 3 | fth | 信仰心 |
| 4 | vit | 生命力 |
| 5 | agi | 敏捷度 |
| 6 | lck | 幸運度 |
| 7 | name | 名前 |
| 8 | level | レベル |
| ... | ... | ... |
| 24 | male | 男 |
| 25 | female | 女 |
| 29 | Human | 人間 |

**R38 translations ARE being loaded and used.** "female", "Human", class names, personality names, alignment descriptions -- all come from R38 and display in English.

### Why stat labels still show Japanese

The stat labels (力, 知恵, 信仰心, 生命力, 敏捷度, 幸運度) and sidebar labels (性別, 種族, 属性) are **NOT rendered from R38 MSG text**. They are rendered using the **font tile glyph system** -- the same system that renders the town menu labels (酒場, ギルド, etc.).

Each label is rendered by displaying individual font tile glyph IDs:
- 力 = glyph tile 346
- 知恵 = glyph tiles 535, 717
- 信仰心 = glyph tiles 308, 354, 320
- 生命力 = glyph tiles 718, 696, 346
- 敏捷度 = glyph tiles 582, 719, 590
- 幸運度 = glyph tiles 720, 721, 590

These glyph tile IDs are rendered from the **kanji font pages** (R1270, R1271, R1273-R1277), **NOT from R1272** (our English font atlas).

### Font Page Architecture

The game uses multiple font atlas resources:

| Resource | Size | Role |
|----------|------|------|
| R1272 | 67,584 bytes | Base font (ASCII, basic chars) -- **WE REPLACE THIS** |
| R1270 | 133,120 bytes | Kanji font page -- **UNTOUCHED** |
| R1271 | 133,120 bytes | Kanji font page -- **UNTOUCHED** |
| R1273 | 133,120 bytes | Kanji font page -- **UNTOUCHED** |
| R1274-R1277 | 264,192 bytes each | Extended kanji pages -- **UNTOUCHED** |

The kanji font page table is at EXE offset `0x004CA9E8` and lists resources:
R1301, R1303, R1269, R1270, R1271, R1273, R1274, R1275, R1276, R1277, R1302.

**R1272 is NOT in this table.** It is loaded separately as the "base" font. Glyph tiles 346, 535, 717, etc. are served by the kanji pages, which remain the original Japanese tiles.

### Why menu_labels.csv stat entries don't work

The `menu_labels.csv` file has entries for stat label glyphs (rows 108-127):
```
stat_346,0x000000,346,0,,stat_label (shared:VIT3),,abbrev
stat_535,0x000000,535,0,,stat_label,in,abbrev
...
```

These entries have `exe_offset=0x000000` because the stat labels are NOT in the EXE menu struct table (Table 2C). The menu struct table only covers the town/battle UI labels (rows 0-107).

Even though `render_menu_tiles.py` renders English text into font atlas positions 346, 535, etc. in R1272, the game **never reads R1272 for these glyph IDs**. It reads from the kanji font pages instead.

### Off-by-one in R38 injection

There is also an off-by-one shift in the R38 message indexing:
- Original R38: MSG 0 = "hp", MSG 1 = "hp/mhp", MSG 2 = "力" (STR)
- Patched R38 in RAM: MSG 0 = "hp/mhp", MSG 1 = "str", MSG 2 = "int"

The patched version appears to have DROPPED MSG 0 ("hp") and shifted all subsequent messages down by one index. This could cause wrong labels/values to appear in contexts where the game uses specific R38 message indices.

---

## Diagnosis Summary

1. **Stat labels (力, 知恵, etc.)**: Rendered via kanji font tiles from R1270-R1277 (unreplaced). NOT from R38 messages. NOT from R1272 (our atlas). **Cannot be fixed by R38 translation alone.**

2. **Sidebar labels (性別, 種族, 属性)**: Same mechanism as stat labels -- kanji font tiles from unreplaced font pages.

3. **"eYY" garble for "Level"**: Likely caused by the off-by-one in R38, where the game reads a wrong message index.

4. **R38 translations ARE working**: "female", "Human", class/race/personality names, alignment descriptions all display correctly from R38.

---

## Required Fix

To translate the stat labels, one of these approaches is needed:

### Option A: Replace kanji font pages (R1270-R1277)
Replace the glyph tiles at positions 346, 535, 717, etc. in the appropriate kanji font page resources with English letter tiles. This requires:
- Determining which font page serves each glyph ID (mapping glyph ranges to resources)
- Editing the binary font data in R1270/R1271/R1273 etc.

### Option B: Patch the EXE rendering code
Modify the game's stat screen rendering code to call R38 message display instead of direct glyph tile rendering. This is complex EXE reverse engineering.

### Option C: Redirect glyph IDs in the EXE
Find where the EXE stores the glyph ID sequences for stat labels (346, 535+717, etc.) and replace them with ASCII glyph IDs that render from R1272 (e.g., replace 346 with glyph IDs for "S","T","R").

Option C is the most promising -- similar to how Patch 4 in `patch_exe.py` replaces banner glyph IDs (719,720 -> 46,69 for "Ne"). The stat label glyph IDs must be stored somewhere in the EXE or in a rendering struct table that hasn't been found yet (hence the `exe_offset=0x000000` entries in menu_labels.csv).

### Off-by-one fix
The R38 message index off-by-one needs to be diagnosed and fixed in `build_full_english_v2.py`. The dropped MSG 0 ("hp") is likely caused by the offset table rebuild logic miscounting or the FFFF group parser skipping the first group.
