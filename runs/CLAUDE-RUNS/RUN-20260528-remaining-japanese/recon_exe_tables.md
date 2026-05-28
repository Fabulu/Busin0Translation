# EXE Hardcoded Japanese Text Tables -- Complete Recon

**Date**: 2026-05-28
**EXE**: `extracted/SLPM_653.78` (4,185,776 bytes, original unpatched)
**Patched EXE**: `build/SLPM_653.78_patched` (identical in data section -- no EXE text has been patched yet)

---

## Summary

| Category | Table ID | Offset Range | Format | Entries | JP Glyphs | Priority |
|----------|----------|-------------|--------|---------|-----------|----------|
| Menu label structs | 2C | 0x3C3000-0x3C5300 | 56-byte struct (glyph+floats) | 106 records | 346 unique | MEDIUM |
| Kana mapping/input table | 2D | 0x3C5B32-0x3C6186 | Glyph-pair lookup | ~300 pairs | ~100 | LOW |
| Chargen kana display grid | 2B-kana | 0x3C83C0-0x3C93A0 | 4-byte records (flag+glyph) | 81 groups | 294 unique | HIGH |
| NPC names | 2F | 0x3C93B0-0x3C93C8 | LE u16 glyph string | 2 names | 9 | LOW |
| Bitmap tab labels | 2E | 0x3C9DA0-0x3C9DFC | Glyph ID refs (6400+ range) | 10 IDs | N/A (bitmap) | MEDIUM |
| Name entry kana grid | 2A | 0x3C9BF0-0x3C9DA0 | 12-byte struct (glyph+5 alts) | 38 entries | 27 kana | HIGH |
| Equipment type suffixes | 2J | 0x3F9D00-0x3F9EC0 | Glyph ID pairs (2036-2047 range) | 12 types | 12 (2000+ range) | LOW |
| Battle system debug strings | 2I | 0x3EE9D0-0x3F3500 | SJIS null-terminated | 161 strings | N/A (SJIS) | LOW (debug) |
| Save slot display names | 2G | 0x3FC720-0x3FC7A8 | SJIS fullwidth | 4 strings | N/A (SJIS) | MEDIUM |
| Suspend save name | 2G | 0x3F9370 | SJIS fullwidth | 1 string | N/A (SJIS) | MEDIUM |
| Misc player-visible | 2L | Various | SJIS | 7 strings | N/A (SJIS) | LOW |

**Total translatable items**: ~380 unique content items across 11 table categories

---

## Table 2C: Menu Label Pair Structs (106 records)

**Offset**: 0x3C3000-0x3C5300
**VA**: 0x004C2F80-0x004C5280
**Format**: 56-byte records, each containing:
```
+0x00: u16 padding(0), u16 icon_glyph     -- menu option icon
+0x04: float[5]                            -- position/scale parameters
+0x18: u16 0, u16 label_A1                 -- normal state glyph 1
+0x1C: u16 0, u16 label_A2                 -- normal state glyph 2
+0x20: u16 0, u16 label_A1 (repeat)
+0x24: u16 0, u16 label_A2 (repeat)
+0x28: u16 1, u16 label_A2 (selected)
+0x2C: u16 1, u16 label_A1 (selected)
+0x30: u16 0, u16 reference_glyph
+0x34: u16 ascii_index, u16 0
```

Each menu option uses **3 single-kanji glyphs** (icon + 2 labels) to represent a concept. This is not multi-character text -- each kanji independently symbolizes a menu action.

**Sample records decoded** (record index, icon, label pair, likely meaning):

