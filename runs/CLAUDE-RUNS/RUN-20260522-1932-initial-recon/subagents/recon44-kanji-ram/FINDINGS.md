# Recon 44: Kanji RAM Search -- Character-to-Glyph Mapping

**Date:** 2026-05-22
**Save State:** `randomdialogue.p2s`, also `NameEntryHiraganamode.p2s`
**EXE:** `extracted/SLPM_653.78` (BUSIN 0)

---

## Executive Summary

**No complete character-to-glyph mapping table exists in RAM.** The game uses the font atlas texture itself as the implicit mapping -- each glyph index maps to a position in the 256x512 atlas at `(index % 21, index / 21)` with 12x12 pixel cells. The character identity is encoded only in the pixel data of each cell.

However, a **159-entry SJIS-to-internal-ID kanji reverse-lookup table** was found at **VA 0x4C9D20** (EXE file offset 0x3C9DA0). This table maps SJIS kanji codes to packed `(row, col)` values used by the name entry system. This is the game's only kanji mapping table.

---

## Key Findings

### 1. BSS Character Struct Table at 0x5191F0 is EMPTY

The BSS area at 0x5191F0 (identified by recon20 as containing 80-byte character structs loaded at runtime) is **all zeros** in the dialogue save state. This suggests either:
- The character table is only populated during name entry mode (but it was also zero in the name entry state)
- The 80-byte structs were misidentified and the actual runtime data is elsewhere
- The BSS table is unused in BUSIN 0

No SJIS codes (hiragana 0x82A0-0x82F1, katakana 0x8340-0x8396, kanji 0x889F-0x9FFC) were found anywhere in the BSS region 0x4FDC80-0x579800.

### 2. No SJIS Character Tables in RAM at All

Systematic searches of the full 32MB EE RAM for:
- Blocks of 7+ consecutive SJIS hiragana codes
- Mixed hiragana+katakana blocks (20+ of each in 60 uint16s)
- Blocks of 15+ SJIS kanji codes in 20 uint16s
- Sorted SJIS tables (30 monotonically increasing values in valid SJIS range)

**All came up empty.** Verified with a fast byte-level scan of the full 32MB:
- Zero hiragana clusters (5+ consecutive SJIS 0x82xx values) in entire RAM
- 85 katakana clusters, ALL in EXE debug strings at 0x4F13xx-0x4F17xx (battle debug messages like "ジャンプアタック", "スタンスマッシュ" etc.) -- NOT character tables

The game does NOT store SJIS character codes as mapping data anywhere in RAM. The font system operates entirely on glyph indices.

### 3. Glyph Property Structs at 0x4C0DF8 -- No Character Codes

The 133 glyph property structs (28 bytes each) at VA 0x4C0DF8 contain:
- Float scale values (240.0 or 480.0)
- Metric byte at offset +9
- Atlas row (0-15) at offset +17
- Atlas column (0-3) at offset +18

Fields at offsets +24 and +26 are always zero -- **no character codes are stored in these structs**.

### 4. KANJI REVERSE-LOOKUP TABLE at VA 0x4C9D20 (EXE offset 0x3C9DA0)

**This is the most important finding.** A table in the EXE data section maps SJIS kanji positions to internal game IDs.

#### Table Format
- **Location:** VA 0x4C9D20, EXE file offset 0x3C9DA0
- **Entry size:** 4 bytes (uint32 LE)
- **Structure:** 44 entries per SJIS row, total ~560 entries
- **Entry format:** `0x0000RRCC` where `RR` = page/row (0x19-0x24), `CC` = char within page (0x00-0x0C)
- **Unused slots:** `0xFFFFFFFF`

#### Slot-to-SJIS Mapping
```
slot_index = (sjis_hi - 0x88) * 44 + (sjis_lo - 0x9F)
```
Where `sjis_hi` is the SJIS first byte (0x88-0x93+) and `sjis_lo` is the second byte (0x9F+).

#### Complete 159-Kanji Table

