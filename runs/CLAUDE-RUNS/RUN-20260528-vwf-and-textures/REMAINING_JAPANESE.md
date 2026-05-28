# Remaining Japanese Text Catalog
**Date**: 2026-05-28
**Build baseline**: v10 (BUSIN0_EN_v10.iso)
**Source**: Consolidated from TODO.md, KNOWN_ISSUES.md, all recon/diag findings

---

## 1. MSG Glyph Text (PACKDATA.DIG Resources)

### 1A. Type-1 MSG Resources (R34-R49 cluster)

| ID | Item | Japanese | Location | Translation Need | Priority |
|----|------|----------|----------|-----------------|----------|
| 1A-1 | R38: Stat labels | 力, 知恵, 信仰心, 生命力, 敏捷度, 幸運度 | `0038_type01.bin`, 177 msgs | Translations EXIST in chunk_r38_fix.json but may not be injected into build. Verify injection pipeline picks them up. | CRITICAL -- blocks character creation/status screens |
| 1A-2 | R43: Tavern bartender dialogue | おうおう、あの依頼はどうなった？ / 一杯ひっかけてくかい？ / etc. | `0043_type01.bin`, 26 msgs | Translate all 26 messages (bartender interactions, prize exchange, yes/no prompts). | HIGH -- blocks tavern gameplay |
| 1A-3 | R45: Remaining shop dialogue | ~28 messages untranslated (msgs 168-191) | `0045_type01.bin` tail | Translate remaining edge-case shop dialogue and floor labels. | MEDIUM -- minor shop interactions |
| 1A-4 | R48: Shop tier names | 107 messages | `0048_type01.bin` | Translations exist in nested dict format but NOT wired into the resource mapping/build pipeline. | MEDIUM -- cosmetic shop labels |
| 1A-5 | R39: Equipment menu (reverted) | 481 of 565 messages untranslated. Equipment screen, status screen, inventory labels. | `0039_type01.bin` (type-15 format) | Type-15 injector introduces extra FFFF causing tavern softlock (M8). Must fix type-15 offset table rebuild first, then translate remaining 481 msgs. | HIGH -- equipment/inventory menus all Japanese |
| 1A-6 | R37: Character creation prompts | 2 of 18 messages untranslated | `0037_type01.bin` | Translate remaining 2 messages. | LOW -- minor chargen prompts |
| 1A-7 | R40: Location names (blank banners) | 酒場, ギルド, etc. | `0040_type01.bin`, 55 msgs | Text IS translated but location banners render as solid rectangles. Glyph IDs still point to blanked-out kanji slots. Need to verify injection or investigate separate location label system. | HIGH -- all location names invisible |

### 1B. Type-2 Embedded Dialogue (Story/NPC)

