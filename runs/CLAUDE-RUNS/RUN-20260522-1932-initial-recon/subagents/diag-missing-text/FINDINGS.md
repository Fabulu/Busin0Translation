# Diagnostic: Missing Japanese Text in BUSIN 0 Translation Patch

**Date:** 2026-05-22
**Status:** Complete

---

## Executive Summary

The game has **only 21 resources with genuine translatable glyph text** out of 296 classified as "MSG." The other 275 are **game data tables** (enemy stats, item parameters, dungeon configs) that happen to use the same FFFF delimiter format but contain numeric/flag values, not text glyphs. The remaining visible Japanese comes from three sources: untranslated MSG resources (R38, R43, R45 tail, R48), pre-rendered cockpit textures, and the EXE name-entry tables.

---

## Task 1: Bar/Tavern Dialogue (店主 speaking Japanese)

### Finding: Tavern bartender dialogue IS in resources 34-49, specifically R43

Resource 43 (`0043_type01.bin`) contains **26 messages** of Bar Luna Light dialogue -- the bartender's game interaction text:

- "Hey, how'd that request go?" (おうおう、あの依頼はどうなった？)
- "Wanna grab a drink?" (一杯ひっかけてくかい？)
- "Wanna check the bulletin board?" (掲鉄板を見るのか？)
- "The game costs 500g per play" (ゲームは１回５００gだぜ)
- Prize exchange dialogue, Yes/No prompts, insufficient gold warnings

**R43 has 0% translation coverage.** This is why the bartender still speaks Japanese.

### The menu buttons (依頼, 王国掲示板, 達成履歴, トラップゲーム, 外に出る)

These are **NOT glyph text**. They are pre-rendered texture images in the CockpitImg system. The bar cockpit textures are likely in resources **R2118-R2120**. The word "酒場" (Tavern) in the screen header is also baked into these textures. These require texture replacement, not text translation.

Evidence from EXE debug strings:
```
Bar Trap Start(%d)!!!       --> トラップゲーム button
Bar Notice Start(%d)!!!     --> 王国掲示板 button
Bar Request Start(%d)!!!    --> 依頼 button
Bar Gift Start(%d)!!!       --> Medal exchange button
Bar History Start(%d)!!!    --> 達成履歴 button
```

---

## Task 2: Initial Story Cutscene After Character Creation

### Finding: No separate cutscene text resources exist

1. **No FMV with text:** The MOVIE/ directory contains only `BSN2_0.DSI` (an index file). There are no video files with baked-in Japanese text. The cutscene appears to be rendered in-engine using the TextEvent system.

2. **TextEvent system:** The EXE contains a "TextEvent" dialogue engine (`TextEventSystemDelete`, `TextEventMsgIdle`, `Event Start`, `Event End`). This system reads message data and renders it using the same font atlas (R1272).

3. **The initial story text is in the same R34-R49 resource cluster.** Resource 49 contains dungeon/story text (109 messages, 100% translated). The story cutscene text after character creation is likely among resources 38 (character details), 46 (bulletin board), or 49 (dungeon exploration/story). All of R49 is fully translated.

4. **If the cutscene still shows Japanese**, the most likely cause is:
   - The text is in **R38** (0% translated, 177 messages including character sheet text that displays right after creation)
   - The text is in an **untranslated portion of R45** (messages 168-191 are untranslated)
   - The CockpitImg textures for the character creation/guild screens (R2121-R2122) still show Japanese headers

5. **BUSIN 1 (USA) reference:** BUSIN 1 stores event scripts as separate EVE/MSG file pairs (`UEDA.MSG`, `KYOUGOKU.MSG`, `FUKAUMI.MSG` in `IMAGE/EVENT/`). In BUSIN 0, these are packed into PACKDATA.DIG. The event MSG data uses the same glyph-indexed format but would be among the 275 Format B resources. However, analysis shows these Format B resources contain **game data tables, not text** (see Task 3 below).

---

## Task 3: Search All 2,881 PACKDATA Resources for Alternative Text Formats

### Finding: Only 15 resources contain genuine text-range glyphs