| Internal ID | SJIS Code | Character |
|-------------|-----------|-----------|
| 0x1900 | 0x889F | 亜 |
| 0x1901 | 0x88A0 | 唖 |
| 0x1902 | 0x88A1 | 娃 |
| 0x1903 | 0x88A2 | 阿 |
| 0x1904 | 0x88A3 | 哀 |
| 0x1905 | 0x88B2 | 梓 |
| 0x1906 | 0x88B3 | 圧 |
| 0x1907 | 0x88B4 | 斡 |
| 0x1908 | 0x88B5 | 扱 |
| 0x1909 | 0x88B6 | 宛 |
| 0x190A | 0x88BD | 或 |
| 0x190B | 0x88BE | 粟 |
| 0x190C | 0x88C0 | 安 |
| 0x1A00 | 0x899F | 押 |
| 0x1A01 | 0x89A0 | 旺 |
| 0x1A02 | 0x89A1 | 横 |
| 0x1A03 | 0x89A2 | 欧 |
| 0x1A04 | 0x89A3 | 殴 |
| 0x1A05 | 0x89B2 | 牡 |
| 0x1A06 | 0x89B3 | 乙 |
| 0x1A07 | 0x89B7 | 温 |
| 0x1A08 | 0x89B8 | 穏 |
| 0x1A09 | 0x89B9 | 音 |
| 0x1A0A | 0x89BD | 何 |
| 0x1A0B | 0x89BE | 伽 |
| 0x1A0C | 0x89C0 | 佳 |
| 0x1B00 | 0x8A9F | 粥 |
| 0x1B01 | 0x8AA0 | 刈 |
| 0x1B02 | 0x8AA1 | 苅 |
| 0x1B03 | 0x8AA2 | 瓦 |
| 0x1B04 | 0x8AA3 | 乾 |
| 0x1B05 | 0x8AA6 | 寒 |
| 0x1B06 | 0x8AA8 | 勘 |
| 0x1B07 | 0x8AA9 | 勧 |
| 0x1B08 | 0x8AAB | 喚 |
| 0x1B09 | 0x8AAD | 姦 |
| 0x1B0A | 0x8AAE | 完 |
| 0x1B0B | 0x8AAF | 官 |
| 0x1B0C | 0x8ABA | 桓 |
| 0x1C00 | 0x8B9F | 供 |
| 0x1C01 | 0x8BA2 | 兇 |
| 0x1C02 | 0x8BA3 | 競 |
| 0x1C03 | 0x8BA6 | 協 |
| 0x1C04 | 0x8BAA | 喬 |
| 0x1C05 | 0x8BAC | 峡 |
| 0x1C06 | 0x8BAD | 強 |
| 0x1C07 | 0x8BAE | 彊 |
| 0x1C08 | 0x8BAF | 怯 |
| 0x1C09 | 0x8BB1 | 恭 |
| 0x1C0A | 0x8BBA | 脅 |
| 0x1C0B | 0x8BBB | 興 |
| 0x1C0C | 0x8BBC | 蕎 |
| 0x1D00 | 0x8CA2 | 犬 |
| 0x1D01 | 0x8CA7 | 県 |
| 0x1D02 | 0x8CAA | 謙 |
| 0x1D03 | 0x8CAC | 軒 |
| 0x1D04 | 0x8CB0 | 顕 |
| 0x1D05 | 0x8CB1 | 験 |
| 0x1D06 | 0x8CB5 | 厳 |
| 0x1D07 | 0x8CB6 | 幻 |
| 0x1D08 | 0x8CB8 | 減 |
| 0x1D09 | 0x8CB9 | 源 |
| 0x1D0A | 0x8CBA | 玄 |
| 0x1D0B | 0x8CBB | 現 |
| 0x1D0C | 0x8CBC | 絃 |
| 0x1E00 | 0x8DA1 | 今 |
| 0x1E01 | 0x8DA2 | 困 |
| 0x1E02 | 0x8DAA | 根 |
| 0x1E03 | 0x8DAC | 混 |
| 0x1E04 | 0x8DB1 | 些 |
| 0x1E05 | 0x8DB3 | 叉 |
| 0x1E06 | 0x8DB7 | 差 |
| 0x1E07 | 0x8DB8 | 査 |
| 0x1E08 | 0x8DB9 | 沙 |
| 0x1E09 | 0x8DBA | 瑳 |
| 0x1E0A | 0x8DBB | 砂 |
| 0x1E0B | 0x8DBC | 詐 |
| 0x1E0C | 0x8DC0 | 座 |
| 0x1E0D | 0x8DC6 | 哉 |
| 0x1E0E | 0x8DC7 | 塞 |
| 0x1E0F | 0x8DC8 | 妻 |
| 0x1F00 | 0x8EA0 | 滋 |
| 0x1F01 | 0x8EA3 | 璽 |
| 0x1F02 | 0x8EAA | 蒔 |
| 0x1F03 | 0x8EAC | 汐 |
| 0x1F04 | 0x8EB1 | 竺 |
| 0x1F05 | 0x8EB3 | 宍 |
| 0x1F06 | 0x8EB4 | 雫 |
| 0x1F07 | 0x8EB5 | 七 |
| 0x1F08 | 0x8EB6 | 叱 |
| 0x1F09 | 0x8EBA | 室 |
| 0x1F0A | 0x8EBB | 悉 |
| 0x1F0B | 0x8EBC | 湿 |
| 0x1F0C | 0x8EC0 | 実 |
| 0x2000 | 0x8FA6 | 嘗 |
| 0x2001 | 0x8FA7 | 奨 |
| 0x2002 | 0x8FA8 | 妾 |
| 0x2003 | 0x8FA9 | 娼 |
| 0x2004 | 0x8FAB | 将 |
| 0x2005 | 0x8FB0 | 床 |
| 0x2006 | 0x8FB4 | 抄 |
| 0x2007 | 0x8FBA | 昭 |
| 0x2008 | 0x8FBD | 梢 |
| 0x2009 | 0x8FBE | 樟 |
| 0x200A | 0x8FBF | 樵 |
| 0x200B | 0x8FC4 | 焼 |
| 0x200C | 0x8FC5 | 焦 |
| 0x2100 | 0x909F | 澄 |
| 0x2101 | 0x90A0 | 摺 |
| 0x2102 | 0x90A1 | 寸 |
| 0x2103 | 0x90A2 | 世 |
| 0x2104 | 0x90A3 | 瀬 |
| 0x2105 | 0x90A4 | 畝 |
| 0x2106 | 0x90A5 | 是 |
| 0x2107 | 0x90A6 | 凄 |
| 0x2108 | 0x90A9 | 姓 |
| 0x2109 | 0x90B0 | 晴 |
| 0x210A | 0x90B5 | 牲 |
| 0x210B | 0x90B8 | 精 |
| 0x210C | 0x90BA | 声 |
| 0x2200 | 0x919F | 臓 |
| 0x2201 | 0x91A6 | 即 |
| 0x2202 | 0x91A8 | 捉 |
| 0x2203 | 0x91AB | 足 |
| 0x2204 | 0x91AF | 賊 |
| 0x2205 | 0x91B0 | 族 |
| 0x2206 | 0x91B2 | 卒 |
| 0x2207 | 0x91B3 | 袖 |
| 0x2208 | 0x91B5 | 揃 |
| 0x2209 | 0x91B8 | 尊 |
| 0x220A | 0x91BD | 多 |
| 0x220B | 0x91BE | 太 |
| 0x220C | 0x91C0 | 詑 |
| 0x2300 | 0x929F | 帖 |
| 0x2301 | 0x92A6 | 懲 |
| 0x2302 | 0x92A8 | 暢 |
| 0x2303 | 0x92AB | 牒 |
| 0x2304 | 0x92AF | 脹 |
| 0x2305 | 0x92B0 | 腸 |
| 0x2306 | 0x92B4 | 超 |
| 0x2307 | 0x92B5 | 跳 |
| 0x2308 | 0x92B6 | 銚 |
| 0x2309 | 0x92BF | 珍 |
| 0x230A | 0x92C1 | 鎮 |
| 0x230B | 0x92C2 | 陳 |
| 0x230C | 0x92C3 | 津 |
| 0x2400 | 0x939F | 董 |
| 0x2401 | 0x93A0 | 蕩 |
| 0x2402 | 0x93A1 | 藤 |
| 0x2403 | 0x93A9 | 陶 |
| 0x2404 | 0x93AF | 同 |
| 0x2405 | 0x93B0 | 堂 |
| 0x2406 | 0x93B2 | 憧 |
| 0x2407 | 0x93B3 | 撞 |
| 0x2408 | 0x93B5 | 瞳 |
| 0x2409 | 0x93B8 | 萄 |
| 0x240A | 0x93BD | 匿 |
| 0x240B | 0x93BE | 得 |
| 0x240C | 0x93C0 | 涜 |

