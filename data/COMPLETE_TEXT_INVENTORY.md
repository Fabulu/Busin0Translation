# COMPLETE TEXT INVENTORY: Busin 0 - Wizardry Alternative Neo

**Date**: 2026-05-22
**ISO**: Busin 0 - Wizardry Alternative Neo (Japan) (v2.01)
**Target**: Full English fan translation

---

## ISO File Structure

| File | Size | Contents | Text? |
|------|------|----------|-------|
| SLPM_653.78 | 4,185,776 bytes | PS2 EXE (game executable) | YES |
| PACKDATA.DIG | ~840 MB | All game resources (2,882 entries) | YES |
| BSN2_0.DSI | 63,176,704 bytes | MPEG-2 video (opening movie) | NO |
| TEMP1.LZH | 334,105,420 bytes | WAV audio (2ch, 44100Hz, 16-bit PCM) | NO |
| IOPRP254.IMG | 264,449 bytes | IOP processor boot image | NO |
| *.IRX (7 files) | ~500 KB total | IOP hardware driver modules | NO |
| SYSTEM.CNF | 54 bytes | Boot configuration | NO |

---

## CATEGORY 1: MSG Glyph-Encoded Text (PACKDATA type-01 resources)

**Encoding**: Custom 16-bit glyph index system (NOT Shift-JIS)
**Font**: 850+ glyph bitmaps in system font atlas
**Total messages**: 1,168 decoded across 21 resources
**STATUS**: TRANSLATED (1,129 of 1,168 messages have English translations)

### Resource Breakdown

| Resource | Messages | Content |
|----------|----------|---------|
| R34 | 29 | Item names (magic stones, equipment) |
| R35 | 23 | Menu labels, status terms |
| R36 | 156 | Spell names, skill descriptions |
| R37 | 18 | Race/class names |
| R38 | 177 | Game settings, reputation tiers, alignment terms |
| R39 | 84 | Equipment menu, inventory actions |
| R40 | 55 | Location names, dungeon floor names |
| R41 | 17 | Church dialogue (healing, resurrection) |
| R42 | 13 | Inn/tavern dialogue |
| R43 | 26 | Shop dialogue, buy/sell labels |
| R44 | 57 | Quest/request system text |
| R45 | 191 | Monster names |
| R46 | 7 | Bulletin board messages |
| R47 | 30 | NPC descriptions, party member traits |
| R48 | 107 | Dungeon location names, area labels |
| R49 | 109 | Dungeon event descriptions, story notes |
| R720 | 7 | Additional menu text |
| R1053 | 17 | Additional game data labels |
| R1908 | 8 | Late-game text |
| R2124 | 5 | Late-game text |
| R2654 | 32 | Late-game quest/event text |

### Translation Status

- **Translated files**: `data/translate_chunks/chunk_00_translated.json` through `chunk_09_translated.json`
- **Coverage**: 1,129 of 1,168 messages (96.7%)
- **Encoded output**: `data/encoded_translations.json` (185 entries with byte-encoded glyph sequences)
- **Supporting data**: `data/translations_items_monsters.json`, `data/translations_dungeon_story.json`

### Additional MSG Resources (not yet decoded)

The resource classification scan found 296 total MSG-structure resources in PACKDATA.DIG.
Only 21 of these have been decoded into the `full_decoded_text.json`.
The remaining ~275 MSG resources (R636, R638, R690, R702, R704, ... R2876) likely contain:
- Duplicate/variant text for different game states
- Additional item/monster data tables
- Battle result text
- Additional NPC dialogue triggers

**WORK REMAINING**: Decode and assess remaining 275 MSG resources for unique translatable content.

---

## CATEGORY 2: Type-2 Embedded Dialogue (Story/NPC conversations)

**Encoding**: Same 16-bit glyph system, embedded within type-02 scene/event resources
**Total resources with embedded dialogue**: 510
**Total embedded messages**: 177,086
**Total embedded dialogue bytes**: 151,425,568
**Resource index range**: R29 to R2659
**STATUS**: FOUND BUT NOT EXTRACTED OR TRANSLATED

