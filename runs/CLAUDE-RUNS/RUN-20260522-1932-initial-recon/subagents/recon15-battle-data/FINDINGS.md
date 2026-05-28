# Battle/Game Data File Analysis -- BUSIN 1 (English PS2)

**Directory:** `extracted_busin1/SOURCE/GAME/BATTLE/DATA/`  
**Date:** 2026-05-22

---

## KEY FINDING: Names Are NOT Stored in These Files

The battle DATA files contain **only numerical game statistics and icon/texture data**. No English (or any) item, spell, or monster names exist within these files. Names are stored separately:

- **Monster names**: Found in the PS2 executable (`SLUS_202.59`) as a fixed-size string table at offset `0x4B0960`, using 16-byte entries with plain ASCII encoding. 108 entries (0-107), including class-based enemy variants.
- **Weapon/armor/item category names**: Found in `SLUS_202.59` at `0x4C2CF0` (8-byte entries): DAGGER, MACE, FLAIL, STAFF, HANDAXE, KATANA, CHOP, STARS, STONE. Armor types at `0x4C2D80`: ARMOR, HELMET, GLOVE, SHIELD. Accessory types at `0x4C2DC8`: CHARM, RING, BOOTS, MANTLE, RIBBON, SPECIAL.
- **Weapon class names**: At `0x4AD320` (16-byte entries): ONE HAND, BOTH HAND, SHORTSWORD, LONGSWORD, GREATSWORD, GREATAXE, CROSSBOW, THROWINGDAGGER.
- **Individual item names** (e.g., "Estoc", "Rapier", specific weapon names): NOT found in the EXE or extracted files. These are likely stored within **PACKDATA.CIG** in the MSG/text system, using the game's 16-bit glyph-index encoding.

---

## MSG File Text Encoding

The `.MSG` files (e.g., `UEDA.MSG`, `KYOUGOKU.MSG`) use **16-bit big-endian character indices**:

| Value Range | Meaning |
|-------------|---------|
| `0x0020-0x007E` | Direct ASCII character codes |
| `0x0080-0x00FF` | Extended character set (accented chars?) |
| `0x0100-0x02FF` | Non-ASCII glyphs (katakana/hiragana/kanji indices) |
| `0xFFD2-0xFFD4` | Paragraph/section control codes |
| `0xFFF9` | Wait/pause control |
| `0xFFE0-0xFFE1` | Choice/selection markers |
| `0xFFFE` | Line break |
| `0xFFFF` | End of text block |

The EXE also contains inline UI text using a **separate custom encoding** where each byte = ASCII value minus 0x20 (so `0x21`='A', `0x22`='B', etc., `0x2E`=space). This encoding is used for menu strings like "Enter Name", "Change Class", equipment slot labels, etc.

---

## File Structure Summary

All `.DAT` files use a **two-table layout**: a stat/data table followed by an icon/texture table, both containing the same number of total slots.

```
File Layout:
[Stat Record 0][Stat Record 1]...[Stat Record N-1]  (stat_stride * N bytes)
[Icon Record 0][Icon Record 1]...[Icon Record N-1]  (icon_stride * N bytes)
Total = N * (stat_stride + icon_stride)
```

### WEAPON00.DAT -- 15,360 bytes

| Property | Value |
|----------|-------|
| Total entry size | 128 bytes (74 stat + 54 icon) |
| Total slots | 120 |
| Active items | 107 (IDs 0-106) |
| Stat record size | 74 bytes |
| Icon record size | 54 bytes |
| ID field | 16-bit BE at stat offset +2 |
| Stat table | `0x0000 - 0x22AF` (8880 bytes) |
| Icon table | `0x22B0 - 0x3BFF` (6480 bytes) |

Stat record layout (74 bytes, 16-bit big-endian fields):
- Offset 0: Previous item ID (link)
- Offset 2: **Current item ID** (0-106 sequential)
- Offset 4-9: Base stats (price at ~offset 4-7 as 32-bit?)
- Offset 10-13: Damage/stats
- Offset 14+: Equipment restrictions, attributes, elemental properties

Records 107-119 exist but are empty (ID=0, all-zero data).

### PROTEC00.DAT -- 11,520 bytes

| Property | Value |
|----------|-------|
| Total entry size | 144 bytes (72 stat + 72 icon) |
| Total slots | 80 |
| Active items | 80 (IDs 0-79) |
| Stat record size | 72 bytes |
| Icon record size | 72 bytes |
| ID field | 16-bit BE at stat offset +2 |
| Stat table | `0x0000 - 0x167F` (5760 bytes) |
| Icon table | `0x1680 - 0x2CFF` (5760 bytes) |

### ACCESS00.DAT -- 5,120 bytes

| Property | Value |
|----------|-------|
| Total entry size | 160 bytes (94 stat + 66 icon) |
| Total slots | 32 |
| Active items | 32 (IDs 0-31) |
| Stat record size | 94 bytes |
| Icon record size | 66 bytes |
| ID field | 16-bit BE at stat offset +0 |
| Stat table | `0x0000 - 0x0BBF` (3008 bytes) |
| Icon table | `0x0BC0 - 0x13FF` (2112 bytes) |

### MAGIC00.DAT -- 3,840 bytes

