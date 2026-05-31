# Phase 4-5: Alignment & Class/Stats Screen Analysis

**Date**: 2026-05-28
**Save States**: `RAMdumps/27-4.p2s` (alignment), `RAMdumps/27-5.p2s` (class/stats)
**Analyst**: Claude Opus 4.6 (1M context)

---

## Screenshot Observations

### 27-4 (Alignment Screen)
- **English working**: "Good", "Neutral", "Evil" labels are English
- **English working**: "Select a race." prompt, "Attribute" header
- **Overflow issue**: Description box overflows to 3 lines -- "Good=justice. May turn Evil. FIG MAG PRI SAM GIZ BIS+"
- **Japanese labels**: Sidebar shows `性別 男` and `種族 Human` -- the LABELS (性別, 種族) remain Japanese while VALUES (男, Human) are English
- **Mixed**: "Level" and "b a" text appears in English

### 27-5 (Class & Parameter Screen)
- **English working**: "Fighter", "Mage", "Priest" class names, "Select alignment." prompt, "Class&Parameter" header, "Bonus Point", stat VALUES (15, 7, 3, 7, 6, 7)
- **ALL SIX stat labels STILL JAPANESE**: 力, 知恵, 信仰心, 生命力, 敏捷度, 幸運度
- **Sidebar labels STILL JAPANESE**: 性別 男, 種族 Human, 属性

---

## Critical Finding: TWO Independent Font Systems

### System 1: TextEvent MSG Renderer (R1272)
| Property | Value |
|----------|-------|
| Resource | **R1272** (our English font atlas) |
| Functions | `func_302DB0` (draw), `func_303C60` (main) |
| Glyph dispatch | `col = glyph_id % 21`, `row = glyph_id / 21` |
| Grid | 21 cols x 42 rows = 882 positions |
| Used for | Dialogue, prompts, class names, race/gender VALUES |
| Status | **WORKING** -- English text renders correctly |

### System 2: Font Tile System (Paged Kanji Resources)
| Property | Value |
|----------|-------|
| Resources | 100 paged resources (R1215-R1311, excluding R1272) |
| Format | PSMT8 (8bpp), various sizes |
| Functions | `func_30B770` (page check), `func_30B840` (render), `func_30B3F0` (manager) |
| Struct array | 50-byte per-glyph structs, max 32 active, base at `GP-26852` (VA 0x4FE70C) |
| Page table | VA 0x4CA710, 200 entries (100 paired), maps page_index to resource handle |
| Used for | Stat labels, sidebar labels, menu labels, town UI, battle UI |
| Status | **NOT PATCHED** -- all font page resources contain original Japanese kanji |

**R1272 is NOT in the font page table.** It is loaded separately and used exclusively by System 1.

---

## Proof That R38 Is Patched but Ignored for Stat Labels

### R38 in RAM Contains English Glyph IDs

Verified in 27-5 save state eeMemory at 0xE14390:

| MSG | RAM Address | Glyph IDs (BE) | Decoded |
|-----|------------|----------------|---------|
| 1 (HP/MHP) | 0xE14392 | 0028, 0030, 000F, 002D, 0028, 0030 | hp/mhp |
| 2 (STR) | 0xE14398 | 0033, 0034, 0032 | str |
| 3 (INT) | 0xE143A0 | 0029, 002E, 0034 | int |
| 4 (FTH) | 0xE143A8 | 0026, 0034, 0028 | fth |
| 5 (VIT) | 0xE143B0 | 0036, 0029, 0034 | vit |
| 6 (AGI) | 0xE143B8 | 0021, 0027, 0029 | agi |
| 7 (LCK) | 0xE143C0 | 002C, 0023, 002B | lck |

A second processed copy at 0xE2A048 contains the same English data plus longer forms: VITAL, AGILI, LUCK.

### Original Japanese R38 (for comparison)

| MSG | Glyph IDs | Japanese |
|-----|-----------|----------|
| 2 | 346 | 力 (chikara) |
| 3 | 535, 717 | 知恵 (chie) |
| 4 | 308, 354, 320 | 信仰心 (shinkoukokoro) |
| 5 | 718, 696, 346 | 生命力 (seimeiryoku) |
| 6 | 582, 719, 590 | 敏捷度 (binshoudo) |
| 7 | 720, 721, 590 | 幸運度 (kouundo) |

### No Japanese R38 Data Exists in RAM

Exhaustive search of 32MB eeMemory:
- Pattern `FFFF 015A FFFE 0217 02CD` (original stat labels): **ZERO hits**
- Pattern `FFFF 015A FFFF` (standalone 力 glyph): **ZERO hits**

**Conclusion**: R38 is fully patched to English. The Japanese kanji on screen do NOT come from R38.

---

## Chargen Renderer Architecture (VA 0x2F1090)