**Note:** These are kanji available in the name entry system. The full game may use additional kanji in dialogue that are NOT in this table.

### 5. Kanji Name Entry Grid at 0x4C9670

The kanji pages for the name entry UI are stored at VA 0x4C9670-0x4C98F0. Each 32-byte entry represents one grid cell with the format:
```
(sub_type:u16, group_id:u16) x 3 repeats + padding
```

Group IDs range from 0x04A9 to 0x04BD (21 sequential kanji pages). These are referenced by 20 pointers at VA 0x4C9930.

### 6. Font Rendering Pointer Table at 0x4C08A0

20 pointers targeting 0x4EA1A0-0x4EA910, which contain **material/color data** (floats for RGBA, lighting parameters) -- NOT character mapping data. Each target is a 112-byte struct with RGB floats. Confirmed by debug string "Map Init!!!" nearby.

### 7. Name Entry Character Table Structure

The name entry glyph index tables at VA 0x4C99B0-0x4C9CE0 use **6-tuples of uint16 glyph indices** per character (one per font size, stride 57). These are organized as multiple small sub-tables (not a single contiguous array), referenced by code at 0x2F5410-0x2F6554.

Confirmed katakana coverage: 45 characters (base glyphs 98-142), identical in both katakana and hiragana save states (the table is static in the EXE).

