# EXE Shop & Item System Text Analysis

**Date**: 2026-05-28
**EXE**: `extracted/SLPM_653.78` (4,185,776 bytes)
**VA offset**: file_offset + 0x000FFF80

---

## Summary

Shop interface labels are **NOT hardcoded as SJIS text** in the EXE. There are zero SJIS shop/trade/buy/sell strings outside debug output. The shop UI works through three mechanisms:

1. **MSG dialogue files** (R44/R45) -- already translated
2. **Menu label structs** (glyph-ID system at 0x3C3000-0x3C5300) -- 160 records, each 56 bytes
3. **Pre-rendered icon textures** (glyph IDs 2036+ from a separate sprite atlas)

---

## Equipment Type Icon Table (Table 2J)

### Icon Animation Table
**Offset**: 0x3F9CF0 - 0x3FA030 (file), VA 0x4F9C70 - 0x4F9FB0
**Format**: 4-byte entries `(u16 variant, u16 glyph_id)`, 4 entries per icon
**Structure per icon**: `{0,gid}, {0,gid}, {1,gid}, {2,gid}` (normal, normal-dup, hover, pressed)
**Range**: Glyph IDs 2035-2086 = **52 icons** (not just 12)

The table stores animation/state variants for each equipment icon. Each icon ID gets 4 slots (16 bytes).

### Item Glyph Base Table
**Offset**: 0x3B38EA - 0x3B39EE (file), VA 0x4B386A - 0x4B396E
**Format**: Array of `u16` base glyph IDs, each representing one item category's icon sprite set
**Count**: 130 entries
**Glyph ID range**: 1604 - 2348
**Step**: ~7 per entry (each category icon uses 7 sub-sprites for animation frames)

This is NOT a 12-type equipment list. It is a comprehensive icon-sprite index covering all item/equipment types, sub-types, and possibly individual special items. The 7-glyph-per-category design means each icon has 7 animation frames in the sprite atlas.

### Item Icon Pair Table
**Offset**: 0x3B376C - 0x3B3CB4 (file)
**Format**: Pairs of `(u16 base1, u16 base2)` -- likely two-part item icons
**Count**: 338 entries
**Glyph ID range**: 112 - 2500+

This table appears to pair two icon halves per item (left-half/right-half of composite icons). The 338 entries likely correspond to the game's full item catalog.

### Code References
The item icon system is referenced at:
- VA 0x001150F8 (file 0x015178): `lui r4, 0x004B` + `addiu r4, r4, 0x1F50` -- loads item system struct base
- VA 0x00115110 (file 0x015190): `addiu r11, r11, 0x3990` -- loads icon data pointer

The rendering function at VA 0x0010C128 (jal target) handles icon display with parameters for variant count and display mode.

---

## Equipment Type Labels: What Glyphs 2036-2047 Represent

These are NOT in the main font atlas (R1272, 882 cells). They reference a **separate equipment icon texture atlas** that contains pre-rendered Japanese type labels as sprites.

Based on Busin 0's equipment system and the 7-glyph-per-category pattern:

| Table Index | Base Glyph | Probable Equipment Type |
|-------------|-----------|------------------------|
| 73 | 2036 | Weapon category (likely 片手剣, One-Hand Sword) |
| 74 | 2043 | Weapon category (likely 両手剣, Two-Hand Sword) |
| 75 | 2050 | Weapon category (likely 短剣, Dagger) |
| 76 | 2057 | Weapon category (likely 棍棒, Club/Mace) |
| 77 | 2064 | Weapon/tool category (likely 杖, Staff) |
| 78 | 2071 | Weapon category (likely 弓, Bow) |
| 79 | 2078 | Weapon category (likely 斧, Axe) |
| 80 | 2085 | Weapon category (likely 槍, Spear) |
| 81 | 2091 | Armor category (likely 兜, Helmet) |
| 82 | 2098 | Armor category (likely 体防具, Body Armor) |
| 83 | 2105 | Armor category (likely 盾, Shield) |
| 84 | 2112 | Armor/accessory category |

**NOTE**: The exact Japanese text on each sprite must be confirmed by locating and decoding the icon texture resource in PACKDATA. The mappings above are educated guesses based on Wizardry conventions.

---

## Shop-Related Menu Struct Records

From the 160-record menu label table at 0x3C3000:

| Record | Offset | Icon | Labels | Ref | Meaning |
|--------|--------|------|--------|-----|---------|
| 41 | 0x3C38F8 | 買(646) | 地/年 | 飽 | Buy-related |
| 84 | 0x3C4260 | 変(652) | 救/宝 | 屋 | Change/Save/Treasure + Shop(屋) |
| 95 | 0x3C44C8 | 聞(614) | 恐/怖 | 品(560) | Hear/Fear + Goods |
| 108 | 0x3C47A0 | 長(660) | 売(871)/礼 | 王 | Long/Sell/Thanks |
| 132 | 0x3C4CE0 | 持(668) | 商(904)/売(905) | 全(584) | **Commerce/Sell** (SHOP MAIN) |
| 151 | 0x3C5108 | 持(668) | 待/忠 | 品(603) | Hold/Wait/Goods (INVENTORY) |

Record 132 is the primary shop menu entry: icon=持(possess), labels=商(commerce)/売(sell), ref=全(all). This likely renders as the "Shop" option or "Buy/Sell All" toggle.

---

## Shop Interface Text NOT Found in EXE

The following were searched for as SJIS strings and glyph-ID sequences, with **NO results**:

- 購入 (kounyuu, purchase)
- 売却 (baikyaku, sale)
- 装備 (soubi, equipment) -- as glyph pair 332+602: not found outside chargen
- 数量/個数 (quantity)
- 単価/値段 (unit price)
- 合計/金額 (total/amount)
- ゴールド/お金 (gold/money)
- 全て/すべて (all)

**Conclusion**: Shop interface labels like "Buy", "Sell", "Price", "Quantity" are either:
1. Part of the R44/R45 dialogue scripts (already translated)
2. Pre-rendered on texture resources (bitmap labels, like the tab labels at glyph IDs 6400+)
3. Not present at all (the game may use icons-only for these actions)

---

## Item Category / Sorting / Filtering

No item category name table, sorting label table, or filter option table was found in the EXE data section. The game's item filtering likely works through:
- The category icon texture (glyph IDs 2036+) showing visual equipment type labels
- The R39 resource which contains equipment type names as MSG text (already translated: 545 entries including equipment types, party ranks, skills)

---

## Patching Strategy

### Equipment Type Icons (Priority: MEDIUM)
The icon sprites (glyph IDs 2036+) are **pre-rendered Japanese text on a texture atlas**. Patching requires:
1. **Find the PACKDATA resource** containing the icon sprite sheet (not yet identified -- needs texture scan)
2. **Edit the texture** to replace Japanese type labels with English equivalents (Sword, Axe, Staff, etc.)
3. The EXE glyph-ID references do NOT need changing -- only the texture content

### Shop Menu Labels (Priority: LOW)
Record 132 and related entries in the menu struct can have their glyph IDs replaced with English letter glyphs. However, each label is only 1-3 single-kanji glyphs -- English equivalents must be very short (3-4 chars max) or the bitmap texture approach (like the 6400+ tab labels) must be used.

### Items Not Requiring EXE Changes
- Shop dialogue (buy/sell prompts, NPC speech) -- handled by R44/R45 MSG files
- Equipment names and descriptions -- handled by R39 MSG resource
- Item category names in menus -- likely handled by R39 or by the icon texture
