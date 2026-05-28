# Glyph Map Consolidation Report

**Date**: 2026-05-22
**Sources**: 9 inference agents (r38, r39, r40, r41, r42, r43, r44, r46, r47)

## Summary

- **Mappings before**: 156
- **Mappings after**: 428
- **New mappings added**: 272
- **Corrections applied**: 3
- **Conflicts found**: 25
- **Low-confidence deferred**: 44

## Corrections Applied

| Glyph | Old | New | Reason |
|-------|-----|-----|--------|
| 341 | ン | 不 | r41,r42,r43,r44: fu-soku pattern; 238 already = N katakana |
| 198 | 鍵 | カ | r38 katakana grid; r46 confirms via multiple words |
| 369 | 明 | 見 | r38+r46: mi-tsukete makes sense; mei-tsukete does not |

## Major Additions

### Katakana Grid (193-273)
Complete katakana syllabary: 81 glyphs. Confirmed by r38, r39, r46, r47, r43.

### Latin Lowercase (33-58)
26 lowercase letters a-z. Verified via English reputation tier names (r38).

### Fullwidth Digits (16-25)
Complete digit set 0-9. Confirmed by r38 and r46.

## Conflicts Found and Resolution

| Glyph | Options | Resolution | Reason |
|-------|---------|------------|--------|
| 39 | g(1H/0M), Ｇ(1H/0M) | g | Highest weighted vote |
| 338 | 今(0H/1M), 皆(0H/0M) | 今 | Highest weighted vote |
| 339 | 経(0H/1M), 気(3H/0M) | 気 | Highest weighted vote |
| 340 | 立(1H/0M), 打(0H/1M) | 立 | Highest weighted vote |
| 351 | 除(1H/0M), 散(1H/0M), 化(1H/0M) | 除 | Highest weighted vote |
| 396 | 改(0H/1M), 教(1H/0M) | 教 | Highest weighted vote |
| 415 | 回(2H/0M), 入(1H/0M) | 回 | Highest weighted vote |
| 421 | 編(1H/0M), 合(1H/0M) | 編 | Highest weighted vote |
| 497 | 出(3H/0M), 定(0H/1M) | 出 | Highest weighted vote |
| 500 | 召(1H/0M), 追(0H/1M) | 召 | Highest weighted vote |
| 501 | 喚(1H/0M), 加(0H/1M) | 喚 | Highest weighted vote |
| 507 | 増(0H/1M), 除(1H/0M) | 除 | Highest weighted vote |
| 508 | 部(1H/0M), 編(0H/1M) | 部 | Highest weighted vote |
| 511 | 果(1H/0M), 格(1H/0M) | 果 | Highest weighted vote |
| 550 | 加(1H/0M), 天(1H/0M) | 加 | Highest weighted vote |
| 587 | 認(0H/1M), 理(1H/0M) | 理 | Highest weighted vote |
| 612 | 払(0H/0M), 雙(0H/1M) | 雙 | Highest weighted vote |
| 620 | 下(1H/0M), 得(0H/1M) | 下 | Highest weighted vote |
| 621 | 解(2H/0M), 強(1H/0M) | 解 | Highest weighted vote |
| 661 | 発(1H/0M), 解(0H/1M) | 発 | Highest weighted vote |
| 722 | 属(0H/1M), 獲(1H/0M) | 獲 | Highest weighted vote |
| 728 | 入(1H/0M), 成(1H/0M) | 入 | Highest weighted vote |
| 855 | 更(2H/0M), 換(1H/0M) | 更 | Highest weighted vote |
| 856 | 去(1H/0M), 取(0H/1M) | 去 | Highest weighted vote |
| 911 | 確(0H/1M), 整(1H/0M) | 整 | Highest weighted vote |

### Glyph 341 Resolution

**Previous**: katakana ン -- **New**: kanji 不

- r41,r42,r43,r44 all found 所持金が[341]足 = 不足 (insufficient)
- Glyph 238 already = ン; 459 already = 不 (font variant duplication confirmed)

## Low-Confidence Inferences (deferred)

44 mappings need additional corroboration:

| Glyph | Char | Confidence | Agents |
|-------|------|------------|--------|
| 315 | 盗 | MEDIUM-SINGLE | r47 |
| 316 | 職 | MEDIUM-SINGLE | r39 |
| 320 | 心 | MEDIUM-SINGLE | r42 |
| 338 | 今 | MEDIUM-SINGLE | r41 |
| 344 | 悔 | MEDIUM-SINGLE | r41 |
| 348 | 盾 | MEDIUM-SINGLE | r47 |
| 352 | 養 | MEDIUM-SINGLE | r42 |
| 406 | 封 | MEDIUM-SINGLE | r47 |
| 490 | 用 | MEDIUM-SINGLE | r39 |
| 494 | 休 | MEDIUM-SINGLE | r42 |
| 534 | 感 | MEDIUM-SINGLE | r38 |
| 535 | 忍 | MEDIUM-SINGLE | r39 |
| 581 | 士 | MEDIUM-SINGLE | r44 |
| 605 | 持 | MEDIUM-SINGLE | r39 |
| 610 | 思 | MEDIUM-SINGLE | r38 |
| 612 | 雙 | MEDIUM-SINGLE | r47 |
| 617 | 翌 | MEDIUM-SINGLE | r42 |
| 618 | 考 | MEDIUM-SINGLE | r38 |
| 647 | 使 | MEDIUM-SINGLE | r44 |
| 666 | 異 | MEDIUM-SINGLE | r39 |
| 669 | 御 | MEDIUM-SINGLE | r44 |
| 670 | 用 | MEDIUM-SINGLE | r44 |
| 671 | 身 | MEDIUM-SINGLE | r42 |
| 672 | 日 | LOW | r41 |
| 689 | 潜 | MEDIUM-SINGLE | r42 |
| 702 | 日 | MEDIUM-SINGLE | r42 |
| 706 | 在 | MEDIUM-SINGLE | r42 |
| 720 | 幸 | MEDIUM-SINGLE | r38 |
| 774 | 活 | MEDIUM-SINGLE | r42 |
| 776 | 業 | MEDIUM-SINGLE | r39 |
| 833 | 戻 | MEDIUM-SINGLE | r47 |
| 839 | 下 | MEDIUM-SINGLE | r39 |
| 843 | 場 | MEDIUM-SINGLE | r42 |
| 852 | 入 | MEDIUM-SINGLE | r44 |
| 853 | 勲 | LOW | r44 |
| 857 | 突 | MEDIUM-SINGLE | r47 |
| 858 | 然 | MEDIUM-SINGLE | r47 |
| 886 | 対 | MEDIUM-SINGLE | r41 |
| 887 | 価 | MEDIUM-SINGLE | r41 |
| 898 | 無 | LOW | r44 |
| 913 | 調 | MEDIUM-SINGLE | r44 |
| 928 | 設 | MEDIUM-SINGLE | r44 |
| 959 | 験 | MEDIUM-SINGLE | r39 |
| 997 | 員 | MEDIUM-SINGLE | r47 |

## New Mappings Added