| # | Offset | Icon | Labels | Ref | Likely Meaning |
|---|--------|------|--------|-----|---------------|
| 0 | 0x3C3000 | 稼 | [683]/美 | [480] | Earn/Beauty (quest?) |
| 1 | 0x3C3038 | 箱 | 追/巨 | [481] | Box/Chase/Giant (storage?) |
| 2 | 0x3C3070 | 欠 | 期/街 | [482] | Lack/Period/Town |
| 3 | 0x3C30A8 | 思 | [689]/番 | [483] | Think/Number (story?) |
| 4 | 0x3C30E0 | 話 | 並/宝 | [484] | Talk/Row/Treasure |
| 5 | 0x3C3118 | 払 | 今/強 | [485] | Pay/Now/Strong |
| 6 | 0x3C3150 | 許 | 壁/命 | 冒 | Permit/Wall/Life + Adventure |
| 7 | 0x3C3188 | 聞 | 器/終 | 険 | Hear/Vessel/End + Danger |
| 8 | 0x3C3268 | 考 | 現/員 | 登 | Think/Current/Member + Register |
| 9 | 0x3C32A0 | 考 | 選/択 | 録 | Think/Select/Choose + Record |
| 10 | 0x3C32D8 | 習 | 必/要 | 開 | Learn/Must/Need + Open |
| 11 | 0x3C3310 | 下 | 値/足 | 帰 | Down/Value/Enough + Return |
| 12 | 0x3C3348 | 解 | 名/前 | 専 | Explain/Name/Before + Specialist |
| 13 | 0x3C3380 | 通 | 高/低 | 所 | Pass/High/Low + Place |
| 22 | 0x3C3690 | 頼 | 高/焼 | 前 | Rely/High/Burn + Before |
| 29 | 0x3C3888 | 冒 | 正/義 | 壁 | Adventure/Justice |
| 40 | 0x3C3C40 | 持 | 常/罠 | 義 | Hold/Constant/Trap |
| 66 | 0x3C44C8 | 聞 | 恐/怖 | 品 | Hear/Fear |
| 84 | 0x3C4CE0 | 持 | 商/売 | 全 | Hold/Commerce/Sell |

**94 unmapped glyph IDs** in this area (IDs 480-930 range). These are kanji not yet in `msg_glyph_map.json`. They MUST be mapped before translation can proceed.

**Patching strategy**: Replace each icon/label/ref glyph ID with the corresponding English letter glyph IDs. Since each label is only 1-2 kanji, English equivalents will need to be short (1-3 chars). Alternatively, replace with MSG resource references if the game can load labels from there.

---

## Table 2B + 2A: Chargen / Name Entry System

### 2B: Chargen Kana Display Grid (0x3C83C0-0x3C93A0)

**VA**: 0x004C8340-0x004C9320
**Format**: 4-byte records `(u16 flag, u16 glyph_id)` separated by `FFFE FFFF` markers

This is the **character name input screen**. Contains 81 groups of kana characters:
- Groups 0-12: Hiragana (ぬ through ぉ, with separators for keyboard rows)
- Groups 13-28: Katakana (ア through プ)
- Groups 29-80: Game-specific single-kanji labels used elsewhere

**Groups 29+** contain single kanji that appear as attribute/status labels:
- Combat: 祠小手宮防攻騎使向行聖罰戦者鎧
- Magic: 悪動飾法魔
- Status: 大王士迷野神石依兵切
- Character: 奥信忍団回腕開名盗武
- Traits: 炎算人心頼落多臆法短上賊
- And many more...

**45 unmapped glyph IDs** in this area need mapping.

### 2A: Name Entry Kana Grid (0x3C9BF0-0x3C9DA0)

**VA**: 0x004C9B70-0x004C9D20
**Format**: 12-byte records `(u16 primary_glyph, u16[5] alternate_glyphs)`

This is the **actual on-screen keyboard grid** for character naming. 38 entries:
- Entries 0-29: Kana characters (あ-ブ) with gaps (null entries at positions 7, 15, 22, etc.)
- Entry 30: null spacer
- Entries 31-35: Punctuation/symbol characters
- Entry 36: glyph 6400 (bitmap: ひらがな tab)
- Entry 37: glyph 6403 (bitmap: tab label)

Each entry's 5 alternate glyph IDs correspond to the **same grid position across different input pages** (hiragana page, katakana page, etc.)

**Patching strategy**: Replace all kana glyph IDs with A-Z (glyph IDs for lowercase a-z are 33-58). The 5 alternate slots per entry allow up to 6 "pages" of characters. For English, one page of A-Z plus one of 0-9 plus symbols should suffice.

---

## Table 2E: Bitmap Tab Labels (0x3C9DA0-0x3C9DFC)

**VA**: 0x004C9D20-0x004C9D7C
**Format**: `(u16 bitmap_glyph_id, u16 padding)` pairs

Contains glyph IDs in the 6400-6409 range. These reference a **separate bitmap font system** (not the main MSG font atlas).

| Glyph ID | Likely Label |
|----------|-------------|
| 6400 | ひらがな (Hiragana) |
| 6401 | カタカナ (Katakana) |
| 6402 | Unknown tab 3 |
| 6403 | Unknown tab 4 |
| 6404 | Unknown tab 5 |
| 6405 | Unknown tab 6 |
| 6406 | Unknown tab 7 |
| 6407 | Unknown tab 8 |
| 6408 | Unknown tab 9 |
| 6409 | Unknown tab 10 |

