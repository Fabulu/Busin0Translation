# EXE Deep Scan: Remaining Japanese Text in SLPM_653.78

**Date:** 2026-05-28
**Scanner:** scan_exe_sjis.py (SJIS + ASCII scan of full data section)
**EXE:** extracted/SLPM_653.78, 4,185,776 bytes

## Summary

- **44 SJIS runs** found in data section (0x3B0000-0x3FDEB0)
- **1,765 ASCII strings** total; 573 matched game-relevant keywords
- **Most SJIS hits are false positives** (floating-point struct data misread as SJIS)
- **All genuine Japanese strings are already patched or are TTY-only debug output**
- **1 unpatched player-visible string found** (Busin 1 save card title at 0x3F9678)

## Classification of All SJIS Hits

### FALSE POSITIVES (struct data, not text)
These are floating-point numbers or struct fields whose byte patterns coincidentally match SJIS encoding. All are 2-char hits with nonsensical kanji.

| Offset | Decoded | Actual Data |
|--------|---------|-------------|
| 0x3BEE3A | 線樋 | Binary data in pre-table area |
| 0x3C3978 + 14 more | 囮院, 沓囮 | Table 2C menu structs (float32 values like 1.0f, 70.0f) |
| 0x3D7485 | 囹埀 | Binary data between tables |
| 0x3D7C78 | 囹奧 | Binary data |
| 0x3D7D74 | 勦勹 | Binary data |
| 0x3DCFE8, 0x3DCFF0 | 囮劔劔 | MPEG decoder library data |
| 0x3DE2B2 | 疏膵瓩 | printf/vfprintf library data |
| 0x3DE309 | 華隆 | Library data |
| 0x3DE320 | 恬狐 | Library data |

### TTY/DEBUG STRINGS (not player-visible)
These all end with `\n` (0x0A) and are printf-style debug output to the PS2 TTY console. Players never see these.

| Offset | Text | Translation |
|--------|------|-------------|
| 0x3EC910 | デバックチェック　！！！！！ | "Debug check !!!!!" |
| 0x3EC930 | デバック戦闘だよ　！！！！！ | "Debug battle !!!!!" |
| 0x3EC950 | デバック戦闘確認　！！！！！ | "Debug battle confirm !!!!!" |
| 0x3F3634 | 壁イベントデータ作成エラー | "Wall event data creation error" |
| 0x3F3B90 | コールバッファオーバーです！！ | "Call buffer overflow!!" |
| 0x3F3CE0 | メモリ足りんで〜！！ | "Not enough memory!!" |
| 0x3F3D00 | アイテム数足りんで〜！！ | "Not enough item slots!!" |
| 0x3F8150 | ガーディアン戦闘！！ | "Guardian battle!!" |
| 0x3F81D0 | 接触！！ | "Contact!!" (mixed with printf format string) |
| 0x3F8EF0 | そのようなＯＴはないです | "No such OT" |
| 0x3FC400 | Q が Over です!!!!!!!!!!! | "Q is Over!!" (debug queue overflow) |
| 0x3FC7F0 | 松野ゲー起動！！ | "Matsuno game boot!!" (dev name easter egg) |

### ALREADY PATCHED by patch_exe.py
These are handled in `build/patch_exe.py`:

| Offset | Original | Patched To |
|--------|----------|------------|
| 0x3FC720 | ＢＵＳＩＮ０ | "BUSIN 0" |
| 0x3FC750 | ＢＵＳＩＮ０データ１ | "BUSIN 0 Data 1" |
| 0x3FC770 | ＢＵＳＩＮ０データ２ | "BUSIN 0 Data 2" |
| 0x3FC790 | ＢＵＳＩＮ０データ３ | "BUSIN 0 Data 3" |
| 0x3F9370 | ＢＵＳＩＮ０中断データ | "BUSIN 0 Suspend" |
| 0x3F8240 | コンティニューロード！ | "Continue loading!" |
| 0x3F8260 | 取り付ける人がいないよ。 | "No one can equip it." |

### UNPATCHED BUT PLAYER-VISIBLE (action needed)

| Offset | Text | Context | Recommended Patch |
|--------|------|---------|-------------------|
| 0x3F9678 | ＢＵＳＩＮ０ | Busin 1 (SLPM-62098) save card title. Shown on PS2 memory card browser when Busin 0 detects a Busin 1 save file. 12 bytes SJIS, 12 bytes available. | "BUSIN 0" (ASCII, same as 0x3FC720) |

## Memory Card Save Structures (complete inventory)

The EXE contains **3 memory card structures**, each with a product ID, save title, and icon filenames:

1. **Busin 0 main saves** (0x3FC650-0x3FC7A0):
   - Product IDs: BISLPM-65378BSN2-0, -1, -2
   - Titles: BUSIN0, BUSIN0 Data 1/2/3 -- **PATCHED**

2. **Busin 0 suspend save** (0x3F9340-0x3F93A0):
   - Contains: BUSIN2-GAME, BUSIN0 Suspend Data -- **PATCHED**

3. **Busin 1 compatibility** (0x3F9660-0x3F96B0):
   - Product ID: BISLPM-62098BUSINWZ (Busin 1 / Wizardry)
   - Title at 0x3F9678: ＢＵＳＩＮ０ -- **NOT PATCHED**
   - This is used when the game reads save data from the original Busin 1

## ASCII Strings Analysis

All 1,765 ASCII strings in the data section were checked. None contain untranslated Japanese romanization or player-visible labels. Categories found:
- **PS2 SDK library messages** (~200): libdma, libpad, libcdvd, MPEG decoder, etc.
- **Game engine debug output** (~1,200): effect system, battle system, dungeon system, menu system, memory management, all ending with `\n`
- **File/resource names** (~50): icon.sys, icon1.ico, BUSIN2-GAME, FCD_* identifiers
- **IOP module paths** (~10): cdrom0:\IOPRP254.IMG, cdrom0:\PADMAN.IRX, etc.
- **ELF section names** (~5): .shstrtab, .strtab, MW MIPS C compiler tag

None of these are player-visible.

## Conclusion

**The EXE is nearly fully cleaned.** Only one actionable item remains:

1. **Add 0x3F9678 to patch_exe.py** -- the Busin 1 save card title "ＢＵＳＩＮ０" (12B SJIS -> "BUSIN 0" ASCII). This is visible on the PS2 memory card browser only in the edge case where a player has both Busin 1 and Busin 0 save files.

All other Japanese text in the EXE is either:
- Already patched (7 strings)
- Debug/TTY output invisible to players (12+ strings)
- False positives from struct/float data (15+ hits)
