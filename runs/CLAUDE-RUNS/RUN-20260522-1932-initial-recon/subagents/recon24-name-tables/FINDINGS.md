# Recon 24: Item, Spell, Monster, and Class Name Tables in the EXEs

**Date:** 2026-05-22
**BUSIN 0 EXE:** `C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78` (4,185,776 bytes)
**BUSIN 1 EXE:** `C:/Programmieren/wizardrytranslation/extracted_busin1/SLUS_202.59` (5,038,496 bytes)

---

## Critical Finding: BUSIN 0 Does NOT Store Game Names in the EXE

**The BUSIN 0 (Japanese) EXE contains NO monster names, item names, spell names, or class names as searchable SJIS text.** Exhaustive searches for:
- Katakana class names (ファイター, シーフ, メイジ, プリースト, etc.) -- **NOT FOUND** (except ロード in a UI sentence)
- Katakana race names (ヒューマン, エルフ, ドワーフ, ノーム) -- **NOT FOUND**
- Kanji RPG terms (戦士, 盗賊, 僧侶, 忍者, 人間) -- **NOT FOUND** (except 侍 as false positives in code bytes)
- Katakana monster names (スライム, ドラゴン, ゴブリン, スケルトン, etc.) -- **NOT FOUND**
- Katakana weapon/armor names (ダガー, メイス, フレイル, スタッフ, etc.) -- **NOT FOUND**
- ASCII equivalents (Fighter, BUBBLY, SLIME, DRAGON, etc.) -- **NOT FOUND**

All game-visible text in BUSIN 0 uses the **16-bit glyph-index encoding** system (confirmed by recon13 and recon15), stored in PACKDATA resources -- NOT as raw SJIS in the EXE.

The only SJIS text in the BUSIN 0 EXE (0x3EC910-0x3FC7F0) consists of:
- Debug logging strings ("デバックチェック！！！！！", "BattleSequenceDataKill : monster_no=%d", etc.)
- Battle system debug messages ("ＡＡ・フロントガードブレイク", "アレイド：援護射撃発見チェック", etc.)
- Save slot names ("ＢＵＳＩＮ０データ１/２/３")
- Event/scene identifiers (KYO_01, EV01_01, SMS_29, etc.)

---

## BUSIN 1 (English) Name Tables -- Complete Inventory

The BUSIN 1 EXE contains significantly more embedded text than BUSIN 0, including game data tables. The EXE has a LOAD segment starting at file offset 0x1000 mapped to VA 0x100000.

### 1. Monster Names Table
| Property | Value |
|----------|-------|
| **File offset** | `0x4B0960` |
| **Entry size** | 16 bytes (null-padded ASCII) |
| **Entry count** | ~108 (62 base + 46 leveled variants) |
| **First entry** | BUBBLY SLIME |
| **Last entry** | LV20 NINJA(B) |

The table includes both base monsters and class-based enemy variants (e.g., "LV3 PRIEST", "MASTER THIEF(B)", "HIGH NINJA(B)").

