# Translate Shops/Church Findings

## Summary

Produced `data/translations_shop_church.json` covering three resources:
- **Resource 41** (Church of Salem): 17 entries -- priest Fouquet's healing dialogue
- **Resource 42** (Adventurer's Inn): 13 entries -- innkeeper lodging/rest/level-up dialogue
- **Resource 45** (Vigger Shop): 130+ entries -- shopkeeper Oda's full dialogue for selling, identifying, uncursing, warehouse, orders, branch management, and expansion

## Guide Coverage

The guide (`dumps/guide_full.txt`) does NOT contain direct line-by-line NPC menu dialogue translations. Instead, it provides:
- Story event dialogue (Fouquet's church quest on lines 3297-3686)
- Gameplay mechanic descriptions (Church: lines 9217-9233 for status effects curable at church)
- Location introductions (Inn: line 1676 waitress welcome; Vigger Shop: line 13092 orc welcome)
- Shop system documentation (lines 13097-13660 covering SELL, IDENTIFY, UNCURSE, EXPANSION, ORDERS, WAREHOUSE, BRANCHES, PART-TIME, SHOP MANAGEMENT)

Translations were constructed by matching Japanese menu text semantics against guide terminology.

## Key Guide Anchors Used

| Japanese Term | Guide Term | Guide Line |
|---|---|---|
| サレム教会 | Church of Salem | 1373, 1647 |
| 冒険者の宿 | Adventurer's Inn | 1665, 1675 |
| ヴィガー商店 | Vigger Shop | 9471, 13092 |
| 所持金が不足 | Insufficient gold | Shared across all three |
| 潜在能力が目覚めました | Potential Ability awakened | 1101, 6320 |
| 倉庫 / ソウコ | Warehouse / Storage | 13222, 15077 |
| 支店 | Branch | 13332, 15097 |
| オーダー | Orders | 13271, 13273 |
| 回復 (in shop context) | Identify | 13136 |
| 殿使 (in shop context) | Uncurse | 13139 |
| 地装メニュー | Expansion Menu | 15073 |
| 買取業種 | Buyback Service | 15104 |
| 配送業種 | Shipping Service | 15079 |
| イベント場 | Event Space | 15100 |
| 休けい所 | Resting Room | 15109 |
| 納品 | Deliver | 13292 |
| 依頼人 / 報酬 / 期日 | Client / Reward / Time Limit | 2678, 3299 |

## Confidence Levels

- **CONFIRMED**: 32 entries -- directly matched against guide text or unambiguous (Yes/No, numbers, proper nouns)
- **HIGH**: 155 entries -- strong contextual match with guide terminology and clear Japanese meaning
- **MEDIUM**: 2 entries -- partial uncertainty in exact nuance (order referral/紹棄)

## Notable Observations

1. **Church R41 lines 6-12 are identical**: All seven lines share the same "divine punishment" warning text. The guide confirms the church cures 7 status effects (Poison, Paralysis, Fear, Stone, Dead, Ash, Possessed), one per line.

2. **Vigger Shop "回復" means "Identify"**: In shop context, 回復 (normally "recovery/heal") is used for item identification, not HP recovery. This is confirmed by guide line 13136 describing the IDENTIFY function.

3. **Oda's dialect**: The orc shopkeeper Oda speaks in a rustic Japanese dialect (だよ, だべ, だか endings). Translations preserve this with colloquial English ("ya," "ain't," dropped g's).

4. **Vigger Shop is the largest resource**: R45 has 167 text entries covering the complete shop management system including seasonal sale events (entries 126-138), branch labels for all 10 labyrinth floors (entries 141-150), and the full expansion system.

5. **Shared strings**: "所持金が不足しています" (Insufficient gold), "はい" (Yes), "いいえ" (No) appear identically across R41, R42, and R45.

## Files Produced

- `data/translations_shop_church.json` -- 197 total translation entries across 3 resources