### Scale

| Metric | Count |
|--------|-------|
| Resources with >50 messages | 235 |
| Resources with 10-50 messages | 149 |
| Resources with <10 messages | 126 |
| Total line_count sum | 29,398 |

### Highest-Volume Resources

| Resource | Messages | Lines | Size | Likely Content |
|----------|----------|-------|------|----------------|
| R2651 | 30,508 | 16 | 149 KB | Large data table (items/stats?) |
| R2653 | 18,162 | 91 | 68 KB | Data table |
| R1094 | 9,953 | 8 | 270 KB | Scene data |
| R1084 | 9,117 | 518 | 590 KB | Major story/dialogue scene |
| R1056 | 7,248 | 42 | 178 KB | Scene data |
| R2659 | 6,276 | 439 | 102 KB | Story dialogue |
| R1112 | 3,051 | 556 | 504 KB | Major story/dialogue scene |
| R1203 | 1,633 | 2,185 | 170 KB | Dense dialogue scene |
| R1148 | 1,843 | 181 | 129 KB | Dialogue scene |
| R1134 | 1,515 | 110 | 315 KB | Dialogue scene |

### Overlap with Category 1

Some type-02 resources (R29-R49) overlap with the already-decoded MSG resources.
These contain the same glyph data but embedded within larger scene containers.

**WORK REMAINING**: 
1. Build extractor for type-02 dialogue sections
2. Decode all 510 resources using established glyph map (428 mappings)
3. Identify unique translatable strings (many may be data tables, not dialogue)
4. Translate all story/NPC dialogue
5. Re-encode and patch back into resources

---

## CATEGORY 3: EXE Hardcoded Strings (SLPM_653.78)

**Encoding**: Shift-JIS in the EXE binary
**EXE size**: 4,185,776 bytes
**STATUS**: IDENTIFIED, NOT TRANSLATED

### String Counts

| Category | Count | Player-Visible? | Translation Priority |
|----------|-------|-----------------|---------------------|
| Battle system (Allied actions, skills) | 109 | YES - shown in battle UI | HIGH |
| Save/load labels | 5 | YES - memory card screens | HIGH |
| Debug/developer strings | 15 | NO - TTY output only | SKIP |
| Binary false positives | ~900 | NO - misinterpreted machine code | SKIP |
| Other genuine Japanese | ~10 | MAYBE - context-dependent | LOW |

### Battle System Strings (109 strings, 0x3EE9D0-0x3F3470)

These are Allied Action names and status messages displayed during combat:
- Skill names: W Slash, Front Guard, Stance Smash, Hold Attack, Rush, Cross Cage Kill, etc.
- Formation names: Scattered Formation, Dense Formation
- Tactical actions: Covering Fire, Support Fire, Magic Cancel, Breath Cancel, etc.
- Advanced combos: Sacred Cross, Warp Attack, Soul Crush, Sonic Sword, Nightmare Quake, etc.
- Status messages: "Allied Break", "Effect Level = %d", "Dispel Success!", "Dispel Failed!"

**NOTE**: Many of these battle strings may also exist in the MSG glyph system (Category 1).
Cross-reference needed to avoid double-translation.

### Save/Load Strings (5 strings, 0x3F8240-0x3FC790)

| Offset | Japanese | English |
|--------|----------|---------|
| 0x3F8240 | コンティニューロード！ | Continue Load! |
| 0x3F9370 | ＢＵＳＩＮ０中断データ | BUSIN 0 Suspend Data |
| 0x3FC750 | ＢＵＳＩＮ０データ１ | BUSIN 0 Data 1 |
| 0x3FC770 | ＢＵＳＩＮ０データ２ | BUSIN 0 Data 2 |
| 0x3FC790 | ＢＵＳＩＮ０データ３ | BUSIN 0 Data 3 |

### Other Player-Facing Strings

