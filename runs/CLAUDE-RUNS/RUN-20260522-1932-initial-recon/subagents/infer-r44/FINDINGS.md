# Resource 0044 (type01) Inference Findings

## Resource Identity

**File**: `extracted/packdata_resources/0044_type01.bin` (2306 bytes)
**Content**: Knight Order (騎士団) management interface UI text
**Messages**: 115 messages total, containing NPC dialogue, menu prompts, error messages, and stat category labels
**Unknown glyphs**: 128 distinct glyph IDs not in `msg_glyph_map.json`

## Summary of Inferences

**49 glyphs inferred** from contextual analysis:
- 30 HIGH confidence (strong contextual evidence from multiple messages)
- 16 MEDIUM confidence (single strong context or reasonable deduction)
- 3 LOW confidence (speculative)

Output saved to: `data/inferred_r44.json`

## HIGH Confidence Mappings (30)

| Glyph | Char | Key Evidence |
|-------|------|-------------|
| 350 | 得 | 獲得 (acquisition) - repeated pattern |
| 351 | 散 | 解散 (disband) |
| 366 | 影 | 影響を与えます (affects) |
| 367 | 行 | 変更を行う (carry out changes); もう行かれるのですか |
| 371 | 与 | 与えます (to give) in 影響を与えます |
| 374 | 対 | に対する/に対して (regarding) |
| 419 | 金 | 所持金 (money on hand) |
| 421 | 合 | 組み合わせ (combination); 合隊 (party merge) |
| 431 | 効 | 効果 (effect) |
| 443 | 編 | 騎士団を編成する (organize the knight order) |
| 496 | 所 | 所持 (possess) in 所持金/所持品 |
| 511 | 果 | 効果 (effect) |
| 603 | 品 | 所持品がいっぱいです (inventory is full) |
| 621 | 解 | 解散 (disband/dissolve) |
| 634 | 来 | よく来てくださいました (welcome) |
| 668 | 持 | お持ちですか (do you have?); 所持 (possess) |
| 707 | 選 | 選んでください (please select) |
| 708 | 択 | 選択してください (please select) |
| 712 | 足 | 足りません (not enough) - msgs 94, 96 |
| 722 | 獲 | 獲得する (acquire treasure) |
| 728 | 成 | 編成 (formation); 作成 (create) |
| 780 | 響 | 影響 (influence) |
| 854 | 組 | 組み合わせ (combination) |
| 855 | 更 | 変更 (change/modification) |
| 920 | 待 | お待ちしておりました (we've been waiting) |
| 925 | 報 | 報酬 (reward) from treasure |
| 926 | 酬 | 報酬 (reward/compensation) |
| 927 | 続 | 続けますか (will you continue?) |
| 929 | 作 | 作成しますか (will you create?) |
| 931 | 退 | 退隊しました (has been discharged) |

## MEDIUM Confidence Mappings (16)

| Glyph | Char | Key Evidence |
|-------|------|-------------|
| 319 | 何 | 何かに御用がありますか (do you have business?) |
| 332 | 装 | 装備品 (equipment items) |
| 414 | 子 | 調子はどうですか (how is the condition?) |
| 497 | 定 | 設定する (to configure) |
| 500 | 追 | 追加できるメンバー (members who can be added) |
| 501 | 加 | 追加 (addition) |
| 581 | 士 | 騎士 - likely size variant of glyph 326=士 |
| 602 | 備 | 装備 (equipment) |
| 647 | 使 | 使いますか (will you use?); may be variant of 281=使 |
| 669 | 御 | 御用 (business, formal) |
| 670 | 用 | 御用 (business/errand) |
| 693 | 今 | 今すぐ (right now) |
| 737 | 決 | 決して (never/absolutely) |
| 852 | 入 | 入隊 (enlist); 入りましょう (let's join) |
| 913 | 調 | 調子 (condition) |
| 928 | 設 | 設定 (setting/configuration) |

## LOW Confidence Mappings (3)

| Glyph | Char | Key Evidence |
|-------|------|-------------|
| 338 | 皆 | 皆無のようです (seems to be none) |
| 853 | 勲 | くん (merit/medal) as formation resource |
| 898 | 無 | 皆無 (none at all) |

## Resource Content Structure

The 115 messages break down into these functional groups:

1. **Msgs 0-17**: NPC greeting/farewell dialogue at the order management desk
2. **Msgs 18-26**: System explanation - how order formation works (editing, パワーアップ, etc.)
3. **Msgs 27-38**: Treasure/reward system explanations (報酬獲得, 影響, 効果)
4. **Msgs 39-58**: Formation flow prompts (select knights, confirm, continue)
5. **Msgs 59-82**: Order management actions (disband, modify, select items)
6. **Msgs 83-84**: Yes/No dialog options
7. **Msgs 85-97**: Error/status messages (inventory full, insufficient funds/items)
8. **Msgs 98-113**: Category/stat labels for order modifications (7 types with their names)

## Key Game Terms Identified

- **騎士団** (knight order) - the organizational unit being managed
- **編成** (formation) - creating/organizing orders
- **入隊/退隊** (enlist/discharge) - adding/removing knights
- **合隊** (merge) - combining party elements
- **解散** (disband) - dissolving an order
- **変更** (change) - modifying order properties
- **オーダー** (order) - katakana loanword, 6 chars: オー???ー (3 unknown katakana)
- **報酬獲得** (reward acquisition) - from treasure
- **効果** (effect) / **影響** (influence) - stat effects

## Unresolved Issues

1. **Katakana mapping**: ~14 katakana glyph IDs (193, 194, 205, 208, 209, 211, 212, 223, 225, 236, 246, 259, 261, 272) remain unmapped. The MSG katakana encoding uses non-sequential IDs that do not follow the name-entry katakana table pattern. The word "オー[212][223][208]ー" (6-char katakana word) appears throughout but cannot be decoded without more katakana anchor points.

2. **Potential glyph map error**: Glyph 341 is mapped as ン in msg_glyph_map.json, but in msg 73 the phrase "所持金がン足しています" should read "所持金が不足しています" (insufficient funds). This suggests 341 may not be ン, or there is a rendering issue. The katakana size-4 table places 341 as タ.

3. **Stat category labels** (msgs 98-113): Seven categories are listed by name for order modifications (e.g., [45][40][48], [346], [535][717], etc.). The low-numbered glyphs (40, 45, 48, 52, 53) may be ASCII-like characters or game-specific symbols. These likely correspond to Busin 0's order stat types.

4. **Formation resource**: "く[853]" (msgs 7, 44, 91, 94) is a consumable resource for forming orders. Tentatively identified as 勲 (merit/medal) but the reading pattern is unusual.

5. **Duplicate kanji IDs**: Glyphs 581 (士?) and 647 (使?) appear to be size variants of already-mapped kanji 326=士 and 281=使. This suggests the font system has multiple renderings of the same character at different glyph IDs.