A systematic scan of all 296 MSG resources checked what percentage of their glyph values fall in the known text range (0-858). Results:

| Category | Count | Description |
|----------|-------|-------------|
| 95%+ in glyph range (genuine text) | 15 | R34-R49 subset + R1161, R1909, R2654 |
| Mixed text+data | 4 | R720, R1053, R1908, R2124 (already decoded) |
| Data tables (glyph values > 1000) | 277 | Game parameters using FFFF delimiters |

The 15 genuine-text resources are:
- R34, R36, R37, R38, R39, R40, R42, R43, R44, R46, R47, R49 (from R34-49 cluster)
- R1161 (73,268 bytes - config/menu data, numbers and labels, not dialogue)
- R1909 (73,268 bytes - nearly identical to R1161)
- R2654 (5,666 bytes - Alleid action text, already 100% translated)

R35, R41, R45, R48 are also genuine text but with fewer segments (still in R34-49 cluster).

### Non-MSG resources

The `non_msg_text_scan.json` confirms: all 1,657 SJIS-flagged non-MSG resources contain **zero genuine Japanese text**. Every SJIS byte-pattern match is a false positive from binary data (textures, 3D models, audio). The game stores ALL text using 16-bit glyph-index encoding in MSG resources, not raw SJIS.

---

## Task 4: FF01 Speaker Tags Beyond R49

### Finding: 83 resources beyond R49 contain FF01 tags, but they are NOT speaker tags

FF01 appears in resources across the 600-2876 range. However, examination reveals these values are **game data parameters**, not speaker name markers. The resources containing them show glyph values like 5120, 12769, 32768, 16384 -- powers of 2 and large round numbers typical of bitfield flags, NOT glyph indices for character names.

Example from R1084 (90 FF01 tags):
```
@0x56: [5120] [12769][1280][32][1536] [1152] 0[3584] [2048] [1024][16384][13312] [24576]
```

This is clearly numerical game data (monster stats, item tables, etc.), not "Speaker Name: dialogue text."

The FF01 tag as a speaker marker was specific to the R46 bulletin board format. Beyond R49, FF01 serves a different purpose in the data table format.

---

## Task 5: Resources in the 600-900, 1000-1400, and 2100-2900 Ranges

### Summary by Range

| Range | MSG Resources | Undecoded | Content |
|-------|--------------|-----------|---------|
| 600-900 | 36 | 35 | Game data tables -- glyph values >1000, bitfield/flag patterns |
| 901-999 | 8 | 8 | Game data tables -- same format |
| 1000-1400 | 98 | 97 | Game data tables -- same format, many very large (100K-938K bytes) |
| 1401-2100 | 27 | 26 | Game data tables -- same format |
| 2100-2900 | 110 | 109 | Game data tables -- same format, includes R2816-R2876 cluster |

### Detailed Examination

**R1701-R1726 (type01, 1700s cluster):** All start with identical header `0100000002000000` and first segment "ブベ [32768][32768] [19456] [16384]..." These are NOT text. The values are bitfields (powers of 2).

**R2816-R2876 (type01, 2800s cluster):** Same header pattern. First segment: "ブベ [11264] [32768][32768] [7168]ブ[4096][4096][1024]..." Also NOT text.

**R899 (type01, 944K bytes):** Contains 10 FF01 tags and massive segments with values in the 30000-65000 range. This is a large game data table, possibly the master monster/encounter database.

**R1161 and R1909:** These two are the only Format B resources outside R34-49 with >95% of glyphs in the text range. However, their content is configuration/menu layout data (numbers like "9 9", "0:", "2", format strings), not story dialogue.

---

## Task 6: Where Are the Other 275 MSG Resources?

### Finding: They are data tables, not text

The classification identified 296 resources as "MSG" based on the presence of FFFF delimiters and glyph-like 16-bit values. However, the FFFF delimiter is used for TWO purposes in BUSIN 0:

1. **Text message separator** (in R34-49, R2654): Separates glyph-indexed text messages with values 0-858
2. **Data record separator** (in all 275 other resources): Separates numeric data records with values typically > 1000

