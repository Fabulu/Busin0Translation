# Inference Pass 2: Resources 2654 and 1053

## Summary

- **Resource 2654** (`2654_type44.bin`): Successfully decoded and analyzed. Contains **34 Alleid Action descriptions** (cooperative combat techniques). Glyph data starts at byte offset 842. Produced **44 new glyph inferences** (24 HIGH, 16 MED, 4 LOW confidence).
- **Resource 1053** (`1053_type03.bin`): **NOT a text resource.** This is a type03 binary file (graphical/texture data, 35200 bytes). The FFFF markers are record separators in a structured data table, not message terminators. No text extraction possible.

## Resource 2654 Content

The 34 messages describe every Alleid Action in the game, matching the English guide's "ALLEID ACTIONS" section. Each message explains:
- Who participates (front row, back row, all members)
- What the action does mechanically
- Limitations (attack count, turn limits)

### Message-to-Alleid Mapping (confirmed via English guide)

| MSG | Alleid Action | Type |
|-----|---------------|------|
| 1 | W-SLASH | Attack |
| 2 | HOLD ATTACK | Attack |
| 3 | STUN SMASH | Attack |
| 4 | BACK ATTACK | Attack |
| 5 | CONCENTRATED ATTACK | Attack |
| 6 | CROSS-GAUGE KILL | Attack |
| 7 | FRONT GUARD | Defense |
| 8 | DENSE FORMATION | Defense |
| 9 | MIRROR IMAGE | Defense |
| 10 | EVASIVE MANEUVER | Defense |
| 11 | BACK COVER | Support |
| 12 | SUPPORT SHOT / INTERCEPT | Support |
| 13 | RESTRICT SHOT | Support |
| 14 | SJ ATTACK (catapult support) | Attack |
| 15 | MAGIC CANCEL | Support |
| 16 | BREATH CANCEL | Support |
| 17 | BACK COVER (variant) | Support |
| 18 | FAKE ATTACK | Attack |
| 19 | CONCENTRATED SPELL | Magic |
| 20 | SILENCE BREAKER / ANTI-MAGIC SHELL | Magic |
| 21 | MAGIC COOPERATION | Magic |
| 22 | ENCHANT | Magic |
| 23 | MAGIC RAPID FIRE | Magic |
| 24 | CONCENTRATED ATTACK (multi-hit) | Attack |
| 25 | SOUL CRASH (back attack combo) | Attack |
| 26 | SONIC SWORD (W-SLASH EX w/ Knight) | Attack |
| 27 | SWEEP ATTACK | Attack |
| 28 | WEAK ATTACK (Hold Attack EX w/ Bishop) | Attack |
| 29 | SACRED CROSS (holy dispel) | Attack |
| 30 | WARP ATTACK | Attack |
| 31 | NIGHTMARE QUAKE (SJ Attack EX w/ Monk) | Attack |
| 32 | GALE SLASH (Conc. Attack EX w/ Knight) | Attack |
| 33 | MULTI-JUMP ATTACK | Attack |

## Glyph Inferences (44 total)

### HIGH Confidence (24)

| Glyph ID | Char | Occurrences | Key Evidence |
|----------|------|-------------|--------------|
| 942 | 衛 | 46x | 前衛/後衛 (front/back row) |
| 583 | 前 | 26x | 前衛 (front row) - duplicate of 510/597 |
| 732 | 後 | 27x | 後衛 (back row), 最後 (end of turn) |
| 279 | 攻 | 44x | 攻め手 (attack move) |
| 293 | 魔 | 31x | 魔法 (magic), 魔王 (magic power) |
| 292 | 法 | 17x | 魔法 (magic spell) |
| 441 | 大 | 9x | 大きなダメージ (big damage) |
| 556 | 与 | 8x | ダメージを与える (deal damage) |
| 592 | 同 | 4x | 同時に (simultaneously) |
| 450 | 武 | 5x | 武器 (weapon) |
| 697 | 器 | 5x | 武器 (weapon) |
| 577 | 受 | 5x | 受ける (receive attack) |
| 536 | 代 | 3x | 代わりに (instead), 身代わり (decoy) |
| 278 | 防 | 3x | 防衛すべき (should be defended) |
| 694 | 強 | 5x | 強力な (powerful), 強制的に (forcefully) |
| 606 | 使 | 3x | 行使 (exercise power) |
| 584 | 全 | 14x | パーティ全員 (all party members) |
| 657 | 振 | 2x | 振るって (swing/brandish weapon) |
| 840 | 唱 | 2x | 唱える (cast/chant spell) |
| 622 | 通 | 2x | 通常攻撃 (normal attack) |
| 795 | 常 | 2x | 通常 (normal/regular) |
| 440 | 退 | 1x | 後退し (retreat) |
| 580 | 消 | 1x | 消えてしまう (disappear) |
| 588 | 的 | 3x | 強制的に (forcefully - adverbial suffix) |

