# Diagnosis: Remaining Japanese Text Sources

**Date:** 2026-05-22
**Status:** Complete

---

## Executive Summary

The remaining Japanese text in the game comes from **three distinct sources**, each requiring a different fix:

| Category | Examples | Source | Fix Required |
|----------|----------|--------|-------------|
| Stat/UI labels | 力, 知恵, 信仰心, 生命力, 敏捷度, 幸運度 | MSG resource 38 (glyph-indexed text, same font atlas 1272) | **Translate R38** (177 messages, 0% translated) |
| Menu buttons | 依頼, 王国掲示板, 達成履歴, トラップゲーム, 外に出る | Pre-rendered texture images in PACKDATA.DIG (CockpitImg system) | **Replace texture resources** |
| Screen headers | 新規登録, 酒場 | Pre-rendered texture images (same CockpitImg system) | **Replace texture resources** |

---

## Finding 1: Stat Names Are MSG Text in Untranslated Resource 38

**The stat names render from the SAME font atlas (resource 1272).** They are NOT from a different font.

Resource 38 contains 177 messages with **0% translation coverage**. It includes:

| Message | Japanese | English | Type |
|---------|----------|---------|------|
| 0 | hp | HP | Stat label |
| 1 | hp/mhp | HP/MHP | Stat display |
| 2 | (missing from decode) | STR | Stat label (力) |
| 3 | 知恵 | INT | Stat label |
| 4 | 信仰心 | FTH | Stat label |
| 5 | 生命力 | VIG | Stat label |
| 6 | 敏捷度 | AGI | Stat label |
| 7 | 幸運度 | LCK | Stat label |
| 8 | 名前 | Name | Field label |
| 9 | レベル | Level | Field label |
| 10 | 種族 | Race | Field label |
| 11 | 果別 | Gender | Field label |
| 12 | 条果 | Alignment | Field label |
| 13 | 職業 | Class | Field label |
| 14 | 果性 | Personality | Field label |
| 15+ | Class names, personalities, spell levels... | ... | ... |

**Why they appear unchanged:** Resource 38 was identified as CRITICAL priority but was never translated (see `recon-translation-gaps/FINDINGS.md`). The game reads these labels as glyph indices from the same MSG format used for all other text. When the glyph indices point to Japanese glyphs in the atlas, Japanese text appears. When the English atlas replaced those glyphs, the indices now point to random English characters (garbled) or the original Japanese kanji shapes that were overwritten.

**Fix:** Translate all 177 messages in resource 38 and re-encode them with English glyph indices. This is purely a text translation task -- no texture hacking needed. Most entries are 1-3 word labels using standard Wizardry vocabulary (STR, INT, FTH, VIG, AGI, LCK, Warrior, Thief, Priest, etc.).

**Files:**
- Raw resource: `extracted/packdata_resources/0038_type01.bin`
- Decoded text: `data/full_decoded_text.json` (search for `"resource": 38`)
- Translation target: `data/translations_menus.json` (should add R38 entries)

---

## Finding 2: Menu Buttons Are Pre-Rendered Texture Images (CockpitImg System)

**The menu buttons (依頼, 王国掲示板, 達成履歴, トラップゲーム, 外に出る) are NOT glyph text.** They are pre-rendered texture images loaded by the game's "CockpitImg" system.

### Evidence

1. **Not in MSG resources:** A full-text search of all 1,168 decoded MSG messages finds NO matches for 王国掲示板, 達成履歴, トラップゲーム, 外に出る, or 新規登録 as standalone menu labels. The word 依頼 appears only within dialogue sentences (e.g., "あの依頼はどうなった？"), not as a standalone button label.

2. **Not in EXE as SJIS text:** A scan of all 1,078 SJIS strings in the EXE found zero matches for any menu button labels. The EXE's Japanese strings are exclusively debug messages (e.g., "デバックチェック！！！！！") and battle action names.

3. **CockpitImg system in EXE:** The EXE contains these debug strings confirming a dedicated image-based cockpit UI system:
   ```
   0x003EC4D0: CockpitImg Init!!!
   0x003FC8C0: TMInit CockpitImgLoadEnd LastMem = (%x)
   ```
   This system loads cockpit images from PACKDATA.DIG during game initialization.

4. **BUSIN 1 reference:** The English predecessor (BUSIN 1, SLUS-20259) stores cockpit textures as separate files on the disc filesystem:
   - `IMAGE/COCKPIT/BAR/BAR_00.TMX` (33,344 bytes) -- Bar/tavern UI texture
   - `IMAGE/COCKPIT/GUILD/GUILD_00.TMX` (33,344 bytes) -- Guild UI texture
   
   In BUSIN 0, these are packed into PACKDATA.DIG instead of existing as loose files.

