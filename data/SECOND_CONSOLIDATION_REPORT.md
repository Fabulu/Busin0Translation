# Second Consolidation Report

**Date**: 2026-05-22
**Previous count**: 428 mappings
**Final count**: 492 mappings (+64 new, 1 correction)

## Sources Merged

Eight inference agents that completed after the first consolidation:

| Agent | Resource | Context | Claimed Inferences |
|-------|----------|---------|-------------------|
| infer-r38 | 0038_type01 | Character creation, class descriptions | 123 |
| infer-r39 | 0039_type15 | Party management menus | 38 katakana + 33 kanji |
| infer-r40 | 0040_type01 | Adventurer's Guild UI | 116 |
| infer-r41 | 0041_type01 | Church of Salem dialogue | 42 |
| infer-r43 | 0043_type01 | Bar Luna Light tavern | 57 |
| infer-r44 | 0044_type01 | Knight Order management | 49 |
| infer-r46 | 0046_type03 | Tavern bulletin board | 204 |
| infer-r47 | 0047_type03 | Battle/treasure system | 48 |

## Corrections Applied

| Glyph | Old Value | New Value | Reason | Flagged By |
|-------|-----------|-----------|--------|------------|
| 198 | カ (already) | カ | Katakana grid position 5; sequential with neighbors | r38, r46 (was corrected in first pass) |
| 341 | 不 (already) | 不 | 不足 context in multiple resources | first pass |
| 358 | し | **外** | MSG 30/32/33/62/70 all require 外(hazusu=remove from party) | r40 |
| 369 | 見 (already) | 見 | 見つけて/見た/見てきた contexts | r38, r46 (was corrected in first pass) |

Only glyph 358 needed correction in this pass (し to 外). The other three corrections (198, 341, 369) had already been applied during the first consolidation.

## New Mappings Added (64 total)

### By Category

- **Kanji**: ~50 new kanji mappings
- **Symbols/Special**: ~5 (hyphen, space variant, etc.)
- **Font variant duplicates**: ~9 (same character at different glyph IDs)

### Notable New Kanji

| Glyph | Char | Meaning | Corroborating Agents |
|-------|------|---------|---------------------|
| 276 | 手 | hand | r39, r46 |
| 309 | 忍 | endure/ninja | r46 |
| 315 | 盗 | steal | r47 |
| 328 | 上 | up/above | r46 |
| 338 | 一 | one | r46 |
| 355 | 殺 | kill | r46 |
| 397 | 毒 | poison | r46 |
| 398 | 帰 | return | r46 |
| 505 | 地 | earth/ground | r40 |
| 534 | 感 | feel | r38, r46 |
| 535 | 知 | know | r46 |
| 578 | 街 | town/street | r46 |
| 590 | 度 | degree/time | r46 |
| 605 | 持 | hold (variant) | r39 |
| 610 | 思 | think | r38, r46 |
| 612 | 払 | pay | r41 |
| 647 | 使 | use (variant) | r39, r44, r46 |
| 698 | 終 | end | r39 |
| 702 | 日 | day/sun | r46 |
| 705 | 現 | present/appear | r46 |
| 720 | 幸 | happiness | r38, r46 |
| 765 | 地 | earth (variant) | r46 |
| 766 | 年 | year | r46 |
| 771 | 下 | below | r46 |
| 833 | 戻 | return | r47 |
| 860 | 忘 | forget | r46 |
| 969 | 了 | complete | r39 |
| 972 | 通 | pass through | r46 |
| 997 | 員 | member | r46, r47 |
| 999 | 依 | depend/request | r46 |
| 1012 | 顔 | face | r46 |

### Font Variant Duplicates Confirmed

The game font atlas stores the same character at multiple glyph IDs (different font sheets/sizes):
- 505/765 = 地, 579/398 = 帰, 605/668 = 持, 647/281 = 使
- 706/997 = 員, 670/881 = 用, 510/714 = 前

## Skipped Mappings

- **195 mappings** were already present in the master map with matching values
- **Many LOW-confidence** single-agent inferences were not merged (require corroboration)
- **Conflicting inferences** between agents (e.g., glyph 351: 除 vs 散 vs 化) kept master's existing value

## Coverage Summary

| Category | Count |
|----------|-------|
| Hiragana | 83 |
| Katakana | 85 |
| Kanji | 280 |
| Latin lowercase | 26 |
| Fullwidth digits | 10 |
| Symbols/punctuation | 6 |
| Other (spaces) | 2 |
| **Total** | **492** |

## Remaining Work

- ~500+ glyph IDs remain unmapped (estimated from high-frequency unknowns)
- Spell incantation text (r47 MSGs 54-61) contains many unmapped poetic kanji
- Knight order stat category labels use low-range glyph IDs (33-58) that overlap with Latin
- Some single-agent MEDIUM inferences could be promoted with additional resource analysis