```
FIRST LOOP (labels): s2+4 linked list
  For each node:
    type = LH 4(s1)       ; 0, 1, or 2
    msg_index = LHU 6(s1)  ; R38 message index
    JAL 0x301E90(type, msg_index)   ; DIRTY-BIT CHECKER, not renderer!
    check update_flag = LH 8(s1)
    if update needed: set render flags
    next = LW 0(s1)

SECOND LOOP (values): s2+8 linked list
  For each node:
    JAL 0x180FD0(tile_id from LHU 4(s1))  ; tile-based render
    next = LW 0(s1)
```

### Function 0x301E90 = DIRTY-BIT CHECKER (NOT a renderer)

This function checks a bitmap to determine if a UI element needs re-rendering:
- Type 0 -> bitmap at `0x00565110`
- Type 1 -> bitmap at `0x005650D0`
- Type 2 -> bitmap at `0x00565090`
- Returns: 1 if bit set (needs update), 0 if clear

It does NOT read glyph data, does NOT call any rendering function, and does NOT output any visual content.

### Where the Actual Stat Label Rendering Happens

`JAL 0x30B840` (font tile render all) is called at VA 0x2F2568 in the main render pass. The font tile system reads glyph IDs from a bytecode-driven data stream.

Function 0x2F9320 (called via function pointer from the bytecode interpreter):
1. Calls `0x2F2E60` to read a big-endian uint16 from a data stream = **glyph tile ID**
2. Calls `0x2F2E60` again to read a second uint16 = position/type parameter
3. Calls `JAL 0x30B770` with r4 = glyph tile ID to register the font tile
4. After registration, applies position values based on the type parameter

**The glyph tile IDs in this data stream are the ORIGINAL Japanese kanji IDs** (346, 535, etc.) because they come from an unpatched UI definition resource, NOT from R38.

---

## Font Page Table (Complete, from 27-5 RAM)

Located at VA 0x4CA710, 200 entries (100 paired):

| Page Range | Resources | Notes |
|-----------|-----------|-------|
| 0-1 | (empty) | Unused |
| 2-109 | R1215-R1268 | Main font pages (54 resources, 2 entries each) |
| 116-117 | R1283 | Extended |
| 118-133 | R1304-R1311 | Kanji pages (8 resources) |
| 134-143 | R1278-R1282 | Extended |
| 144-179 | R1284-R1301 | Extended (18 resources) |
| 180-181 | R1303 | Extended |
| 182-187 | R1269-R1271 | Base kanji set |
| 188-197 | R1273-R1277 | Kanji pages |
| 198-199 | R1302 | Final page |

**R1272 is completely absent from this table.** It belongs exclusively to System 1.

---

## Font Tile Struct State (27-5 Save)

The font tile struct array base at `GP-26852` (VA 0x4FE70C) = **0x00000000 (NULL)**.
The page array at `GP-26856` (VA 0x4FE708) = **0x00000000 (NULL)**.

This means the font tile system's runtime state has been released. The kanji visible on screen were rendered to the GS framebuffer before the system state was freed. The GS VRAM retains the rendered pixels.

---

## Menu Struct Table (EXE Baked Data)

161 entries x 56 bytes at VA 0x4C2F80 (EXE file offset 0x3C2F58).

Each entry has a font tile glyph ID at offset +50. These are NOT the stat label kanji (346, 535 etc.) but rather DIFFERENT glyph IDs (475-603 range) used for menu UI elements.

The stat label kanji glyph IDs are stored in an **unpatched UI definition resource** (likely R1190, PACKDATA resource 1190) that is loaded at runtime. R1190 is a bytecode script (5,182 bytes) that drives the chargen screen layout. The bytecode contains the original Japanese glyph tile IDs as inline data.

---

## Root Cause Summary

The stat labels remain Japanese because of a THREE-LAYER rendering architecture:

```
Layer 1: R38 (data source)
  - Contains English glyph IDs (51=s, 52=t, 50=r for "STR")
  - R38 IS patched and loaded correctly
  - But R38 is ONLY used for value labels (race name, class name, gender)
  - R38 stat label messages (2-7) are read for dirty-bit checks ONLY

Layer 2: UI Bytecode Resource (R1190 or similar)
  - Contains the ORIGINAL Japanese glyph tile IDs (346, 535, 717, etc.)
  - These IDs are read by the bytecode interpreter (function 0x2F9320)
  - Passed to the font tile system (JAL 0x30B770)
  - This resource has NOT been patched

Layer 3: Font Tile Resources (R1215-R1311, excluding R1272)
  - Contain the actual kanji bitmap tiles
  - Indexed by glyph tile ID -> page_index -> font page resource
  - These PSMT8 texture resources have NOT been patched
```

The chargen screen uses R38 for CLASS VALUES (Fighter, Mage, etc.) via System 1 (R1272). But for STAT LABELS, it uses the font tile system (System 2) with glyph IDs from the UI bytecode resource, rendering from unpatched font page resources.