### The 275 "MSG" resources are actually:

| Type | Likely Content | Evidence |
|------|---------------|----------|
| type01 (195 total) | NPC scripts, encounter tables, dungeon configs | Values are bitfields (powers of 2), large round numbers |
| type02 (65 total) | Scene/event parameters | Fixed-width records with parameter-like values |
| type03 (12 total) | Special data (7 decoded as "actual MSG" in R34-49) | Mixed |
| type04 (9 total) | Game state/save data structures | Large structured records |
| Other types | Various system data | Anomalous value patterns |

### The actual translatable text resources are:

**21 resources already decoded** (R34-49 + R720, R1053, R1908, R2124, R2654) containing 1,168 messages.

Of these, the untranslated portions are:
- **R38**: 177 messages, 0% translated (stat labels, class names, personality traits)
- **R43**: 26 messages, 0% translated (tavern bartender dialogue)
- **R45**: 28 messages untranslated (edge-case shop dialogue, floor labels)
- **R48**: 107 messages, 0% mapped (translations exist but not wired into resource mapping)
- **R720, R1053, R1908, R2124**: 37 messages total, poorly decoded (likely not player-facing text)

---

## Complete Map of All Japanese Text Sources

### 1. Glyph-Indexed MSG Text (translatable via text pipeline)

| Priority | Resource | Messages | Translated | Content |
|----------|----------|----------|------------|---------|
| CRITICAL | R38 | 177 | 0% | Stat labels, class/race/personality names |
| HIGH | R43 | 26 | 0% | Tavern bartender dialogue |
| MEDIUM | R45 tail | 28 | 0% | Edge-case shop dialogue, floor labels |
| LOW | R48 | 107 | mapped* | Shop tier names (translations exist, need wiring) |

### 2. Pre-Rendered Textures (require image replacement)

| Resource | Content | Fix |
|----------|---------|-----|
| R2118-R2120 | Bar/tavern cockpit UI (依頼, 王国掲示板, 達成履歴, etc.) | Replace TMX textures |
| R2121-R2122 | Guild cockpit UI (新規登録, etc.) | Replace TMX textures |
| R2124 | Menu overlay texture | Replace TMX texture |

### 3. Executable Data (require EXE patching)

| Offset | Content | Fix |
|--------|---------|-----|
| 0x4C9AB0-0x4CA607 | Name entry kana grids | Patch EXE tables |

### 4. Battle Effect Sprites

| File | Content | Fix |
|------|---------|-----|
| MOJI.TMZ | Damage numbers, MISS/HIT text | Replace TMZ texture |

---

## Conclusion

**The "275 undecoded MSG resources" are a red herring.** They are game data tables that use the same FFFF delimiter format as text but contain numeric parameters, not glyphs. The actual Japanese text that needs translation is concentrated in:

1. **3 untranslated MSG resources** (R38, R43, R45 tail) = ~231 messages
2. **~6 CockpitImg texture resources** (R2118-R2124) = pre-rendered menu buttons
3. **EXE name-entry tables** = kana input grids
4. **R48 translation wiring** = existing translations need to be connected to the build pipeline

The initial story cutscene text is either in R49 (already translated) or rendered from R38 character sheet labels (untranslated). If Japanese still appears during the post-creation sequence, translating R38 should resolve it.

---

## Key File References

| File | Path |
|------|------|
| Resource classification | `dumps/resource_classification.json` |
| MSG structure analysis | `dumps/msg_structure_analysis.json` |
| MSG header analysis | `dumps/msg_header_analysis.json` |
| Non-MSG text scan | `dumps/non_msg_text_scan.json` |
| Decoded text database | `data/full_decoded_text.json` |
| Glyph map | `data/msg_glyph_map.json` |
| R38 raw resource | `extracted/packdata_resources/0038_type01.bin` |
| R43 raw resource | `extracted/packdata_resources/0043_type01.bin` |
| Previous diagnosis | `runs/.../subagents/diag-japanese-remaining/FINDINGS.md` |
| Translation gaps audit | `runs/.../subagents/recon-translation-gaps/FINDINGS.md` |