---

## Architecture Summary

```
MSG File (dialogue)
  |
  v
uint16 BE glyph indices (0-857)
  |
  v
Font Atlas Texture (256x512, 21x42 grid of 12x12 cells)
  |
  v
Visual character at position (index % 21, index / 21)
```

The game has NO runtime glyph-to-SJIS mapping table. The only mappings that exist are:

| Table | VA | EXE offset | Purpose | Direction |
|-------|-----|-----------|---------|-----------|
| ASCII glyph table | 0x4C07F0 | 0x3C0870 | ASCII char -> glyph index | char -> glyph |
| Name entry katakana | 0x4C99B0 | 0x3CA9B0+ | Grid position -> 6 glyph indices | position -> glyph |
| Kanji reverse lookup | 0x4C9D20 | 0x3C9DA0 | SJIS kanji code -> internal ID | SJIS -> ID |
| Per-glyph properties | 0x4C0DF8 | 0x3C0E78 | Glyph index -> atlas coords, metrics | glyph -> rendering |

**None of these provide: glyph index -> character identity.** That mapping exists only in the font atlas pixels.

---

## Implications for Translation

1. **The complete glyph-to-character mapping must be derived from the font atlas image via OCR or visual identification.** There is no shortcut -- no table in RAM or the EXE provides this.

2. **The kanji reverse-lookup table at 0x4C9D20 provides 159 confirmed kanji characters** that the name entry system supports. These are a subset of all kanji used in the game.

3. **For replacing the font:** Replace the font atlas texture (PACKDATA resource 1272) with new character glyphs, then update the ASCII glyph table at 0x4C07F0 to map ASCII codes to the new glyph positions.

4. **For reading MSG files:** Each uint16 glyph index must be mapped to a character by looking up what character is drawn at that position in the font atlas. This requires a table file (.tbl) built from visual identification.

---

## Files Produced

- `eeMemory.bin` -- Extracted RAM dump from randomdialogue.p2s
- `search1.py` through `s13.py` -- Analysis scripts
- This file -- Complete findings
