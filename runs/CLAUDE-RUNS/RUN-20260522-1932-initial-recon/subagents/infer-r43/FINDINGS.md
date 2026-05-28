# Resource 0043 Glyph Inference -- FINDINGS

**Resource**: `extracted/packdata_resources/0043_type01.bin` (1416 bytes, 87 messages)
**Output**: `data/inferred_r43.json`
**Date**: 2026-05-22

## Summary

Inferred 57 unknown glyph IDs from resource 43 (Bar Luna Light -- Trap Game and Medal Exchange dialogue).
- 49 HIGH confidence
- 7 MEDIUM confidence
- 1 LOW confidence

## Resource Identity

This resource contains UI dialogue for the **Bar Luna Light** tavern, specifically:
1. **Trap Game** (practice and play modes)
2. **Medal Exchange** (trade medals for prize items)
3. **Personal Deeds** (list of completed requests/quests)
4. General barkeep greetings and responses

Speaker is **Gin Barbus**, the barkeep, using casual rough male Japanese (だぜ、ねえ、etc.).

## Key Vocabulary Confirmed

| Glyph Pair | Word | Meaning | Occurrences |
|------------|------|---------|-------------|
| 242+93+225 | ゲーム | Game | 10 msgs |
| 906+619 | 練習 | Practice | 3 msgs |
| 529+855 | 交換 | Exchange | 5 msgs |
| 786+635 | 依頼 | Request | 3 msgs |
| 910+603 | 景品 | Prize | 4 msgs |
| 496+668 | 所持 | Possession | 4 msgs |
| 226+249+233 | メダル | Medal | 10 msgs |
| 709+710 | 必要 | Required | 1 msg |
| 908+909 | 残念 | Too bad | 1 msg |
| 562+308 | 自信 | Confidence | 1 msg |
| 339+552+379+855 | 気分転換 | Change of pace | 1 msg |
| 901+902 | 引受 | Accept/take on | 1 msg |
| 911+587 | 整理 | Organize | 1 msg |

## Katakana Confirmed

| ID | Char | Evidence |
|----|------|----------|
| 193 | ア | アイテム (item) |
| 194 | イ | アイテム, プレイ |
| 211 | テ | アイテム |
| 225 | ム | ゲーム, アイテム |
| 233 | ル | メダル |
| 234 | レ | プレイ |
| 242 | ゲ | ゲーム |
| 261 | プ | プレイ |

Note: Glyph 194=イ appears to be a separate entry from the already-mapped 59=イ. This may represent a different font position or visual variant.

## Numeric/Symbol Confirmed

| ID | Char | Evidence |
|----|------|----------|
| 16 | ０ | 500G price display |
| 17 | １ | "1 round" display |
| 21 | ５ | 500G price display |
| 39 | Ｇ | Gold currency symbol |
| 415 | 回 | Counter for rounds |

These are consistent with the existing mapping 18=２, suggesting sequential number assignment around IDs 15-25.

## Unresolved Glyphs

The following glyph IDs from this resource remain unresolved:

- **92, 212, 222**: Part of the expression [212][222][222][92] in MSG 25 (exclamation/address before comma). Likely katakana.
- **208**: In [193]ン[208] compound (MSG 26). Something that "beats you" in the trap game context.
- **899, 900**: In [899]鉄[900] compound (MSG 7). A 3-character term containing 鉄.
- **904, 905**: In [904][905]あがったりだぜ (MSG 27). An expression about being "finished/done for."
- **998**: Standalone in MSG 79. Possibly a UI marker or symbol (※).

## Anomaly: Glyph 341

Glyph 341 is mapped as ン (katakana N) in the glyph map, confirmed by the Ingo name cross-reference. However, in MSGs 75 and 81 it appears in the pattern "がン足しています" which is grammatically nonsensical. The expected text would be "が不足しています" (is insufficient). This suggests either:
1. Glyph 341 has dual usage (ン in names, 不 in certain compound contexts)
2. A rendering/template quirk in the game engine
3. An error in the glyph map for ID 341

## Full Decoded Text (with inferences applied)

```
MSG  0: [separator]
MSG  1: おうおう、
MSG  2: あの依頼はどうなった？
MSG  4: よう、
MSG  5: 一杯ひっかけてくかい？
MSG  7: [899]鉄[900]を明るのか？
MSG 10: 何か依頼を
MSG 11: 引き受けてくれるのか？
MSG 13: お客さんがこれまでに
MSG 14: こなした依頼を
MSG 15: 数えてやろう。
MSG 16: 気分転換に
MSG 17: ゲームでもしていけよ
MSG 19: なんだ、
MSG 20: もう帰るってのか？
MSG 22: おっ
MSG 23: ゲームをしていくか？
MSG 25: [212][222][222][92]、
MSG 26: [193]ン[208]にやられちゃ
MSG 27: [904][905]あがったりだぜ。
MSG 28: 自信がないなら
MSG 29: 練習でもしてみな
MSG 31: ゲームは１回５００Ｇだぜ。
MSG 34: ゲームで集めたメダルと
MSG 35: アイテムを交換するぜ。
MSG 37: ゲームで損したくなければ
MSG 38: しっかり練習しろよ
MSG 40: ゲームを始めていいか？
MSG 43: おいおい、金が足りねえと
MSG 44: ゲームはできねえぜ。
MSG 46: 残念だな、メダルは
MSG 47: なしだ
MSG 49: ほら、メダルをやるよ
MSG 52: どの景品がほしいんだ？
MSG 55: その景品と
MSG 56: 交換したいのか？
MSG 58: 誰に持たせるんだい？
MSG 61: ほらよ
MSG 64: 持ち物を整理してから
MSG 65: 来てくれよ。
MSG 67: はい
MSG 68: いいえ
MSG 69: 練習をはじめますか？
MSG 70: ゲームをはじめますか？
MSG 71: （１プレイ ５００Ｇ）
MSG 72: メダル [count display]
MSG 73: メダルと景品を
MSG 74: 交換しますか？
MSG 75: 所持金が[ン]足しています
MSG 77: 所持メダル
MSG 78: 必要メダル
MSG 80: を受け取った
MSG 81: メダルが[ン]足しています
MSG 82: それと交換するには
MSG 83: メダルが足りねえぜ
MSG 85: 任務をこなしていません
MSG 86: 所持品がいっぱいです
```
