# EXE Table 2C: Menu Button/Navigation Label System -- Deep Analysis

**Date**: 2026-05-28
**EXE**: `extracted/SLPM_653.78`
**Table offset**: 0x3C3000-0x3C46F8+56 = 0x3C3000-0x3C4730 (106 records x 56 bytes)
**Virtual address**: 0x004C2F80

---

## 1. Struct Format (56 bytes per record)

```
Offset  Size  Type     Field               Description
------  ----  ----     -----               -----------
0x00    2     u16      flags_or_state       0x0000 = active, 0xFFFF = disabled/separator
0x02    2     u16      icon_glyph           Menu icon glyph ID (rendered left of label)
0x04    4     float    scale                Always 1.0 (uniform scale factor)
0x08    4     float    width                Pixel width of label area (40-300)
0x0C    4     float    spacing              Character spacing multiplier (1.0-3.0)
0x10    4     float    param_4              Always 1.5 (y-scale or line height?)
0x14    4     float    param_5              Always 0.05 (alpha/fade parameter?)
0x18    2     u16      state1_flag_A        Flag for state 1 glyph A (0=normal, FFFF=none)
0x1A    2     u16      state1_glyph_A       Label glyph 1, state 1 (normal)
0x1C    2     u16      state1_flag_B        Flag for state 1 glyph B
0x1E    2     u16      state1_glyph_B       Label glyph 2, state 1 (normal)
0x20    2     u16      state2_flag_A        Flag for state 2 glyph A
0x22    2     u16      state2_glyph_A       Label glyph 1, state 2 (= state1_A)
0x24    2     u16      state2_flag_B        Flag for state 2 glyph B
0x26    2     u16      state2_glyph_B       Label glyph 2, state 2 (= state1_B)
0x28    2     u16      highlight_flag       0x0001=has highlight, 0xFFFF=no highlight, 0x0000=variant
0x2A    2     u16      highlight_glyph_1    Highlighted state glyph 1 (= glyph_B when flag=1)
0x2C    2     u16      highlight_flag_2     Always 0x0001 when highlight exists
0x2E    2     u16      highlight_glyph_2    Highlighted state glyph 2 (= glyph_A when flag=1)
0x30    2     u16      padding              Always 0x0000
0x32    2     u16      reference_glyph      Reference glyph (G field) -- see analysis below
0x34    2     u16      menu_index           Index linking to menu system (46-116)
0x36    2     u16      padding_end          Always 0x0000
```

### State System

Each record defines 3 visual states for the menu label:

- **State 1** (bytes 0x18-0x1F): Normal state -- `[flag_A][glyph_A][flag_B][glyph_B]`
- **State 2** (bytes 0x20-0x27): Duplicate of state 1 (identical glyphs, verified 104/106 match)
- **Highlighted** (bytes 0x28-0x2F): Selected/hover state
  - When highlight_flag = 0x0001: shows glyphs B+A (reversed order from normal)
  - When highlight_flag = 0xFFFF: no highlight (glyph slots set to 0xFFFF)

The 2 mismatches (records 18, 95) have state 2 glyph B = 0xFFFF while state 1 has a valid glyph, suggesting state 2 may be a "disabled" visual variant.

### Float Parameters

| Parameter | Offset | Range | Meaning |
|-----------|--------|-------|---------|
| scale | 0x04 | Always 1.0 | Uniform scale |
| width | 0x08 | 1-300 | Label area width in pixels |
| spacing | 0x0C | 1.0-3.0 | Inter-glyph spacing |
| param_4 | 0x10 | Always 1.5 | Possibly y-scale |
| param_5 | 0x14 | Always 0.05 | Possibly alpha/fade |

---

## 2. Critical Answer: Can We Replace Composite Glyphs with ASCII Sequences?

**NO. The struct format does NOT support multi-character ASCII replacement.**

Each menu label has EXACTLY 3 glyph rendering slots:
- 1 icon glyph (bytes 0x02-0x03)
- 2 label glyphs (bytes 0x1A-0x1B and 0x1E-0x1F)