**Patching strategy**: The bitmap font texture resource (unknown PACKDATA resource) must be found and edited to show English tab labels like "ABC", "abc", "Sym". Changing the glyph IDs alone will not work since the 6400+ range is a separate rendering system.

---

## Table 2F: NPC Names (0x3C93B0-0x3C93C8)

**VA**: 0x004C9330-0x004C9348
**Format**: LE u16 glyph strings, null-terminated

| Offset | Text | Translation |
|--------|------|-------------|
| 0x3C93B0 | エミーリア | Emilia |
| 0x3C93C0 | リュート | Lute |

Two NPC names hardcoded in the EXE. These should be patched to their English equivalents using the same glyph ID system.

Surrounding entries at 0x3C93A0 and 0x3C93E0 contain glyph IDs in the 6500-15600 range (likely bitmap references for NPC portrait labels or similar).

**Patching strategy**: Replace katakana glyph IDs with ASCII letter glyph IDs. "Emilia" = glyphs for E,m,i,l,i,a. "Lute" = glyphs for L,u,t,e. Ensure null terminator preserved.

---

## Table 2J: Equipment Type Suffixes (0x3F9D00-0x3F9EC0)

**VA**: 0x004F9C80-0x004F9E40
**Format**: Glyph ID pairs in 2036-2047 range, followed by small index values

12 equipment type labels using glyph IDs 2036-2047. These are NOT in the standard MSG font atlas (0-858 range) -- they likely reference a separate equipment icon/label texture.

| Glyph ID | Probable Equipment Type |
|----------|----------------------|
| 2036 | Weapon type 1 (sword?) |
| 2037 | Weapon type 2 (axe?) |
| 2038 | Weapon type 3 (staff?) |
| 2039 | Armor type 1 |
| 2040 | Armor type 2 |
| 2041 | Shield |
| 2042 | Helmet |
| 2043 | Accessory 1 |
| 2044 | Accessory 2 |
| 2045 | Item type 1 |
| 2046 | Item type 2 |
| 2047 | Item type 3 |

**Patching strategy**: Like bitmap tabs, these reference a separate texture. Must find and edit the source texture, or remap to ASCII glyph IDs if the renderer supports it.

---

## Table 2I: Battle System Debug Strings (0x3EE9D0-0x3F3500)

**VA**: 0x004EE950-0x004F3480
**Format**: SJIS null-terminated strings

161 strings, all debug/TTY output. **NOT player-visible**. Categories:

1. **Allied Action names** (109): `AA・フロントガードブレイク`, `Allied 001 : Wスラッシュ`, etc.
2. **Effect level reports** (42): `効果レベル = %d`, `アレイドブレイク`
3. **Status messages** (10): `ホールド！！`, `ディスペル成功！`, `ディスペル失敗！`

These are printed to the PS2 TTY debug console during battle and are invisible to players on retail hardware.

**Patching strategy**: No patching needed. These are developer debug output only.

---

## Table 2G: Save Slot Display Names (SJIS)

| Offset | SJIS Text | English | Notes |
|--------|-----------|---------|-------|
| 0x3FC720 | BUSIN0 | BUSIN 0 | MC browser title |
| 0x3FC750 | BUSIN0 Data 1 | BUSIN 0 Data 1 | Save slot 1 |
| 0x3FC770 | BUSIN0 Data 2 | BUSIN 0 Data 2 | Save slot 2 |
| 0x3FC790 | BUSIN0 Data 3 | BUSIN 0 Data 3 | Save slot 3 |
| 0x3F9370 | BUSIN0 Suspend Data | BUSIN 0 Suspend | Suspend save |
| 0x3F9678 | BUSIN0 | BUSIN 0 | Card title (2nd) |

**Patching strategy**: Replace fullwidth SJIS bytes with ASCII equivalents. The katakana portions need translation. Must stay within original buffer length.

---

## Table 2L: Miscellaneous Player-Visible SJIS Strings

