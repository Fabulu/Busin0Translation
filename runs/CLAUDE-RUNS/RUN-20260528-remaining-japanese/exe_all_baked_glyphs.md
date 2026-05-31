# Complete Inventory: All Hardcoded Japanese Glyph IDs in the EXE

**Date:** 2026-05-28
**EXE:** `extracted/SLPM_653.78` (4,185,776 bytes)
**Scan range:** Full data section 0x3AB000-0x3FD000 (335,872 bytes)

---

## Executive Summary

There are **three distinct systems** that render Japanese text, each using a different mechanism:

| System | Location | Glyph ID Range | Mechanism | Translation Method |
|--------|----------|---------------|-----------|-------------------|
| **Menu struct tiles** | EXE 0x3C3000-0x3C5174 | 475-921 | Pre-rendered bitmap tiles in R1272 font atlas | Replace atlas tiles with English |
| **MSG resource text** | PACKDATA R38, R39, etc. | 274-1747 | Composable glyph rendering (standard text engine) | Replace glyph IDs with ASCII (33-58) in MSG data |
| **SJIS strings** | EXE 0x3F9370-0x3FC790 | N/A (raw SJIS) | Direct SJIS text rendering | Overwrite with ASCII |

**The only glyph IDs that need new font tiles in R1272 are tile IDs 475-921 used by the menu struct system.** Everything else is either composable text (handled by MSG re-encoding) or raw SJIS strings (handled by direct byte patching).

---

## SYSTEM 1: Menu Struct Pre-Rendered Tiles (THE MAIN TARGET)

### Location: EXE 0x3C3000-0x3C5174

152 entries, each 56 bytes. Each entry defines a menu button with:
- **Label tile** (offset 2): Single tile ID for the button label, range 604-674 (70 unique)
- **State tiles** (offsets 26-46): Tiles for normal/selected/disabled visual states, range 683-921 (236 unique)
- **Extra tiles** (offset 50): Additional tile for sub-label or icon, range 475-603 (124 unique)

### Complete Tile ID Inventory

**ALL 430 unique tile IDs used by menu structs (glyph positions 475-921):**

#### Extra Tiles (offset 50): IDs 475-603

These appear to be sub-labels or category indicators. 124 unique IDs:

```
475, 480-603 (contiguous except 586 missing)
```

Decoded text (from glyph map -- note: many are incorrect single-kanji readings since these are pre-rendered multi-character labels, not composable glyphs):

| ID Range | Count | Notes |
|----------|-------|-------|
| 475 | 1 | Used as "blank/none" marker across many entries |
| 480-489 | 10 | Unmapped or misc (480-484 unmapped, 485-489 mapped) |
| 490-603 | 114 | Various menu sub-labels |

#### Label Tiles (offset 2): IDs 604-674

70 unique button label tiles (one per button type). Missing: 606.

These are the primary button text tiles shown to the player. Each is a pre-rendered Japanese text bitmap (e.g., "装備", "魔法", "戦う", etc.).

#### State Tiles (offsets 26-46): IDs 683-921

236 unique tiles for visual states (normal, selected, disabled, hover). Missing from range: 899, 900, 901.

These are visual variants of the label tiles -- same text, different colors/effects.

### Gaps in 475-921 Range

17 IDs not referenced by any menu entry:
```
476, 477, 478, 479, 586, 606, 675, 676, 677, 678, 679, 680, 681, 682, 899, 900, 901
```

These may be unused/reserved tile positions in the R1272 atlas.

### Menu Entry Mapping (All 152 Entries)

