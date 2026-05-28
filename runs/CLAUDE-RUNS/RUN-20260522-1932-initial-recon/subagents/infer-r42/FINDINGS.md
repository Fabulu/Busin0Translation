# Resource 42 (0042_type01.bin) - Adventurer's Inn Dialogue

## Overview
Resource 42 contains the Adventurer's Inn system messages.
15 messages total: 1 control/index table, 1 padding, 13 dialogue/system messages.
Matches English guide section "THE JEWEL OF VENOA DUHAN ADVENTURER'S INN".

Source file: `C:/Programmieren/wizardrytranslation/extracted/packdata_resources/0042_type01.bin` (614 bytes)
Glyph map: `C:/Programmieren/wizardrytranslation/data/msg_glyph_map.json`
Output JSON: `C:/Programmieren/wizardrytranslation/data/inferred_r42.json`

## Key Discovery: Glyph 341 Mapping Error
The current msg_glyph_map.json maps glyph 341 to katakana "N" but contextual analysis
across both r42 and r43 strongly indicates it should be "fu/not" (kanji). Evidence:
- Message 12: must read "funds insufficient" (not "funds N-sufficient")
- r43 message 82: medals must be "insufficient" not "N-sufficient"
- Glyph 238 is already correctly mapped to katakana N
- Having two glyphs mapped to the same katakana character is suspicious

## Full Decoded Text (with inferences)

### Message 0 (Control/Index Table)
```
[CTRL:14][NUL][CTRL:60][NUL][CTRL:66][NUL]hi[NUL][210][NUL][276][NUL]say[NUL][362][NUL][442][NUL][502][NUL]wall[NUL][530][NUL][540][NUL][566][NUL][594]
```
This is a jump/index table with glyph IDs as menu pointers. The NUL (glyph 0) separators
and ASCII characters (14='(', 60='X', 66='^') suggest this is metadata, not displayed text.

### Message 1 (Padding)
```
[NUL]
```

### Message 2 (Welcome - First Visit)
Raw: [486][487][287]no[842]heyoukoso. kokoha[320][671]wo[494]me, mata[498]tana[346]wo[620]ru[843][496].
```
冒(486)険(487)者(287)の宿(842)へようこそ。
ここは心(320)身(671)を休(494)め、
また新(498)たな力(346)を得(620)る場(843)所(496)。
```
Inferred: 冒険者の宿へようこそ。ここは心身を休め、また新たな力を得る場所。
English: "Welcome to the Adventurer's Inn. This is a place to rest mind and body, and gain new power."
Guide match: "Welcome to the Inn, dear guest! If you are tired, please stay with us."

### Message 3 (Welcome - Level Up Available)
Raw: [486][487][287]no[842]heyoukoso. oya, [234][257][233][193][272][261]sareru[546]gaoraremasune.
```
冒(486)険(487)者(287)の宿(842)へようこそ。
おや、レ(234)ベ(257)ル(233)ア(193)ッ(272)プ(261)される方(546)がおられますね。
```
Inferred: 冒険者の宿へようこそ。おや、レベルアップされる方がおられますね。
English: "Welcome to the Adventurer's Inn. Oh, there seems to be someone who can level up."
Guide match: "sleep can help an adventurer grow over the course of a night."

### Message 4 (Room Available)
Raw: [842][844]sareruno desuka. o[845][553]ha[846]iteiruno de go[586][320]kudasai.
```
宿(842)泊(844)されるのですか。
お部(845)屋(553)は空(846)いているので
ご安(586)心(320)ください。
```
Inferred: 宿泊されるのですか。お部屋は空いているのでご安心ください。
English: "Will you be staying? The room is available, so please don't worry."

### Message 5 (Farewell - Leaving)
Raw: mou[497][661]sareruno desuka? douka o[339]wotsukete.
```
もう出(497)発(661)されるのですか？
どうかお気(339)をつけて。
```
Inferred: もう出発されるのですか？どうかお気をつけて。
English: "Are you leaving already? Please take care."

### Message 6 (Stay Confirmation)
Raw: o[844]ri ni nararemasu ka?
```
お泊(844)りに
なられますか？
```
Inferred: お泊りになられますか？
English: "Would you like to stay?"

### Message 7 (Post-Rest Farewell)
Raw: goyukkuri dekimashitaka? yoki[494][352]ha[617][702]heno[774][346]. mata irashite kudasaine.
```
ごゆっくりできましたか？
よき休(494)養(352)は翌(617)日(702)への活(774)力(346)。
またいらしてくださいね。
```
Inferred: ごゆっくりできましたか？よき休養は翌日への活力。またいらしてくださいね。
English: "Were you able to relax? Good rest is vitality for tomorrow. Please come again."

### Message 8 (Insufficient Funds - Polite)
Raw: ara, o[419]ga[712]rinai youdesune. mata o[890]shi kudasai.
```
あら、お金(419)が足(712)りない
ようですね。
またお越(890)しください。
```
Inferred: あら、お金が足りないようですね。またお越しください。
English: "Oh, it seems you don't have enough money. Please come again."

