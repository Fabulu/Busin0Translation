# Inferred Glyph Mappings for Resource 0040_type01.bin

## Context

Resource 40 is the **Adventurer Guild party management UI** in Busin 0 (Wizardry Alternative Neo).
84 messages covering: welcome, party composition, registration, class change,
delete member, party join/withdraw, sort options, error messages.

## Statistics

- Total messages: 84
- Total inferred glyphs: 116
- Remaining unknowns: 0
- HIGH confidence: 29
- MEDIUM confidence: 28
- LOW confidence: 59

## Correction to Existing Map

**Glyph 358**: Existing map has し (shi) but context proves it should be 外 (hazusu = remove).
Evidence: MSG 30/32/33/62/70 all require 外.
e.g. MSG 33: リーダーはパーティから外せません (leader cannot be removed from party).

## Key Vocabulary

| Japanese | Reading | Glyph IDs | Meaning |
|----------|---------|-----------|---------|
| パーティ | paatii | 259+93+211+268 | Party |
| リーダー | riidaa | 232+93+249+93 | Leader |
| 冒険者 | boukensha | 486+487+287 | Adventurer |
| 登録 | touroku | 491+492 | Registration |
| 転職 | tenshoku | 379+504 | Class change |
| 削除 | sakujo | 506+507 | Delete |
| 召喚 | shoukan | 500+501 | Summon |
| 選択 | sentaku | 707+708 | Select |
| 追加 | tsuika | 549+550 | Addition |
| 離脱 | ridatsu | 797+798 | Withdrawal |
| 変更 | henkou | 652+879 | Change |
| 職業 | shokugyou | 504+517 | Occupation |
| 必要 | hitsuyou | 709+710 | Necessary |
| 名前 | namae | 713+714 | Name |
| 高レベル | kou reberu | 715+234+257+233 | High level |
| 低レベル | tei reberu | 716+234+257+233 | Low level |
| 能力 | nouryoku | 502+503 | Ability |
| ステータス | suteetasu | 205+211+93+208+205 | Status |

## Methodology

1. Decoded resource 40 using known glyph map (msg_glyph_map.json)
2. Cross-referenced with English guide (guide_full.txt) Adventurer Guild section
3. Guide menu items: WITHDRAW FROM PARTY, CHANGE NAME, DELETE REGISTERED MEMBER,
   CHANGE CLASS, SORT (alphabetical, highest/lowest level, occupation)
4. Used Japanese compound word patterns, particles, verb conjugations
5. Verified consistency across all 84 messages
6. Identified correction to existing map (glyph 358)

## Decoded Messages

```
MSG   0: [NULL]
MSG   1: ようこそ、冒険者よ 
MSG   2: [NULL]
MSG   3: [NULL]
MSG   4: 今のパーティ構成の
MSG   5: 冒険者登録を開いてやろう
MSG   6: [NULL]
MSG   7: [NULL]
MSG   8: おや、もう帰て行くのか？
MSG   9: [NULL]
MSG  10: [NULL]
MSG  11: ‘冒険召喚‘
MSG  12: 能力ステータス
MSG  13: 転職
MSG  14: 地階
MSG  15: 召喚削除
MSG  16: パーティ追加
MSG  17: パーティ離脱
MSG  18: 転職を行います。
MSG  19: その人を転職させる
MSG  20: 該当はありません。
MSG  21: 級前の転職日から[NUM][VAR]経過経
MSG  22: していないため、転職を完了できません。
MSG  23: 冒険者登録から階級を削除します。
MSG  24: 削除先は一緒と装に外せません。
MSG  25: リーダーの
MSG  26: 召喚削除はできません。
MSG  27: その人を削除する
MSG  28: 該当はありません。
MSG  29: 冒険に追加済の人は、
MSG  30: まずパーティから外してください。
MSG  31: パーティメンバーに加えます。
MSG  32: パーティメンバーから外します。
MSG  33: リーダーはパーティから外せません。
MSG  34: 階級を変更します。
MSG  35: その人の階級を変更する
MSG  36: 該当はありません。
MSG  37: 他員と同じ職業を
MSG  38: 選択しています。
MSG  39: 転職に必要なスロッが
MSG  40: ンプしています。
MSG  41: 条件が合わないため
MSG  42: 転職できません。
MSG  43: に転職しますか？
MSG  44: に転職しました。
MSG  45: 本当に削除して
MSG  46: よろしいですか？
MSG  47: 入れ替えるメンバーを
MSG  48: 選択してください。
MSG  49: パーティ並替
MSG  50: [LABEL][VAR]名前
MSG  51: 高レベル前
MSG  52: 低レベル前
MSG  53: 職業前
MSG  54: パーティメンバーを並替順に
MSG  55: 替順に並べます。
MSG  56: 階級の[LABEL][VAR]名前に並べます。
MSG  57: 高レベルの者から前に並べます。
MSG  58: 低レベル前の者から前に並べます。
MSG  59: 職業（遅い／速い／早速い）前に
MSG  60: 並べます。
MSG  61: 転職する職業を選択してください。
MSG  62: 魔石は全て外されます。
MSG  63: 使われている壁は転職できません。
MSG  64: 使いの魔石を殿いてください。
MSG  65: ＬボタンかＲボタンをおすと
MSG  66: 早送り頭へ物ります。
MSG  67: スロッと条件があわないため
MSG  68: 転職できません。
MSG  69: リーダーが動けないため
MSG  70: 隠壁を外せません。
MSG  71: ヒナ
MSG  72: リ鍵ルン
MSG  73: ワレワワ
MSG  74: ルア
MSG  75: サラ
MSG  76: パーティリーダーです。
MSG  77: 冒険者登録より召喚された人です。
MSG  78: あなたのパーティに、とちゅうから
MSG  79: 加入された人です。
MSG  80: 特召喚のため、冒険に隠壁を
MSG  81: 召喚することができます。
MSG  82: 芽のめばえていないオートマターは
MSG  83: 現在緒／パーティランクがありません
```

