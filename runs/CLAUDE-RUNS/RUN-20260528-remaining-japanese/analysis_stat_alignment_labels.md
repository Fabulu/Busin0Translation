# Analysis: Stat Labels, Alignment Labels, and the Fighter/Neutral Anomaly

**Date**: 2026-05-28
**Source**: R38 (PACKDATA resource 0038_type01.bin, 7512 bytes)
**EXE Table 2B**: 0x3C83C0-0x3C93A0 (chargen kana grid, NOT the label table)

---

## CRITICAL FINDING: The Labels Are NOT in the EXE

The stat/alignment/race/class labels are stored in **PACKDATA resource 38 (R38)**, NOT in the EXE at Table 2B. Table 2B (0x3C83C0-0x3C93A0) contains the **chargen kana display grid** (hiragana/katakana keyboard for name entry), not UI labels.

R38 is a type-01 MSG resource using the standard glyph-index format (BE uint16 stream, FFFE terminators).

---

## R38 Structure Overview

| Offset Range | Entry IDs | Category | Count | Notes |
|-------------|-----------|----------|-------|-------|
| 0x000-0x2F0 | - | Glyph palette/header | 376 glyphs | Font definition area |
| 0x2F0-0x30A | 0 | HP label | 1 | `[7492]hp` (7492 = bitmap glyph?) |
| 0x2FA-0x340 | 1-7 | **Stat labels** | 7 | hp/mhp, STR, INT, FTH, VIT, AGI, LCK |
| 0x340-0x39E | 8-17 | Chargen field labels | 10 | Name, Level, Race, Gender, etc. |
| 0x39E-0x3E4 | 18-24 | Spell level labels | 7 | lv1 through lv7 |
| 0x3E4-0x3F0 | 25-26 | Gender | 2 | Male, Female |
| 0x3F0-0x404 | 27-28 | World names | 2 | Io, Europa |
| 0x404-0x454 | 29-34 | **Race labels** | 6 | Human, Elf, Gnome, Dwarf, Hobbit, Automater |
| 0x454-0x4DE | 35-52 | **Class labels** | 18 | Fighter through Thief-Beauty |
| 0x4DE-0x632 | 53-86 | **Personality traits** | 34 | Used for chargen personality system |
| 0x632-0x0E50 | 87-144 | Personality descriptions | 58 | Long text explaining each personality |
| 0x0E50-0x1268 | 145-166 | Race/alignment descriptions | 22 | Chargen help text |
| 0x1268-0x1A70 | 167-218 | Class descriptions | 52 | Chargen help text |
| 0x1AB6-0x1AFC | 220-228 | **Alignment labels** | 9 | Good/Neutral/Evil in multiple formats |
| 0x1B02-0x1D58 | 229-257 | **Reputation labels** | 29 | Already in English lowercase! |

---

## Stat Labels (Entries 1-7)

| Entry | Offset | Glyph IDs | Japanese | English Target |
|-------|--------|-----------|----------|----------------|
| 1 | 0x2FA | 40,48,15,45,40,48 | hp/mhp | HP/MHP |
| 2 | 0x30A | 346 | 力 | STR |
| 3 | 0x310 | 535,717 | 知恵 | INT |
| 4 | 0x318 | 308,354,320 | 信仰心 | FTH |
| 5 | 0x322 | 718,696,346 | 生命力 | VIT |
| 6 | 0x32C | 582,719,590 | 敏捷度 | AGI |
| 7 | 0x336 | 720,721,590 | 幸運度 | LCK |

**Patching plan**: Replace glyph IDs with lowercase ASCII equivalents (a=33..z=58):
- STR: s=51, t=52, r=50 (3 glyphs, fits in 3-glyph slot)
- INT: i=41, n=46, t=52 (3 glyphs, fits in 2-glyph slot -- NEED to check if expandable)
- FTH: f=38, t=52, h=40 (3 glyphs, fits exactly)
- VIT: v=54, i=41, t=52 (3 glyphs, fits exactly)
- AGI: a=33, g=39, i=41 (3 glyphs, fits exactly)
- LCK: l=44, c=35, k=43 (3 glyphs, fits exactly)

