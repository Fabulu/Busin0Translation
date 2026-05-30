# RAM R38 Debug Analysis - stillbad-5 & stillbad-6

## Executive Summary

**R38 IS English in RAM.** The untranslated "attributes" visible in stillbad-5/6 come from **R34 (0034_type20.raw)**, which is only 2.4% translated (28/1143 messages).

## Methodology

1. Extracted `eeMemory.bin` (32MB EE RAM) from both `.p2s` save states (ZIP archives)
2. Searched RAM for R38 glyph patterns and FFFF-delimited message structures
3. Compared RAM content with R38 ISO file and original JP R38
4. Traced untranslated Japanese messages back to their source resource

## Key Findings

### 1. R38 Data in RAM (Confirmed English)

R38 loads into RAM at **0x00E14382** (region 1) and **0x01098000** (region 2).

Region 1 contains stat/character labels -- ALL translated:
- STR, INT, FTH, VIT, AGI, LCK
- NAME, LEVEL, RACE, GENDER, ALIGNMENT, CLASS, PERSONALITY
- SORCERY, HOLY MAGIC, ATTRIBUTES
- Race names: HUMAN, EUROPA, ELF, GNOME, DWARF, HOBBIT, AUTOMATA
- Class names: FIGHTER, THIEF, MAGE, PRIEST, NINJA, BISHOP, SAMURAI, etc.
- Personality names: MILITANT, WASTEFUL, LONELY, SOCIABLE, etc.
- Personality descriptions: all English multi-line text

Region 2 contains monster/creature names -- ALL translated:
- DRAGON FLY, ROTTING CORPSE, BORING BEETLE, ORC, KOBOLD, etc.
- VAMPIRE LORD, MAELIFIC, BANSHEE, SERAPH, ARCHANGEL, etc.

### 2. The RAM Buffer Extends Beyond R38

The RAM buffer at 0x00E14382 contains **282 FFFF-delimited messages**, but R38 only has **189 messages**. Messages 0-188 are R38 content. Messages 189+ come from **other resources loaded into the same buffer**.

### 3. Source of Japanese: R34 (0034_type20.raw)

Japanese messages at RAM indices 198-281 were traced to **R34 (0034_type20.raw)**, confirmed by byte-pattern matching:

| RAM Msg Index | Content | Source Resource |
|---|---|---|
| 189-218 | Item names (English: HEALING STONE, WAR GOD STONE, etc.) | R34 (translated portion) |
| 198-200 | Talisman names (Japanese) | R34 @ 0x0284 |
| 203 | Item name (Japanese) | R34 |
| 219-232 | Category labels (Japanese) | R34 |
| 233-238 | Item type labels (Japanese) | R34 @ 0x04AA+ |
| 241-281 | Race/class descriptions (Japanese, multi-line) | R34 @ 0x05DE+ |

### 4. R34 Translation Status

```
R34 (0034_type20.raw): 1164 FFFF markers, 71,680 bytes (patched)
- English:  28 messages  (2.4%)
- Japanese: 389 messages (34.0%)
- Mixed:    726 messages (63.5%)
- Empty:    20 messages  (1.7%)
```

R34 is a **type20** resource (not type01 like the dialogue files). Only 28 out of 1143 non-empty messages have been translated to English. The remaining 1115 messages are still fully or partially Japanese.

### 5. Glyph Encoding Note

The RAM uses a **different glyph ID encoding** than the R38 file on disk:
- R38 file: glyph 0x29 = 'A', 0x2A = 'B', ..., 0x28 = '0' (game's internal glyph table, offset -0x20 from ASCII)
- RAM: glyph 0x41 = 'A', 0x42 = 'B', ..., 0x48 = 'H' (ASCII-like, after game engine transforms)

The game engine remaps glyph IDs by adding +0x20 when loading into the display buffer. This means R38 file content is correct despite appearing as "!#()%6%-%.4" when read as raw ASCII (that's actually "ACHIEVEMENT" in the game's glyph table).

### 6. stillbad-5 vs stillbad-6

The RAM region 0xE14000-0xE18000 is **byte-for-byte identical** between both save states. Same loaded data, same untranslated messages.

## RAM Addresses

| Address | Content |
|---|---|
| 0x00E14300 | Offset table for messages |
| 0x00E14382 | First FFFF marker (R38 message data begins) |
| 0x00E160F2 | Last R38 message (msg 188) |
| 0x00E16A7E | Post-R38 data begins (R34 content, msg 189) |
| 0x00E17324 | End of FFFF-delimited messages |
| 0x01098004 | R38 region 2 (monster/item names, all English) |

## Action Required

**R34 (0034_type20.raw) needs translation.** It contains:
- Item/equipment names and descriptions
- Talisman names
- Category labels
- Race and class detailed descriptions (multi-line)
- This is a type20 resource with 1164 messages, currently at 2.4% coverage

The R38 translation is complete and correctly loaded into RAM.

## Files Used
- `C:/Programmieren/wizardrytranslation/RAMdumps/stillbad-5.p2s`
- `C:/Programmieren/wizardrytranslation/RAMdumps/stillbad-6.p2s`
- `C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/r38_from_iso.bin`
- `C:/Programmieren/wizardrytranslation/extracted/packdata_raw/0038_type01.raw`
- `C:/Programmieren/wizardrytranslation/extracted/packdata_raw/0034_type20.raw`
- `C:/Programmieren/wizardrytranslation/build/packdata_resources/0034_type20.raw`