| Glyph | Char | Confidence | Sources |
|-------|------|------------|---------|
| 16 | ０ | CONFIRMED | r38, r46 |
| 17 | １ | CONFIRMED | r38, r46 |
| 19 | ３ | CONFIRMED | r38, r46 |
| 20 | ４ | CONFIRMED | r38, r46 |
| 21 | ５ | CONFIRMED | r38, r46 |
| 22 | ６ | CONFIRMED | r38, r46 |
| 23 | ７ | CONFIRMED | r38, r46 |
| 24 | ８ | CONFIRMED | r38, r46 |
| 25 | ９ | CONFIRMED | r38, r46 |
| 33 | a | HIGH | r38 |
| 34 | b | HIGH | r38 |
| 35 | c | HIGH | r38 |
| 36 | d | HIGH | r38 |
| 37 | e | HIGH | r38 |
| 38 | f | HIGH | r38 |
| 39 | g | HIGH | r38 |
| 40 | h | HIGH | r38 |
| 41 | i | HIGH | r38 |
| 42 | j | HIGH | r38 |
| 43 | k | HIGH | r38 |
| 44 | l | HIGH | r38 |
| 45 | m | HIGH | r38 |
| 46 | n | HIGH | r38 |
| 47 | o | HIGH | r38 |
| 48 | p | HIGH | r38 |
| 49 | q | HIGH | r38 |
| 50 | r | HIGH | r38 |
| 51 | s | HIGH | r38 |
| 52 | t | HIGH | r38 |
| 53 | u | HIGH | r38 |
| 54 | v | HIGH | r38 |
| 55 | w | HIGH | r38 |
| 56 | x | HIGH | r38 |
| 57 | y | HIGH | r38 |
| 58 | z | HIGH | r38 |
| 91 | ・ | HIGH | r38 |
| 92 | ！ | HIGH | r41, r47 |
| 193 | ア | CONFIRMED | r38, r46, r43, r39, r47 |
| 194 | イ | CONFIRMED | r38, r46, r43, r39, r47 |
| 195 | ウ | CONFIRMED | r38, r39, r46 |
| 196 | エ | CONFIRMED | r38, r39, r46 |
| 199 | キ | CONFIRMED | r38, r39, r46 |
| 200 | ク | CONFIRMED | r38, r39, r46 |
| 201 | ケ | CONFIRMED | r38, r39, r46 |
| 202 | コ | CONFIRMED | r38, r39, r46 |
| 203 | サ | CONFIRMED | r38, r39, r46 |
| 204 | シ | CONFIRMED | r38, r39, r46 |
| 205 | ス | CONFIRMED | r38, r39, r46, r47 |
| 206 | セ | CONFIRMED | r38, r39, r46 |
| 207 | ソ | CONFIRMED | r38, r39, r46 |
| 208 | タ | CONFIRMED | r38, r39, r46, r47 |
| 209 | チ | CONFIRMED | r38, r39, r46 |
| 210 | ツ | CONFIRMED | r38, r39, r46 |
| 211 | テ | CONFIRMED | r38, r46, r43, r39, r47 |
| 212 | ト | CONFIRMED | r38, r39, r46 |
| 213 | ナ | CONFIRMED | r38, r39, r46 |
| 214 | ニ | CONFIRMED | r38, r39, r46 |
| 215 | ヌ | CONFIRMED | r38, r39, r46 |
| 216 | ネ | CONFIRMED | r38, r39, r46 |
| 217 | ノ | CONFIRMED | r38, r39, r46 |
| 218 | ハ | CONFIRMED | r38, r39, r46 |
| 219 | ヒ | CONFIRMED | r38, r39, r46 |
| 220 | フ | CONFIRMED | r38, r39, r46 |
| 221 | ヘ | CONFIRMED | r38, r39, r46 |
| 222 | ホ | CONFIRMED | r38, r39, r46 |
| 223 | マ | CONFIRMED | r38, r39, r46 |
| 224 | ミ | CONFIRMED | r38, r39, r46 |
| 225 | ム | CONFIRMED | r38, r46, r43, r39, r47 |
| 227 | モ | CONFIRMED | r38, r39, r46, r47 |
| 228 | ヤ | CONFIRMED | r38, r39, r46 |
| 229 | ユ | CONFIRMED | r38, r39, r46 |
| 230 | ヨ | CONFIRMED | r38, r39, r46 |
| 231 | ラ | CONFIRMED | r38, r39, r46 |
| 232 | リ | CONFIRMED | r38, r39, r46 |
| 233 | ル | CONFIRMED | r38, r46, r43, r39, r47 |
| 234 | レ | CONFIRMED | r38, r46, r43, r39, r47 |
| 235 | ロ | CONFIRMED | r38, r39, r46 |
| 236 | ワ | CONFIRMED | r38, r39, r46 |
| 237 | ヲ | CONFIRMED | r38, r39, r46 |
| 240 | ギ | CONFIRMED | r38, r39, r46 |
| 241 | グ | CONFIRMED | r38, r39, r46 |
| 242 | ゲ | CONFIRMED | r38, r39, r46, r43 |
| 243 | ゴ | CONFIRMED | r38, r39, r46 |
| 244 | ザ | CONFIRMED | r38, r39, r46 |
| 245 | ジ | CONFIRMED | r38, r39, r46 |
| 246 | ズ | CONFIRMED | r38, r39, r46 |
| 247 | ゼ | CONFIRMED | r38, r39, r46 |
| 248 | ゾ | CONFIRMED | r38, r39, r46 |
| 250 | ヂ | CONFIRMED | r38, r39, r46 |
| 251 | ヅ | CONFIRMED | r38, r39, r46 |
| 252 | デ | CONFIRMED | r38, r39, r46, r47 |
| 253 | ド | CONFIRMED | r38, r39, r46 |
| 255 | ビ | CONFIRMED | r38, r39, r46 |
| 256 | ブ | CONFIRMED | r38, r39, r46 |
| 257 | ベ | CONFIRMED | r38, r39, r46, r47 |
| 258 | ボ | CONFIRMED | r38, r39, r46 |
| 259 | パ | CONFIRMED | r38, r39, r46, r47 |
| 260 | ピ | CONFIRMED | r38, r39, r46 |
| 261 | プ | CONFIRMED | r38, r46, r43, r39, r47 |
| 262 | ペ | CONFIRMED | r38, r39, r46, r47 |
| 263 | ポ | CONFIRMED | r38, r39, r46 |
| 264 | ャ | CONFIRMED | r38, r39, r46 |
| 265 | ュ | CONFIRMED | r38, r39, r46 |
| 266 | ョ | CONFIRMED | r38, r39, r46 |
| 267 | ァ | CONFIRMED | r38, r39, r46 |
| 269 | ゥ | CONFIRMED | r38, r39, r46 |
| 270 | ェ | CONFIRMED | r38, r39, r46 |
| 271 | ォ | CONFIRMED | r38, r39, r46 |
| 272 | ッ | CONFIRMED | r38, r39, r46, r47 |
| 285 | 罰 | HIGH | r41 |
| 286 | 戦 | HIGH | r38 |
| 287 | 者 | CONFIRMED | r38, r39, r40, r42 |
| 289 | 悪 | HIGH | r38 |
| 296 | 王 | HIGH | r46 |
| 297 | 士 | HIGH | r38 |
| 300 | 神 | CONFIRMED | r41, r46 |
| 308 | 信 | CONFIRMED | r46, r43 |
| 313 | 死 | HIGH | r46 |
| 319 | 人 | HIGH | r46 |
| 332 | 装 | HIGH | r39, r44 |
| 337 | 中 | HIGH | r38 |
| 339 | 気 | CONFIRMED | r42, r46, r43 |
| 340 | 立 | HIGH | r41 |
| 346 | 力 | CONFIRMED | r42, r38, r41, r47 |
| 349 | 女 | HIGH | r46 |
| 350 | 得 | HIGH | r44 |
| 351 | 除 | HIGH | r39 |
| 366 | 影 | HIGH | r44 |
| 367 | 行 | CONFIRMED | r39, r46, r44 |
| 370 | 成 | CONFIRMED | r39, r47 |
| 371 | 与 | HIGH | r44 |
| 374 | 対 | HIGH | r44 |
| 377 | 滅 | HIGH | r46 |
| 379 | 転 | CONFIRMED | r40, r43 |
| 396 | 教 | HIGH | r46 |
| 401 | 侍 | HIGH | r38 |
| 413 | 復 | HIGH | r46 |
| 414 | 子 | HIGH | r46, r44 |
| 415 | 回 | CONFIRMED | r46, r43 |
| 419 | 金 | CONFIRMED | r42, r41, r43, r44 |
| 421 | 編 | HIGH | r39 |
| 428 | 復 | HIGH | r39 |
| 431 | 効 | HIGH | r44 |
| 443 | 編 | HIGH | r44 |
| 486 | 冒 | CONFIRMED | r42, r40, r46 |
| 487 | 険 | CONFIRMED | r42, r40 |
| 491 | 登 | HIGH | r40 |
| 492 | 録 | HIGH | r40 |
| 496 | 所 | CONFIRMED | r42, r41, r43, r44 |
| 497 | 出 | CONFIRMED | r42, r46, r47 |
| 498 | 新 | CONFIRMED | r42, r47 |
| 500 | 召 | HIGH | r40 |
| 501 | 喚 | HIGH | r40 |
| 502 | 能 | HIGH | r40 |
| 503 | 力 | HIGH | r40 |
| 504 | 職 | HIGH | r40 |
| 506 | 削 | HIGH | r40 |
| 507 | 除 | HIGH | r40 |
| 508 | 部 | HIGH | r39 |
| 511 | 果 | HIGH | r44 |
| 516 | 性 | HIGH | r46 |
| 517 | 業 | HIGH | r40 |
| 520 | 善 | HIGH | r38 |
| 529 | 交 | HIGH | r43 |
| 538 | 迷 | HIGH | r46 |
| 543 | 仲 | HIGH | r39 |
| 544 | 間 | HIGH | r39 |
| 546 | 方 | HIGH | r42, r41 |
| 548 | 限 | HIGH | r46 |
| 549 | 追 | HIGH | r40 |
| 550 | 加 | HIGH | r40 |
| 552 | 分 | HIGH | r43 |
| 553 | 屋 | HIGH | r42 |
| 562 | 自 | HIGH | r43 |
| 572 | 何 | CONFIRMED | r39, r47 |
| 573 | 宮 | HIGH | r46 |
| 574 | 探 | HIGH | r46 |
| 575 | 索 | HIGH | r46 |
| 586 | 安 | HIGH | r42 |
| 587 | 理 | HIGH | r43 |
| 591 | 果 | HIGH | r47 |
| 602 | 備 | HIGH | r39, r44 |
| 603 | 品 | CONFIRMED | r43, r44 |
| 608 | 箱 | HIGH | r47 |
| 613 | 許 | HIGH | r38, r47 |
| 619 | 習 | HIGH | r43 |
| 620 | 下 | HIGH | r41 |
| 621 | 解 | CONFIRMED | r39, r44 |
| 634 | 来 | HIGH | r44 |
| 635 | 頼 | HIGH | r43 |
| 653 | 全 | HIGH | r46, r47 |
| 656 | 誰 | HIGH | r39 |
| 660 | 長 | HIGH | r46 |
| 661 | 発 | HIGH | r42 |
| 662 | 目 | HIGH | r42 |
| 668 | 持 | CONFIRMED | r42, r43, r44, r41, r39, r47 |
| 675 | 覚 | HIGH | r42 |
| 682 | 功 | CONFIRMED | r39, r47 |
| 685 | 追 | HIGH | r47 |
| 693 | 今 | HIGH | r39, r44 |
| 700 | 能 | HIGH | r38, r42 |
| 707 | 選 | CONFIRMED | r39, r40, r44 |
| 708 | 択 | CONFIRMED | r39, r40, r44 |
| 709 | 必 | CONFIRMED | r39, r40, r41, r43 |
| 710 | 要 | CONFIRMED | r39, r40, r41, r43 |
| 712 | 足 | CONFIRMED | r42, r41, r43, r44, r39 |
| 713 | 名 | HIGH | r40 |
| 714 | 前 | HIGH | r40 |
| 715 | 高 | HIGH | r40 |
| 716 | 低 | HIGH | r40 |
| 718 | 生 | HIGH | r38 |
| 722 | 獲 | HIGH | r44 |
| 728 | 入 | HIGH | r39 |
| 730 | 冒 | HIGH | r46 |
| 737 | 決 | HIGH | r39, r44 |
| 742 | 手 | HIGH | r41 |
| 749 | 言 | HIGH | r46 |
| 767 | 内 | HIGH | r39 |
| 768 | 容 | HIGH | r39 |
| 773 | 結 | HIGH | r47 |
| 775 | 回 | HIGH | r39 |
| 780 | 響 | HIGH | r44 |
| 786 | 依 | HIGH | r43 |
| 797 | 離 | HIGH | r40 |
| 798 | 脱 | HIGH | r40 |
| 800 | 替 | HIGH | r39 |
| 834 | 治 | HIGH | r41 |
| 842 | 宿 | HIGH | r42 |
| 844 | 泊 | HIGH | r42 |
| 845 | 部 | HIGH | r42 |
| 846 | 空 | HIGH | r42 |
| 849 | 恐 | HIGH | r47 |
| 850 | 怖 | HIGH | r47 |
| 851 | 十 | HIGH | r41 |
| 854 | 組 | CONFIRMED | r39, r44 |
| 855 | 更 | CONFIRMED | r39, r44 |
| 856 | 去 | HIGH | r41 |
| 859 | 逃 | HIGH | r47 |
| 867 | 助 | HIGH | r41 |
| 876 | 錠 | HIGH | r47 |
| 879 | 更 | HIGH | r40 |
| 880 | 何 | HIGH | r41 |
| 881 | 用 | HIGH | r41 |
| 883 | 教 | HIGH | r41 |
| 884 | 会 | HIGH | r41 |
| 888 | 奉 | HIGH | r41 |
| 889 | 達 | HIGH | r41 |
| 890 | 越 | CONFIRMED | r42, r41 |
| 891 | 療 | HIGH | r41 |
| 892 | 頼 | CONFIRMED | r41, r46 |
| 899 | 掲 | HIGH | r46 |
| 900 | 板 | HIGH | r46 |
| 901 | 引 | HIGH | r43 |
| 902 | 受 | HIGH | r43 |
| 904 | 商 | HIGH | r46 |
| 906 | 練 | HIGH | r43 |
| 908 | 残 | HIGH | r39, r43 |
| 909 | 念 | HIGH | r43 |
| 910 | 景 | HIGH | r43 |
| 911 | 整 | HIGH | r43 |
| 920 | 待 | HIGH | r44 |
| 925 | 報 | HIGH | r44 |
| 926 | 酬 | HIGH | r44 |
| 927 | 続 | HIGH | r44 |
| 929 | 作 | HIGH | r44 |
| 931 | 退 | HIGH | r44 |
| 935 | 期 | HIGH | r46 |
| 946 | 情 | HIGH | r46 |
| 956 | 店 | HIGH | r46 |
| 965 | 報 | HIGH | r46 |
| 978 | 階 | HIGH | r46 |
| 1014 | 書 | HIGH | r46 |