These are duplicated across 3 states but never expanded. The zero bytes between glyph slots are FLAGS (part of `[u16 flag, u16 glyph_id]` pairs), not spare capacity.

### Viable Translation Strategies

**Strategy A: Font Atlas Replacement (RECOMMENDED)**
- Replace font atlas tiles at glyph IDs 480-866 with English word bitmaps
- Each 16x16 (or similar) glyph cell gets a pre-rendered English abbreviation
- The icon glyph shows a symbol; the two label glyphs show English text split across 2 tiles
- Example: "Tavern" = icon tile with beer mug + label tile 1 "Tav" + label tile 2 "ern"
- Adjust the `width` float (offset 0x08) to accommodate wider English text
- Adjust the `spacing` float (offset 0x0C) for proper kerning

**Strategy B: EXE Code Patch**
- Modify the menu label rendering routine to read variable-length glyph strings
- Would require finding and patching the MIPS code that reads these structs
- Most complex but most flexible solution

**Strategy C: Hybrid Approach**
- Use the icon glyph slot for a descriptive mini-icon
- Use the 2 label glyph slots with custom font atlas entries containing English words
- The `width` parameter (40-300 pixels) gives room to render wider content
- Many entries already have width=120-300, providing adequate space

---

## 3. Record Grouping by Menu Index

Records sharing the same `menu_index` value belong to the same menu screen. The game loads all records with a matching index when entering a particular menu.

### Identified Menu Groups

**NOTE**: Glyph ID mappings below use msg_glyph_map.json which was built for MSG text rendering. Many IDs in the 480-866 range render DIFFERENT characters on the font atlas than what the map indicates. The "decoded" kanji shown are the MAP values, not necessarily what displays in-game. Visual verification against font atlas tile images is required.

#### Group idx=50 (1 record) -- Record 0
- Single entry with icon + 2 label glyphs
- Width: 120, Spacing: 3.0
- Map values: icon=607[稼] labels=683[偉]+684[美]

#### Group idx=51 (2 records) -- Records 1, 97
- Width: 100/40
- Map values: icons=608[箱], 604[味]

#### Group idx=52 (1 record) -- Record 2
- Width: 90

#### Group idx=53 (2 records) -- Records 3, 98

#### Group idx=54 (3 records) -- Records 4, 22, 90
- Contains one empty separator (rec 90)

#### Group idx=55 (2 records) -- Records 5, 99

#### Group idx=56 (2 records) -- Records 6, 94

#### Group idx=57 (1 record) -- Record 7

#### Group idx=58 (1 record) -- Record 8

#### Group idx=59 (1 record) -- Record 9

#### Group idx=60 (2 records) -- Records 10, 11
- Two options in the same menu

#### Group idx=61 (1 record) -- Record 12

#### Group idx=62 (1 record) -- Record 13

#### Group idx=63 (2 records) -- Records 14, 89
- Rec 89 is icon-only separator

#### Group idx=64 (1 record) -- Record 15

#### Group idx=65 (1 record) -- Record 16

#### Group idx=66 (1 record) -- Record 17

#### Group idx=67 (1 record) -- Record 18

#### Group idx=68 (1 record) -- Record 19

#### Group idx=69 (1 record) -- Record 20

#### Group idx=70 (1 record) -- Record 21

#### Group idx=71 (1 record) -- Record 23

#### Group idx=72 (1 record) -- Record 26

#### Group idx=73 (2 records) -- Records 27, 87

#### Group idx=74 (2 records) -- Records 28, 88

#### Group idx=75 (3 records) -- Records 29, 85, 86

#### Group idx=76 (1 record) -- Record 30

#### Group idx=77 (1 record) -- Record 31

#### Group idx=78 (1 record) -- Record 32

#### Group idx=79 (1 record) -- Record 33

#### Group idx=80 (1 record) -- Record 34

#### Group idx=81 (1 record) -- Record 35

#### Group idx=82 (1 record) -- Record 36

#### Group idx=83 (1 record) -- Record 37

#### Group idx=84 (2 records) -- Records 38, 91

