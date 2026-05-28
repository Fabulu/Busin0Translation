# Resource 0041 Inference Findings

## Location Identified: Church of Salem (サレム教会)

Resource `0041_type01.bin` (1000 bytes, 18 messages) contains the **Church of Salem service NPC dialogue** in Busin 0 (Wizardry Alternative Neo).

## Evidence for Identification

- MSG 1-2: Greeting pattern "ここはサレム教会" (This is Salem Church) and "サレム教会へようこそ" (Welcome to Salem Church)
- MSG 14: "治療を頼みますか？" (Will you request healing?) -- core church service
- MSG 15-16: はい / いいえ (Yes / No) -- standard RPG service menu
- MSG 5-12: Archaic priestly language with そなた (thou), であろう (shall), ねば (must) -- matches the Church of Salem priest Fouqet's characterization in the English guide as having a "very interesting personality"
- MSG 6-12: Seven identical copies of a threatening sermon about divine punishment (天罰) -- one per party member slot

## Message Translations

| MSG | Japanese (decoded) | English Translation |
|-----|-------------------|---------------------|
| 0 | (blank/padding) | (empty) |
| 1 | ここはサレム教会。!何用な方が 今日どんな消息で？ | This is Salem Church. What business brings you? What news today? |
| 2 | サレム教会へようこそ。おや、お手の助けが 必要なようですな。 | Welcome to Salem Church. Oh my, it seems you need some help/assistance. |
| 3 | 助けを必要とされる方は どなたですかな。 | Who is the one in need of help? |
| 4 | では、おがサレム教会に 必要なだけの対価を いただきましょうか。 | Well then, shall we receive sufficient compensation for Salem Church? |
| 5 | 十分な対価金も[支払]せず 神のお力にすがろうとは! [悔改]め、立ち去るがよい | Without paying sufficient compensation, you dare cling to God's power! Repent and leave! |
| 6-12 | 神への対価を奉らねば そなた達は必ず 天罰を下られるであろう。 | If you do not offer compensation to God, you shall certainly receive divine punishment. |
| 13 | お手の助けが必要になれば いつでも対価を[支払]して お越しくだされ。 | When you need assistance, pay the compensation and please come visit anytime. |
| 14 | 治療を頼みますか？ | Will you request healing? |
| 15 | はい | Yes |
| 16 | いいえ | No |
| 17 | 所持金がン分しています | Held money is [in]sufficient (note: glyph 341 mapped as katakana ン but context suggests 不 for 不足) |

## Inferred Glyph Mappings (42 total)

### HIGH Confidence (27 mappings)

| Glyph ID | Char | Reading | Compound Word | Evidence |
|----------|------|---------|---------------|----------|
| 0 | (space) | - | padding/null | 66.5% of all glyph occurrences |
| 203 | サ | sa | サレム (Salem) | Katakana in location name |
| 225 | ム | mu | サレム (Salem) | Katakana in location name |
| 234 | レ | re | サレム (Salem) | Katakana in location name |
| 285 | 罰 | batsu | 天罰 (divine punishment) | Paired with 550=天 |
| 300 | 神 | kami | 神 (God) | Church theological context |
| 340 | 立 | tatsu | 立ち去る (leave) | Godan verb tachisaru |
| 346 | 力 | chikara | お力 (power, hon.) | 神のお力にすがる |
| 419 | 金 | kin/kane | 対価金, 所持金 | Money/payment for church services |
| 490 | 息 | soku | 消息 (news/tidings) | Paired with 545=消 |
| 546 | 方 | kata | 方 (person, hon.) | Honorific "person/one" |
| 550 | 天 | ten | 天罰 (divine punishment) | Paired with 285=罰 |
| 620 | 下 | kudasu | 天罰を下す (hand down) | Passive: 下られる |
| 709 | 必 | hitsu/kanarazu | 必要, 必ず | Necessary / certainly |
| 710 | 要 | you | 必要 (necessary) | Always paired with 709 |
| 712 | 分 | bun | 十分 (sufficient) | Paired with 851=十 |
| 742 | 手 | te | 手助け (assistance) | Paired with 867=助 |
| 834 | 治 | chi/ji | 治療 (healing) | Paired with 891=療 |
| 851 | 十 | juu | 十分 (sufficient) | Paired with 712=分 |
| 856 | 去 | saru | 立ち去る (leave) | 去る = to leave |
| 867 | 助 | jo/tasuke | 助け (help) | 手助け, 助け |
| 880 | 何 | nani | 何用 (what business) | Paired with 881=用 |
| 881 | 用 | you | 何用 (what business) | Paired with 880=何 |
| 883 | 教 | kyou | 教会 (church) | Duplicate of confirmed glyph 733 |
| 884 | 会 | kai | 教会 (church) | Paired with 883=教 |
| 888 | 奉 | tatematsuru | 奉る (dedicate/offer) | Godan: 奉らねば |
| 889 | 達 | tachi | 達 (plural marker) | そなた達 = you all |
| 890 | 越 | koshi | お越し (visit, hon.) | お越しくだされ |
| 891 | 療 | ryou | 治療 (healing) | Paired with 834=治 |
| 892 | 頼 | tanomu | 頼む (request) | 頼みますか |