5. **Bar subsystem debug strings confirm UI structure:**
   ```
   Bar Trap Start(%d)!!!       --> トラップゲーム button
   Bar Notice Start(%d)!!!     --> 王国掲示板 button  
   Bar Request Start(%d)!!!    --> 依頼 button
   Bar Gift Start(%d)!!!       --> Medal exchange button
   Bar History Start(%d)!!!    --> 達成履歴 button
   Guild Start(%d)!!!          --> Guild screen
   ```

### Candidate PACKDATA Resources for CockpitImg

Based on the loading sequence analysis, the CockpitImg textures are likely in the **resource cluster 2118-2125**:

| Resource | Type | Payload Size | Likely Content |
|----------|------|-------------|----------------|
| 2118 | type01 | 263,360 B | 512x512 PSMT8 grayscale -- **Bar cockpit background** |
| 2119 | type01 | 33,984 B | 256x256 or smaller -- **Bar button sheet** |
| 2120 | type01 | 33,984 B | 256x256 or smaller -- **Bar button sheet (alt state)** |
| 2121 | type01 | 263,360 B | 512x512 PSMT8 grayscale -- **Guild cockpit background** |
| 2122 | type01 | 33,984 B | 256x256 or smaller -- **Guild button sheet** |
| 2123 | type01 | 736 B | 32x32 -- **Small icon/cursor** |
| 2124 | type01 | 33,808 B | 256x256 PSMT4 (colored) -- **Menu overlay texture** |
| 2125 | type01 | 308 B | Tiny -- **Pointer/cursor sprite** |

Resources 2119, 2120, 2122 are especially suspicious: their payload size (33,984 bytes) closely matches the BUSIN 1 cockpit TMX file size (33,344 bytes). The difference (640 bytes) could be due to a different palette structure or additional metadata.

Resources 2118 and 2121 (263,360 bytes each) were previously identified as "PSMT8 with grayscale CLUT" (see `impl09-all-fonts/FINDINGS.md`) and are strong candidates for the main cockpit background textures that contain pre-rendered Japanese text.

### Fix Strategy

1. **Dump resources 2118-2125 as images** using the GS header parser (same approach used for resource 1272)
2. **Visually identify** which resources contain Japanese menu button text
3. **Create replacement textures** with English button text rendered in the same style
4. **Inject replacements** into PACKDATA.DIG using the same pipeline as the font atlas

This is a **texture replacement** task, fundamentally different from the MSG text translation pipeline. It requires:
- Understanding each texture's pixel format (PSMT4 vs PSMT8)
- Matching the original visual style (button borders, shadows, text color)
- Ensuring the replacement text fits the button bounding boxes

---

## Finding 3: Screen Headers Are Part of the Same CockpitImg System

**The header text (新規登録, 酒場) is rendered from the same pre-rendered texture images as the menu buttons.** The game's "AllIns" (All-In-Screen) system handles the full-screen cockpit/menu layouts:

```
AllIns BG Init!!!       -- Background layer initialization
AllIns Menu Init!!!     -- Menu overlay initialization  
AllIns ComTex Init!!!   -- Common texture initialization
All Ins Tex Init!!!     -- Full texture initialization
```

The header text "酒場" (Tavern/Bar) and "新規登録" (New Registration) are baked into the cockpit background textures alongside the menu buttons. They are NOT separate resources -- they share the same texture atlas with the button graphics.

**Fix:** Same as Finding 2 -- replace the cockpit texture resources.

---

## Finding 4: Font Atlas Usage Is Singular (Resource 1272 Only)

**The game uses resource 1272 for ALL glyph-based text rendering.** There is no second font atlas.

### Evidence (from recon23, impl09)

1. Resource 1272 is the **only PSMT4 256x512 texture** in all 2,883 PACKDATA resources
2. Resource 1272 is the **only PSMT4 texture with a grayscale descending CLUT** suitable for font rendering
3. The 13 font descriptors at EXE offset 0x3C0700 all reference the same 256x512 atlas, treating it as two stacked 256x256 pages
4. `FCD_event_font` and `FCD_battle_font` are runtime allocation names for the **same texture data**, not separate resources
5. `SysFont Init` + `SysFontImgLoadEnd` in the loading sequence loads a single font resource

### Why Stat Names Still Appear Japanese

The stat names appear Japanese NOT because they use a different font, but because:
- Resource 38 (character stats UI) has **0% translation** -- the glyph indices still point to Japanese characters
- When the English font atlas replaced Japanese glyphs, these untranslated glyph indices now either:
  - Display garbled/wrong English characters (if the original glyph slot was reassigned)
  - Display blank/missing glyphs (if the original glyph slot was cleared)
  - Still show recognizable Japanese (if the user is seeing screenshots from BEFORE the atlas patch)

---

## Finding 5: Complete Inventory of Japanese Text Sources

### Covered by MSG Resource Translation (glyph-indexed text)

