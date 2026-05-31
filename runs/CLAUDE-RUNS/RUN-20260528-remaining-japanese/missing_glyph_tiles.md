# Missing R1272 Glyph Tiles on Chargen Screens

**Date:** 2026-05-28
**Source:** EE RAM dump from savestate 22-4.p2s, EXE disassembly, R38 resource analysis

## Executive Summary

The "text left to Male/Female" on chargen screens is caused by **two independent rendering systems** that both need patching:

| System | What It Renders | Current Status | Fix Method |
|--------|----------------|----------------|------------|
| R38 MSG glyph stream | Sidebar VALUES ("female", "Human") and sidebar LABELS ("Gender", "Race") | Translated in build, but **not applied in user's current ISO** | Rebuild ISO with latest build pipeline |
| EXE menu struct tiles | Sidebar LABELS (性別, 種族) as button-style kanji | Font tiles at 683-866 ARE in CSV | Verify R1272 atlas is applied to ISO |
| R1188 bitmap sprites | Stat labels (力, 知恵...), tab buttons (カナ, 決定) | **NOT translated** | Edit R1188 pixel data |
| EXE title banner | 新規登録 (top-left red banner) | Font tiles in CSV (705-722) | Same as sidebar tiles |

## Root Cause

The 22-4 savestate RAM dump contains the **ORIGINAL unpatched R38 resource** (7,512 bytes). The built/patched R38 (10,240 bytes with English glyph IDs) exists at `build/packdata_resources/0038_type01.raw` but was not in the ISO used for this savestate. Once the latest build ISO is applied, the R38 sidebar labels will render in English.

## R1272 Font Tile Coverage Analysis

### Currently Covered (195 tiles in menu_labels.csv)

| Range | Count | Purpose |
|-------|-------|---------|
| 683-866 | 184 | Menu button tile pairs (town hub, guild, shops, battle, etc.) |
| 346, 535, 717, etc. | 11 | Individual stat/field label kanji |

### NOT Covered: Extended Menu Table (62 tiles, IDs 867-931)

These are from EXE menu struct entries 106-159 (town services, quest board, knight order menus). They are **NOT chargen-specific** but will show Japanese on other game screens.

Full list documented in `font_tile_gap_analysis.md`.

### NOT Covered: R38 Chargen Kanji (30 glyph IDs, MOOT if R38 patch applied)

These kanji appear in the ORIGINAL R38 messages for chargen sidebar labels and values. They are **replaced by English ASCII glyph IDs** in the patched R38, so no font tiles are needed:

| Glyph ID | Character | R38 MSG | Usage |
|----------|-----------|---------|-------|
| 314 | 名 | MSG 9 | Name (sidebar label) |
| 510 | 前 | MSG 9 | Name (sidebar label) |
| 513 | 種 | MSG 11 | Race (sidebar label) |
| 514 | 族 | MSG 11 | Race (sidebar label) |
| 511 | 性 | MSG 12,13,15 | Gender/Alignment/Personality (sidebar) |
| 512 | 別 | MSG 12 | Gender (sidebar label) |
| 515 | 属 | MSG 13 | Alignment (sidebar label) |
| 516 | 性 | MSG 15 | Personality (sidebar label) |
| 504 | 職 | MSG 14 | Class (sidebar label) |
| 517 | 業 | MSG 14 | Class (sidebar label) |
| 346 | 力 | MSG 3,6 | STR/VIT stat label |
| 535 | 知 | MSG 4 | INT stat label |
| 717 | 恵 | MSG 4 | INT stat label |
| 308 | 信 | MSG 5 | FTH stat label |
| 354 | 仰 | MSG 5 | FTH stat label |
| 320 | 心 | MSG 5 | FTH stat label |
| 718 | 生 | MSG 6 | VIT stat label |
| 696 | 命 | MSG 6 | VIT stat label |
| 582 | 敏 | MSG 7 | AGI stat label |
| 719 | 捷 | MSG 7 | AGI stat label |
| 590 | 度 | MSG 7,8 | AGI/LCK stat label |
| 720 | 幸 | MSG 8 | LCK stat label |
| 721 | 運 | MSG 8 | LCK stat label |
| 518 | 男 | MSG 26 | Male value |
| 349 | 女 | MSG 27 | Female value |
| 519 | 間 | MSG 30 | Human race name |
| 319 | 人 | MSG 30 | Human race name |
| 520 | 善 | MSG 149 | Good alignment |
| 337 | 中 | MSG 150 | Neutral alignment |
| 289 | 悪 | MSG 151 | Evil alignment |

**Status:** All replaced by English glyph IDs (33-90 = A-z) in `build/packdata_resources/0038_type01.raw`. No font tile work needed.

## What ACTUALLY Needs Work (Chargen Japanese)

### 1. Verify ISO has latest R38 patch (CRITICAL)