| Offset | Japanese | English | Notes |
|--------|----------|---------|-------|
| 0x3F8150 | ガーディアン戦闘！！ | Guardian Battle!! | Battle intro |
| 0x3F8260 | 取り付ける人がいないよ。 | No one to equip it on. | Equipment error |
| 0x3F8EF0 | そのようなＯＴはないです!!! | No such OT exists!!! | Error message |
| 0x3FC7F0 | 松野ゲー起動！！ | Matsuno Game Start!! | Developer credit |

**WORK REMAINING**:
1. Patch battle skill names in EXE (109 strings)
2. Patch save/load labels (5 strings)
3. Patch miscellaneous player-facing strings (~5 strings)
4. Ensure string length constraints are respected (fixed-size buffers in EXE)

---

## CATEGORY 4: Image-Based Text (TMX Textures)

**Format**: PS2 TMX/TIM2 texture format (4-bit and 8-bit indexed color)
**Location**: PACKDATA.DIG type-03 and type-04 resources
**Total type-03 (texture) resources**: 226
**Total type-04 (model/texture) resources**: 201
**STATUS**: IDENTIFIED, NOT CATALOGED

### Known Image-Text Elements

Based on screenshots and game analysis, the following UI elements contain rendered Japanese text as images:

1. **System font atlas** (glyph bitmaps for the MSG text system)
   - 850+ kanji/kana/symbol glyphs at ~12x12 or 16x16 pixels
   - Must be replaced with Latin alphabet glyphs for English
   - Already partially created: `build/english_font_atlas.bin`

2. **Menu button textures**
   - Main menu options (New Game, Continue, Options, etc.)
   - In-game menu buttons (Items, Magic, Equipment, Status, etc.)

3. **Location header banners**
   - Town area names displayed as decorative headers
   - Dungeon floor title cards

4. **Battle UI overlays**
   - "VICTORY", "DEFEAT", "LEVEL UP" banners
   - Allied Action name displays
   - Status effect icons with text labels

5. **Shop/Inn/Church UI frames**
   - Price labels, service descriptions
   - Menu option text within decorated frames

6. **Title screen / Logo**
   - Game title (may keep Japanese or add English subtitle)
   - Copyright notices

7. **Name entry screen**
   - Hiragana/katakana grid (existing screenshots confirm this)
   - Mode labels (ひらがな/カタカナ/etc.)
   - Needs replacement with Latin alphabet input grid

**WORK REMAINING**:
1. Extract and catalog all type-03 texture resources
2. Identify which textures contain text vs. pure artwork
3. Create English replacement textures (pixel art / font rendering)
4. Handle CLUT (palette) preservation during replacement
5. Re-encode as TMX and patch into PACKDATA.DIG

---

## CATEGORY 5: FMV Video (BSN2_0.DSI)

**Format**: Custom PS2 container wrapping MPEG-2 video stream
**Size**: 63,176,704 bytes (60.2 MB)
**Header**: 64-byte custom header, MPEG data starts at offset 0x40
**STATUS**: ANALYZED - NO TEXT CONTENT

### Analysis Results

- MPEG-2 video stream confirmed (sequence headers, GOP headers present)
- No Private Stream 1 packets (subtitle stream) detected
- SJIS byte pair distribution is uniform across all 60MB (random noise from video data)
- Single continuous video stream (one sequence header at 0x40)

### Conclusion

The opening movie is a pure video stream with no embedded text overlays or subtitle tracks.
If the movie contains any visible text, it is burned into the video frames themselves (hard-subtitled).
This would require frame-by-frame video editing to modify -- extremely low priority.

**WORK REMAINING**: Watch the opening movie to confirm whether any text is burned into frames.
If yes, decide whether to re-encode the video or leave Japanese text in the cinematic.

---

## CATEGORY 6: Audio (TEMP1.LZH)

**Format**: WAV audio (RIFF container)
**Specs**: 2 channels, 44100 Hz, 16-bit PCM
**Size**: 334,105,420 bytes (318.6 MB)
**STATUS**: NO TEXT

Despite the .LZH extension, this file is a standard WAV audio file containing the game's
streaming audio (music and/or voice). No text content.