Sample entries:
```
[  0] BUBBLY SLIME
[  1] GAS DRAGON
[  2] BOGY CAT
[  3] DRAGON FLY
[  4] ROTTING CORPSE
[  5] BORING BEETLE
[  6] UNDEAD KOBOLD
[  7] GIANT TOAD
[  8] HUGE SPIDER A
[  9] HUGE SPIDER B
[ 10] GIANT SPIDER
[ 11] GAZE HOUND
[ 12] EARTH GIANT
[ 13] WILL `O WISP
[ 14] GARGOYLE
...
[105] HIGH NINJA(B)
[106] LV20 NINJA(B)
```

### 2. Monster Type / Tribe Names
| Property | Value |
|----------|-------|
| **File offset** | `0x4C32C8` |
| **Entry size** | 8 bytes |
| **Entry count** | 20 |

```
[ 0] ROGE        [ 1] ZOMBIE      [ 2] OGRE        [ 3] PIXIE
[ 4] ORC         [ 5] KOBOLD      [ 6] SPIRIT      [ 7] WYVERN
[ 8] SHADE       [ 9] CHIMERA     [10] VAMPIRE     [11] HARPY
[12] INCUBUS     [13] WARGOD      [14] DEMON       [15] GHOST
[16] DEATH 2     [17] ANGEL       [18] FAERIE      [19] DEATH
```

### 3. Race Names
| Property | Value |
|----------|-------|
| **File offset** | `0x4C36F0` (indices 8-12 of a larger block at 0x4C36B0) |
| **Entry size** | 8 bytes |
| **Entry count** | 5 |

```
HOBBIT, GNOME, DWARF, ELF, HUMAN
```

### 4. Class Names
| Property | Value |
|----------|-------|
| **File offset** | `0x4C3718` (indices 13-19 of same block) |
| **Entry size** | 8 bytes |
| **Entry count** | 7 |

```
BISHOP, PALADIN, PRIEST, NINJA, SAMRAI, THIEF, FIGHTER
```
Note: "SAMRAI" is a typo for "SAMURAI" (fixed elsewhere at 0x4C3828 as "SAMURAI").

### 5. Alignment Names
| Property | Value |
|----------|-------|
| **File offset** | `0x4C3750` (indices 20-21 of same block) |
| **Entry size** | 8 bytes |
| **Entry count** | 2 + 1 neutral |

```
EVIL, GOOD, --
```

### 6. Weapon Type Categories
| Property | Value |
|----------|-------|
| **File offset** | `0x4C2CF0` |
| **Entry size** | 8 bytes |
| **Entry count** | 9 |

```
DAGGER, MACE, FLAIL, STAFF, HANDAXE, KATANA, CHOP, STARS, STONE
```

### 7. Weapon Class Names (Weapon List UI)
| Property | Value |
|----------|-------|
| **File offset** | `0x4AD320` |
| **Entry size** | 16 bytes |
| **Entry count** | 8 |

```
ONE HAND, BOTH HAND, SHORTSWORD, LONGSWORD, GREATSWORD, GREATAXE, CROSSBOW, THROWINGDAGGER
```

### 8. Armor Type Categories
| Property | Value |
|----------|-------|
| **File offset** | `0x4C2D80` (indices 18-21 of block at 0x4C2CF0) |
| **Entry size** | 8 bytes |
| **Entry count** | 4 |

```
ARMOR, HELMET, GLOVE, SHIELD
```

### 9. Accessory Type Categories
| Property | Value |
|----------|-------|
| **File offset** | `0x4C2DC8` |
| **Entry size** | 8 bytes |
| **Entry count** | 6 |

```
CHARM, RING, BOOTS, MANTLE, RIBBON, SPECIAL
```

### 10. Battle Command Names
| Property | Value |
|----------|-------|
| **File offset** | `0x4C35A0` (indices 5-14 of block) |
| **Entry size** | 8 bytes |
| **Entry count** | 10 |

```
FIGHT, PARRY, MAGIC, DISPELL, BLADE, ITEM, CHANGE, ESCAPE, SHIFT, ALLIED
```

### 11. Monster Special Attack Types
| Property | Value |
|----------|-------|
| **File offset** | `0x4C3634` (indices 4-14 of block at 0x4C3630) |
| **Entry size** | 8 bytes |
| **Entry count** | 11 |

```
BREATH, ECHO, WAVE, CALL, BACK, WHISTLE, THREAD, GAZE, BOSS1, BOSS2, FRONT
```

### 12. Spell Effect Categories
| Property | Value |
|----------|-------|
| **File offset** | `0x4C3E98` |
| **Entry size** | 8 bytes |
| **Entry count** | 17 |

```
AC DOWN, AC UP, RETURN, FIRE, THUNDER, DAMAGE, REB ASH, REBIRTH,
FUUIN, LOST, ASH, SLEEP, FEAR ON, DARK, SPIDER, GAZE, MP UP
```

### 13. Spell Effect Labels (Debug System)
| Property | Value |
|----------|-------|
| **File offset** | `0x4B9D18` |
| **Entry size** | 16 bytes |
| **Entry count** | 28 |

```
DEATH OFF Q, DEATH ON Q, LOST SPELL, CRITICAL, ENE DRAIN, DEATH OFF,
DEATH ON, SPEED UP, DAMAGE UP, REB LOST, REB TRUE, B SILENCE,
FUUIN END, IJOU OFF, FEAR OFF, STONE OFF, STONE ON, POISON OFF,
POISON ON, DARK OFF, SPIDER OFF, GAZE OFF, PARA OFF, PARALYZE,
HP UP (A), HP UP (L), HP UP (M), HP UP (S)
```

### 14. "Kizuna" (Bond/Allied Skill) Types
| Property | Value |
|----------|-------|
| **File offset** | `0x4C2E80` (indices 0-7 of block) |
| **Entry size** | 8 bytes |
| **Entry count** | 8 |

```
ZOU, GI, MEI, YOSI, TOMO, SIN, TIKA, KIZUNA
```
These are romanized Japanese bond-type names (ZOU=像/image, GI=義/justice, MEI=銘/inscription, YOSI=義/righteousness, TOMO=友/friend, SIN=信/faith, TIKA=力/power, KIZUNA=絆/bond).

### 15. Difficulty/Resistance Levels
At 0x4C2DA0 (indices 22-24 of weapon block):
```
WEAK, NORMAL, STRONG
```

### 16. Personality Types (Romanized Japanese)
At 0x4C3848 (indices 51-53 of race/class block):
```
OKUBYOU (臆病/cowardly), YUMOU (勇猛/brave), DOUMOU (獰猛/ferocious)
```

---

## Tables NOT Found in Either EXE

The following are **confirmed NOT present** in the EXE files and are stored in PACKDATA resources:
- **Individual item names** (specific weapon/armor/accessory names like Estoc, Rapier, etc.)
- **Individual spell names** (e.g., Heal, Fire, etc. -- NOT classic Wizardry names like HALITO/KATINO)
- **NPC names**
- **Location/dungeon names**

These are stored using the 16-bit glyph-index encoding in MSG/text resources within PACKDATA.DIG (BUSIN 0) or PACKDATA.CIG (BUSIN 1).

---

## ELF Load Mapping

| EXE | File offset formula | Data section range (file) |
|-----|---------------------|--------------------------|
| BUSIN 0 | `VA = file_offset + 0x0FFF80` | 0x300000 - 0x3FDC80 |
| BUSIN 1 | `VA = file_offset + 0x0FF000` | 0x460000 - 0x4C3441 |

BUSIN 1's data section is ~0x16 0000 bytes larger than BUSIN 0's, which accounts for the additional English text tables and debug editor UI labels that were added during localization.

---

## Implications for Translation

1. **Name tables must be found in PACKDATA**, not the EXE. The EXE only has category labels and the BUSIN 1 monster name table.
2. **BUSIN 0's EXE does not need name table patching** since names are in external resources.
3. **BUSIN 1's monster name table at 0x4B0960** is a useful reference for mapping monster IDs to English names.
4. **The glyph-index encoding** used by PACKDATA MSG resources is the key format to crack for name extraction. Each character is a 16-bit big-endian index into the font texture atlas.
5. The **weapon.dat / protec.dat / tool.dat / access.dat / magic.dat** files in PACKDATA contain numerical stats only (confirmed by recon15), with names stored separately in the MSG system.

---

## Scanner Script

Script location: `C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260522-1932-initial-recon/subagents/recon24-name-tables/scan_names.py`
(Note: Script was not written due to .py file write restrictions. All analysis was performed via inline Python commands.)