| ID | Item | Japanese | Location | Translation Need | Priority |
|----|------|----------|----------|-----------------|----------|
| 1B-1 | R1198: Early game scenes | Guild intro, Vera dialogue, tavern narration (88 msgs) | Type-2 Section 2 | Translated but REVERTED to Japanese due to Section 2 size growth causing text loop (M9). Need Section 1 opcode offset patching OR fixed-size injection. | CRITICAL -- entire early game in Japanese |
| 1B-2 | R1193/R1194: Opening narration dialogue | Battle of Banquo story text | Type-2 resources outside R1196-R1213 range | Not yet extracted or translated. Falls outside targeted range. Need to extract, translate, inject. | HIGH -- first text player sees |
| 1B-3 | R1347: Shop dialogue | 10 messages | Type-2 gap resource | Translate + inject | MEDIUM |
| 1B-4 | R1348: Unknown dialogue | 8 messages | Type-2 gap resource | Translate + inject | MEDIUM |
| 1B-5 | R1349: Vigger Friends points | 11 messages | Type-2 gap resource | Translate + inject | MEDIUM |
| 1B-6 | R1351: Romi character dialogue | 23 messages | Type-2 gap resource | Translate + inject | MEDIUM |
| 1B-7 | R1352: Melanie/Kunnal dialogue | 21 messages | Type-2 gap resource | Translate + inject | MEDIUM |
| 1B-8 | R1355: Story text | 53 messages | Type-2 gap resource | Translate + inject | MEDIUM -- ~126 msgs total in gap |
| 1B-9 | R1126: Mid-game dialogue | 171 dialogue lines | Type-2, Section 2 | Decode, translate, inject. Potentially significant story content. | MEDIUM |
| 1B-10 | R1134: Mid-game dialogue | 110 dialogue lines | Type-2, Section 2 | Decode, translate, inject. | MEDIUM |
| 1B-11 | R1148: Mid-game dialogue | 181 dialogue lines | Type-2, Section 2 | Decode, translate, inject. | MEDIUM |
| 1B-12 | R1118: Mid-game dialogue | 22 dialogue lines | Type-2, Section 2 | Decode, translate, inject. | MEDIUM |
| 1B-13 | R2587: Late-game dialogue | 42 messages | Type-2 | Translate + inject | LOW -- late game |
| 1B-14 | R2604: Late-game dialogue | 5 messages | Type-2 | Translate + inject | LOW -- late game |
| 1B-15 | R2659: Late-game dialogue | 2 messages (possibly 439 lines per inventory) | Type-2 | Already in type2_dialogue_full but may not be translated. Verify. | LOW -- late game |
| 1B-16 | Stray Japanese sentence in exposition | Unknown resource | Seen in-game amid English text | Likely from untranslated gap resource. Will resolve when R1347-R1355 are done. | MEDIUM -- breaks immersion |

**Note on type-2 scale**: The full PACKDATA has 510 type-2 resources with embedded dialogue totaling ~29,398 lines. The items above are the KNOWN remaining resources with confirmed dialogue. Many of the 510 resources are binary data tables with false-positive FFFF patterns. The 275 "undecoded MSG" resources in type-1 have been assessed as data tables with no translatable content (T8, T9 -- CLOSED).

---

## 2. EXE Hardcoded Glyph Tables (SLPM_653.78)

| ID | Item | Japanese | Location (file offset) | Translation Need | Priority |
|----|------|----------|----------------------|-----------------|----------|
| 2A | Name entry kana grid | Full hiragana + katakana grids (~200 characters) | EXE 0x3C99B8-0x3CA6EF (file), VA 0x4C99B0-0x4CA607 | Replace all kana glyph IDs with Latin A-Z, 0-9, space, backspace. Requires understanding grid layout (rows/columns) and patching LE uint16 glyph ID pairs. | HIGH -- name entry unusable for English names |
| 2B | Stat/attribute labels (chargen) | 力, 知恵, 信仰心, 生命力, 敏捷度, 幸運度, class names, race names | EXE 0x3C844A-0x3C8F64 | These are SEPARATE from R38 MSG labels. The EXE has its own hardcoded glyph ID tables for the character creation screen labels. Must patch with English glyph IDs. | CRITICAL -- chargen labels garbled |
| 2C | Menu label pair structs | Various menu option labels | EXE 0x3C3026-0x3C5174 | Decode struct format, replace Japanese glyph IDs with English equivalents. | MEDIUM -- menu UI labels |
| 2D | Kana mapping table | Kana-to-glyph lookup | EXE 0x3C5B32-0x3C6186 | May need updating to support Latin input mapping. | LOW -- related to name entry |
| 2E | Tab/button bitmap glyph IDs | ひらがな, カタカナ, etc. (name entry tab labels) | EXE 0x3C9DA0-0x3C9DFC | These reference glyph IDs 6400+ (bitmap font range, NOT the MSG font atlas). Need special handling -- see section 5. | MEDIUM -- name entry tabs show kana labels |
| 2F | NPC names (hardcoded) | エミリア (Emilia), リュート (Lute) | EXE 0x3C93AE-0x3C93D0 | Small table, patch with English glyph IDs. | LOW -- cosmetic, names may already be in English via MSG |
| 2G | Save slot names | ＢＵＳＩＮ０中断データ, ＢＵＳＩＮ０データ１/２/３ | EXE 0x3FC750-0x3FC790 (SJIS fullwidth) | Already patched in `build/patched_type2/SLPM_653.78` but NOT injected into ISO. Need to update EXE in ISO directly. | MEDIUM -- memory card screen |
| 2H | Save/load prompt | コンティニューロード！ | EXE 0x3F8240 (SJIS) | Patch SJIS string to "Continue Load!" | MEDIUM -- save/load screen |
| 2I | Battle system strings | 109 Allied Action names + status messages at 0x3EE9D0-0x3F3470 | EXE data section (SJIS) | Likely debug/TTY strings NOT player-visible. Need to verify in battle first. If visible, patch all 109. | LOW -- may be debug-only |
| 2J | Type suffix table | Equipment type labels | EXE 0x3F9D00-0x3F9EC0 | Glyph ID table for equipment type suffixes. Needs English equivalents. | LOW -- equipment screen detail |
| 2K | Font width tables | Width values for all 248 glyphs (4 tables) | EXE 0x3DDC48-0x3DDF48 | Currently REVERTED (M13). Changing widths breaks Japanese glyph rendering at shared positions. Must translate ALL labels using those glyph slots first, then patch widths. | LOW -- cosmetic spacing, dangerous to patch |
| 2L | Misc player-facing strings | ガーディアン戦闘！！, 取り付ける人がいないよ。, 松野ゲー起動！！ | Various EXE offsets (SJIS) | Patch ~5 miscellaneous strings. Length-constrained by original buffer sizes. | LOW -- rare/edge case |