#### Group idx=85 (1 record) -- Record 39

#### Group idx=86 (1 record) -- Record 40

#### Group idx=87 (1 record) -- Record 42

#### Group idx=88 (6 records) -- Records 43, 58-62
- Largest group. Contains icon-only separators and label entries
- Pattern: icon-only entries (58, 60) alternate with label entries (59, 61, 62)
- This suggests a multi-page or tabbed menu

#### Group idx=89 (8 records) -- Records 41, 44, 69-74
- Second largest group
- Contains icon-only separators at records 69, 72

#### Group idx=90 (7 records) -- Records 45, 63-68
- Contains separators at records 63, 66

#### Group idx=91 (6 records) -- Records 46, 80-84
- Contains separators at records 80, 81

#### Group idx=92 (4 records) -- Records 47, 75-77

#### Group idx=93 (7 records) -- Records 48, 100-105
- Contains separators at records 100, 102

#### Group idx=94 (1 record) -- Record 49

#### Group idx=95 (1 record) -- Record 50

#### Group idx=96 (1 record) -- Record 51

#### Group idx=112 (1 record) -- Record 24

#### Group idx=113 (1 record) -- Record 25

#### Group idx=116 (3 records) -- Records 52, 92, 93
- Contains separators at records 92, 93

---

## 4. Town Navigation Identification Attempt

The town navigation menu would contain buttons for: Bar Luna Light (酒場), Adventurer's Guild (冒険者ギルド), Vigger Shop (店), Adventurer's Inn (宿屋), Church of Salem, and Request Board (依頼).

**Problem**: Without correct glyph-to-character mappings for IDs 480-866 in the EXE context, we cannot definitively identify which records correspond to which town locations by text content alone.

### Structural Clues for Town Navigation

Town navigation would likely be a group with 5-8 entries (one per location). Candidate groups:

| idx | Records | Active Labels | Width Range | Candidate? |
|-----|---------|--------------|-------------|-----------|
| 47 | 53-57 | 5 entries | 1-60 | POSSIBLE -- 5 navigation targets |
| 88 | 43,58-62 | 3 labels + 3 separators | 60-80 | Tabbed/sub-menu |
| 89 | 41,44,69-74 | 5 labels + 3 separators | 70-150 | POSSIBLE -- multi-section |
| 90 | 45,63-68 | 4 labels + 3 separators | 70-90 | Sub-menu |
| 91 | 46,80-84 | 3 labels + 3 separators | 80-120 | Sub-menu |
| 93 | 48,100-105 | 4 labels + 3 separators | 50-80 | Sub-menu |

**Group idx=47** is the strongest candidate for town navigation:
- 5 active label entries (records 53-57)
- Records 53, 54, 55 have no icon (icon=FFFF) -- text-only labels
- Records 56, 57 share icon 605
- Matches the expected 5 town destinations (Bar, Guild, Shop, Inn, Quests)

### Key Records for Town Navigation (idx=47)

| Rec | Offset | Icon | Label A | Label B | G | Width | Highlight |
|-----|--------|------|---------|---------|---|-------|-----------|
| 53 | 0x3C3B98 | (none) | 789 | 790 | 475 | 1 | NO |
| 54 | 0x3C3BD0 | (none) | 791 | 792 | 475 | 60 | NO |
| 55 | 0x3C3C08 | (none) | 793 | 794 | 532 | 60 | NO |
| 56 | 0x3C3C40 | 605 | 795 | 796 | 533 | 60 | NO |
| 57 | 0x3C3C78 | 605 | 797 | 798 | 534 | 60 | NO |

Record 53 has width=1, which may indicate it is hidden or a header. The other 4 have width=60.

**To confirm these are the town navigation buttons**, visual verification is needed by:
1. Examining font atlas tiles for glyph IDs 789-798, 605, 475, 532-534
2. Cross-referencing with PCSX2 memory viewer at runtime
3. Checking the EXE code that loads menu_index=47

---

## 5. Separator/Header Pattern

Many menu groups use a pattern of alternating icon-only "header" records and label records:

```
[icon-only rec] [label rec] [label rec]   -- 2 options under one heading
[icon-only rec] [label rec] [label rec]   -- 2 more options under another heading
```

This creates a visual hierarchy in the menu:

```
[ICON]                    <-- section header (separator/icon-only)
  [ICON] Label1 Label2   <-- menu option 1
  [ICON] Label1 Label2   <-- menu option 2
[ICON]                    <-- next section header
  [ICON] Label1 Label2   <-- menu option 3
```

---

## 6. Reference Glyph (G Field, byte 0x32)

The G field at offset 0x32 contains a glyph ID that does NOT appear to be rendered alongside the label. Its purpose is unclear but possible uses include:

- **Text description lookup**: Could index into a description string table
- **Category/type marker**: Groups related menu items
- **Accessibility label**: Alternative text for the menu option
- **Unused/legacy**: May be vestigial from development

When G = 475 (the glyph for 王 "king"), it consistently appears in empty/separator records, suggesting 475 is a placeholder/null value for this field.

---

## 7. Full Record Table

| Rec | Offset | Icon ID | Icon | Label A ID | A | Label B ID | B | HL | G ID | G | Width | Spc | Idx |
|-----|--------|---------|------|-----------|---|-----------|---|----|------|---|-------|-----|-----|
| 0 | 0x3C3000 | 607 | 稼 | 683 | 偉 | 684 | 美 | HL | 480 | ? | 120 | 3.0 | 50 |
| 1 | 0x3C3038 | 608 | 箱 | 685 | 追 | 686 | 巨 | HL | 481 | ? | 100 | 2.0 | 51 |
| 2 | 0x3C3070 | 609 | 欠 | 687 | 期 | 688 | 街 | HL | 482 | ? | 90 | 1.0 | 52 |
| 3 | 0x3C30A8 | 610 | 思 | 689 | 誓 | 690 | 番 | HL | 483 | 無 | 90 | 1.8 | 53 |
| 4 | 0x3C30E0 | 611 | 話 | 691 | 並 | 692 | 宝 | NO | 484 | ? | 90 | 1.0 | 54 |
| 5 | 0x3C3118 | 612 | 払 | 693 | 今 | 694 | 強 | HL | 485 | 光 | 70 | 1.0 | 55 |
| 6 | 0x3C3150 | 613 | 許 | 695 | 壁 | 696 | 命 | NO | 486 | 冒 | 50 | 1.5 | 56 |
| 7 | 0x3C3188 | 614 | 聞 | 697 | 器 | 698 | 終 | HL | 487 | 険 | 60 | 1.0 | 57 |
| 8 | 0x3C31C0 | 615 | ！ | 699 | 雇 | 700 | 能 | NO | 488 | 広 | 60 | 1.3 | 58 |
| 9 | 0x3C31F8 | 616 | 看 | 701 | 団 | 702 | 日 | NO | 489 | 刻 | 60 | 1.2 | 59 |
| 10 | 0x3C3230 | 617 | 扉 | 703 | 予 | 704 | 可 | HL | 490 | 息 | 80 | 2.5 | 60 |
| 11 | 0x3C3268 | 618 | 考 | 705 | 現 | 706 | 員 | HL | 491 | 登 | 60 | 1.6 | 60 |
| 12 | 0x3C32A0 | 618 | 考 | 707 | 選 | 708 | 択 | HL | 492 | 録 | 60 | 1.6 | 61 |
| 13 | 0x3C32D8 | 619 | 習 | 709 | 必 | 710 | 要 | NO | 493 | 開 | 60 | 1.6 | 62 |
| 14 | 0x3C3310 | 620 | 下 | 711 | 値 | 712 | 足 | HL | 494 | 帰 | 180 | 3.0 | 63 |
| 15 | 0x3C3348 | 621 | 解 | 713 | 名 | 714 | 前 | HL | 495 | 専 | 80 | 1.0 | 64 |
| 16 | 0x3C3380 | 622 | 通 | 715 | 高 | 716 | 低 | HL | 496 | 所 | 250 | 2.0 | 65 |
| 17 | 0x3C33B8 | 623 | ? | 717 | 恵 | 718 | 生 | HL | 497 | 出 | 100 | 1.0 | 66 |
| 18 | 0x3C33F0 | 624 | 求 | 719 | 捷 | 720 | 幸 | 00 | 498 | 新 | 120 | 2.5 | 67 |
| 19 | 0x3C3428 | 625 | ? | 721 | 運 | 722 | 獲 | NO | 499 | 兵 | 120 | 1.0 | 68 |
| 20 | 0x3C3460 | 626 | 途 | 723 | 果 | 724 | 解 | HL | 500 | 召 | 90 | 2.0 | 69 |
| 21 | 0x3C3498 | 627 | 自 | 725 | 避 | 726 | 神 | HL | 501 | 喚 | 130 | 2.0 | 70 |
| 22 | 0x3C34D0 | 628 | 世 | 727 | 聖 | 728 | 入 | NO | 502 | 能 | 100 | 2.0 | 54 |
| 23 | 0x3C3508 | 612 | 払 | 729 | 振 | 730 | 冒 | HL | 503 | 力 | 70 | 1.0 | 71 |
| 24 | 0x3C3540 | 629 | 界 | 731 | 将 | 732 | 後 | HL | 504 | 職 | 200 | 3.0 | 112 |
| 25 | 0x3C3578 | 630 | 避 | 733 | 教 | 734 | 授 | HL | 505 | 地 | 120 | 2.5 | 113 |
| 26 | 0x3C35B0 | 631 | 降 | 735 | 美 | 736 | 現 | NO | 506 | 削 | 120 | 2.5 | 72 |
| 27 | 0x3C35E8 | 632 | 突 | 737 | 決 | 738 | 個 | HL | 507 | 除 | 130 | 2.5 | 73 |
| 28 | 0x3C3620 | 633 | 固 | 739 | 基 | 740 | 甲 | NO | 508 | 部 | 120 | 2.0 | 74 |
| 29 | 0x3C3658 | 634 | 来 | 741 | 本 | 742 | 手 | NO | 509 | 隊 | 130 | 2.2 | 75 |
| 30 | 0x3C3690 | 635 | 頼 | 743 | 高 | 744 | 焼 | HL | 510 | 前 | 300 | 3.0 | 76 |
| 31 | 0x3C36C8 | 636 | 違 | 745 | 優 | 746 | 探 | NO | 511 | 果 | 120 | 1.5 | 77 |
| 32 | 0x3C3700 | 637 | 応 | 747 | 扱 | 748 | 答 | NO | 512 | 別 | 90 | 1.4 | 78 |
| 33 | 0x3C3738 | 638 | 系 | 749 | 言 | 750 | く | HL | 513 | 種 | 120 | 2.5 | 79 |
| 34 | 0x3C3770 | 639 | 恵 | 751 | 器 | 752 | 向 | HL | 514 | 族 | 70 | 1.3 | 80 |
| 35 | 0x3C37A8 | 640 | 血 | 753 | 待 | 754 | 楽 | HL | 515 | 条 | 100 | 1.5 | 81 |
| 36 | 0x3C37E0 | 641 | 込 | 755 | 都 | 756 | 格 | HL | 516 | 性 | 100 | 1.5 | 82 |
| 37 | 0x3C3818 | 642 | 判 | 757 | 素 | 758 | 内 | NO | 517 | 業 | 90 | 2.0 | 83 |
| 38 | 0x3C3850 | 643 | 貴 | 759 | 形 | 760 | 近 | HL | 518 | 男 | 140 | 2.5 | 84 |
| 39 | 0x3C3888 | 644 | 冒 | 761 | 正 | 762 | 義 | HL | 519 | 壁 | 90 | 2.0 | 85 |
| 40 | 0x3C38C0 | 645 | 婦 | 763 | 休 | 764 | 息 | NO | 520 | 枚 | 80 | 1.0 | 86 |
| 41 | 0x3C38F8 | 646 | 買 | 765 | 地 | 766 | 年 | HL | 521 | 飽 | 150 | 3.0 | 89 |
| 42 | 0x3C3930 | 647 | 使 | 767 | 内 | 768 | 容 | HL | 522 | 怪 | 80 | 1.5 | 87 |
| 43 | 0x3C3968 | 648 | 高 | 769 | 威 | 770 | 難 | HL | 523 | 伝 | 80 | 1.6 | 88 |
| 44 | 0x3C39A0 | 649 | 絆 | 771 | 下 | 772 | 呪 | HL | 524 | 家 | 70 | 1.7 | 89 |
| 45 | 0x3C39D8 | 650 | 余 | 773 | 結 | 774 | 活 | HL | 525 | 孤 | 80 | 1.5 | 90 |
| 46 | 0x3C3A10 | 651 | 計 | 775 | 回 | 776 | 器 | HL | 526 | 独 | 90 | 1.7 | 91 |
| 47 | 0x3C3A48 | 652 | 変 | 777 | 稀 | 778 | 特 | HL | 527 | 的 | 80 | 1.7 | 92 |
| 48 | 0x3C3A80 | 653 | 全 | 779 | 経 | 780 | 響 | HL | 528 | 社 | 80 | 1.7 | 93 |
| 49 | 0x3C3AB8 | 654 | 死 | 781 | 闘 | 782 | 系 | HL | 529 | 交 | 70 | 1.7 | 94 |
| 50 | 0x3C3AF0 | 655 | 夫 | 783 | 失 | 784 | 消 | NO | 530 | 所 | 130 | 3.0 | 95 |
| 51 | 0x3C3B28 | 656 | 誰 | 785 | 性 | 786 | 依 | NO | 531 | 集 | 140 | 2.5 | 96 |
| 52 | 0x3C3B60 | 657 | 振 | 787 | 就 | 788 | 覚 | HL | 475 | 王 | 130 | 2.3 | 116 |
| 53 | 0x3C3B98 | FFFF | -- | 789 | 退 | 790 | 有 | NO | 475 | 王 | 1 | 1.0 | 47 |
| 54 | 0x3C3BD0 | FFFF | -- | 791 | 打 | 792 | 俺 | NO | 475 | 王 | 60 | 1.8 | 47 |
| 55 | 0x3C3C08 | FFFF | -- | 793 | 華 | 794 | 発 | NO | 532 | 慎 | 60 | 1.8 | 47 |
| 56 | 0x3C3C40 | 605 | 持 | 795 | 常 | 796 | 罠 | NO | 533 | 義 | 60 | 1.8 | 47 |
| 57 | 0x3C3C78 | 605 | 持 | 797 | 離 | 798 | 脱 | NO | 534 | 感 | 60 | 1.8 | 47 |
| 58 | 0x3C3CB0 | 605 | 持 | FFFF | -- | FFFF | -- | NO | 475 | 王 | 60 | 1.8 | 88 |
| 59 | 0x3C3CE8 | FFFF | -- | 799 | 先 | 800 | 替 | HL | 535 | 知 | 70 | 1.7 | 88 |
| 60 | 0x3C3D20 | 658 | 緒 | FFFF | -- | FFFF | -- | NO | 475 | 王 | 70 | 1.7 | 88 |
| 61 | 0x3C3D58 | FFFF | -- | 801 | 記 | 802 | 述 | HL | 536 | 代 | 70 | 1.7 | 88 |
| 62 | 0x3C3D90 | 659 | 城 | 803 | 柄 | 804 | 般 | HL | 537 | 間 | 70 | 1.7 | 88 |
| 63 | 0x3C3DC8 | 658 | 緒 | FFFF | -- | FFFF | -- | NO | 475 | 王 | 70 | 1.7 | 90 |
| 64 | 0x3C3E00 | FFFF | -- | 805 | 価 | 806 | 巨 | HL | 538 | 迷 | 90 | 1.7 | 90 |
| 65 | 0x3C3E38 | 651 | 計 | 807 | 傷 | 808 | 深 | HL | 539 | 元 | 90 | 1.7 | 90 |
| 66 | 0x3C3E70 | 651 | 計 | FFFF | -- | FFFF | -- | NO | 475 | 王 | 90 | 1.7 | 90 |
| 67 | 0x3C3EA8 | FFFF | -- | 809 | 辛 | 810 | 国 | HL | 540 | 口 | 90 | 1.7 | 90 |
| 68 | 0x3C3EE0 | 651 | 計 | 811 | 勇 | 812 | 雰 | HL | 541 | 限 | 90 | 1.7 | 90 |
| 69 | 0x3C3F18 | 651 | 計 | FFFF | -- | FFFF | -- | NO | 475 | 王 | 90 | 1.7 | 89 |
| 70 | 0x3C3F50 | FFFF | -- | 813 | 打 | 814 | 嘆 | HL | 542 | 雲 | 80 | 1.5 | 89 |
| 71 | 0x3C3F88 | 647 | 使 | 815 | 囲 | 816 | 境 | HL | 543 | 仲 | 80 | 1.5 | 89 |
| 72 | 0x3C3FC0 | 650 | 余 | FFFF | -- | FFFF | -- | NO | 475 | 王 | 80 | 1.5 | 89 |
| 73 | 0x3C3FF8 | FFFF | -- | 817 | 危 | 818 | 険 | HL | 544 | 間 | 80 | 1.5 | 89 |
| 74 | 0x3C4030 | 647 | 使 | 819 | 刻 | 820 | 若 | HL | 545 | 消 | 80 | 1.5 | 89 |
| 75 | 0x3C4068 | 650 | 余 | 821 | 憎 | 822 | 護 | HL | 546 | 方 | 80 | 1.5 | 92 |
| 76 | 0x3C40A0 | 653 | 全 | 823 | 堂 | 824 | 祈 | HL | 547 | 該 | 80 | 1.7 | 92 |
| 77 | 0x3C40D8 | 653 | 全 | 825 | 療 | 826 | 座 | HL | 548 | 限 | 80 | 1.7 | 92 |
| 78 | 0x3C4110 | 653 | 全 | 827 | 黙 | 828 | 禁 | NO | 549 | 追 | 80 | 1.7 | 49 |
| 79 | 0x3C4148 | 607 | 稼 | 829 | 奴 | 830 | 声 | NO | 550 | 加 | 120 | 3.0 | 49 |
| 80 | 0x3C4180 | 607 | 稼 | FFFF | -- | FFFF | -- | NO | 475 | 王 | 120 | 3.0 | 91 |
| 81 | 0x3C41B8 | FFFF | -- | FFFF | -- | FFFF | -- | NO | 475 | 王 | 80 | 1.7 | 91 |
| 82 | 0x3C41F0 | FFFF | -- | 831 | 所 | 832 | ? | HL | 551 | 乙 | 80 | 1.7 | 91 |
| 83 | 0x3C4228 | 652 | 変 | 833 | 戻 | 834 | 治 | HL | 552 | 分 | 80 | 1.7 | 91 |
| 84 | 0x3C4260 | 652 | 変 | 835 | 救 | 836 | 宝 | HL | 553 | 屋 | 80 | 1.7 | 91 |
| 85 | 0x3C4298 | 652 | 変 | 837 | 制 | 838 | 穏 | NO | 554 | 大 | 80 | 1.7 | 75 |
| 86 | 0x3C42D0 | 635 | 頼 | 839 | 放 | 840 | 唱 | NO | 555 | 胆 | 300 | 3.0 | 75 |
| 87 | 0x3C4308 | 635 | 頼 | 841 | ? | 842 | 宿 | HL | 556 | 与 | 300 | 3.0 | 73 |
| 88 | 0x3C4340 | 633 | 固 | 843 | 場 | 844 | 泊 | NO | 557 | 蓄 | 120 | 2.0 | 74 |
| 89 | 0x3C4378 | 634 | 来 | FFFF | -- | FFFF | -- | NO | 475 | 王 | 130 | 2.2 | 63 |
| 90 | 0x3C43B0 | FFFF | -- | FFFF | -- | FFFF | -- | NO | 475 | 王 | 80 | 1.0 | 54 |
| 91 | 0x3C43E8 | FFFF | -- | 845 | 部 | 846 | 空 | HL | 558 | 向 | 60 | 1.0 | 84 |
| 92 | 0x3C4420 | 644 | 冒 | FFFF | -- | FFFF | -- | NO | 475 | 王 | 120 | 2.0 | 116 |
| 93 | 0x3C4458 | FFFF | -- | FFFF | -- | FFFF | -- | NO | 475 | 王 | 1 | 1.0 | 116 |
| 94 | 0x3C4490 | FFFF | -- | 847 | ? | 848 | 棒 | NO | 559 | 穏 | 100 | 1.0 | 56 |
| 95 | 0x3C44C8 | 614 | 聞 | 849 | 恐 | 850 | 怖 | 00 | 560 | 品 | 60 | 1.0 | 46 |
| 96 | 0x3C4500 | 604 | 味 | 851 | 十 | 852 | 造 | HL | 561 | 色 | 40 | 1.5 | 46 |
| 97 | 0x3C4538 | 604 | 味 | 853 | 勲 | 854 | 組 | HL | 562 | 自 | 40 | 1.5 | 51 |
| 98 | 0x3C4570 | 609 | 欠 | 855 | 更 | 856 | 去 | HL | 563 | 己 | 90 | 1.0 | 53 |
| 99 | 0x3C45A8 | 611 | 話 | 857 | 突 | 858 | 然 | HL | 564 | 勤 | 90 | 1.0 | 55 |
| 100 | 0x3C45E0 | 613 | 許 | FFFF | -- | FFFF | -- | NO | 475 | 王 | 50 | 1.5 | 93 |
| 101 | 0x3C4618 | 654 | 死 | 859 | 逃 | 860 | 忘 | HL | 565 | 力 | 70 | 1.7 | 93 |
| 102 | 0x3C4650 | 654 | 死 | FFFF | -- | FFFF | -- | NO | 475 | 王 | 70 | 1.7 | 93 |
| 103 | 0x3C4688 | 654 | 死 | 861 | 咲 | 862 | 草 | HL | 566 | 重 | 70 | 1.7 | 93 |
| 104 | 0x3C46C0 | 654 | 死 | 863 | 花 | 864 | 園 | HL | 567 | 漢 | 70 | 1.7 | 93 |
| 105 | 0x3C46F8 | 654 | 死 | 865 | 拶 | 866 | 挨 | HL | 568 | 勉 | 70 | 1.7 | 93 |

