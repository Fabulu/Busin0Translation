# R39 Inline Japanese Glyph Patching

## Overview

`tools/patch_r39_inline.py` patches ALL inline Japanese glyph IDs in R39's extra
data section (bytes 2702+) with English equivalents. It runs AFTER `inject_r39_v2.py`
and reads/writes `build/packdata_resources/0039_type15.raw`.

## What It Patches (104 records total, 0 truncated)

### Spell Names (records 2-57, 56 entries)
Japanese katakana spell names replaced with abbreviated English:
- クレタ -> Crt, クルド -> Crd, ティール -> Teal
- アナライズ -> Anlyz, ウィーク -> Weak, デプス -> Dpt
- プロテクト -> Prtct, アンカーズ -> UCurs, リヴィヴ -> Reviv
- Full list in script (56 spells total)

### Combat Skill Names (records 117-125, 9 entries)
- 決定 -> OK
- Wスラッシュ -> WSlash
- スタンスマッシュ -> StSmash
- ホールドアタック -> HoldAtk
- マジックシールド -> MagcSld
- etc.

### NPC Names (records 428-436, 9 entries)
- ヴィガー -> Vigor
- ミリィ -> Mil
- ルーシー -> Lucy
- etc.

### Equipment Categories (records 453-510, 16 entries)
- アクセサリー -> Accsry
- アイテム -> Item
- ダガー -> Dgr
- ショートソード -> ShrtSwd
- ロングソード -> LngSwd
- etc.

### Body Part Chip Names (records 517-526, 10 entries)
- ハンドチップ -> HandCp
- ボディチップ -> BodyCp
- アームチップ -> ArmChp
- レッグチップ -> LegChp
- ブレインチップ -> BrnChp

### Unidentified Weapon Types (records 493-516, 4 entries)
- ?メイス -> ?Mac
- ?フレイル -> ?Flal
- ?ブーツ -> ?Bot
- ?マント -> ?Clk

## Technical Details

### Constraint
Each FFFF-delimited record has a fixed number of uint16 content word slots.
Japanese characters use 1 slot each (glyph IDs 95-900+). English ASCII characters
also use 1 slot each (glyph IDs 0-94). Therefore English text must be <= the number
of Japanese characters in the original. Shorter English is padded with 0x0000.

### Safety
- FFFF delimiters: preserved (558 count verified)
- FFFE line-break delimiters: preserved (763 count verified)
- Pre-extra-data bytes (0-2701): untouched
- File size: unchanged (26624 bytes)
- Records NOT patched: complex UI script records (60-115, 382-403, 550+) which
  contain interleaved control data and cannot be safely modified without understanding
  the full UI scripting format.

### Build Integration
Added as Step 3.1 in `build/build_v9.py`, immediately after Step 3 (R39 injection).

## What Remains Japanese

The extra data section also contains:
- **UI script records** (recs 60-115, 382-403): Complex records with positioning,
  color, and layout control codes interleaved with glyph content. These define
  stat screens, sidebar layouts, and equipment display logic. The Japanese class
  names (侍, 忍者, etc.) and stat labels embedded in these records are rendered
  from TEXTURE data in R1188, not from these glyph IDs -- the glyph IDs here
  serve as identifiers for the UI engine, not as visible text.
- **Index/offset tables** (recs 0, 58, 116, 380, 404, 426, 441, 548): Contain
  offset values that look like glyph IDs but are actually byte offsets. Must not
  be touched.
- **Status message records** (recs 550-557): Complex formatting with control
  codes 0xFF01 and 0xFFF0.