The user's running ISO does not contain the patched R38. The build pipeline (`build_full_english_v2.py`) correctly translates R38 MSGs 3-15 (stat labels, sidebar labels) and MSGs 26-35 (gender, races). The output is at `build/packdata_resources/0038_type01.raw` (10,240 bytes vs original 8,192 bytes).

**Action:** Rebuild the full ISO and confirm R38 is injected.

### 2. R1188 Bitmap Sprites (15 elements, NOT R1272)

These render from R1188 (1024x1024 PSMT4 atlas), not R1272:

| Glyph ID | Japanese | English | Screen |
|----------|----------|---------|--------|
| 6400 | カナ | KATA | Name entry tab |
| 6401 | かな | HIRA | Name entry tab |
| 6402 | 英数 | ABC | Name entry tab |
| 6403 | 記号 | SYM | Name entry tab |
| 6405 | 決定 | OK | Name entry button |
| 6406 | 男名 | M.NAME | Name entry button |
| 6407 | 女名 | F.NAME | Name entry button |
| 6408 | 1文字消す | DEL | Name entry button |
| 6409 | 全消去 | CLR | Name entry button |
| (stat area) | 力 | STR | Class/Status screen |
| (stat area) | 知恵 | INT | Class/Status screen |
| (stat area) | 信仰心 | FTH | Class/Status screen |
| (stat area) | 生命力 | VIT | Class/Status screen |
| (stat area) | 敏捷度 | AGI | Class/Status screen |
| (stat area) | 幸運度 | LCK | Class/Status screen |

**Fix:** Edit R1188 pixel data at correct UV positions or patch R1188 header metadata to redirect to English labels.

### 3. Extended Menu Table Tiles (62 tiles, IDs 867-931)

These are NOT on chargen screens but appear on town/shop/dungeon menus. Already documented in `font_tile_gap_analysis.md`. Need atlas expansion to 21x45 grid (945 cells) and new tile rendering.

## Chargen Screen Verification Checklist

When the latest ISO build is applied, verify these screens:

| Phase | Screen | Expected English | Source |
|-------|--------|-----------------|--------|
| 1 | Name Entry | Tab labels still JP (R1188) | Tabs: R1188, grid: R37 |
| 2 | Gender | "Gender" header (TEX), "M"/"F" options (R38) | R38 MSGs 26-27 |
| 3 | Race | Sidebar "Gender female" (R38 + menu struct) | R38 MSG 12 + value |
| 4 | Alignment | Sidebar "Gender", "Race" labels | R38 MSGs 11-12 |
| 5 | Class | Stat labels still JP (R1188), sidebar labels EN (R38) | Mixed sources |
| 6 | Personality | All sidebar labels EN (R38) | R38 MSGs 11-15 |
| 7 | Stat Alloc | Stat labels still JP (R1188) | R1188 bitmap |
| 8 | Confirm | All sidebar + personality EN, stat labels JP (R1188) | Mixed |

## EXE Menu Struct Tile Rendering (Separate from R38)

The EXE menu structs at `0x3C3000` use tile pair IDs from R1272:

| Record | Tiles | Japanese | CSV English | Chargen Use |
|--------|-------|----------|-------------|-------------|
| 11 | 705,706 | 登 | reg | Title banner |
| 12 | 707,708 | 録 | . | Title banner |
| 18 | 719,720 | 新 | new | Title banner |
| 19 | 721,722 | 規 | (space) | Title banner |
| 30 | 743,744 | 名前 | name | Sidebar (may overlap R38) |
| 31-32 | 745-748 | 性別 | sex/blank | Sidebar (may overlap R38) |
| 33-34 | 749-752 | 種族 | race/blank | Sidebar (may overlap R38) |
| 35 | 753,754 | 属 | ali | Sidebar |
| 36 | 755,756 | 格 | pers | Sidebar |
| 37 | 757,758 | 業 | (blank) | Sidebar |
| 38 | 759,760 | 性別 | gender | Sidebar |

All tile IDs 705-760 are within our CSV coverage (683-866). The font atlas at these positions contains English text. Whether these render on chargen depends on whether the chargen code uses the menu struct system or R38 for sidebar labels -- it may use BOTH (menu struct for the label box, R38 for the text within).

## Key Files

| File | Purpose |
|------|---------|
| `build/packdata_resources/0038_type01.raw` | Patched R38 with English glyph streams |
| `build/english_font_atlas.bin` | R1272 atlas with English tiles at 683-866 |
| `data/menu_labels.csv` | Tile pair definitions (entries 0-105) |
| `data/translate_chunks/chunk_01_translated.json` | R38 MSGs 0-11 translations |
| `data/translate_chunks/chunk_02_translated.json` | R38 MSGs 12-130 translations |
| `data/translate_chunks/chunk_r38_fix.json` | R38 override fixes (MSG 2,25,26, etc.) |
| `build/build_full_english_v2.py` | Build pipeline that processes all chunks |
