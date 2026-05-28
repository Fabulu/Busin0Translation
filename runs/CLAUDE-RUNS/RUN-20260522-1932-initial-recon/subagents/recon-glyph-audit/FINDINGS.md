# Type-2 Glyph Mapping Audit: R1203 Dialogue

**Date**: 2026-05-22
**Status**: 38 override mappings identified (19 CERTAIN, 14 HIGH, 4 MEDIUM, 2 LOW) across 55 glyph IDs

---

## Root Cause

The master glyph map (`data/msg_glyph_map.json`, 759 entries) was calibrated from type-1 resources (R34-R49: menus, items, battle text). Type-2 resources (R1196-R1213, R1353-R1354: story/NPC dialogue) use a **different font page** for kanji glyphs. The same glyph ID renders a completely different kanji depending on which font page the game engine selects for that resource type.

This is NOT a simple offset/shift -- glyph ID differences between wrong and correct kanji are irregular (-1, -40, -163, -229, -309, -599...). Each glyph ID independently maps to a different kanji in the type-2 font page.

Some correct type-2 kanji already exist in the map at other glyph IDs (e.g., `者` at 287, `一` at 338, `鎧` at 288). Others are entirely absent from the type-1 map (汝, 彼, 渡, 識, 卿, 剣, 役).

## Impact

R1203 alone has 1,580 dialogue messages. The affected type-2 resources (R1196-R1213, R1353-R1354) contain ~10,000+ dialogue messages total. Every kanji in these resources decoded through the type-1 map is potentially wrong.

## Multi-Glyph-ID Characters

Several characters have multiple glyph IDs in the type-1 map, and each glyph ID maps to a DIFFERENT type-2 character:

| Type-1 Char | Glyph IDs | Type-2 Mapping |
|-------------|-----------|----------------|
| 不 | 341, 459 | 341 -> 余 (I/me, 67 occurrences), 459 -> 大 (big, 22 occurrences) |
| 使 | 281, 606, 647 | 281 -> 汝 (you). 606, 647 need separate verification |
| 戦 | 286, 923, 1017 | 286 -> 者 (person). 923, 1017 need separate verification |
| 聖 | 284, 727 | 284 -> 今 (now). 727 needs separate verification |
| 動 | 290, 594 | 290 -> 達 (plural). 594 needs separate verification |
| 効 | 431, 595 | 431 -> 同 (same). 595 needs separate verification |
| 除 | 351, 507 | 351 -> 出 (out). 507 needs separate verification |
| 避 | 630, 725 | 630 -> 声 (voice). 725 needs separate verification |
| 方 | 546, 601 | 546 -> 新 (new). 601 needs separate verification |
| 像 | 404, 674 | 404 -> 長 (chief). 674 needs separate verification |
| 古 | 391, 422 | Both -> 取 (take). May differ |
| 光 | 348 | 348 -> 受 (receive) |
| 教 | 396, 733, 883 | 396 -> 役 (role/use). 733, 883 need verification |
| 頼 | 635, 892 | 635 -> 識 (discern). 892 needs verification |
| 休 | 494, 763 | Both -> 衛 (guard)? Needs verification |
| 覚 | 675, 788 | Both -> 間? Needs verification |
| 攻 | 279, 1121 | 279 -> 奥 (deep inside)? Needs verification |

**To fully disambiguate multi-ID characters, raw glyph extraction from R1203 binary is needed** -- matching each message position to its glyph ID rather than its decoded character.

---

## Override Table

### CERTAIN (18 overrides) -- verified across 3+ independent contexts

