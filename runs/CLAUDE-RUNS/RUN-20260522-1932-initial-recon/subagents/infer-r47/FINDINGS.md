# Resource 47 Glyph Inference Findings

## Overview

Decoded resource `0047_type03.bin` (1962 bytes, type03 format with pointer table header).
Contains **73 system messages** covering battle, treasure chests, spell incantations, level-up, and party management.

## Key Structural Finding

**The katakana_glyph_map.json (name-entry font) is NOT compatible with the dialogue/message font.**
When both maps contain the same glyph ID, they map to DIFFERENT characters (e.g., glyph 226 = "Me" in messages but "So" in name-entry). Only `msg_glyph_map.json` is valid for message decoding.

## Dialogue Font Katakana Block

Discovered a sequential katakana block in the dialogue font (approximate ranges):

| Range | Content |
|-------|---------|
| 193-197+ | Basic katakana (ア=193, イ=194, ...オ=197) with kanji gaps |
| 205-211+ | ス=205, ...タ=208, ...テ=211 |
| 225-227 | ム=225, メ=226(confirmed), モ=227 |
| 233-234 | ル=233, レ=234, ...ン=238(confirmed) |
| 239+ | ガ行 dakuten (ガ=239 confirmed) |
| 249+ | ダ行 dakuten (ダ=249 confirmed, デ=252) |
| 254+ | バ行 dakuten (バ=254 confirmed, ベ=257) |
| 259-263 | パ行 (パ=259, プ=261, ペ=262) |
| 268+ | Small kana (ィ=268 confirmed, ッ=272) |

## Confirmed Loanword Reconstructions

| Japanese | English | Glyph IDs |
|----------|---------|-----------|
| モンスター | Monster | 227,238,205,208,93 |
| パーティ | Party | 259,93,211,268 |
| アイテム | Item | 193,194,211,225 |
| ディスペル | Dispel | 252,268,205,262,233 |
| レベル | Level | 234,257,233 |
| アップした | Increased | 193,272,261 + した |

## Inferred Kanji (48 total, 30 HIGH confidence)

### HIGH Confidence (30)

| ID | Hex | Char | Reading | Evidence |
|----|-----|------|---------|----------|
| 193 | 0x00C1 | ア | a | アイテム=item, アップ=up |
| 194 | 0x00C2 | イ | i | アイテム=item |
| 205 | 0x00CD | ス | su | モンスター=monster |
| 208 | 0x00D0 | タ | ta | モンスター=monster |
| 211 | 0x00D3 | テ | te | アイテム, パーティ |
| 225 | 0x00E1 | ム | mu | アイテム=item |
| 227 | 0x00E3 | モ | mo | モンスター=monster |
| 233 | 0x00E9 | ル | ru | ディスペル, レベル |
| 234 | 0x00EA | レ | re | レベル=Level |
| 252 | 0x00FC | デ | de | ディスペル=Dispel |
| 257 | 0x0101 | ベ | be | レベル=Level |
| 259 | 0x0103 | パ | pa | パーティ=Party |
| 261 | 0x0105 | プ | pu | アップした=increased |
| 262 | 0x0106 | ペ | pe | ディスペル=Dispel |
| 272 | 0x0110 | ッ | small tsu | アップ=up |
| 346 | 0x015A | 力 | ryoku | Stat suffix (攻撃力 etc.) |
| 351 | 0x015F | 化 | ka | 強化された=strengthened |
| 370 | 0x0172 | 成 | sei | 成功した=succeeded |
| 415 | 0x019F | 入 | hai/nyu | 入りこめない=can't fit in |
| 497 | 0x01F1 | 出 | de/da | 逃げ出す=flee, み出す |
| 498 | 0x01F2 | 新 | shin/atara | 新たな=new |
| 572 | 0x023C | 何 | nani | 何も持っていなかった=had nothing |
| 591 | 0x024F | 果 | ka | 結果=result |
| 608 | 0x0260 | 箱 | hako | 箱を開錠=unlock chest |
| 612 | 0x0264 | 隙 | suki | 隙をついた=exploited opening |
| 621 | 0x026D | 強 | tsuyoi | すこし/とても強い=strong |
| 668 | 0x029C | 持 | mo(tsu) | 持っていなかった=didn't have |
| 682 | 0x02AA | 功 | kou | 成功した=succeeded |
| 685 | 0x02AD | 追 | o(u) | 追いかけた=chased |
| 773 | 0x0305 | 結 | ketsu | 結果=result |
| 849 | 0x0351 | 恐 | kyou | 恐怖にかられて=gripped by fear |
| 850 | 0x0352 | 怖 | fu | 恐怖=fear |
| 859 | 0x035B | 逃 | ni(geru) | 逃げ出す=flee |
| 876 | 0x036C | 錠 | jou | 開錠=unlock |

### MEDIUM Confidence (14)

| ID | Hex | Char | Reading | Evidence |
|----|-----|------|---------|----------|
| 92 | 0x005C | ! | - | Doubled sentence-end exclamation |
| 315 | 0x013B | 盗 | nusu(mu) | Wizardry thief steal mechanic |
| 340 | 0x0154 | 打 | u(tsu) | 打ち取る=strike down |
| 348 | 0x015C | 盾 | tate | Spell incantation: shield |
| 406 | 0x0196 | 封 | fuu | 封じた=sealed (status effect) |
| 508 | 0x01FC | 編 | a(mu) | 編み出す=devise |
| 613 | 0x0265 | 許 | yuru(su) | Spell: 許さず=not allowing |
| 653 | 0x028D | 全 | zen | 全員=all members |
| 661 | 0x0295 | 解 | kai | 解明しました=clarified |
| 833 | 0x0341 | 戻 | modo(ru) | Spell: 戻れ=return |
| 856 | 0x0358 | 取 | to(ru) | 打ち取る=strike down |
| 857 | 0x0359 | 突 | totsu | 突然=suddenly |
| 858 | 0x035A | 然 | zen | 突然=suddenly |
| 997 | 0x03E5 | 員 | in | 全員=all members |

## Message Categories

1. **Battle actions** (MSG 2-10, 24-26, 64-65): Monster attacks, fear/flee, item theft
2. **Treasure system** (MSG 11-16, 21-23): Chest unlock, empty chest, steal results
3. **UI/Menu** (MSG 13, 17-20, 27-30, 41-47): Menu options, difficulty labels
4. **Stats/Level** (MSG 31-40, 48-51): Level display, class levels, stat names
5. **Spell incantations** (MSG 54-61): Poetic invocations for magic spells
6. **Party management** (MSG 62-72): Party stat changes, level-up notifications

## Still Unresolved (74 glyph IDs)

Notable unknowns include:
- Variable/format codes: 0x0000, 0x0021, 0x0027, 0x0028, 0x002D, 0x0030 (likely stat/level variable insertion markers)
- Stat/class names: 0x02D2+0x015E (a class/stat pair), 0x02D4 (paired with 消)
- Spell incantation terms: 0x029A, 0x02F7, 0x034A, 0x034B
- Party member identifiers: 0x028D, 0x03E5 (possibly 全員=all members, MEDIUM confidence)

## Files

- Output: `data/inferred_r47.json` (48 mappings)
- Source binary: `extracted/packdata_resources/0047_type03.bin`
- Reference map: `data/msg_glyph_map.json`
- Guide: `dumps/guide_full.txt`