| Resource | Messages | Translation | Content |
|----------|----------|-------------|---------|
| R34 | 29 | 100% | Magic stones |
| R35 | 23 | 100% | Game settings |
| R36 | 156 | 100% | Items/monsters |
| R37 | 18 | 89% | Character creation |
| **R38** | **177** | **0%** | **Stat labels, class names, personality traits** |
| R39 | 84 | 100% | Party management |
| R40 | 55 | 100% | Adventurer's Guild |
| R41 | 17 | 100% | Church of Salem |
| R42 | 13 | 100% | Adventurer's Inn |
| **R43** | **26** | **0%** | **Tavern bartender dialogue** |
| R44 | 57 | 100% | Knight Order |
| R45 | 191 | 85% | Vigger Shop |
| R46 | 7 | 100% | Bulletin board |
| R47 | 30 | 100% | Battle/treasure |
| **R48** | **107** | **0%*** | **Shop tier names** |
| R49 | 109 | 100% | Dungeon exploration |
| R2654 | 32 | 100% | Alleid actions |

*R48 translations exist in nested dict format but aren't wired into the resource mapping.

### NOT Covered by MSG Translation (require texture replacement)

| Source | Content | Resources | Fix |
|--------|---------|-----------|-----|
| CockpitImg (Bar) | 依頼, 王国掲示板, 達成履歴, トラップゲーム, 外に出る, 酒場 header | R2118-R2120 | Replace texture |
| CockpitImg (Guild) | 新規登録, Guild menu buttons | R2121-R2122 | Replace texture |
| CockpitImg (Other) | Camp/status/dungeon menu backgrounds | R2124, possibly others | Replace texture |
| Battle effects (MOJI) | Damage numbers, MISS/HIT | Disc files IMAGE/BATTLE/EFFECT/MOJI.TMZ | Replace TMZ texture |
| Name entry keyboard | Katakana/hiragana grid | EXE tables at 0x4C9AB0-0x4CA607 | Patch EXE |

### Summary of Remaining Work

| Priority | Task | Effort |
|----------|------|--------|
| CRITICAL | Translate R38 (stat labels, 177 msgs) | 1-2 hours |
| HIGH | Translate R43 (tavern dialogue, 26 msgs) | 30 min |
| HIGH | Identify & replace CockpitImg textures (R2118-R2124) | 4-8 hours |
| MEDIUM | Wire R48 translations into resource mapping | 30 min |
| MEDIUM | Translate R45 tail (28 remaining msgs) | 30 min |
| LOW | Replace MOJI.TMZ battle effect sprites | 2 hours |
| LOW | Patch EXE name entry tables | 2 hours |

---

## Recommended Next Steps

### Immediate (unblocks most visible Japanese text)

1. **Translate Resource 38:** This single resource covers all stat names, class names, personality traits, race names, and character sheet field labels. Most are 1-2 word labels with well-known Wizardry translations.

2. **Dump resources 2118-2125 as images:** Write a script to decode these type01 GS texture resources and output them as PNG files. This will reveal exactly which textures contain the pre-rendered Japanese menu buttons.

### Short-term (cockpit texture replacement)

3. **Create English cockpit textures:** Once the Japanese textures are dumped, create replacement textures with English button text. This requires:
   - Matching the pixel format (PSMT8 for backgrounds, PSMT4 for overlays)
   - Preserving button positions and dimensions
   - Rendering English text in a visually compatible style

4. **Inject replacement textures:** Use the rebuild_packdata.py pipeline to inject modified resources.

### Medium-term (completeness)

5. **Patch EXE name entry system:** Replace katakana/hiragana grids with Latin alphabet layout.
6. **Replace MOJI battle sprites:** Only needed if damage display text is in Japanese.

---

## File References

| File | Path | Purpose |
|------|------|---------|
| Font atlas | `extracted/packdata_resources/1272_type01.bin` | The ONE font atlas |
| Stat labels resource | `extracted/packdata_resources/0038_type01.bin` | Untranslated R38 |
| Bar cockpit texture | `extracted/packdata_resources/2118_type01.bin` | Candidate bar background |
| Bar button sheet | `extracted/packdata_resources/2119_type01.bin` | Candidate button texture |
| Guild cockpit texture | `extracted/packdata_resources/2121_type01.bin` | Candidate guild background |
| EXE | `extracted/SLPM_653.78` | Game executable |
| BUSIN 1 Bar TMX | `extracted_busin1/IMAGE/COCKPIT/BAR/BAR_00.TMX` | Reference English texture |
| BUSIN 1 Guild TMX | `extracted_busin1/IMAGE/COCKPIT/GUILD/GUILD_00.TMX` | Reference English texture |
| Decoded text | `data/full_decoded_text.json` | All decoded MSG messages |
| Translation gaps | `runs/.../recon-translation-gaps/FINDINGS.md` | Coverage audit |