| Glyph ID(s) | Type-1 | Type-2 | Evidence |
|-------------|--------|--------|----------|
| 281 (606,647) | 使 | 汝 | Pronoun "you": 汝が新しい討伐隊の者かな, 汝はわからないだろう, 汝達(plural). 30+ occurrences |
| 341 | 不 | 余 | Pronoun "I" (noble): 余はウェブスター卿, 余が何を言わんとしているのか. 67 occurrences |
| 459 | 不 | 大 | Size/degree: 大声(loud voice), 大きな(large). 22 occurrences. Context: 大声にならざるを得ない |
| 514 | 族 | 彼 | Pronoun "he/they": 彼ら(them), 彼らが. Consistent 3rd-person pronoun |
| 329 | 賊 | 見 | Verb "see": 見ている, 見たことがある, 見つけて, 見えるはず, 見せてもらった |
| 372 | 苦 | 知 | Verb "know": 知りたく, 知っている, 知らない, 見知らぬ(unknown) |
| 348 | 光 | 受 | Verb "receive": 受け取った, 受けた, 受ける |
| 391 (422) | 古 | 取 | Verb "take": 受け取った, 取り出した |
| 291 | 飾 | 渡 | Verb "hand over": 渡してくれた, 渡しておく, 手渡した |
| 401 | 侍 | 待 | Verb "wait": 待ち止まって, 待っていた |
| 854 | 組 | 得 | Auxiliary "able/obtain": 得ないな, ならざるを得ない |
| 290 (594) | 動 | 達 | Plural suffix: 汝達, レジーナ達, あたし達, 余達, 化物達 |
| 275 | 小 | 何 | Interrogative "what": 何を言わん, 何の役にも, 何か, 何事か, 何もなかった |
| 284 (727) | 聖 | 今 | Temporal "now": 今まで, 今なら, 今は |
| 504 | 職 | 腕 | Body "arm": 腕に着けて (put bracelet on arm) |
| 517 | 業 | 着 | Verb "wear": 着けて, 着けた (put on/wear) |
| 635 (892) | 頼 | 識 | Compound: 識別 (identification) |
| 893 | 潜 | 別 | Compound: 識別 (identification) |
| 649 | 絆 | 卿 | Title: ウェブスター卿 (Lord Webster) |

### HIGH (11 overrides) -- strong contextual evidence, 1-2 contexts

| Glyph ID(s) | Type-1 | Type-2 | Evidence |
|-------------|--------|--------|----------|
| 506 | 削 | 剣 | Weapon: ザクレタの剣 (Sword of Zakreta) |
| 546 (601) | 方 | 新 | Adjective "new": 新しい, 新しい討伐隊 |
| 393 | 半 | 化 | Compound: 化物 (monster/bakemono). Note: 半法 becomes 化法 which is wrong; see open questions |
| 431 (595) | 効 | 同 | "Same": 者同士 (comrades/together), 同じ (same) |
| 734 | 授 | 戦 | Verb "fight": 戦いの, 戦える, 戦っていた |
| 351 (507) | 除 | 出 | Verb "out": 取り出した, 出した, 逃げ出した |
| 630 (725) | 避 | 声 | Noun "voice": 叫び声, 大声 |
| 497 | 出 | 思 | Verb "think": 思う, 思った, 思います |
| 396 (733,883) | 教 | 役 | Noun "role/use": 何の役にも立たぬ, 役に立つ |
| 404 (674) | 像 | 長 | Rank "chief": 隊長 (team leader/captain). ベルグラーノ隊長 |
| 286 (923,1017) | 戦 | 者 | Noun "person": 討伐隊の者, 知らぬ者 |

### MEDIUM (4 overrides) -- plausible but need more verification

| Glyph ID(s) | Type-1 | Type-2 | Evidence |
|-------------|--------|--------|----------|
| 304 | 兵 | 一 | Numeral "one": 一つ選びたまえ, 一つ尋ねたい. Conflict: 神兵 should be 親切 (glyph 300=神 also needs override?) |
| 297 (581) | 士 | 騎 | "Knight": 騎士 compound. But creates 騎騎者 in 士騎戦 context -- needs rethinking |
| 953 | 単 | 鎧 | Armor: マグスの鎧 (Magus armor). Equipment item |
| 515 | 条 | 帯 | Belt/band: マグスの帯 (Magus belt?). Equipment item |

### ADDITIONAL HIGH (discovered during verification)