---

## Fix Options

### Option A: Patch the UI Bytecode Resource (R1190)
Replace the Japanese glyph tile IDs in R1190's bytecode with English glyph tile IDs.
- **Problem**: The font tile system (System 2) has NO English letter tiles in any of its 100 page resources. There are no ASCII glyphs to redirect to.
- **Additional work**: Would need to add English tiles to one of the font page resources.

### Option B: Patch Font Page Resources (Replace Kanji Tiles)
Edit the PSMT8 font page resources (R1215-R1311) to replace specific kanji tiles with English letter glyphs.
- **Problem**: Kanji glyph 346 (力) appears in multiple contexts beyond stat labels. Replacing it globally affects all uses.
- **Scale**: Need to replace ~15 unique kanji tiles across multiple font page resources.

### Option C: EXE Code Patch -- Redirect Stat Labels to System 1
Modify the chargen renderer to call the TextEvent renderer (System 1, R1272) for stat labels instead of the font tile system (System 2).
- **Pros**: Clean separation, uses our existing English R1272 atlas
- **Cons**: Requires significant EXE code injection, need to find code cave space

### Option D: EXE Code Patch -- Add R1272 to Font Page Table
Add R1272 as a new entry in the font page table and modify the UI bytecode to use glyph IDs that map to R1272 positions.
- **Problem**: R1272 is PSMT4 (4bpp) while all font page resources are PSMT8 (8bpp). Format mismatch would cause rendering artifacts.

### Option E: EXE Code Patch -- Intercept render_glyph_sprite
Hook the `render_glyph_sprite` function (VA 0x494350) to substitute glyph IDs at render time for specific stat label glyphs.
- **Pros**: Surgical, doesn't affect any resource files
- **Cons**: Complex, 993 calls to this function exist

### Recommended: Option C (EXE Code Redirect)
The cleanest approach is to patch the chargen renderer to call System 1 for stat labels. This uses the existing English R1272 atlas and avoids touching the complex font page resources or UI bytecode. The R38 messages 2-7 already contain the correct English glyph IDs for System 1.

---

## Sidebar Label Analysis (性別, 種族, 属性)

The sidebar labels use the SAME font tile system (System 2):
- 性別 = glyph tiles 511, 512
- 種族 = glyph tiles 513, 514
- 属性 = glyph tiles 515, 511

These are referenced in the menu struct table:
- entry[31]: glyph 511 at +50 (性)
- entry[32]: glyph 512 at +50 (別)
- entry[33]: glyph 513 at +50 (種)
- entry[34]: glyph 514 at +50 (族)
- entry[35]: glyph 515 at +50 (属)

The menu struct table is in the EXE data section (VA 0x4C2F80). These entries define the sidebar layout. The glyph IDs here directly reference font tile system tiles.

To translate the sidebar labels, either:
1. Patch the menu struct glyph IDs at +50 to reference English tiles (requires adding English tiles to font page resources)
2. Patch the EXE rendering code to use System 1 for sidebar labels

---

## Key Addresses (27-5 Save State)

| What | VA | Content |
|------|-----|---------|
| R38 glyph stream (English) | 0xE14390 | Big-endian uint16 glyph IDs, FFFF-terminated |
| R38 processed copy | 0xE2A048 | English stat labels with position data |
| Font page table | 0x4CA710 | 200 x uint32 resource handles |
| Font tile struct base ptr | 0x4FE70C | NULL (system released) |
| Page array ptr | 0x4FE708 | NULL (system released) |
| Dirty-bit checker | 0x301E90 | Checks bitmap, returns 0/1 |
| Font tile render loop | 0x30B840 | Renders all active font tiles |
| Font tile page check | 0x30B770 | Registers glyph for rendering |
| Chargen renderer | 0x2F1090 | Main chargen screen renderer |
| Chargen main render | 0x2F2490 | Calls font tile render at 0x2F2568 |
| Bytecode glyph reader | 0x2F2E60 | Reads BE uint16 from data stream |
| Stat msg index table | 0x4D46C8 | uint32[6] = {2,3,4,5,6,7} |
| Menu struct table | 0x4C2F80 | 161 x 56-byte entries |
| GP register | 0x504FF0 | Global pointer |

## Files Referenced

- Save state: `RAMdumps/27-5.p2s` (extracted to `RAMdumps/27-5_extracted/`)
- EXE: `extracted/SLPM_653.78`
- Build R38: `build/packdata_resources/0038_type01.raw` (10,240 bytes, English)
- Original R38: `extracted/packdata_resources/0038_type01.bin` (7,512 bytes, Japanese)
- UI resource: `extracted/packdata_resources/1190_type01.bin` (5,182 bytes, bytecode)
- Prior analyses: `stat_render_trace.md`, `glyph_range_dispatch.md`, `font_pages_analysis.md`, `exe_stat_glyph_finder.md`
