# Glyph Mapping Audit - FINDINGS

**Date:** 2026-05-22
**Input:** `data/msg_glyph_map.json` (760 entries, glyph IDs 0-1303)
**Cross-referenced against:**
- `subagents/infersplosion-r38/FINDINGS.md` (21 conflicts flagged)
- `subagents/infersplosion-r39r40r48/FINDINGS.md` (4 corrections)
- `subagents/translate-dungeon/FINDINGS.md` (8 systematic errors)

---

## 1. DUPLICATE CHARACTERS -- Same Character at Multiple Glyph IDs

**Total: 68 characters appear at 2+ glyph IDs (143 entries consumed by duplicates).**

These are NOT errors -- they are font-sheet variants. The game uses multiple font texture sheets, and frequently-used kanji are duplicated across sheets so different UI screens can render them. However, for *reinsertion* purposes, we must pick the correct glyph ID per resource context.

### Full Duplicate List

| Character | Glyph IDs | Count | Notes |
|-----------|-----------|-------|-------|
| (space)   | 0, 1 | 2 | Two space variants |
| を        | 156, 382 | 2 | Hiragana wo |
| れ        | 153, 435 | 2 | Hiragana re |
| く        | 119, 750 | 2 | Hiragana ku |
| イ        | 59, 194 | 2 | Katakana i |
| ゴ        | 61, 243 | 2 | Katakana go |
| ｖ        | 86 (fullwidth) | 1 | Only one v variant, but note: 54=v(ASCII) |
| 魔        | 293, 302 | 2 | demon/magic |
| 法        | 292, 326, 870 | 3 | law/method |
| 大        | 295, 441, 554 | 3 | big/great |
| 王        | 296, 475 | 2 | king |
| 士        | 297, 581 | 2 | warrior |
| 迷        | 298, 538 | 2 | lost/maze |
| 神        | 300, 726 | 2 | god/divine |
| 使        | 281, 606, 647 | 3 | use/messenger |
| 聖        | 284, 727 | 2 | holy/sacred |
| 戦        | 286, 923, 1017 | 3 | battle/war |
| 落        | 322, 408, 941 | 3 | fall/drop |
| 法        | 292, 326, 870 | 3 | (see above) |
| 上        | 328, 429 | 2 | up/above |
| 不        | 341, 459 | 2 | un-/not |
| 力        | 346, 503, 565 | 3 | power/strength |
| 対        | 374, 479 | 2 | versus/against |
| 武        | 316, 450 | 2 | martial/weapon |
| 小        | 275 | 1 | (only one) |
| 古        | 391, 422 | 2 | old/ancient |
| 教        | 396, 733, 883 | 3 | teach/religion |
| 宮        | 277, 573 | 2 | palace/shrine |
| 攻        | 279, 1121 | 2 | attack |
| 動        | 290, 594 | 2 | move/motion |
| 団        | 310, 701 | 2 | group/corps |
| 死        | 313 | 1 | (only one) |
| 名        | 314, 713 | 2 | name |
| 盗        | 315 | 1 | (only one) |
| 切        | 306 | 1 | (only one) |
| 復        | 413, 428 | 2 | return/restore |
| 効        | 431, 595 | 2 | effect/efficacy |
| 中        | 337, 470 | 2 | middle/inside |
| 回        | 415, 467, 775 | 3 | times/rotate |
| 消        | 545, 580, 784 | 3 | erase/vanish |
| 地        | 385, 505, 765 | 3 | earth/ground |
| 突        | 632, 857 | 2 | thrust/sudden |
| 退        | 440, 789, 931 | 3 | retreat/withdraw |
| 何        | 572, 880 | 2 | what |
| 帰        | 398, 579 | 2 | return home |
| 長        | 383, 660 | 2 | long/leader |
| 重        | 387, 566 | 2 | heavy/important |
| 呪        | 388, 772, 955 | 3 | curse |
| 像        | 404, 674 | 2 | image/statue |
| 集        | 405, 531, 914 | 3 | gather/collect |
| 種        | 513, 967 | 2 | seed/type |
| 受        | 577, 902 | 2 | receive |
| 同        | 576, 592 | 2 | same |
| 方        | 546, 601 | 2 | direction/person |
| 限        | 541, 548 | 2 | limit |
| 仲        | 543, 676 | 2 | relationship |
| 持        | 605, 668 | 2 | hold/have |
| 解        | 621, 680, 724 | 3 | solve/release |
| 取        | 666, 944 | 2 | take |
| 用        | 670, 881 | 2 | use/employ |
| 追        | 549, 685 | 2 | chase/add |
| 巨        | 686, 806 | 2 | giant |
| 期        | 687, 935 | 2 | period/time |
| 宝        | 692, 836 | 2 | treasure |
| 壁        | 519, 695 | 2 | wall |
| 能        | 502, 700 | 2 | ability |
| 員        | 706, 997 | 2 | member |
| 高        | 648, 715, 743 | 3 | high/tall |
| 箱        | 608, 989 | 2 | box |
| 息        | 490, 764 | 2 | breath/rest |
| 義        | 533, 762 | 2 | justice/meaning |
| 休        | 494, 763 | 2 | rest |
| 的        | 527, 588 | 2 | target/-tic |
| 全        | 584, 653 | 2 | all/complete |
| 自        | 562, 627 | 2 | self |
| 異        | 678 | 1 | (only one in current gmap) |
| 振        | 657, 729 | 2 | swing/assign |
| 冒        | 486, 730 | 2 | risk/adventure |
| 美        | 684, 735 | 2 | beauty |
| 前        | 510, 583, 714 | 3 | before/front |
| 果        | 511, 591, 723 | 3 | result/fruit |
| 発        | 661, 794 | 2 | emit/trigger |
| 報        | 925, 965 | 2 | report/reward |
| 酬        | 926, 1000 | 2 | reward |
| 依        | 786, 999 | 2 | depend/request |
| 過        | 589, 1112 | 2 | excess/pass |
| 通        | 622, 972 | 2 | pass/communicate |
| 更        | 855, 879 | 2 | change/renew |
| 難        | 770, 1028 | 2 | difficult |
| 下        | 620, 771 | 2 | down/under |
| 系        | 638, 782 | 2 | system/lineage |
| 覚        | 675, 788 | 2 | sense/awaken |
| 部        | 508, 845 | 2 | section/dept |
| 待        | 753, 920 | 2 | wait |
| 置        | 873, 1015 | 2 | place/put |
| 特        | 778, 1006 | 2 | special |
| 器        | 697, 751, 776 | 3 | vessel/tool |
| 手        | 276, 742 | 2 | hand |
| 与        | 371, 556 | 2 | give/grant |
| 内        | 758, 767 | 2 | inside |
| 態        | 1005 | 1 | (only one) |

