# R1188 Atlas Visual Inspection Report

**Date**: 2026-05-28
**Source**: `build/textures_to_edit/R1188_CORRECT_dbw512.png` (1024x1024, 8-bit grayscale)
**Deswizzle**: PSMT4 with dbw_ct32=512

---

## Atlas Structure Overview

R1188 is a **font glyph atlas**, not a UI label sheet. It contains individual character glyphs in a grid layout. The game composes multi-character UI labels at runtime by reading individual glyph cells from this atlas.

The atlas is split into two halves separated by a 16px empty vertical gap:

| Region | Pixel Range | Cell Size | Content |
|--------|------------|-----------|---------|
| Left half | x=0-495, y=0-1008 | 24x24 (first col 16px) | Large glyphs (main display font) |
| Vertical gap | x=496-511 | -- | Empty (16px separator) |
| Right half | x=512-1023, y=0-1008 | ~16x16 (estimated) | Small glyphs (UI/composite font, mirrors left) |
| Bottom strip | y=1008-1023 | -- | Empty (unused) |

---

## Left Half: Detailed Section Map

### Row Layout

| Row | Y Range | Height | Content | Japanese? |
|-----|---------|--------|---------|-----------|
| A upper | y=1-22 | 22px | `5 6 7 8 9 : ; < = > ? [sp] A B C D E F G H I` | No (ASCII) |
| A lower | y=24-47 | 24px | `[?] (c) a b c d e f g h i j k l m n o p q r s` | No (ASCII) |
| B (symbols) | y=49-71 (x=0-159) | 23px | `x O x <- -> _ [sp]` | No (symbols) |
| B (hiragana) | y=49-71 (x=160-495) | 23px | `a i u e o ka ki ku ke ko sa shi su se` | **YES** |
| C | y=73-93 | 21px | `ya yu yo ra ri ru re ro wa wo n ga gi gu ge go za ji su ze zo` | **YES** |
| D | y=95-117 | 23px | Hiragana dakuten tail + Katakana: `a i u e o ka ki ku ke ko sa n su se so ta chi` | **YES** |
| E | y=119-141 | 23px | Katakana continued: `ra ri ru re ro wa n ga gi gu ge go za ji zu ze so da di du` | **YES** |
| Kanji 1-36 | y=143-1006 | 24px each | 756 kanji glyphs in 36 rows x 21 columns | **YES** |

### Column Layout (Left Half)

21 columns with these x-boundaries:

```
Col  0: x=  0- 15 (16px wide, narrow first column)
Col  1: x= 17- 39 (23px glyph + 1px gap)
Col  2: x= 41- 63
Col  3: x= 65- 87
Col  4: x= 89-111
Col  5: x=113-135
Col  6: x=137-159
Col  7: x=161-183
Col  8: x=185-207
Col  9: x=209-231
Col 10: x=233-255
Col 11: x=257-279
Col 12: x=281-303
Col 13: x=305-327
Col 14: x=329-351
Col 15: x=353-375
Col 16: x=377-399
Col 17: x=401-423
Col 18: x=425-447
Col 19: x=449-471
Col 20: x=473-495
```

---

## Japanese Text Regions (All Locations)

### Region 1: Hiragana Block

| Coordinate | Value |
|------------|-------|
| **x** | 160 |
| **y** | 48 |
| **width** | 336 |
| **height** | 46 |
| **Rows** | 2 (y=48-71, y=72-93) |
| **Glyphs** | ~35 hiragana characters (a-zo, including dakuten) |

Individual hiragana visible: あ い う え お か き く け こ さ し す せ や ゆ よ ら り る れ ろ わ を ん が ぎ ぐ げ ご ざ じ ぜ ぞ

### Region 2: Katakana Block

| Coordinate | Value |
|------------|-------|
| **x** | 0 |
| **y** | 94 |
| **width** | 496 |
| **height** | 48 |
| **Rows** | 2 (y=94-117, y=118-141) |
| **Glyphs** | ~42 katakana characters (including dakuten/handakuten) |

Individual katakana visible: ア イ ウ エ オ カ キ ク ケ コ サ シ ス セ ソ タ チ ラ リ ル レ ロ ワ ン ガ ギ グ ゲ ゴ ザ ジ ズ ゼ ダ ヂ ヅ (plus a few hiragana dakuten at the start of row D)

### Region 3: Kanji Grid (LARGEST Japanese region)

| Coordinate | Value |
|------------|-------|
| **x** | 0 |
| **y** | 142 |
| **width** | 496 |
| **height** | 866 |
| **Rows** | 36 |
| **Columns** | 21 |
| **Total Cells** | 756 |
| **All occupied?** | Yes -- every cell contains a kanji glyph |

Sample kanji from first row (y=143-165):
ブ 引 何 岸 宮 去 橋 険 故 向 行 今 次 者 人 静 騒 達 渡 悲 負

Sample kanji from last filled row (y=983-1006):
盟 忌 吊 柵 拙 島 衆 町 叶 渉 戒 績 憧 屍 槽 蒸 盲 兜 糸 村 絆

### Region 4: Right Half (Small Font Mirror)

| Coordinate | Value |
|------------|-------|
| **x** | 512 |
| **y** | 0 |
| **width** | 512 |
| **height** | 1008 |
| **Cell size** | ~16x16 (estimated) |
| **Content** | Same character set as left half, rendered at smaller size |