**NOTE**: If this contains Japanese voice acting, dubbing/subtitling would be a separate project
far beyond the scope of text translation.

---

## CATEGORY 7: System Files (No Text)

| File | Purpose | Text? |
|------|---------|-------|
| IOPRP254.IMG | IOP boot ROM replacement image | NO |
| SIO2MAN.IRX | Serial I/O manager driver | NO |
| PADMAN.IRX | Controller driver | NO |
| MCMAN.IRX | Memory card filesystem driver | NO |
| MCSERV.IRX | Memory card server driver | NO |
| LIBSD.IRX | Sound driver | NO |
| MODMIDI.IRX | MIDI module | NO |
| MODHSYN.IRX | Hardware synthesizer module | NO |
| MODMSIN.IRX | Software synthesizer module | NO |
| MUS.IRX | Music streaming module | NO |
| SYSTEM.CNF | Boot configuration (BOOT2, VER, VMODE) | NO |

---

## CATEGORY 8: PACKDATA.DIG Resource Type Summary

| Type | Count | Contents | Text? |
|------|-------|----------|-------|
| 01 | 1,642 | MSG glyph data, game data tables | YES (296 have MSG structure) |
| 02 | 617 | Scene/event containers with embedded dialogue | YES (510 have dialogue) |
| 03 | 226 | Textures (TMX format) | SOME (UI textures with text) |
| 04 | 201 | 3D models with textures | SOME (model textures may have text) |
| 05 | 33 | Animation data | NO |
| 06 | 46 | Effect/mixed data | UNLIKELY |
| 07 | 10 | Unknown | UNLIKELY |
| 08 | 16 | Unknown | UNLIKELY |
| 09 | 4 | Unknown | UNLIKELY |
| 10 | 11 | Data tables | MAYBE |
| 11 | 7 | Unknown | UNLIKELY |
| 12 | 15 | Unknown | UNLIKELY |
| 13-181 | 38 | Various rare types | UNLIKELY |
| **Total** | **2,882** | | |

---

## MASTER SUMMARY

| # | Category | Items | Status | Priority | Effort |
|---|----------|-------|--------|----------|--------|
| 1 | MSG glyph text (R34-R49 + extras) | 1,168 messages | 96.7% TRANSLATED | DONE | Low |
| 2 | Embedded dialogue (510 resources) | ~177,086 messages | NOT STARTED | CRITICAL | Very High |
| 3 | EXE battle strings | 109 strings | IDENTIFIED | HIGH | Low |
| 4 | EXE save/load + misc strings | ~15 strings | IDENTIFIED | HIGH | Low |
| 5 | Image-based UI text (textures) | Unknown count | NOT CATALOGED | HIGH | High |
| 6 | System font atlas replacement | 850+ glyphs | IN PROGRESS | CRITICAL | Medium |
| 7 | Name entry screen | 1 screen | IDENTIFIED | MEDIUM | Medium |
| 8 | FMV video text | 0 (none found) | COMPLETE | N/A | N/A |
| 9 | Remaining MSG resources (275) | Unknown | NOT ASSESSED | MEDIUM | Medium |

### Critical Path

1. **Font atlas**: Replace Japanese glyph bitmaps with English characters (in progress)
2. **Category 2 extraction**: Build tools to extract embedded dialogue from type-02 resources
3. **Category 2 translation**: Translate the ~29,398 dialogue lines (the bulk of the game)
4. **Category 5 textures**: Create English UI textures for menus, buttons, labels
5. **Category 3-4 EXE patching**: Patch hardcoded strings in the executable
6. **Integration**: Rebuild PACKDATA.DIG and create patched ISO

### Estimated Total Translatable Text

| Source | Estimated Strings | Estimated Characters |
|--------|-------------------|---------------------|
| MSG glyph text | 1,168 | ~15,000 |
| Embedded dialogue | ~29,398 lines | ~500,000+ |
| EXE strings | ~130 | ~2,000 |
| Image text | ~50-100 labels | ~500 |
| **TOTAL** | **~30,800+** | **~520,000+** |
