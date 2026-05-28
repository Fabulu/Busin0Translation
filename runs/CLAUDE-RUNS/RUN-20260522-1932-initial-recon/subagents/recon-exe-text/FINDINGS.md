# EXE Hardcoded Text Analysis: SLPM_653.78

## Executive Summary

The PS2 EXE (4.1 MB ELF binary) contains very few player-visible strings. Nearly all
text in the EXE is developer-only debug output. Menu labels like "Camp", "System",
"Library", "Save", "Load", "Status", "Option", "Yes/No", equipment names, spell names,
and all in-game dialogue are NOT in the EXE -- they are stored in the 296 MSG resources
within PACKDATA.DIG using 16-bit glyph-index encoding.

## Player-Visible Strings Requiring Translation

### CATEGORY 1: Memory Card Save Slot Names (DEFINITELY player-visible)

These appear in the PS2 memory card browser and on save/load screens:

| Offset     | SJIS Bytes                                       | Japanese            | English Translation         | Notes                    |
|------------|--------------------------------------------------|---------------------|-----------------------------|--------------------------|
| 0x3FC720   | 82 61 82 74 82 72 82 68 82 6D 82 4F              | BUSIN0              | BUSIN 0                     | Save title (icon.sys)    |
| 0x3FC750   | 82 61 82 74 82 72 82 68 82 6D 82 4F 83 66 81 5B 83 5E 82 50 | BUSIN0 Data 1 | BUSIN 0 Data 1              | Save slot 1 display name |
| 0x3FC770   | 82 61 82 74 82 72 82 68 82 6D 82 4F 83 66 81 5B 83 5E 82 51 | BUSIN0 Data 2 | BUSIN 0 Data 2              | Save slot 2 display name |
| 0x3FC790   | 82 61 82 74 82 72 82 68 82 6D 82 4F 83 66 81 5B 83 5E 82 52 | BUSIN0 Data 3 | BUSIN 0 Data 3              | Save slot 3 display name |
| 0x3F9370   | 82 61 82 74 82 72 82 68 82 6D 82 4F 92 86 92 66 83 66 81 5B 83 5E | BUSIN0 Suspend Data | BUSIN 0 Suspend Data | Suspend save name        |
| 0x3F9678   | 82 61 82 74 82 72 82 68 82 6D 82 4F              | BUSIN0              | BUSIN 0                     | Save card title (2nd)    |
| 0x3F9670   | (BUSIN 1 compat area)                            | BUSIN0              | BUSIN 0                     | BUSIN 1 import label     |

These are fullwidth katakana renderings of "BUSIN0" plus "data 1/2/3" and "suspend data".
They appear on the PS2 memory card management screen. Translation is optional since they
are brand names, but "Data 1/2/3" and "Suspend Data" could be localized.

### CATEGORY 2: Memory Card Directory Names (NOT translatable)

These are filesystem directory names on the memory card. They MUST stay as-is:

| Offset     | String                    | Purpose                       |
|------------|---------------------------|-------------------------------|
| 0x3F92B0   | BISLPM-65378BSN2-3        | Suspend save directory        |
| 0x3F9450   | BISLPM-65378BSN2-0        | Save slot 0 directory         |
| 0x3F9470   | BISLPM-65378BSN2-1        | Save slot 1 directory         |
| 0x3F9490   | BISLPM-65378BSN2-2        | Save slot 2 directory         |
| 0x3F9660   | BISLPM-62098BUSINWZ       | BUSIN 1 save import directory |

### CATEGORY 3: Memory Card File Names (NOT translatable)

| Offset     | String       | Purpose                       |
|------------|--------------|-------------------------------|
| 0x3F9338   | icon.sys     | PS2 save icon descriptor      |
| 0x3F9348   | icon1.ico    | Save icon animation frame 1   |
| 0x3F9388   | icon2.ico    | Save icon animation frame 2   |
| 0x3F9398   | icon3.ico    | Save icon animation frame 3   |
| 0x3F92C8   | BUSIN2-GAME  | Save data filename            |

### CATEGORY 4: Potentially Visible Debug/Error Messages

These may display under error conditions. Whether they appear depends on the
error handling code paths:

| Offset     | Japanese                          | Translation                        | Likely Visible? |
|------------|-----------------------------------|------------------------------------|-----------------|
| 0x3F8240   | コンティニューロード！              | Continue Load!                     | Possibly (TTY)  |
| 0x3F8260   | 取り付ける人がいないよ。            | No one available to equip to.      | Possibly (TTY)  |
| 0x3F8EF0   | そのようなOTはないです!!!           | No such OT exists!!!               | No (dev only)   |
| 0x3FC7F0   | 松野ゲー起動！！                   | Matsuno game startup!!             | No (boot msg)   |

### CATEGORY 5: Format Strings (Debug only, NOT player-visible)

| Offset     | String         | Purpose                |
|------------|----------------|------------------------|
| 0x3F96B8   | C:%d           | Debug: CPU stat        |
| 0x3F96C0   | G:%d           | Debug: GPU stat        |
| 0x3F96C8   | M:%d           | Debug: Memory stat     |
| 0x3EE8E8   | : %d           | Sequence monster no    |
| 0x3F0368   | : %d           | Monster SE no          |

## Menu Labels NOT in the EXE

Exhaustive search confirmed these common menu items are ABSENT from the EXE:

- キャンプ (Camp) -- NOT FOUND
- システム (System) -- NOT FOUND (only in debug strings like "MenuSystemLoadEnd")
- ライブラリ (Library) -- NOT FOUND (only in debug strings like "Library Init")
- セーブ (Save) -- NOT FOUND
- ロード (Load) -- NOT FOUND (only partial match in "コンティニューロード")
- ステータス (Status) -- NOT FOUND
- オプション (Option) -- NOT FOUND
- 装備/そうび (Equip) -- NOT FOUND
- じゅもん (Spell) -- NOT FOUND
- 防御 (Defend) -- NOT FOUND
- 逃げる (Flee) -- NOT FOUND
- はい/いいえ (Yes/No) -- NOT FOUND
- メモリーカード (Memory Card) -- NOT FOUND

**Conclusion**: All UI menu text is rendered from glyph-index data in PACKDATA.DIG resources,
not from SJIS strings in the EXE.

## Debug Strings Classification

Of the ~464 SJIS strings previously identified in the EXE data section, ALL are debug-only:

- **Battle system debug** (~120 strings): Allied attack names, effect level reports,
  dispel results, formation names -- all printed to TTY console, never rendered on screen
- **Resource loading debug** (~80 strings): "XXXLoadEnd LastMem = (%x)" format
- **Error/warning debug** (~50 strings): Buffer overflow, null pointer, data errors
- **PS2 SDK messages** (~40 strings): libpad, libmc, cdvd, MPEG decoder messages
- **3D model/scene names** (~100 strings): b01a_door_a, b01a_curve_b, etc.
- **Memory card operations debug** (~20 strings): Mcrd_DeleteFile, MemoryData size

## Font/Glyph Infrastructure in EXE

| Offset      | Size      | Description                                          |
|-------------|-----------|------------------------------------------------------|
| 0x3C08A2    | ~108 bytes| ASCII glyph mapping table (char codes 0x21-0x5D)     |
| 0x3CA692    | ~110 bytes| Sequential glyph index table (0-55)                  |
| 0x3DDC48    | 248 bytes | Font width table (proportional widths, values 4-16)  |
| 0x3DDD48    | 248 bytes | Font width table (duplicate/alternate size)           |
| 0x3DDE48    | 248 bytes | Font width table (duplicate/alternate size)           |
| 0x3DDF48    | 248 bytes | Font width table (duplicate/alternate size)           |
| 0x3DC3B8    | 10 bytes  | "0123456789" digit glyph source                      |
| 0x3DC3A0    | 16 bytes  | Color palette data (RGBA values)                     |

The font width tables have 248 entries each, suggesting the system font supports
~248 glyphs. Four copies exist (likely for different font sizes or styles).

## Strings That Need Translation (Final Count)

**Total: 5-7 strings** (all memory card save display names)

| Priority | Count | Category                  |
|----------|-------|---------------------------|
| HIGH     | 0     | Menu/UI labels            |
| MEDIUM   | 5     | Save slot display names   |
| LOW      | 2     | Debug messages (optional) |

The save slot names (BUSIN0 Data 1/2/3, BUSIN0 Suspend Data) are the ONLY
player-visible text hardcoded in the EXE. Everything else is either debug output
or filesystem identifiers that must remain unchanged.

## Key Takeaway

The EXE is NOT where the translation effort needs to focus. The game's text
architecture puts all player-visible text into the PACKDATA.DIG MSG resources
using glyph-index encoding. The EXE contains only the rendering engine, game
logic, and memory card management strings.
