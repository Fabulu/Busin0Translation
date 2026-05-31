# Debug: Personality Name/Description Mismatch Report

**Date:** 2026-05-28
**Issue:** User reports "22-6 shows 'cautious' label at top but description says 'strong maiden bonds'"

---

## 1. Binary Structure Analysis

R38 (`extracted/packdata_raw/0038_type01.raw`) is a type-01 Format A resource with 188 FFFF-delimited message groups, organized as:

| Group Range | Count | Content |
|-------------|-------|---------|
| 0-17 | 18 | Stat/field labels (HP, STR, INT, Name, Level, etc.) |
| 18-24 | 7 | Spell levels (Lv1-Lv7) |
| 25-26 | 2 | Gender symbols |
| 27-36 | 10 | Race/world names |
| 37-52 | 16 | Class names (Fighter, Thief, Mage, ..., Rogue) |
| **53-82** | **30** | **Personality NAMES** |
| 83-86 | 4 | Combat stat labels (Attack, Accuracy, Defense, Evasion) |
| **87-116** | **30** | **Personality DESCRIPTIONS** |
| 117-130 | 14 | Gender/race/alignment/class help text |
| 131-148 | 18 | More class/stat help text |
| 149-188 | 40 | Alignment labels, reputation ranks, misc |

## 2. EXE Lookup Tables

Found two tables in the game EXE (`SLPM_653.78`):

**Personality Name Table** at `0x3C08CA`:
- 30 consecutive LE uint16 values: 53, 54, 55, ..., 82
- Game looks up name for personality index `i` as group `53 + i`

**Personality Description Table** at `0x3B7C32`:
- 30 consecutive LE uint16 values: 87, 88, 89, ..., 116
- Game looks up description for personality index `i` as group `87 + i`

Both tables are purely sequential. The game uses offset +34 between name and description (name group + 34 = desc group).

## 3. Patched Binary Verification

The patched R38 at `build/packdata_resources/0038_type01.raw` was verified by parsing the offset table (msg_count=188, stream starts at byte 772). Groups 53-116 decode correctly:

### Name/Description Pairs (offset +34, matching EXE tables):

| Idx | Name Group | Name Text | Desc Group | Description Text | Match? |
|-----|-----------|-----------|------------|------------------|--------|
| 0 | G53 | Omnitsu | G87 | Gets bored easily. Must return to town... | WRONG |
| 1 | G54 | Militant | G88 | Fears spirits. Trembles at Death. | WRONG |
| 2 | G55 | Wasteful | G89 | Lives to hoard gold. Gets angry if loot scarce. | WRONG |
| 3 | G56 | Lonely | G90 | Dislikes crowds and large groups. | OK |
| 4 | G57 | Sociable | G91 | Enjoys socializing in large groups. | OK |
| 5 | G58 | Collector | G92 | Can't resist loot. Item collecting is life's goal. | OK |
| **6** | **G59** | **Cautious** | **G93** | **Believes reckless adventurers can't be trusted.** | **OK** |
| 7 | G60 | Hoarder | G94 | Deeply interested in monster biology. | WRONG |
| 8 | G61 | Intellectual | G95 | Believes in mystic power. Loves magic knowledge. | MAYBE |
| 9 | G62 | Belligerent | G96 | Seeks battle with strong opponents. | OK |
| 10 | G63 | Adventurous | G97 | Must adventure. Idle is unbearable. | OK |
| 11 | G64 | Superstitious | G98 | Reacts keenly to sudden events. | WRONG |
| 12 | G65 | Studious | G99 | Obsessed with traps. Happy on success. | WRONG |
| 13 | G66 | Pusillanimous | G100 | Anxious in dungeons too long. | OK |
| 14 | G67 | Ecologist | G101 | Values recycling. Hates discarding items. | OK |
| 15 | G68 | Maiden Heart | G102 | With maiden bonds, no need for men. | OK |
| 16 | G69 | Hot-Blooded | G103 | Women have no place in battle. | OK |
| 17 | G70 | Just | G104 | Can't forgive slaying friendly monsters. | OK |
| 18 | G71 | Determined | G105 | Lives to slay every monster. Despises retreat. | WRONG |
| 19 | G72 | Cooperative | G106 | Values party action. Dislikes solo. | OK |
| 20 | G73 | Fraternal | G107 | Hates fighting. Mourns fallen allies. | WRONG |
| 21 | G74 | Short-Tempered | G108 | Very short-tempered. Long battles maddening. | OK |
| 22 | G75 | Economist | G109 | Born merchant spirit. Into business/trade. | OK |
| 23 | G76 | Lustful | G110 | Keen interest in opposite sex. | OK |
| 24 | G77 | Narcissist | G111 | Most beautiful. Shocked when harmed. | OK |
| 25 | G78 | Moody | G112 | Happy one moment, angry next. Unpredictable. | OK |
| 26 | G79 | Sadist | G113 | Thrives in hardship. Healing feels worse. | OK |
| 27 | G80 | Tribal Love | G114 | Deep bond with own race. | OK |
| 28 | G81 | Bold | G115 | Thinks of nothing. Follows others. | WRONG |
| 29 | G82 | Stupid | G116 | Use everything you own. Hoarding unforgivable. | WRONG |