### MEDIUM Confidence (16)

| Glyph ID | Char | Occurrences | Key Evidence |
|----------|------|-------------|--------------|
| 290 | 動 | 15x | 発動 (activate magic) |
| 630 | 避 | 5x | 回避力 (evasion power) |
| 467 | 回 | 21x | 回数 (count), 回避 (evasion) |
| 541 | 限 | 6x | 制限される (be limited) |
| 837 | 制 | 9x | 制限 (restriction/limit) |
| 595 | 効 | 7x | 効果 (effect/result) |
| 790 | 有 | 2x | 有効 (effective) |
| 429 | 上 | 4x | 上げ (raise up) |
| 604 | 味 | 5x | 味方 (ally/companion) |
| 601 | 方 | 6x | 味方 (ally/companion) |
| 479 | 対 | 3x | 対する (regarding/against) |
| 1303 | 囮 | 2x | 囮 (decoy/bait) |
| 600 | 進 | 3x | 進化 (evolution of alleid) |
| 466 | 化 | 6x | 進化 (evolution) |
| 405 | 集 | 2x | 編集 (edit/reorganize) |
| 565 | 力 | 6x | 威力/効力 (power/effectiveness) |

### LOW Confidence (4)

| Glyph ID | Char | Occurrences | Key Evidence |
|----------|------|-------------|--------------|
| 1294 | 存 | 3x | 存在 (existence/presence of class) |
| 701 | 在 | 3x | 存在 (existence) |
| 1257 | 的 | 4x | 標的/対象 (target) |
| 570 | 敵 | 2x | 敵 (enemy) |

## Remaining Unknowns (resource 2654)

The following glyph IDs remain unresolved (insufficient context or conflicting evidence):

- **329, 333** - Appear in class/person references; possibly class names
- **294** - Precedes 罰(=発?); possibly 集 (gather) or 合 (combine)
- **410, 651, 439** - Appear in status effect compound; possibly 状態異常 (status abnormality)
- **442, 690** - Part of とび[442][690] (projectile/thrown weapon compound); possibly 道具 (tool)
- **456, 703** - Appear together in attack positioning; possibly 背後 (behind) or 遠距離 (long range)
- **680, 809, 1100** - Part of defensive stat compounds
- **631, 664, 823** - Appear in effect/result descriptions
- **Many 1x occurrences**: 275, 282, 284, 291, 303, 305, 345, 354, 368, 434, 439, 444, 483, 596, 599, 617, 645, 654, 655, 663, 711, 725, 740, 758, 772, 776, 781, 805, 809, 874, 878, 1018, 1100, 1277

## Observations on Glyph Map

1. **Many duplicates exist**: Glyphs like 前(510/597/583), 後(732), 大(295/441), 力(346/503/565) have multiple glyph IDs mapping to the same character. This is likely because different font pages or text systems in the game use different glyph indices.

2. **Potential gmap corrections**: The existing mapping of 285=罰 may actually be 285=発 based on extensive context (発動=activate is far more common than 罰動 in combat descriptions). Similarly, 614=聞 may be 614=命 (命中=hit rate).

3. **Resource 1053 is non-text**: The type03 format appears to be graphical/binary data with a structured record table. The first bytes contain LE uint32 records (index, size, offset, padding). No glyph decoding is applicable.

## Output Files

- `C:/Programmieren/wizardrytranslation/data/inferred_pass2_r2654_r1053.json` - All 44 inferences in standard format