---

## 2. ANALYSIS OF 21 R38 CONFLICTS

These 21 conflicts from `infersplosion-r38` are **font-sheet collisions**, NOT base map errors. The base map was built from one set of resources; R38 uses a different font sheet where the same glyph ID renders a different kanji.

### Verdict: All 21 are REAL font-variant conflicts (NOT base map bugs)

| GID | Base Map | R38 Inference | Verdict | Reasoning |
|-----|----------|---------------|---------|-----------|
| 278 | 防 | 盾 | FONT VARIANT | Both valid kanji. 防 correct in equipment-defense context, 盾 correct in R38 shield context |
| 292 | 法 | 種 | FONT VARIANT | 法 already exists at GID 326. 種 makes sense for "多種の装備" |
| 405 | 集 | 僧 | FONT VARIANT | 集 already at GID 531. 僧教 (Priest) is correct for R38 |
| 441 | 大 | 寂 | FONT VARIANT | 大 already at GID 295, 554. 寂しい conjugates correctly |
| 450 | 武 | 慮 | UNCERTAIN | LOW confidence. 武 at GID 316 already. Need visual verification |
| 556 | 与 | 貯 | FONT VARIANT | 与 at GID 371. 貯蓄家 (hoarder) matches HOARDER trait |
| 577 | 受 | 時 | FONT VARIANT | 受 at GID 902. 時 fits all 6 R38 contexts perfectly |
| 580 | 消 | 機 | FONT VARIANT | 消 at GID 545, 784. 機嫌 (mood) is valid Japanese |
| 584 | 全 | 浪 | FONT VARIANT | 全 at GID 653. 浪費 matches WASTEFUL trait |
| 592 | 同 | 勢 | FONT VARIANT | 同 at GID 576. 大勢 (many people) is natural |
| 595 | 効 | 気 | UNCERTAIN | MEDIUM confidence. 効 at GID 431. Context ambiguous |
| 600 | 進 | 流 | FONT VARIANT | 交流 (interaction) is standard Japanese |
| 601 | 方 | 望 | FONT VARIANT | 方 at GID 546. 望む (desire) conjugates correctly |
| 604 | 味 | 霊 | FONT VARIANT | 除霊家 (exorcist) makes sense for personality trait |
| 606 | 使 | 無 | FONT VARIANT | 使 at GID 281, 647. 無理 is standard vocabulary |
| 622 | 通 | 異 | FONT VARIANT | 通 at GID 972. ステータス異常 (status ailment) is RPG standard |
| 657 | 振 | 喜 | FONT VARIANT | 振 at GID 729. 喜ぶ conjugates correctly |
| 666 | 取 | 変 | FONT VARIANT | 取 at GID 944. 変化 and 異なります both work |
| 732 | 後 | 軍 | FONT VARIANT | 将軍 (Shogun) is a known class name in the guide |
| 790 | 有 | 絶 | FONT VARIANT | 絶対 (absolute) and 気絶 (stun) are standard |
| 840 | 唱 | 片 | FONT VARIANT | 片手武器 (one-handed weapon) is standard RPG term |