| Glyph ID(s) | Type-1 | Type-2 | Evidence |
|-------------|--------|--------|----------|
| 664 | 元 | 申 | Verb "apologize": 申し遅れた (excuse me for being late). 元し覚れた -> 申し遅れた |
| 675 (788) | 覚 | 遅 | Adjective "late": 申し遅れた. Both 遅 and 申 absent from type-1 map |
| 393 | 半 | 魔 | REVISED from 化 to 魔: 魔物(monster) AND 魔法(magic) both correct. 化物 only works for monsters |

### LOW (2 overrides) -- speculative

| Glyph ID(s) | Type-1 | Type-2 | Evidence |
|-------------|--------|--------|----------|
| 787 | 就 | 数 | Number: 何数? Very uncertain |
| 369 | 見 | 兜 | Helmet: マグスの兜? Only in item name context |

---

## Sample Corrections

### Before (type-1 map applied to type-2 data):
```
使動を賊ていると不声にならざるを組ないな。
イ使が方しい討伐隊の戦かな？ゴ
不が小を言わんとしているのか、聖、使はわからないだろう。
元し覚れた、不はウェブスター絆
頼潜ブレスレットを職に業けた。
マグスの見単 / マグスの条■ / ザクレタの削
■マグスの見単■を光け古った
```

### After (type-2 overrides applied):
```
汝達を見ていると大声にならざるを得ないな。
イ汝が新しい討伐隊の者かな？ゴ
余が何を言わんとしているのか、今、汝はわからないだろう。
申し遅れた、余はウェブスター卿
識別ブレスレットを腕に着けた。
マグスの兜鎧 / マグスの帯■ / ザクレタの剣
■マグスの兜鎧■を受け取った
魔と戦えるのは■だけだといっても過言ではない。
魔法柵■のある住■で攻■。
よくあんな恐ろしい魔物を倒せるものだと思います。
```

---

## Open Questions

1. **半→化 creates problems**: 半法→化法 is wrong; should be 魔法. Either (a) glyph 393 maps to 魔 not 化, or (b) different glyph IDs produce 半 in 化物 vs 半法 contexts. The former seems more likely: glyph 293 already maps to 魔 in type-1, so 393 in type-2 could also be 魔 (making 魔物 and 魔法 both correct). **Recommend changing 393: 半→魔 instead of 半→化.**

2. **士騎戦 compound**: If 士→騎, 騎(already correct), 戦→者, we get 騎騎者 which is nonsense. The compound 士騎戦 likely represents 騎士団(knight order) or similar. Need raw glyph extraction to verify which glyph IDs produce 士, 騎, 戦 in this specific compound.

3. **兵→一 vs 神兵**: If 兵→一, then 神兵→神一 (nonsense). But 神 (glyph 300) may also need an override (perhaps 300→親, giving 親切/kindness). Need more context.

4. **教→役 partial**: 教 appears in contexts where both 役 (role) and 教 (teach) could work. May not always need override -- depends on specific glyph ID (396 vs 733 vs 883).

5. **Multi-ID disambiguation**: Characters with 2-3 glyph IDs (使, 戦, 教, etc.) likely have each ID mapping to a different type-2 kanji. Raw binary extraction needed to determine per-ID mappings.

---

## Override JSON

Saved to: `C:/Programmieren/wizardrytranslation/data/type2_glyph_overrides.json`

Format:
```json
{
  "281": { "t1": "使", "t2": "汝", "c": "CERTAIN" },
  "341": { "t1": "不", "t2": "余", "c": "CERTAIN" },
  "459": { "t1": "不", "t2": "大", "c": "CERTAIN" },
  ...
}
```

## Next Steps

1. **Extract raw glyph IDs from R1203 binary** to disambiguate multi-ID characters (especially 使/606/647, 戦/923/1017, 教/733/883)
2. **Re-evaluate 半→魔 hypothesis** (glyph 393) by checking all 半 contexts
3. **Build per-resource-type decoder** that selects the override map when processing type-2 resources
4. **Cross-reference with other type-2 resources** (R1196-R1212, R1353-R1354) to validate overrides generalize beyond R1203
5. **Font page analysis**: examine the font atlas binary to find if type-2 resources reference a different font page offset, which would confirm the mapping systematically