| Entry | EXE Offset | Label Tile | State Tiles | Extra Tile | Likely Purpose |
|-------|-----------|------------|-------------|------------|----------------|
| 0 | 0x3C3000 | 607 | 683, 684 | 480 | Town menu option |
| 1 | 0x3C3038 | 608 | 685, 686 | 481 | Town menu option |
| 2 | 0x3C3070 | 609 | 687, 688 | 482 | Town menu option |
| 3 | 0x3C30A8 | 610 | 689, 690 | 483 | Town menu option |
| 4 | 0x3C30E0 | 611 | 691, 692 | 484 | Town menu option |
| 5 | 0x3C3118 | 612 | 693, 694 | 485 | Town menu option |
| 6 | 0x3C3150 | 613 | 695, 696 | 486 | Town menu option |
| 7 | 0x3C3188 | 614 | 697, 698 | 487 | Town menu option |
| 8 | 0x3C31C0 | 615 | 699, 700 | 488 | Town menu option |
| 9 | 0x3C31F8 | 616 | 701, 702 | 489 | Town menu option |
| 10 | 0x3C3230 | 617 | 703, 704 | 490 | Chargen/registration |
| 11 | 0x3C3268 | 618 | 705, 706 | 491 | Chargen/registration |
| 12 | 0x3C32A0 | 618 | 707, 708 | 492 | Chargen/selection |
| 13 | 0x3C32D8 | 619 | 709, 710 | 493 | Chargen/requirement |
| 14 | 0x3C3310 | 620 | 711, 712 | 494 | Chargen/stats |
| 15 | 0x3C3348 | 621 | 713, 714 | 495 | Chargen/name |
| 16 | 0x3C3380 | 622 | 715, 716 | 496 | Chargen/high-low |
| 17 | 0x3C33B8 | 623 | 717, 718 | 497 | Status/INT-FTH |
| 18 | 0x3C33F0 | 624 | 719, 720 | 498 | Status/AGI-LCK |
| 19 | 0x3C3428 | 625 | 721, 722 | 499 | Status/EXP |
| 20 | 0x3C3460 | 626 | 723, 724 | 500 | Status/defense |
| 21 | 0x3C3498 | 627 | 725, 726 | 501 | Status/evasion |
| 22 | 0x3C34D0 | 628 | 727, 728 | 502 | Status/ability |
| 23 | 0x3C3508 | 612 | 729, 730 | 503 | Status/power |
| 24 | 0x3C3540 | 629 | 731, 732 | 504 | Camp/class |
| 25 | 0x3C3578 | 630 | 733, 734 | 505 | Camp/location |
| 26 | 0x3C35B0 | 631 | 735, 736 | 506 | Camp/delete |
| 27 | 0x3C35E8 | 632 | 737, 738 | 507 | Camp/remove |
| 28 | 0x3C3620 | 633 | 739, 740 | 508 | Party/squad |
| 29 | 0x3C3658 | 634 | 741, 742 | 509 | Party/group |
| 30 | 0x3C3690 | 635 | 743, 744 | 510 | Party/name |
| 31 | 0x3C36C8 | 636 | 745, 746 | 511 | Party/gender |
| 32 | 0x3C3700 | 637 | 747, 748 | 512 | Party/type |
| 33 | 0x3C3738 | 638 | 749, 750 | 513 | Party/race |
| 34 | 0x3C3770 | 639 | 751, 752 | 514 | Party/tribe |
| 35 | 0x3C37A8 | 640 | 753, 754 | 515 | Party/attribute |
| 36 | 0x3C37E0 | 641 | 755, 756 | 516 | Party/nature |
| 37 | 0x3C3818 | 642 | 757, 758 | 517 | Party/job |
| 38 | 0x3C3850 | 643 | 759, 760 | 518 | Party/male |
| 39 | 0x3C3888 | 644 | 761, 762 | 519 | Adventure |
| 40 | 0x3C38C0 | 645 | 763, 764 | 520 | Rest/good |
| 41 | 0x3C38F8 | 646 | 765, 766 | 521 | Buy |
| 42 | 0x3C3930 | 647 | 767, 768 | 522 | Use/equip |
| 43 | 0x3C3968 | 648 | 769, 770 | 523 | Difficulty |
| 44 | 0x3C39A0 | 649 | 771, 772 | 524 | Bond/curse |
| 45 | 0x3C39D8 | 650 | 773, 774 | 525 | Recovery |
| 46 | 0x3C3A10 | 651 | 775, 776 | 526 | Heal/restore |
| 47 | 0x3C3A48 | 652 | 777, 778 | 527 | Change/special |
| 48 | 0x3C3A80 | 653 | 779, 780 | 528 | Complete |
| 49 | 0x3C3AB8 | 654 | 781, 782 | 529 | Battle/fight |
| 50 | 0x3C3AF0 | 655 | 783, 784 | 530 | Lose/dispel |
| 51 | 0x3C3B28 | 656 | 785, 786 | 531 | Gather |
| 52 | 0x3C3B60 | 657 | 787, 788 | 475 | Assign (reuse) |
| 53-54 | 0x3C3B98+ | 65535 | 789-792 | 475 | Blank/conditional |
| 55-58 | 0x3C3C08+ | mixed | 793-798 | 532-534 | Submenus |
| 59-151 | 0x3C3CE8+ | mixed | 799-921 | 535-603 | Battle/shop/church/dungeon |

---

## SYSTEM 2: MSG Resource Composable Text (ALREADY HANDLED)

### Location: PACKDATA resources (R35, R37, R38, R39, R40, R41, R42, R44, R45, R48)

These use BE uint16 glyph IDs in the standard text rendering engine. Kanji glyph IDs found in R38 stat labels:

| R38 Entry | Glyph IDs | Japanese | English | Translation Method |
|-----------|-----------|----------|---------|-------------------|
| 2 (STR) | 346 | 力 | str | Replace with 51,52,50 |
| 3 (INT) | 535, 717 | 知恵 | int | Replace with 41,46,52 |
| 4 (FTH) | 308, 354, 320 | 信仰心 | fth | Replace with 38,52,40 |
| 5 (VIT) | 718, 696, 346 | 生命力 | vit | Replace with 54,41,52 |
| 6 (AGI) | 582, 719, 590 | 敏捷度 | agi | Replace with 33,39,41 |
| 7 (LCK) | 720, 721, 590 | 幸運度 | lck | Replace with 44,35,43 |
| 8 (Name) | 314, 510 | 名前 | name | Replace with 46,33,45,37 |
| 9 (Level) | 234, 257, 233 | レベル | level | Already katakana |
| 10 (Race) | 513, 514 | 種族 | race | Replace with 50,33,35,37 |
| 11 (Gender) | 511, 512 | 性別 | gender | Replace with 39,37,46,36,37,50 |
| 12 (Attr) | 515, 511 | 属性 | align | Replace with 33,44,41,39,46 |
| 13 (Class) | 504, 517 | 職業 | class | Replace with 35,44,33,51,51 |
| 14 (Personality) | 511, 516 | 性性 | nature | Replace accordingly |

**These do NOT need new font tiles.** They use the existing glyph atlas tiles (same tiles that render dialogue text). The kanji glyph IDs (274+) in R38 will be replaced with ASCII letter glyph IDs (33-58) during MSG re-encoding.

Additional kanji glyph IDs in R38 entries include race names, class names, alignment labels, personality traits, and field labels (entries 15-257). All will be replaced with ASCII equivalents via the standard build pipeline.

---

## SYSTEM 3: SJIS Strings (TRIVIAL)

### Location: EXE 0x3F9370-0x3FC790

| Offset | Japanese | English | Size |
|--------|----------|---------|------|
| 0x3F9370 | BUSIN0中断データ | BUSIN0 Suspend Data | 24 bytes |
| 0x3FC720 | BUSIN0 | BUSIN0 | 12 bytes |
| 0x3FC750 | BUSIN0データ1 | BUSIN0 Data 1 | 20 bytes |
| 0x3FC770 | BUSIN0データ2 | BUSIN0 Data 2 | 20 bytes |
| 0x3FC790 | BUSIN0データ3 | BUSIN0 Data 3 | 20 bytes |

These are memory card save display strings. Patched by overwriting SJIS bytes with ASCII.

---

## OTHER EXE GLYPH TABLES (NOT PLAYER-VISIBLE TEXT)

### Full Glyph Availability List (0x3B3136-0x3B3844)
- 903 uint16 values, 296 unique kanji glyph IDs (274-964)
- **Purpose:** Lookup table defining which glyphs are available in the font atlas
- **NOT rendered as text** -- data table only

### Chargen Kana Grid (0x3C844A-0x3C8F64)
- Hiragana (112-191) and katakana (193-272) for name entry keyboard
- **No kanji labels** -- purely kana input grid

### Name Entry Grid (0x3C99B8-0x3CA6EF)
- 149 kanji glyph IDs (274-426) available for character naming
- **Displayed as selectable kanji** in name entry screen
- These render through the standard glyph atlas, not pre-rendered tiles

### Kana Mapping Table (0x3C5B32-0x3C6186)
- Kana input method mapping
- **No kanji present**

### NPC Names (0x3C93AE-0x3C93D0)
- "エミーリア" (Emilia) and "リュート" (Lute)
- **Katakana only** -- rendered via standard glyph atlas, IDs 193-272

### Tab/Button Bitmap Glyph IDs (0x3C9DA0-0x3C9DFC)
- IDs 6400-6408 -- these are large bitmap tile references, NOT standard glyphs
- **Separate texture system** -- tab button images (already identified in tab label analysis)

### Font Width Tables (0x3DDC48-0x3DDF48)
- 4 x 248 byte width tables
- **Not glyph IDs** -- pixel width values per glyph position

### Debug Strings (0x3EE9D0-0x3F3500)
- ~300+ printf-format debug messages in SJIS
- **Not player-visible** -- developer diagnostics only

---

## COMPLETE LIST: Glyph IDs Needing Font Tiles in R1272

### Pre-Rendered Menu Tiles: 430 IDs

These are the ONLY glyph positions that need new English font tiles drawn in the R1272 atlas:

```
475, 480-585, 587-605, 607-674, 683-898, 902-921
```

Broken down:
- **Extra/sub-label tiles** (475, 480-585, 587-603): 125 tiles
- **Label tiles** (604-605, 607-674): 70 tiles  
- **State tiles** (683-898, 902-921): 236 tiles (but many are color variants of label tiles)

### Unique Visual Labels (Deduplicated)

Since state tiles are just color variants of label tiles, the actual number of unique Japanese text strings to translate is approximately **70** (the label tile count). Each label has ~3 state variants (normal, selected, disabled) that show the same text in different visual styles.

---

## ACTION ITEMS

1. **Extract the 70 label tiles** from R1272 at glyph positions 604-674 to identify what Japanese text each one shows
2. **Create English replacement tiles** for all 430 positions (70 labels x ~3 states each + 125 extras)
3. **Patch R38/R39/etc.** to replace kanji glyph IDs with ASCII letter IDs (already in build pipeline)
4. **Patch 5 SJIS save strings** at 0x3F9370-0x3FC790 (trivial)
5. **No other EXE modifications needed** for Japanese glyph removal