| Offset | Japanese | English | Visibility |
|--------|----------|---------|-----------|
| 0x3F8240 | コンティニューロード！ | Continue Load! | Save/load screen |
| 0x3F8260 | 取り付ける人がいないよ。 | No one to equip to. | Equipment screen |
| 0x3F8150 | ガーディアン戦闘！！ | Guardian Battle!! | Possibly TTY |
| 0x3F8EF0 | そのようなOTはないです!!! | No such OT!!! | Error (dev) |
| 0x3FC7F0 | 松野ゲー起動！！ | Matsuno game boot!! | Boot screen (dev) |
| 0x3F3B90 | コールバッファオーバーです！！ | Call buffer overflow!! | Error (dev) |
| 0x3FC400 | Q が Over です!!!!!!!!!!! | Q is Over!!! | Error (dev) |

Only the first two are potentially player-visible. The rest are developer debug messages.

---

## Table 2D: Kana Mapping / Input Conversion Table (0x3C5B32-0x3C6186)

**VA**: 0x004C5AB2-0x004C6106
**Format**: Paired glyph ID lookup entries for kana-to-glyph conversion

This table maps input codes to display glyphs. It contains entries like:
```
input_code -> display_glyph (with separator codes 8, 9, 11)
```

This is used by the text input system to convert button presses to displayed kana characters. For English translation, this table needs to be reprogrammed to map button presses to A-Z.

---

## Unmapped Glyph IDs

**94 unmapped IDs in menu area** (480-930 range):
480, 481, 482, 483, 484, 485, 488, 489, 499, 522, 523, 537, 542, 559, 570, 571, 615, 616, 617, 623, 625, 626, 631, 633, 639, 643, 645, 654, 655, 663, 683, 689, 703, 736, 740, 748, 754, 793, 802-832, 835, 838, 841, 847, 861-866, 871, 872, 874, 875, 877, 878, 882, 885, 886, 896, 897, 903, 907, 912, 917, 924, 930

**45 unmapped IDs in chargen area** (294-474 range):
294, 305, 323, 331, 333, 345, 352, 357, 361, 364, 368, 373, 380, 384, 386, 390, 394, 400, 407, 409, 416, 417, 420, 424, 425, 426, 427, 430, 437, 439, 442, 444, 446, 447, 448, 453, 455, 457, 461, 464, 465, 469, 471, 473, 474

These must be added to `data/msg_glyph_map.json` before EXE text can be fully decoded and translated.

---

## Priority Ranking

### Tier 1: CRITICAL (blocks core gameplay)
1. **Table 2A**: Name entry kana grid -- players cannot type English names
2. **Table 2B-kana**: Chargen kana display -- name input unusable
3. **Table 2E**: Bitmap tab labels -- name entry tabs unreadable

### Tier 2: HIGH (visible Japanese in main flow)
4. **Table 2C**: Menu label pair structs -- all menu options show kanji
5. **Table 2B-labels**: Chargen attribute labels (groups 29-80) -- stat labels unreadable

### Tier 3: MEDIUM (secondary UI elements)
6. **Table 2G**: Save slot display names -- memory card screen
7. **Table 2L** (first 2): Continue Load / equip messages

### Tier 4: LOW (polish / debug)
8. **Table 2F**: NPC names -- may be redundant with MSG
9. **Table 2J**: Equipment type suffixes -- needs texture work
10. **Table 2D**: Kana mapping table -- needed only if name entry is reworked
11. **Table 2I**: Battle debug strings -- invisible to players
12. **Table 2L** (remaining 5): Developer debug messages

---

## Patching Recommendations

### For glyph-ID tables (2A, 2B, 2C, 2F):
1. Read the original glyph IDs at known offsets
2. Map Japanese glyph IDs to English ASCII glyph IDs (a=33, b=34, ..., A=33 with uppercase flag, etc.)
3. Write replacement glyph IDs as LE u16 at the same offsets
4. **Constraint**: Cannot exceed original entry count or change struct size

### For SJIS strings (2G, 2L):
1. Replace SJIS bytes with ASCII bytes
2. Pad with nulls if English is shorter than Japanese
3. **Constraint**: Must not exceed original byte length

### For bitmap references (2E, 2J):
1. Find the PACKDATA texture resources containing these bitmap glyphs
2. Edit the texture images to show English text
3. Re-encode and inject via PACKDATA rebuild
4. The glyph IDs in the EXE may also need updating if the texture layout changes

### For name entry rework (2A + 2D):
1. Replace kana grid entries (12-byte records) with A-Z, 0-9, space, backspace
2. Update the kana mapping table (2D) to map button inputs to ASCII characters
3. Update tab labels (2E) from hiragana/katakana to "ABC"/"123"/"Sym"
4. This is the most complex EXE patching task -- requires understanding the full input flow