| Property | Value |
|----------|-------|
| Stat record size | 52 bytes |
| ID field | **32-bit BE at stat offset +0** (1-based!) |
| Active spells | ~53 (IDs 1-55, with gaps) |
| Total slots | ~60 (3840 / 64 = 60 if total_entry=64) |

Unlike item files, MAGIC00 uses **1-based 32-bit IDs** at offset 0. Empty slots have ID=0. Records where the 32-bit ID at offset 0 is 0 are unused. The gap pattern suggests spell categories:
- IDs 1-8 (slot 8 empty), 9-28 (slot 18 empty), 31-36 (slots 37-38 empty), 39-55

### STONE00.DAT -- 3,840 bytes

| Property | Value |
|----------|-------|
| Stat record size | 12 bytes |
| Total slots | 320 (3840 / 12) |
| Active items | ~30+ (IDs 0-30+) |
| ID field | 16-bit BE at stat offset +0 |

Compact 12-byte records with 6 fields of 16-bit BE each:
- Field 0: Item ID
- Field 1: Sub-ID or link
- Field 2: Unknown stat (~67-91 common values, possibly durability/power)
- Field 3: Duplicate of ID
- Field 4: Unknown stat
- Field 5: Unknown stat

### TOOL00.DAT -- 1,280 bytes

| Property | Value |
|----------|-------|
| Total entry size | 128 bytes (32 stat + 96 icon) |
| Total slots | 10 |
| Active items | 10 (IDs 0-9) |
| Stat record size | 32 bytes |
| Icon record size | 96 bytes |
| ID field | 16-bit BE at stat offset +0 |

### ALLIED00.DAT -- 448 bytes

| Property | Value |
|----------|-------|
| Total entry size | 64 bytes (32 stat + 32 icon) |
| Total slots | 7 |
| Active items | 7 (IDs 0-6) |
| Stat record size | 32 bytes |
| Icon record size | 32 bytes |
| ID field | 16-bit BE at stat offset +0 |

### MATE00.DAT -- 4,480 bytes

| Property | Value |
|----------|-------|
| Total entry size | 70 bytes (32 stat + 38 icon) |
| Total slots | 64 |
| Active companions | 62 (IDs 0-61) |
| Stat record size | 32 bytes |
| Icon record size | 38 bytes |
| ID field | 16-bit BE at stat offset +2 |

### STATUS.SSD -- 19,328 bytes

| Property | Value |
|----------|-------|
| Possible record size | 128 bytes (19328/128 = 151 records) |
| ID field | No sequential IDs found |

STATUS.SSD has no clear sequential ID pattern. It likely contains monster/character stat templates or status effect definitions. The 128-byte record hypothesis gives 151 entries, but the data structure appears more complex (possibly hierarchical or grouped by category). Contains both 0x00000000 and 0xFFFFFFFF sentinel values.

---

## Monster Name Table in SLUS_202.59

**Location:** `0x4B0960`  
**Entry size:** 16 bytes (fixed, null-padded ASCII)  
**Encoding:** Plain ASCII  
**Count:** 108 entries (indices 0-107)

Entries 0-61 contain full monster names (e.g., "BUBBLY SLIME", "FIRE DRAGON", "VAMPIRE LORD"). Entries 62-107 contain name fragments/suffixes used for a procedural name-building system for enemy variants (e.g., "AGON" suffix for dragon types, "INJA" for ninja types).

Sample entries:
```
[  0] "BUBBLY SLIME"      [ 10] "GIANT SPIDER"
[  1] "GAS DRAGON"        [ 22] "FIRE DRAGON"  
[  4] "ROTTING CORPSE"    [ 25] "MAELIFIC"
[  6] "UNDEAD KOBOLD"     [ 41] "NINETAIL"
[ 14] "GARGOYLE"          [ 51] "SWORDMAN"
```

---

## EXE File References

The executable (`SLUS_202.59`, 5,038,496 bytes) contains file paths for loading battle data from PACKDATA.CIG:

```
source/game/battle/data/weapon00.dat    (also weapon01-04)
source/game/battle/data/protec00.dat    (also protec01-04)
source/game/battle/data/tool00.dat      (also tool01-04)
source/game/battle/data/access00.dat    (also access01-04)
source/game/battle/data/stone00.dat
source/game/battle/data/magic00.dat     (also magic01-04)
source/game/battle/data/mate00.dat      (also mate01-04)
source/game/battle/data/allied00.dat    (also allied01-04)
source/game/battle/data/status.ssd
source/game/battle/data/output00-11.sav
```

The `00-04` suffix variants suggest difficulty tiers or progressive data updates.

---

## Implications for BUSIN 0 Translation

1. **Battle data files are name-free**: The `.DAT` files contain only numerical stats and icon graphics. Translating BUSIN 0 does NOT require modifying these files for name changes.

2. **Names are stored externally**: Item/spell names are resolved by ID lookup into name tables stored either in the executable or in MSG-format text files within PACKDATA.

3. **The two-table layout** (stat table + icon table, same record count) should be consistent between BUSIN 0 and BUSIN 1, making it possible to cross-reference item IDs.

4. **Record sizes and ID fields** may differ between BUSIN 0 and BUSIN 1, but the general architecture (16-bit BE IDs, fixed-size records, two-table layout) is likely shared.

5. **Translation effort focuses on**: The executable's name tables (for monster names) and the MSG/text system within PACKDATA (for item/spell names and descriptions).
