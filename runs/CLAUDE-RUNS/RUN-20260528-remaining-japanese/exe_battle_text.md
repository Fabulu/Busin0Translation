# EXE Battle System Text Analysis

**Date:** 2026-05-28  
**EXE:** `extracted/SLPM_653.78` (4,185,776 bytes)  
**Scan method:** SJIS pattern search + glyph ID sequence search + MIPS immediate analysis  
**Regions scanned:**  
- `0x3B0000`-`0x3EE9D0` (data section, main)  
- `0x3EE9D0`-`0x3F3500` (debug/TTY section -- explicitly labeled)  
- `0x3F3500`-`0x3FD000` (data section, post-debug)  
- `0x000100`-`0x3B0000` (MIPS code section, for glyph ID immediate values)

---

## Executive Summary

**No player-visible battle text was found hardcoded in the EXE.** All battle display text (enemy names, damage messages, spell names, status effects, victory/defeat messages) comes from MSG resources (R47 for combat encounters, R39 for spell/skill names), not from the EXE. The EXE contains only:

1. **115 debug/TTY battle strings** (0x3EE9D0-0x3F3500) -- printf output to PS2 dev console, invisible to players
2. **3 post-debug TTY strings** referencing battles -- also invisible
3. **Font infrastructure tables** -- glyph ordering, width tables, sort tables; no displayable text
4. **Chargen grid kanji** that include battle-related single characters (攻, 防, 戦, etc.) but these are name-input keyboard data, not rendered battle labels

---

## Detailed Search Results

### A. SJIS Battle Term Search (27 terms tested)

| Term | Japanese | Hits | Region | Verdict |
|------|----------|------|--------|---------|
| attack | 攻撃 | 5 | DEBUG | All in debug printf: "player attack weapon create", "Allied 024/038: focused attack" |
| defend | 防御 | 0 | -- | Not found as SJIS anywhere in EXE |
| evade | 回避 | 0 | -- | Not found |
| hit | 命中 | 0 | -- | Not found |
| damage | ダメージ | 0 | -- | Not found (only ASCII `damage=%d` debug) |
| poison | 毒 | 2 | code | False positive: random byte coincidence in MIPS instructions |
| paralysis | 麻痺 | 0 | -- | Not found |
| petrify | 石化 | 0 | -- | Not found |
| sleep | 睡眠 | 0 | -- | Not found |
| confusion | 混乱 | 0 | -- | Not found |
| flee | 逃走 | 1 | DEBUG | "Allied 050: mass flee" |
| victory | 勝利 | 0 | -- | Not found |
| defeat | 敗北 | 0 | -- | Not found |
| annihilated | 全滅 | 0 | -- | Not found |
| battle | 戦闘 | 3 | DEBUG+data_post | "Debug battle!!", "Guardian battle!!" -- all TTY |
| experience | 経験値 | 0 | -- | Not found |
| death | 死亡 | 0 | -- | Not found |
| revive | 復活 | 0 | -- | Not found |
| spell | 呪文 | 2 | DEBUG | "Allied 019/047: spell concentration formation" |
| magic | 魔法 | 6 | DEBUG | "Monster magic use", "Allied: magic cooperation/rapid-fire" |
| level up | レベルアップ | 0 | -- | Not found |
| game over | ゲームオーバー | 0 | -- | Not found |
| preemptive | 先制攻撃 | 0 | -- | Not found |
| ambush | 不意打ち | 0 | -- | Not found |
| critical | クリティカル | 0 | -- | Not found |
| miss | ミス | 0 | -- | Not found as SJIS |
| guard | ガード | 3 | DEBUG | "Front guard break", "Allied 007/041: front guard" |
| resist | 抵抗 | 1 | DEBUG | "Dispel resist value = %d" |
| effect | 効果 | 56 | DEBUG | All "effect level = %d" debug output |

### B. Glyph ID Sequence Search (19 multi-glyph battle terms)

Searched for consecutive LE uint16 glyph ID patterns in data sections:

| Term | Glyph IDs | Hits | Verdict |
|------|-----------|------|---------|
| attack (攻撃) | [1121, 982] | 0 | Not found |
| defend (防御) | [278, 669] | 0 | Not found |
| evade (回避) | [775, 725] | 0 | Not found |
| hit (命中) | [696, 470] | 0 | Not found |
| damage (ダメージ) | [249, 226, 93, 245] | 0 | Not found |
| miss (ミス) | [224, 205] | 0 | Not found |
| guard (ガード) | [239, 93, 253] | 0 | Not found |
| magic (魔法) | [302, 1386] | 0 | Not found |
| battle (戦闘) | [1190, 1180] | 0 | Not found |
| annihilated (全滅) | [1027, 1032] | 0 | Not found |
| revive (復活) | [1181, 1398] | 0 | Not found |
| poison (毒) | [397] | 5 | All in font ordering tables or chargen grid -- infrastructure, not text |
| action (行動) | [367, 1104] | 0 | Not found |
| critical (クリティカル) | [200, 232, 211, 268, 198, 233] | 0 | Not found |
| preemptive (先制) | [799, 837] | 0 | Not found |
| item (アイテム) | [193, 194, 211, 225] | 0 | Not found |
| level (レベル) | [234, 257, 233] | 0 | Not found |
| turn (ターン) | [208, 93, 238] | 0 | Not found |
| experience (経験) | [779, 1143] | 0 | Not found |

### C. MIPS Code Immediate Value Analysis

Searched for `LI $rX, <glyph_id>` instructions (ADDIU $rX, $zero, imm) in the code section. Battle glyph IDs found as immediates:

| Glyph ID | Character | Refs | Verdict |
|----------|-----------|------|---------|
| 205 (ス) | 1 | Coincidental -- common small integer |
| 224 (ミ) | 62 | Coincidental -- 224 = 0xE0 is extremely common (mask, pixel value, stride) |
| 226 (メ) | 1 | Coincidental |
| 249 (ダ) | 4 | All at 0x38CExx-0x38DAxx, coincidental struct data |
| 301 (石) | 11 | Coincidental -- 301 used as array size/index |
| 696 (命) | 1 | Coincidental |

None of these are actual glyph rendering calls. They are ordinary numeric constants that happen to match glyph ID values. True glyph rendering in this game uses the MSG resource system, not hardcoded immediate values.

---

## Debug Section Battle Strings (0x3EE9D0-0x3F3500)

All 115 battle-related strings in this region are TTY debug output (all end with `\n` newline). Key categories:

### Monster Action Debug (0x3EEF20-0x3EF310)
```
MonsterNo=%d : ATTACK : PlayerNo=%d
MonsterNo=%d : MAGIC
MonsterNo=%d : BREATH
MonsterNo=%d : ESCAPE
MonsterNo=%d : GUARD
MonsterNo=%d : PROJECTILE ATTACK
...
```

### Hit/Damage Calculation Debug (0x3F0980-0x3F0AE0)
```
Attack Player=%d : BaseHit=%d
Attack Monster=%d : BaseHit=%d
Critical Monster=%d : Critical=%d : BaseCritical=%d
Monster Critical !!
```

### Allied Action Debug (0x3F13D0-0x3F34FF)
56 entries for Allied techniques (Wスラッシュ, フロントガード, etc.) with 効果レベル = %d pattern.

### Battle System Debug (0x3F0350-0x3F0860)
```
BattleActionLink : allied_tblno=%d
BattleFontKill : FCD_battle_font
BattleSceneDataRead : texture data kill
```

**Verdict:** All debug. These strings are never rendered on screen -- they go to the PS2 TTY serial console used during development.

---

## Post-Debug Section (0x3F3500-0x3FD000)

3 battle-related Japanese strings found:

| Offset | Text | Type | Player-Visible? |
|--------|------|------|-----------------|
| 0x3F8150 | ガーディアン戦闘！！\n | TTY debug | NO -- ends with \n |
| 0x3F81D0 | 接触！！ : product = %f...\n | TTY debug | NO -- printf format string |
| 0x3FCBC0 | TMLogo BattleSystemLoadEnd... | TTY debug | NO -- ASCII debug |

---

## Where Battle Text Actually Lives

Based on this analysis, all player-visible battle text is in MSG resources:

| Content | Source | Status |
|---------|--------|--------|
| Enemy names | R47 battle encounter messages | Translated |
| Damage/hit messages | R47 battle messages | Translated |
| Spell/skill names | R39 spell/skill table | Translated |
| Status effect names | R47 battle messages | Translated |
| Victory/defeat messages | R47 battle messages | Translated |
| Level up messages | R47 battle messages | Translated |
| Flee messages | R47 battle messages | Translated |
| Battle menu commands (Attack, Defend, etc.) | Menu struct table at 0x3C3000 (Table 2C) | Handled separately |

---

## Action Items

**None for battle text specifically.** The EXE contains zero player-visible hardcoded battle text. All battle display text comes from MSG resources which are already translated.

The only remaining unpatched player-visible string in the entire EXE is:
- `0x3F9678`: Busin 1 save card title "ＢＵＳＩＮ０" (already documented in exe_deep_scan.md)

This is a memory card browser string, not battle-related.