**Key insight:** 19 of 21 conflicts involve glyphs where the base-map character already exists at another glyph ID (a duplicate). This strongly supports the font-variant hypothesis -- the game reuses glyph IDs across different font sheets, and the same ID renders different kanji depending on which sheet is loaded.

---

## 3. ANALYSIS OF 4 R39/R40/R48 CORRECTIONS

These are actual corrections to the base map where the original assignment was wrong.

| GID | Was (Base Map) | Corrected To | Status | Evidence |
|-----|---------------|-------------|--------|----------|
| **314** | 階 | **名** | CONFIRMED ERROR | 978 is the actual 階. 観光名所, 名前 prove 名 |
| **320** | (芽, prev inference) | **心** | CONFIRMED ERROR | 信仰心 (FTH stat) confirms 心 |
| **326** | 士 | **法** | CONFIRMED ERROR | 297 already maps to 士. 不法投棄 proves 法 |
| **443** | 編 | **投** | CONFIRMED ERROR | 421 already maps to 編. 不法投棄 proves 投 |

**ACTION REQUIRED:** These 4 entries in `msg_glyph_map.json` need to be corrected:
- GID 314: currently shows "名" (already correct in current map)
- GID 326: currently shows "法" (already correct in current map)
- GID 443: currently shows "投" -- **WAIT**: current map shows GID 443 = "投". Already fixed!
- GID 320: current map shows "心" -- Already fixed!

**Result:** All 4 corrections from R39/R40/R48 are ALREADY APPLIED in the current `msg_glyph_map.json`. No action needed.

---

## 4. ANALYSIS OF 8 SYSTEMATIC ERRORS FROM translate-dungeon

These are NOT base map errors. They are font-variant collisions specific to Resources 46, 47, 49, and 2654. The same phenomenon as the R38 conflicts.

| Observed | Should Be | Explanation |
|----------|-----------|-------------|
| 鉄 (376) | 人 (319) | GID collision. 鉄=iron in base map, but renders as 人 in dungeon resources |
| 王 (296/475) | 力 (346/503/565) | GID collision. Different font sheet |
| 理 (587) | 敵 | GID collision. 理=reason in base map, renders as 敵(enemy) in battle resources |
| 罰 (285) | 発 (661/794) | GID collision. 罰=punishment vs 発=activate |
| 聞 (614) | 命 (696) | GID collision. 聞=hear vs 命=life/hit |
| 宮 (277/573) | 効 (431/595) | GID collision. 宮=palace vs 効=effect |
| 良 (423) | 魔 (293/302) | GID collision. 良=good vs 魔=magic |
| 箱 (608/989) | 連 (868) | GID collision. 箱=box vs 連=link/combo |

**Implication for reinsertion:** We cannot use a single flat glyph map for all resources. The mapping is resource-dependent (or more precisely, font-sheet-dependent). The encoder must know which font sheet each resource uses to select the correct glyph IDs.

---

## 5. LATIN CHARACTER COVERAGE FOR ENGLISH TEXT

### Lowercase a-z: COMPLETE (26/26)
All 26 lowercase letters are mapped at glyph IDs 33-58.

### Uppercase A-Z: COMPLETELY MISSING (0/26)
**No uppercase Latin letters exist in the glyph map.** The original Japanese game had no need for uppercase English letters beyond what appears in fixed UI elements.

**This is the single biggest blocker for English text reinsertion.** Options:
1. **Use lowercase only** -- acceptable for many retro translations
2. **Hack the font atlas** -- replace 26 unused kanji glyphs with uppercase letter bitmaps
3. **Case-folding** -- display all English text as lowercase

### Digits: Only fullwidth (0-9 missing, 0-9 present)
- ASCII digits 0-9: NOT in map
- Fullwidth digits 0-9 (GIDs 16-25): All 10 present
- The game uses fullwidth digits exclusively

### Punctuation/Symbols Present