---

## 8. Summary of Key Findings

### Struct is FIXED at 3 glyphs per label
- 1 icon + 2 label glyphs, duplicated across 3 states
- No room for variable-length ASCII text within the struct
- The `width` float can be adjusted but the glyph count cannot change

### Translation requires font atlas editing
- Replace font atlas tiles for glyph IDs used by menu labels (IDs 480-866) with pre-rendered English text bitmaps
- Each 16x16 tile becomes one piece of an English word (e.g., "Tav" + "ern")
- The icon tile can show a descriptive symbol or the first part of the word
- Must update `width` and `spacing` floats to accommodate English text width

### Glyph map is UNRELIABLE for IDs 480+
- The msg_glyph_map.json was built for MSG text rendering
- IDs 480+ in the font atlas may render as different characters than what the map indicates
- Visual verification of each font atlas tile is required before mapping IDs to meanings

### Town navigation is likely idx=47
- Records 53-57 at offsets 0x3C3B98-0x3C3C78
- 5 entries matching the expected town destinations
- Glyph IDs 789-798, 605, 532-534 need visual verification

### Next Steps
1. Visually examine font atlas tiles for ALL glyph IDs used in Table 2C (IDs 480-866)
2. Build a correct glyph-to-character mapping for the EXE context
3. Identify which records correspond to which in-game menus via PCSX2 memory tracing
4. Design English font atlas replacement tiles (fitting 2-3 English characters per 16x16 tile)
5. Patch the EXE: update glyph IDs + width/spacing floats