**Key constraint**: All EXE glyph tables use LE uint16 (little-endian), unlike MSG files which use BE uint16 (big-endian).

---

## 3. CockpitImg Textures (Pre-Rendered UI Backgrounds)

| ID | Item | Japanese | Location (PACKDATA resource) | Translation Need | Priority |
|----|------|----------|----------------------------|-----------------|----------|
| 3A | Bar/Tavern background | 酒場 (header), menu layout frame | R2118 (263,360 B, 512x512 PSMT8) | Dump as image, redraw English "Tavern" header, re-encode PSMT8. | HIGH -- main hub screen |
| 3B | Bar button sheet (state 1) | 依頼 (Request), 王国掲示板 (Kingdom Board), 達成履歴 (Achievement History), トラップゲーム (Trap Game), 外に出る (Go Outside) | R2119 (33,984 B) | Create English button labels: "Request", "Bulletin Board", "History", "Trap Game", "Exit" | HIGH -- bar menu buttons all Japanese |
| 3C | Bar button sheet (state 2) | Same buttons, alternate/selected state | R2120 (33,984 B) | Same as 3B but for highlighted/pressed state. | HIGH -- matches 3B |
| 3D | Guild background | 新規登録 (New Registration) header, guild layout | R2121 (263,360 B, 512x512 PSMT8) | Redraw English "Guild" or "Registration" header. | HIGH -- guild screen |
| 3E | Guild button sheet | Guild menu option buttons | R2122 (33,984 B) | Create English guild menu buttons (Register, Edit, Dismiss, etc.) | HIGH -- guild menu |
| 3F | Menu overlay texture | Camp/status/dungeon menu elements | R2124 (33,808 B, 256x256 PSMT4?) | Identify text content by dumping, create English replacement. | MEDIUM -- in-game menus |
| 3G | Other cockpit textures | Possibly shop, church, inn backgrounds | R2123 (736 B), R2125 (308 B), possibly others | R2123/R2125 are tiny (icons/cursors), unlikely text. Scan nearby resources for additional cockpit screens. | LOW -- may not contain text |

**Technical approach**: Dump resources using GS header parser (same as font atlas R1272). Identify pixel format (PSMT4 vs PSMT8). Edit pixel data to replace Japanese text with English. Preserve palette (CLUT), dimensions, and alpha. Re-encode and inject via rebuild_packdata.py.