**Problem**: Only lowercase a-z are in the glyph map (IDs 33-58). No uppercase A-Z. Labels will render as "str", "int", etc.

---

## Alignment Labels (Entries 220-228)

| Entry | Offset | Glyph IDs | Text | Purpose |
|-------|--------|-----------|------|---------|
| 220 | 0x1AB6 | 520,8,39,9 | 善「g」 | Good with abbreviation |
| 221 | 0x1AC2 | 337,340,8,46,9 | 中立「n」 | Neutral with abbreviation |
| 222 | 0x1AD0 | 289,8,37,9 | 悪「e」 | Evil with abbreviation |
| 223 | 0x1ADC | 520 | 善 | Good (standalone) |
| 224 | 0x1AE2 | 337,340 | 中立 | Neutral (standalone) |
| 225 | 0x1AEA | 289 | 悪 | Evil (standalone) |
| 226 | 0x1AF0 | 39 | g | Good abbreviation letter |
| 227 | 0x1AF6 | 46 | n | Neutral abbreviation letter |
| 228 | 0x1AFC | 37 | e | Evil abbreviation letter |

**Key insight**: The alignment system uses THREE formats:
1. Full kanji + abbreviation letter in brackets: 善「g」
2. Standalone kanji: 善
3. Single letter abbreviation: g/n/e

The letters g/n/e are already ASCII lowercase glyph IDs (39/46/37). These ARE rendered via the standard glyph system.

**Glyph 520 is mapped to 枚**: This is a glyph map error. Glyph 520 should be 善 (good), not 枚 (counter for flat objects). Same issue as glyph 511 (mapped to 果 but should be 性).

---

## The "Fighter" and "Neutral" Anomaly -- DEBUNKED

**Finding: Neither "Fighter" nor "Neutral" appears in English anywhere in the game data.**

- "Fighter" does NOT exist as ASCII text in the EXE or any PACKDATA resource
- "Neutral" does NOT exist as ASCII text in the EXE or any PACKDATA resource
- The class label for Fighter is entry 35: glyph IDs [286, 581] = 戦士 (Japanese kanji)
- The alignment "Neutral" is entry 224: glyph IDs [337, 340] = 中立 (Japanese kanji)