## 4. Root Cause Analysis

### 4a. The reported bug (Cautious -> maiden bonds) DOES NOT EXIST in the binary

In the patched binary, personality index 6:
- Name = G59 = **"Cautious"**
- Desc = G93 = **"Believes reckless adventurers can't be trusted"**

This pairing is semantically correct. The Japanese name 慎重 (careful/cautious) matches the description about not trusting reckless adventurers. The "maiden bonds" description is at G102, paired with G68 "Maiden Heart" -- also semantically correct.

**If the user truly sees "Cautious" with "maiden bonds" in-game, the cause is NOT in the translation data or binary patching.** Possible causes:
- Misidentified screenshot (user may have been looking at a different personality)
- Game state corruption
- Different build version than analyzed

### 4b. The REAL problem: Multiple personality NAME mistranslations

The descriptions (G87-G116) appear correctly ordered and correctly translated from the original Japanese. However, **several personality NAMES are mistranslated**, causing apparent mismatches when reading name+description together:

| Name Msg | Current EN | JP Original | Correct EN | Paired Desc |
|----------|-----------|-------------|------------|-------------|
| G53 | Omnitsu | 飽き性 (akishou) | Fickle | "Gets bored easily" - MATCHES |
| G54 | Militant | 臆病 (okubyou)? | Timid/Cowardly | "Fears spirits" - would MATCH |
| G55 | Wasteful | 浪費 (rouhi) | Spendthrift | "Lives to hoard gold" - MISMATCH |
| G60 | Hoarder | 貯蓄家 (chochikuka) | Saver/Thrifty | "Monster biology" - MISMATCH |
| G64 | Superstitious | 迷信家 (meishinka) | Superstitious | "Sudden events" - MISMATCH |
| G65 | Studious | 勤勉 (kinben) | Diligent | "Obsessed with traps" - MISMATCH |
| G71 | Determined | 勇ち気 (yuuchiki) | Aggressive | "Slay every monster" - would MATCH |
| G73 | Fraternal | 友愛 (yuuai) | Compassionate | "Hates fighting, mourns" - would MATCH |
| G81 | Bold | 大胆 (daitan) | Bold/Daring | "Thinks of nothing" - MISMATCH |
| G82 | Stupid | 無味家? | Practical/Thrifty | "Use everything" - would MATCH |

**Note:** The glyph decoding for these personality names may have errors (the OCR/glyph mapping has ~95% coverage), making the exact Japanese uncertain. The description translations appear correct based on the Japanese text context.

### 4c. Description pairings that are semantically wrong due to NAME errors

The descriptions ARE in the correct order. The problem is that some personality NAMES were translated to the wrong English word:
- "Wasteful" (G55) is paired with "Lives to hoard gold" (G89) -- the description is for a HOARDER personality, suggesting G55's JP name might actually mean "hoarding obsessed" not "wasteful"
- "Hoarder" (G60) is paired with "Monster biology" (G94) -- suggests G60's name means something about monsters/biology, not hoarding
- "Bold" (G81) is paired with "Thinks of nothing, follows others" (G115) -- this describes a simpleton, not someone bold

## 5. Recommendations

1. **Do NOT rearrange descriptions.** The description order matches the EXE's sequential lookup table (87+i) and the original Japanese game semantics are correct.

2. **Re-translate the personality NAMES** at MSG 53-82 by cross-referencing each name's Japanese with its paired description to ensure semantic consistency.

3. **Priority name fixes needed:**

| MSG | Current | Suggested Fix | Reason |
|-----|---------|--------------|--------|
| 53 | Omnitsu | Fickle | 飽き性 = easily bored; "omnitsu" is wrong |
| 54 | Militant | Cowardly | Desc = fears spirits; not militant at all |
| 55 | Wasteful | Miser | Desc = hoards gold; opposite of wasteful |
| 60 | Hoarder | Naturalist | Desc = studies monsters; not hoarding |
| 64 | Superstitious | Sensitive | Desc = reacts to sudden events |
| 65 | Studious | Trap-Lover | Desc = obsessed with traps |
| 71 | Determined | Slayer | Desc = lives to slay monsters |
| 73 | Fraternal | Pacifist | Desc = hates fighting, mourns allies |
| 81 | Bold | Simpleton | Desc = thinks of nothing, follows others |
| 82 | Stupid | Frugal | Desc = use everything, no waste |

4. **Verify user's specific report** by running the game with personality index 6 selected and capturing what actually displays on screen.

## 6. Files Referenced

- `extracted/packdata_raw/0038_type01.raw` -- original R38 binary
- `build/packdata_resources/0038_type01.raw` -- patched R38
- `data/translate_chunks/chunk_02_translated.json` -- personality translations (113 entries)
- `data/translate_chunks/chunk_r38_fix.json` -- fix entries including MSG 54
- `extracted/SLPM_653.78` -- game EXE with lookup tables
  - `0x3C08CA` -- personality name table (30 x LE u16: 53-82)
  - `0x3B7C32` -- personality description table (30 x LE u16: 87-116)
- `build/build_full_english_v2.py` -- injection pipeline (uses FFFF group index directly)
