# Infersplosion R44 + R45: Second-Pass Inference Report

## Overview

**Date:** 2026-05-22  
**Agent:** infersplosion-r44r45  
**Method:** Second inference pass with 497-entry consolidated glyph map, cross-referenced against English guide (`dumps/guide_full.txt`, latin-1 encoding), prior inferred files (r38-r47), and Japanese RPG domain knowledge.  
**Binary format:** Big-endian uint16, 0xFFFF message terminators, 0xFFFE newlines.

## Resources Decoded

### Resource 44 (0044_type01.bin) - Knight Order / Automata Management
- **File size:** 2306 bytes = 1153 uint16 values
- **Messages:** 58 (pointer table of 58 entries precedes message data)
- **Total glyphs in messages:** 841
- **Unknown glyph IDs:** 45
- **Context:** Alchemy Guild interface for managing Automata (ancient elven combat automatons). Functions include knight order formation, Automata chip creation from cursed equipment, and stat customization.

### Resource 45 (0045_type01.bin) - Vigger Shop
- **File size:** 6950 bytes = 3475 uint16 values  
- **Messages:** 197 (largest resource decoded so far)
- **Total glyphs in messages:** 2443
- **Unknown glyph IDs:** 45
- **Context:** Vigger Shop - the game's item shop run by a girl named Lucy and her orc employees. Functions: sell items, buy items, identify items, uncurse equipment, warehouse management, branch store expansion, order fulfillment, part-time worker hiring, and seasonal events.

## Key Discoveries

### Wizardry Attribute Names (from R44 stat menus)
The Automata stat customization menus (M41-M54) revealed the full Japanese names for all six Wizardry attributes:

| Attribute | Japanese | Glyph IDs | New Inferences |
|-----------|----------|-----------|----------------|
| HP (mhp)  | mhp      | (latin)   | none |
| STR       | 力       | 346       | none (already mapped) |
| INT       | 知恵     | 535, **717** | **717=恵** |
| FTH/WIS   | 信仰心   | 308, **354**, **320** | **354=仰, 320=心** |
| VIT/VIG   | 生命力   | 718, **696**, 346 | **696=命** |
| AGI       | 敏捷度   | **582**, **719**, 590 | **582=敏, 719=捷** |
| LCK       | 幸運度   | 720, **721**, 590 | **721=運** |

### Vigger Shop Commerce Vocabulary (from R45)
The Vigger Shop dialogue, written in heavy rural/orc dialect, revealed core commerce kanji:

| Compound | Meaning | Glyph IDs |
|----------|---------|-----------|
| 売却     | sell/dispose | **905**=売, **1023**=却 |
| 買取     | purchase/buyback | **646**=買 |
| 納品     | deliver goods | **958**=納 |
| 評判     | reputation | **962**=評, **642**=判 |
| 倉庫     | warehouse | **948**=倉, **940**=庫 |
| 拡張     | expansion | **950**=拡, **954**=張 |
| 増設     | extend/add | **947**=増, **873**=設 |
| 支店     | branch store | **402**=支 |
| 業種     | business type | 776=業, **967**=種 |
| 配送     | delivery/shipping | **959**=配, **949**=送 |
| 紹介     | introduction/referral | **434**=紹, **936**=介 |
| 荷物     | luggage/cargo | **933**=荷, 581=物 |
| 客足     | customer traffic | **937**=客 |
| 雇う     | to hire | **699**=雇 |

### Automata Lore Text (R44 M4)
One message describes the Automata in poetic terms, matching the guide's description of them as "legacy of ancient elven civilization, loyal friend and soldier":

```
[遥][古][呪][昔]の[遺][産]。
[歳][月]に[朽]ちぬ、[永][久]き自動人[形]に御用がありますか？
```
"The legacy of ancient times. Do you have business with the eternal automaton that never decays with time?"

### Seasonal Events (R45 M126-138)
The Vigger Shop has seasonal sale events matching real calendar:
- M126: ニューイヤーバーゲン中 (New Year's Bargain)
- M127: ふゆのクリアランス中 (Winter Clearance)
- M128: フレッシュマンセール中 (Freshman Sale)
- M129: サマーバーゲン中 (Summer Bargain)
- M130: なつのホラースペシャル中 (Summer Horror Special)
- M131: 歳末大売出し中 (Year-End Big Sale) -- confirmed **687=末**
- M132: 冒金事チャレンジフェア中 (Adventurer Challenge Fair)
- M133-138: Various 買取解除中 (Buyback Unlock events)

### Glyph 581 Resolution
Previous inferences disagreed on glyph 581:
- R39: 品 (goods)
- R43: 物 (thing)  
- R44 prior: 士 (warrior)

**Resolution:** 581 = **物** (mono = thing/object). R45 provides overwhelming evidence:
- 持ち物 (belongings) - M38, M67, M68
- 品物 (goods) - M26
- 荷物 (luggage) - M68

The R44 prior inference of 士 was based on 騎[581] but this likely read 騎物 which doesn't make sense. The R44 M3 "騎[581]" may be a misparse or the glyph adjacent to 騎 is actually 280=騎 followed by 297=士 (which is already mapped), not 581.

### Conflict Notes

| Glyph | This Inference | Prior Inference | Resolution |
|-------|---------------|-----------------|------------|
| 581   | 物 (HIGH)     | R44:士, R39:品, R43:物 | 物 - R45 evidence is conclusive |
| 852   | 造 (MEDIUM)   | R44:入                 | 造 - fits chip/branch creation; 728=入 already mapped |
| 853   | 勲 (MEDIUM)   | R39:枠                 | 勲 - formation merit resource; both plausible |
| 898   | 杯 (MEDIUM)   | R44:無, R43:杯         | 杯 - いっぱい (full) consistent across resources |
| 723   | 率 (MEDIUM)   | --                     | 率 - rate/percentage in stat contexts |

## Confidence Distribution

- **HIGH confidence:** 35 mappings (42%)
- **MEDIUM confidence:** 33 mappings (40%)
- **LOW confidence:** 15 mappings (18%)
- **Total:** 83 unique glyph IDs inferred

## Output Files

- `data/infersplosion_r44_r45.json` - Complete inference data with evidence
- This file: `FINDINGS.md`
- Intermediate decode files: `_r44_decode.txt`, `_r45_decode.txt` (in project root)