**Reference**: BUSIN 1 (English predecessor, SLUS-20259) has equivalent files at `IMAGE/COCKPIT/BAR/BAR_00.TMX` (33,344 B) and `IMAGE/COCKPIT/GUILD/GUILD_00.TMX` (33,344 B). These can serve as style/layout references.

---

## 4. TextEventImage Textures (Narration Overlays)

| ID | Item | Japanese | Location | Translation Need | Priority |
|----|------|----------|----------|-----------------|----------|
| 4A | Intro slideshow narration | その悲惨な戦争は... (multiple slides telling the Battle of Banquo backstory) | Pre-rendered texture images loaded by TextEventImage system. NOT in any MSG resource. Characters 悲惨争役々憶 do not exist in MSG font. | Must find the PACKDATA resources containing these texture images, create English replacement slides. This is image editing, not text encoding. | HIGH -- first narrative the player sees |

**Evidence**: EXE contains `TextEventImageDrawRequest` and `SetTextEventImageData` debug strings confirming image-based rendering. Exhaustive search of entire 1.2 GB ISO found zero text-encoded matches for the intro narration in any encoding.

**Important distinction**: Items 1B-2 (R1193/R1194) are MSG glyph dialogue resources that were missed from the translation range. Item 4A is the SEPARATE pre-rendered texture slideshow that appears BEFORE the MSG dialogue. Both contribute to the intro being in Japanese, but they require different fix approaches.

**Fix strategy**: Locate the TextEventImage texture resources in PACKDATA (likely near R1193-R1194 or in a dedicated texture block). Dump them as images, create English text overlays matching the original visual style, re-encode and inject.

---

## 5. Bitmap Font Glyph Labels (Name Entry Tabs, Special UI)

| ID | Item | Japanese | Location | Translation Need | Priority |
|----|------|----------|----------|-----------------|----------|
| 5A | Name entry tab labels | ひらがな (Hiragana), カタカナ (Katakana), possibly more mode labels | EXE glyph IDs at 0x3C9DA0-0x3C9DFC referencing glyph indices 6400+ | These reference a SEPARATE bitmap font system (glyph IDs 6400+), not the main MSG font atlas (0-858). The 6400+ range likely maps to a different texture resource containing pre-rendered tab label graphics. Need to: (1) find which PACKDATA resource contains the 6400+ bitmap font, (2) identify the tab label graphics within it, (3) replace with "ABC" / "abc" / "Symbol" or similar English labels. | MEDIUM -- name entry screen tabs unreadable |
| 5B | Battle effect text | MISS, HIT, damage numbers, possibly ミス/ヒット | `IMAGE/BATTLE/EFFECT/MOJI.TMZ` (1,440 B) and `MOJI1.TMZ` (identical) on disc filesystem | These are battle effect sprites, not the main font. Source texture was `moji2.tim`. Likely contains only digits 0-9 and short status words. Need to dump TMZ, check if any text is Japanese (MISS/HIT may already be in English). If Japanese, create English sprite replacements. | LOW -- battle numbers likely already numeric/English |
| 5C | Victory/Defeat/Level Up banners | 勝利, 敗北, レベルアップ (if they exist as textures) | Unknown PACKDATA resources (type-03/04 texture resources) | Not yet confirmed to exist. May be rendered via MSG glyph system instead of textures. Need to verify in-game during battle. | LOW -- unconfirmed |

---

## 6. Cross-Cutting Issues (Affect Multiple Categories)