### MEDIUM Confidence (8 mappings)

| Glyph ID | Char | Reading | Notes |
|----------|------|---------|-------|
| 92 | ! | - | Sentence-end emphasis; could also be a different punctuation |
| 338 | 今 | ima/kon | In greeting context, possibly 今日 (today) |
| 344 | 悔 | kui | Imperative "repent" context |
| 396 | 改 | aratame | Part of 悔い改める (to repent) |
| 496 | 所 | sho | 所持金 (held money) |
| 668 | 持 | ji/mochi | 所持金 (held money) |
| 885 | お | o | Honorific prefix |
| 886 | 対 | tai | 対価 (compensation) |
| 887 | 価 | ka | 対価 (compensation) |

### LOW Confidence (2 mappings)

| Glyph ID | Char | Reading | Notes |
|----------|------|---------|-------|
| 287 | 締 | shime? | Unknown in imperative clause; could be part of 引き締める or similar |
| 672 | 日 | hi/nichi | Tentative; in greeting context |
| 612 | 払 | harai | 支払 (payment) - but conflicts with 490=息 in 消息 context |

## Open Issues

1. **Glyph 490 dual-use**: Appears as 消[490] (likely 消息=news) in MSG 1 and as [490][612]する (likely 支払する=to pay) in MSG 5/13. Cannot be the same kanji in both contexts. Either 490=息 or 490=支; further cross-resource evidence needed.

2. **Glyph 341 (confirmed ン) in MSG 17**: `所持金がン分しています` is grammatically broken. Context strongly suggests this should read `所持金が不足しています` (insufficient funds), implying either 341=不 (contradicting confirmed mapping) or a different message parsing.

3. **Glyph 287**: Still unknown. Appears only in MSG 5 line 3 in `[344][396][287]め、立ち去るがよい`. The phrase seems to be an imperative command related to repentance.

4. **Glyph 885**: Mapped tentatively as お (honorific) but this would be unusual as a separate glyph since hiragana お=116 is already mapped in the base set. Could be a kanji like 御 (go/on, formal honorific prefix).

5. **MSG 6-12 duplicate**: Seven identical copies suggest per-party-member display of the priest's refusal/warning when payment is insufficient.

## Cross-Reference with English Guide

The guide describes the Church of Salem priest Fouqet as having a "very interesting personality" that makes people avoid his commissions. The threatening tone of MSG 5-12 (demanding payment, threatening divine punishment, telling people to leave) perfectly matches this characterization. The church offers healing services (治療) for a price (対価).

## Output Files

- `data/inferred_r41.json` -- full inference results with decoded messages
- `build/infer_r41_map.json` -- inference mapping used by decode script
- `build/infer_r41.py` -- decode script
- `build/r41_decoded.txt` -- initial raw decode output