### Message 9 (Stay Prompt - Simple)
Raw: [842][844]shimasuka?
```
宿(842)泊(844)しますか？
```
Inferred: 宿泊しますか？
English: "Will you stay?"

### Message 10 (Yes)
```
はい
```
Note: Contains glyph 0 (NUL) between は and い, likely a display spacing artifact.

### Message 11 (No)
```
いいえ
```

### Message 12 (Insufficient Funds - System)
Raw: [496][668][419]ga[341*][712]shiteimasu
```
所(496)持(668)金(419)が不(341*)足(712)しています
```
Inferred: 所持金が不足しています
English: "You do not have enough money."
*Note: Glyph 341 is mapped as katakana N but context requires kanji "not/un-" (不)

### Message 13 (Potential Ability Awakened)
Raw: [689][706][700][346]ga[662][675]memashita
```
潜(689)在(706)能(700)力(346)が目(662)覚(675)めました
```
Inferred: 潜在能力が目覚めました
English: "A potential ability has awakened!"
Guide match: "POTENTIAL ABILITY" system - abilities awaken at LVL20-30 during rest at inn.

### Message 14 (Awakening Template Suffix)
Raw: ga[662][675]memashita
```
が目(662)覚(675)めました 
```
Inferred: が目覚めました
English: "...has awakened!"
This is a template suffix where the game engine prepends the specific ability name.

## Glyph Inference Summary

### High Confidence (20 glyphs)
| Glyph | Char | Reading | Context |
|-------|------|---------|---------|
| 287 | 者 | sha | 冒険者 (adventurer) |
| 339 | 気 | ki | お気をつけて (take care) |
| 419 | 金 | kin/kane | お金 (money), 所持金 (funds) |
| 486 | 冒 | bou | 冒険者の宿 |
| 487 | 険 | ken | 冒険者の宿 |
| 496 | 所 | sho/tokoro | 所持金, 場所 |
| 497 | 出 | shutsu | 出発 (departure) |
| 498 | 新 | shin/atara | 新たな (new) |
| 553 | 屋 | ya | 部屋 (room) |
| 586 | 安 | an | ご安心 (peace of mind) |
| 661 | 発 | hatsu | 出発 (departure) |
| 662 | 目 | me | 目覚め (awakening) |
| 668 | 持 | ji/mo | 所持 (possession) |
| 675 | 覚 | kaku/sa | 目覚め (awakening) |
| 712 | 足 | soku/ta | 不足, 足りない |
| 842 | 宿 | shuku/yado | 冒険者の宿, 宿泊 |
| 844 | 泊 | haku/to | 宿泊, お泊り |
| 845 | 部 | bu | お部屋 (room) |
| 846 | 空 | kuu/a | 空いている (available) |
| 890 | 越 | etsu/ko | お越しください (please come) |

### Medium Confidence (14 glyphs)
| Glyph | Char | Reading | Context |
|-------|------|---------|---------|
| 320 | 心 | shin/kokoro | 心身, ご安心 |
| 346 | 力 | ryoku/chikara | 活力, 能力, 新たな力 |
| 352 | 養 | you | 休養 (recuperation) |
| 494 | 休 | kyuu/yasu | 休め, 休養 |
| 546 | 方 | kata | される方 (person, polite) |
| 617 | 翌 | yoku | 翌日 (next day) |
| 620 | 得 | toku/e | 力を得る (gain power) |
| 671 | 身 | shin/mi | 心身 (mind and body) |
| 689 | 潜 | sen | 潜在能力 |
| 700 | 能 | nou | 潜在能力 |
| 702 | 日 | jitsu/hi | 翌日 (next day) |
| 706 | 在 | zai | 潜在能力 |
| 774 | 活 | katsu | 活力 (vitality) |
| 843 | 場 | ba/jou | 場所 (place) |

### Low Confidence (7 glyphs)
| Glyph | Char | Reading | Context |
|-------|------|---------|---------|
| 193 | ア | a | レベルアップ (level up) |
| 233 | ル | ru | レベルアップ |
| 234 | レ | re | レベルアップ |
| 257 | ベ | be | レベルアップ |
| 261 | プ | pu | レベルアップ |
| 272 | ッ | small-tsu | レベルアップ |
| 341 | 不 | fu/bu | 不足 (CORRECTION: currently mis-mapped as katakana N) |

### Mapping Correction Needed
- **Glyph 341**: Currently mapped as katakana N in msg_glyph_map.json. Should be kanji "not/un-".
  Evidence: appears in "funds insufficient" pattern across r42 and r43.
  Glyph 238 already correctly maps to katakana N, making 341 a suspicious duplicate.

## Cross-Reference Notes
- Glyphs 419, 496, 668, 712, 339, 341 confirmed via r43 (0043_type01.bin) tavern/game dialogue
- r43 line 43: "おいおい、金(419)が足(712)りねえと" (informal version of same money check)
- r43 line 76: "所(496)持(668)金(419)が不(341)足(712)しています" (identical system message)
- r43 line 86: "所(496)持(668)品(603)がいっぱいです" (confirms 496=所, 668=持)