| ID | Issue | Description | Affected Items | Priority |
|----|-------|-------------|---------------|----------|
| 6A | Font atlas uppercase fix (T1) | A-Z must be at glyph slots 33-58. Currently renders uppercase as hiragana. | ALL MSG text, ALL EXE glyph tables | CRITICAL -- prerequisite for everything |
| 6B | Punctuation glyph remapping (T2) | Period, comma, dash, colon, apostrophe at wrong glyph slots. | ALL MSG text rendering | CRITICAL -- prerequisite |
| 6C | Text truncation (M14) | English text overflows fixed display area (~22 char visual limit). X-advance patched 24->14 but truncation persists at same character count. | All translated dialogue | HIGH -- blocks readability |
| 6D | Section 1 opcode patching | DISPLAY_TEXT opcodes use hardcoded byte offsets into Section 2. When Section 2 grows (English text longer), offsets break. | All type-2 variable-size injections (1B-1 especially) | CRITICAL -- blocks proper injection |
| 6E | Type-15 format bug (A2) | v2 pipeline introduces extra FFFF in type-15 resources, shifting all message indices. | 1A-5 (R39 equipment menu) | HIGH -- blocks R39 |
| 6F | EXE not in ISO | Patched EXE at build/patched_type2/SLPM_653.78 not written into ISO. | 2G, 2H, all EXE patches | MEDIUM -- all EXE work is wasted until injection |

---

## Priority Summary

### Tier 0: Prerequisites (must fix before anything else works)
1. **6A** Font atlas uppercase fix (T1) -- in progress, code ready
2. **6B** Punctuation glyph remapping (T2) -- in progress, code ready
3. **6D** Section 1 opcode offset patching -- needed for variable-size type-2 injection

### Tier 1: Blocks Gameplay (player cannot progress or use core features)
4. **1A-1** R38 stat/class/race labels (translations exist, verify injection)
5. **1B-1** R1198 early game scenes (translated but reverted; needs offset patching)
6. **2B** EXE chargen stat/attribute labels (hardcoded glyph table)
7. **2A** EXE name entry grid (kana -> Latin alphabet)
8. **1A-5** R39 equipment menu (fix type-15 injector first)
9. **1A-7** R40 location banners (translated but rendering blank)

### Tier 2: Highly Visible Japanese (player sees Japanese in main flow)
10. **1A-2** R43 tavern bartender dialogue (26 msgs, 0% translated)
11. **3A-3E** CockpitImg bar/guild textures (all menu buttons Japanese)
12. **1B-2** R1193/R1194 opening narration dialogue
13. **4A** Intro slideshow texture images
14. **6C** Text truncation fix (readability)

### Tier 3: Gap Resources and Mid-Game Content
15. **1B-3 to 1B-8** R1347-R1355 gap resources (~126 messages)
16. **1B-9 to 1B-12** R1100-R1190 range (~484 dialogue lines)
17. **1A-3** R45 remaining shop dialogue (28 msgs)
18. **1A-4** R48 shop tier names (wire existing translations)

### Tier 4: Late Game and Polish
19. **1B-13 to 1B-15** Late-game resources R2587, R2604, R2659 (~49 messages)
20. **2G-2H** EXE save slot names + continue prompt (already patched, need ISO injection)
21. **3F** Menu overlay texture R2124
22. **5A** Name entry tab labels (bitmap font 6400+ range)
23. **2C** EXE menu label pair structs
24. **2J** EXE type suffix table

### Tier 5: Cosmetic / Unconfirmed
25. **2I** Battle system strings (109, likely debug-only)
26. **2F** EXE NPC names (may be redundant with MSG)
27. **2K** Font width tables (dangerous to patch, reverted)
28. **2L** Misc EXE strings (~5)
29. **5B** MOJI.TMZ battle effect sprites (likely already English)
30. **5C** Victory/Defeat banners (unconfirmed if textured)
31. **1A-6** R37 remaining 2 messages
32. **3G** Other cockpit textures (tiny, likely icons)

---

## Estimated Scale

| Category | Items | Est. Strings | Status |
|----------|-------|-------------|--------|
| 1A: Type-1 MSG | 7 resources | ~700 messages | ~70% translated, injection issues |
| 1B: Type-2 embedded | 16 items | ~750 messages | ~15% translated, offset patching needed |
| 2: EXE hardcoded | 12 tables | ~500+ glyph IDs | ~5% patched |
| 3: CockpitImg | 7 textures | ~25 button/header labels | 0% done |
| 4: TextEventImage | 1 slideshow | ~5-10 slides | 0% done |
| 5: Bitmap font | 3 items | ~10 labels | 0% done |
| 6: Cross-cutting | 6 issues | N/A | 2 in progress |