**What the user likely saw**:
- The alignment **abbreviation letter "n"** on the status screen -- this IS English, but it's just a single letter, not the word "Neutral"
- Class names in the original Wizardry series (the PS2 remake may mix English and Japanese UI elements from the original game's design)
- Or possibly a different region/version of the game

**What IS in English**: The reputation/fame labels (entries 230-257) are ALREADY stored as English lowercase text using the standard glyph system:
- commoner, hooligan, evil, venom fang, villain, gangster, cruelty, vicious, dangerous, curiosity, adventurer, guard, boldness, bravery, famous, veteran, conqueror, hero, queen guard, honest person, kind, reliable, great heart, fairness, noble, achievement, sage, god hand

These prove the engine CAN render multi-character English text using glyph IDs 33-58 (a-z). The reputation labels work because they only use lowercase letters, which are in the font atlas.

---

## Race Labels (Entries 29-34)

| Entry | Offset | Glyph IDs | Japanese | English Target |
|-------|--------|-----------|----------|----------------|
| 29 | 0x404 | 319,519 | 人間* | human |
| 30 | 0x40C | 196,233,220 | エルフ | elf |
| 31 | 0x416 | 217,93,225 | ノーム | gnome |
| 32 | 0x420 | 248,235,93,220 | ドワーフ | dwarf |
| 33 | 0x42C | 222,255,272,212 | ホビット | hobbit |
| 34 | 0x438 | 197,93,212,224,208,93 | オートマター | automater |

*Note: 人壁 is a glyph map error -- glyph 519 should be 間, not 壁.

---

## Class Labels (Entries 35-52)

| Entry | Offset | Glyph IDs | Japanese | Likely Class | English Target |
|-------|--------|-----------|----------|-------------|----------------|
| 35 | 0x454 | 286,581 | 戦士 | Fighter | fighter |
| 36 | 0x45C | 315,498 | 盗賊 | Thief | thief |
| 37 | 0x464 | 280,342,343 | 騎事持* | Mage | mage |
| 38 | 0x46E | 726,727 | 神聖 | Priest | priest |
| 39 | 0x476 | 583,287 | 忍者 | Ninja | ninja |
| 40 | 0x47E | 402 | 侍 | Samurai | samurai |
| 41 | 0x484 | 531,746 | 集教* | Bishop | bishop |
| 42 | 0x48C | 499,581 | 兵士 | Soldier | soldier |
| 43 | 0x494 | 730,419,342,343 | 冒書事持* | Alchemist? | alchemist |
| 44 | 0x4A0 | 533,498 | 義賊 | Robin Hood | robin hood |
| 45 | 0x4A8 | 224,238,200 | モンク | Monk | monk |
| 46 | 0x4B2 | 284,499,581 | 聖兵士 | Holy Soldier | paladin |
| 47 | 0x4BC | 353,499,581 | 暗兵士 | Dark Soldier | dark knight |
| 48 | 0x4C6 | 852,443 | 将後* | General? | general |
| 49 | 0x4CE | 746,853 | 教授 | Professor | professor |
| 50 | 0x4D6 | 684,315 | 美盗 | Thief-Beauty | rogue |

*Multiple glyph map errors visible (騎事持 should be 呪術師, etc.)

---

## Translation Strategy

### What works NOW (via R38 patching):
1. **Stat labels** -- Replace kanji glyph IDs with ASCII lowercase letter IDs
2. **Alignment labels** -- Replace kanji with "good"/"neutral"/"evil" using glyph IDs
3. **Race labels** -- Replace with English ("human", "elf", "dwarf", etc.)
4. **Class labels** -- Replace with English ("fighter", "thief", "mage", etc.)
5. **Personality traits** -- Replace with English names
6. All long description texts (entries 87-218)

### Constraints:
- **Only lowercase a-z available** (glyph IDs 33-58) + digits 0-9 (IDs 16-25) + space (ID 0)
- No uppercase letters in the font atlas
- Must stay within FFFE-terminated entry boundaries
- R38 is a PACKDATA resource, so it can be rebuilt and reinjected via the standard build pipeline
- Entry length CAN be changed since entries are FFFE-delimited (not fixed-offset)

### What still needs work:
- **Uppercase letters** -- Need to add A-Z glyphs to the font atlas texture, or accept all-lowercase
- **Glyph map corrections** -- At least 10 errors identified (glyph 511=性 not 果, 515=属 not 条, 519=間 not 壁, 520=善 not 枚, etc.)
- **Chargen field labels** (entries 8-17) -- 性別/属性/耐性/呪術呪法/神聖呪法 need translation

---

## Glyph Map Errors Identified in R38

| Glyph ID | Current Map | Should Be | Evidence |
|----------|-------------|-----------|----------|
| 511 | 果 | 性 | Entry 11: 511+512 = 性別 (gender) |
| 515 | 条 | 属 | Entry 12: 515+511 = 属性 (attribute) |
| 519 | 壁 | 間 | Entry 29: 319+519 = 人間 (human) |
| 520 | 枚 | 善 | Entry 223: alignment "good" |
| Various in classes | Multiple | Multiple | Class names decode incorrectly |

---

## Summary

The "Fighter/Neutral shows in English" premise was incorrect. All stat, alignment, race, and class labels are stored as Japanese kanji glyph sequences in R38. However, the engine DOES support English text rendering via the lowercase glyph IDs (33-58), as proven by the 29 reputation labels (entries 230-257) that are already in English. The translation path is clear: replace kanji glyph IDs with ASCII letter glyph IDs in R38, which is a standard PACKDATA MSG resource that goes through the normal build pipeline.