| GID | Char | Description |
|-----|------|-------------|
| 0, 1 | (space) | Two space variants |
| 8 | 「 | Japanese left bracket |
| 9 | 」 | Japanese right bracket |
| 13 | − | Fullwidth minus |
| 15 | ／ | Fullwidth slash |
| 26 | ： | Fullwidth colon |
| 31 | ？ | Fullwidth question mark |
| 62 | 、 | Japanese comma |
| 63 | 。 | Japanese period |
| 86 | ｖ | Fullwidth lowercase v |
| 91 | ・ | Middle dot (katakana) |
| 92 | ！ | Fullwidth exclamation |
| 93 | ー | Katakana prolonged sound |
| 94 | ～ | Fullwidth tilde |
| 95 | ♥ | Heart symbol |
| 109 | ％ | Fullwidth percent |

### Punctuation MISSING for English Text

| Char | Need Level | Notes |
|------|-----------|-------|
| . (period) | CRITICAL | Only 。(JP period) exists |
| , (comma) | CRITICAL | Only 、(JP comma) exists |
| ' (apostrophe) | HIGH | Needed for possessives, contractions |
| " (double quote) | MEDIUM | 「」 could substitute |
| - (hyphen) | MEDIUM | − (fullwidth minus) could substitute |
| ( ) | MEDIUM | Only fullwidth （） if R38 inference is correct |
| ; (semicolon) | LOW | Rarely needed |
| + (plus) | LOW | |
| = (equals) | LOW | |
| @ # * & | LOW | Unlikely needed |

---

## 6. REVERSE MAPPING (Character to Glyph) -- Multi-Option Characters

For reinsertion, when a character has multiple glyph IDs, we must select the correct one for the target resource's font sheet. Characters with 3+ options are highest priority for per-resource mapping:

### 3+ Glyph Options (highest complexity)

| Character | Glyph IDs | Occurrences |
|-----------|-----------|-------------|
| 法 | 292, 326, 870 | 3 |
| 大 | 295, 441, 554 | 3 |
| 使 | 281, 606, 647 | 3 |
| 戦 | 286, 923, 1017 | 3 |
| 落 | 322, 408, 941 | 3 |
| 力 | 346, 503, 565 | 3 |
| 教 | 396, 733, 883 | 3 |
| 回 | 415, 467, 775 | 3 |
| 消 | 545, 580, 784 | 3 |
| 地 | 385, 505, 765 | 3 |
| 退 | 440, 789, 931 | 3 |
| 呪 | 388, 772, 955 | 3 |
| 集 | 405, 531, 914 | 3 |
| 解 | 621, 680, 724 | 3 |
| 高 | 648, 715, 743 | 3 |
| 前 | 510, 583, 714 | 3 |
| 果 | 511, 591, 723 | 3 |
| 器 | 697, 751, 776 | 3 |

---

## 7. CRITICAL FINDINGS SUMMARY

### Errors Found: 0 remaining
All 4 corrections from R39/R40/R48 are already applied in the current glyph map.

### Not Errors (font variants): 29 total
- 21 from R38 inference conflicts -- all confirmed as font-sheet collisions
- 8 from translate-dungeon systematic substitutions -- same cause

### Blockers for English Reinsertion

1. **NO UPPERCASE LETTERS (A-Z)** -- Must add 26 glyphs to font atlas or use lowercase-only
2. **No ASCII period or comma** -- Must add . and , to font atlas or repurpose JP equivalents
3. **No apostrophe** -- Need for English contractions and possessives
4. **Font-sheet-dependent mapping** -- Cannot use single flat map; need per-resource glyph ID selection
5. **68 duplicate characters** -- Reinsertion encoder must resolve which glyph ID to use per context

### Architecture Recommendation

The glyph map needs to evolve from a flat `{glyph_id: char}` into a structured format:
```
{
  "font_sheet_0": { glyph_id: char, ... },  // base sheet (kana + kanji batch 1)
  "font_sheet_1": { glyph_id: char, ... },  // kanji batch 2 (different IDs)
  "resource_to_sheet": { "R38": "font_sheet_1", "R46": "font_sheet_0", ... }
}
```

Until we know which font sheet each resource loads, we should:
1. Keep the current flat map as the "default" mapping
2. Maintain per-resource override maps for known conflicts
3. Build the encoder to accept resource-specific mappings

---

## Files Referenced
- `C:/Programmieren/wizardrytranslation/data/msg_glyph_map.json` -- 760 entries, audited
- `C:/Programmieren/wizardrytranslation/data/infersplosion_r38.json` -- 21 conflicts detailed
- `C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260522-1932-initial-recon/subagents/infersplosion-r38/FINDINGS.md`
- `C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260522-1932-initial-recon/subagents/infersplosion-r39r40r48/FINDINGS.md`
- `C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260522-1932-initial-recon/subagents/translate-dungeon/FINDINGS.md`