The right half contains a smaller-scale rendering of the same glyph set (ASCII + kana + kanji) used for UI text compositing. The cell boundaries are less regular than the left half.

---

## Summary of All Japanese Text Regions

| # | Region | Bbox (x, y, w, h) | Type | Glyph Count |
|---|--------|--------------------|------|-------------|
| 1 | Hiragana (in Row B) | (160, 48, 336, 24) | Hiragana | ~14 |
| 2 | Hiragana (Row C) | (0, 72, 496, 22) | Hiragana + dakuten | 21 |
| 3 | Hira/Kata (Row D) | (0, 94, 496, 24) | Hiragana tail + Katakana | 21 |
| 4 | Katakana (Row E) | (0, 118, 496, 24) | Katakana + dakuten | 21 |
| 5 | Kanji Grid | (0, 142, 496, 866) | Kanji | 756 |
| 6 | Right Half (small) | (512, 0, 512, 1008) | All Japanese (mirror) | ~800+ |
| | **TOTAL** | | | **~1633+** |

---

## Non-Japanese Regions

| # | Region | Bbox (x, y, w, h) | Content |
|---|--------|--------------------|---------|
| 1 | ASCII upper | (0, 0, 496, 23) | Digits 5-9, punctuation, A-I |
| 2 | ASCII lower | (0, 24, 496, 47) | Copyright symbol, a-s |
| 3 | Symbols | (0, 48, 160, 24) | x O x arrows underscore |
| 4 | Vertical gap | (496, 0, 16, 1024) | Empty separator |
| 5 | Bottom strip | (0, 1008, 1024, 16) | Empty/unused |

---

## PCSX2-Captured UI Labels (Composed from Atlas Glyphs)

These are the 16 runtime-composed labels the game reads from R1188 at VRAM page 0x2214. Each label is composed from individual glyph cells at runtime, NOT stored as pre-rendered text.

### Tab Labels (48x20px)

| Dump Hash | Japanese | English | Glyph IDs |
|-----------|----------|---------|-----------|
| `16625baf` | 性別 | Gender | 6400-series |
| `19a39fbc` | カナ | Katakana (tab) | 6400 |
| `1f839869` | 英数 | Alphanumeric (tab) | 6402 |
| `6f1fb24f` | 決定 | Confirm/OK | 6405 |
| `88ff8b57` | 記号 | Symbols (tab) | 6403 |
| `9677cb23` | (unclear - possibly かな/男名/女名) | Hiragana/M-name/F-name | 6401/6406/6407 |
| `9bec87b4` | 種族 | Race | sidebar label |
| `c89b469f` | 属性 | Alignment | sidebar label |

### Stat Labels (64x16px)

| Dump Hash | Japanese | English |
|-----------|----------|---------|
| `280ea82c` | 力 | STR |
| `4841ef9a` | 幸運度 | LCK (Luck) |
| `5d0c6327` | 敏捷度 | AGI (Agility) |
| `aa43f966` | 生命力 | VIT (Vitality) |
| `bb20512b` | 信仰心 | FTH (Faith) |
| `d4552342` | 知恵 | INT (Intelligence) |
| `f2013a64` | HP/MAX | HP/MAX (not Japanese) |

### Other Labels (40x24px)

| Dump Hash | Japanese | English |
|-----------|----------|---------|
| `d09a04bd` | 職業 | Class |

---

## Key Findings

1. **R1188 is a pure font/glyph atlas** -- it does NOT contain pre-composed UI labels. All UI text (tab labels, stat labels, button labels, title text) is composed at runtime from individual glyph cells.

2. **Japanese text covers ~95% of the atlas surface area.** The only non-Japanese content is two rows of ASCII (40 chars) and a few symbols at the top of the left half.

3. **The left half contains 833 identifiable glyph cells**: 40 ASCII/symbol + 77 kana + 756 kanji.

4. **The right half mirrors the left half** at a smaller rendering size, roughly doubling the total glyph count.

5. **To translate UI labels**, individual glyph cells at specific grid positions must be replaced with English equivalents. The game looks up glyph IDs (e.g., 6400-6412) which map to specific UV coordinates in this atlas via a BSS lookup table at VA 0x4EBBEC.

6. **The "title text" (shinki touroku / new registration)** is NOT in this atlas -- it is composed via R1272 tile IDs referenced from EXE data structs.

---

## Generated Files

| File | Description |
|------|-------------|
| `r1188_annotated_sections.png` | Full atlas with color-coded section boundaries |
| `r1188_2x.png` | 2x scaled clean version |
| `r1188_kanji_grid_detail.png` | Zoomed kanji grid with cell boundaries |
| `crop_top_row*_left.png` | 3x zoomed crops of top rows (left half) |
| `crop_top_row*_right.png` | 3x zoomed crops of top rows (right half) |
| `crop_main_grid_left_sample.png` | 3x zoomed sample of kanji grid |
| `crop_bottom_left.png` | 3x zoomed bottom rows |
| `label_*_alpha.png` | 4x zoomed alpha-extracted PCSX2 label dumps |
| `right_half_y*_zoom.png` | 4x zoomed right-half samples |
