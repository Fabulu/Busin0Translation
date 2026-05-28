# Infersplosion R49 + R46: Second Inference Pass

**Date:** 2026-05-22
**Base mapping:** 497 entries (msg_glyph_map.json)
**Method:** Parse BE uint16 glyph streams, contextual inference + guide cross-reference

## Resources Analyzed

| Resource | Type | Content | Messages | Glyphs | Unknowns Before | Inferred |
|----------|------|---------|----------|--------|-----------------|----------|
| 0049_type01.bin | type01 | Dungeon exploration text | 111 | 1150 | 39 | 35 |
| 0046_type03.bin | type03 | Tavern bulletin board | 153 | 1367 | 30 | 24 |

**Total new inferences:** 52 unique glyph mappings (some shared between resources)

## R49 - Dungeon Exploration Text

Resource 49 contains environmental descriptions shown when exploring Karman's Labyrinth. Messages describe obstacles, interactable objects, treasure chests, traps, stairs, and environmental details.

### HIGH Confidence Inferences (R49)

| Glyph | Char | Compound | Evidence |
|-------|------|----------|----------|
| 275 | 小 | 小さな (small) | MSG100: 小さなふくろが落ちている |
| 291 | 飾 | 飾られている (displayed) | MSG15,16,88,104: statues/equipment displayed |
| 317 | 炎 | 炎 (fire/flames) | MSG77: 炎が道をふさいでいる; MSG80: 炎がもえ上がって |
| 322 | 落 | 落ちている (fallen) | MSG100: 落ちている; also R46 落ち着け |
| 404 | 像 | 像 (statue) | MSG15,82-84: 女神の団像, 不気味な像 (variant of 674) |
| 422 | 古 | 古びた (aged) | MSG11: 古びたタルが (aged barrel) |
| 561 | 色 | 金色/銀色 (gold/silver color) | MSG101,102,109: key and plate colors |
| 581 | 士 | 騎士 (knight) | MSG108: 騎士の顔の像 (variant of 297/326) |
| 609 | 欠 | 欠けた (chipped) | MSG16,107: 欠けた団像 |
| 641 | 込 | 飛び込め (jump in) | MSG33: とび込めそう; also R46 書き込む |
| 664 | 元 | 足元 (at one's feet) | MSG13: 足元にがい骨が |
| 672 | 体 | 死体 (corpse) | MSG90: 死体がよこたわっている |
| 735 | 美 | 美しい (beautiful) | MSG94,110: 美しい祠/さいだん |
| 759 | 形 | 人形/形 (figure/shape) | MSG20: 人形; MSG25: 変わった形の壁 |
| 796 | 罠 | 罠 (trap) | MSG38: の罠がしかけられています |
| 799 | 先 | 先 (ahead) | MSG28: 階段の先が行きどまり |
| 836 | 宝 | 宝箱 (treasure chest) | MSG34-37,52 (variant of 692) |
| 873 | 置 | 装置/置かれて (device/placed) | MSG17,26,30: 装置, 置かれている |
| 918 | 遠 | 遠くに (in the distance) | MSG78: 遠くに階段が見える |
| 952 | 派 | 立派 (splendid) | MSG88: 立派な装備品が飾られている |
| 957 | 穴 | 穴 (hole) | MSG76: とびおりられそうな穴がある |
| 979 | 段 | 階段 (stairs) | MSG28-30,56,57,78,81 |
| 984 | 議 | 不思議 (mysterious) | MSG85: 不思議な形の像が |
| 989 | 箱 | 宝箱 (treasure chest) | MSG34-37,52 (variant of 608) |

### R49 Decoded Sample Messages (with new mappings)

```
MSG  0: 特に変わったところはない (Nothing particularly unusual)
MSG  5: カギがかかっている (It's locked)
MSG  7: ハシが上がっていて通れない (Bridge is raised, can't pass)
MSG 12: 目の前にがい骨が転がっている (Bones rolling in front of you)
MSG 15: 女神の団像が飾られている (Goddess group statue is displayed)
MSG 29: 階段がある (There are stairs)
MSG 34: 宝箱を開けますか？ (Open the treasure chest?)
MSG 38: の罠がしかけられています (A trap is set)
MSG 76: とびおりられそうな穴がある (There's a hole you could jump down)
MSG 78: 遠くに階段が見える (Stairs visible in the distance)
MSG 85: 不思議な形の像が (A mysteriously shaped statue)
MSG 88: 立派な装備品が飾られている (Splendid equipment is displayed)
MSG 90: 死体がよこたわっている (A corpse is lying there)
```

## R46 - Tavern Bulletin Board

Resource 46 contains the message board messages at the Bar Luna Light tavern. Citizens of Duhan post gossip, quest hints, and commentary about events in the game.

### HIGH Confidence Inferences (R46)

| Glyph | Char | Compound | Evidence |
|-------|------|----------|----------|
| 304 | 兵 | 兵士 (soldier) | MSG31,77: 兵士団がまた殺されて |
| 494 | 休 | お休み (break/rest) | MSG85/138: お休みします |
| 536 | 存 | 生存 (survival) | MSG76: 王女さま生存の知らせで |
| 560 | 好 | 好き (like) | MSG32: ゴーモンが好きらしい |
| 589 | 過 | し過ぎた (overdid) | MSG61/101: コーフンし過ぎた |
| 598 | 着 | 落ち着け (calm down) | MSG69: ほんとに落ち着けって |
| 690 | 番 | 一番 (number one/most) | MSG25: 一番古い |
| 697 | 市 | 市民 (citizen) | MSG1,80: 市民のみなさま |
| 790 | 絶 | 気絶 (faint) | MSG37: 気絶させられると |
| 801 | 記 | 日記 (diary) | MSG28,47: シムゾンの日記には |
| 966 | 民 | 市民 (citizen) | MSG1,80: 市民のみなさま |
| 1002 | 倒 | 倒した (defeated) | MSG71/118: ウェブスターを倒したヤツが |

### R46 Decoded Sample Messages (with new mappings)

```
MSG  1: この度、ドゥーハン市民のみなさまが (This time, citizens of Duhan...)
MSG 28: シムゾンの日記には、地下８階まで (In Simson's diary, down to B8F...)
MSG 32: 騎女はゴーモンが好きらしい (The female knight seems to like Gomon)
MSG 37: 気絶させられるとキビシイので (If made to faint, it's tough)
MSG 69: ジジイほんとに落ち着けって (Old man, really calm down!)
MSG 71: ７階でウェブスターを倒したヤツが (The one who defeated Webster on B7F)
MSG 76: 王女さま生存の知らせで (With news of the princess's survival)
```

## Variant Glyphs Discovered

The game font uses multiple glyph slots for the same kanji. This pass discovered 7 new variant pairs:

| Primary | Variant | Character | Notes |
|---------|---------|-----------|-------|
| 692 | 836 | 宝 (treasure) | R49 dungeon font variant |
| 608 | 989 | 箱 (box) | R49 dungeon font variant |
| 674 | 404 | 像 (statue) | R49 dungeon font variant |
| 297,326 | 581 | 士 (warrior) | Third variant slot |
| 310 | 701 | 団 (group) | R46 bulletin board variant |
| 767 | 758 | 内 (inside) | R46 variant |
| 286 | 1017 | 戦 (battle) | R46 variant |

## Remaining Unknowns

**R49 (4 remaining):** 26, 107 (likely menu/control codes in MSG53), 829 (LOW: possibly 獣=beast), 933 (LOW: possibly 鉱=ore)

**R46 (4 remaining):** 320, 468, 678, 793 - insufficient context for confident inference

## Output Files

- `data/infersplosion_r49_r46.json` - Full inference results with confidence levels and evidence
